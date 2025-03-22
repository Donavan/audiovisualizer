"""FFmpeg utility functions for audio-visual processing.

This module provides utilities for handling FFmpeg operations including command
generation, execution, and processing of audio and video files.
"""

import os
import subprocess
import tempfile
import logging
import json
import shlex
from typing import Dict, List, Optional, Tuple, Union, Any
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ffmpeg_utils')

class FFmpegError(Exception):
    """Exception raised for errors in FFmpeg operations."""
    pass

class FFmpegProcessor:
    """Handles FFmpeg operations for video processing.
    
    This class encapsulates FFmpeg command generation, execution, and result processing.
    
    Attributes:
        ffmpeg_path (str): Path to the FFmpeg executable.
        ffprobe_path (str): Path to the FFprobe executable.
        temp_dir (str): Directory for temporary files.
    """
    
    def __init__(self, 
                 ffmpeg_path: str = 'ffmpeg', 
                 ffprobe_path: str = 'ffprobe',
                 temp_dir: Optional[str] = None):
        """Initialize FFmpegProcessor.
        
        Args:
            ffmpeg_path: Path to the FFmpeg executable. Defaults to 'ffmpeg'.
            ffprobe_path: Path to the FFprobe executable. Defaults to 'ffprobe'.
            temp_dir: Directory for temporary files. If None, system temp directory is used.
        """
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self._validate_ffmpeg()
    
    def _validate_ffmpeg(self) -> None:
        """Validate that FFmpeg and FFprobe are available and executable."""
        try:
            subprocess.run(
                [self.ffmpeg_path, '-version'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                check=True
            )
            subprocess.run(
                [self.ffprobe_path, '-version'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                check=True
            )
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            raise FFmpegError(
                f"FFmpeg tools not found or not executable. Please ensure FFmpeg is installed. Error: {str(e)}"
            )
    
    async def get_media_info(self, file_path: str) -> Dict[str, Any]:
        """Get detailed information about a media file.
        
        Args:
            file_path: Path to the media file.
            
        Returns:
            A dictionary containing media file information.
            
        Raises:
            FFmpegError: If FFprobe command fails or file doesn't exist.
        """
        if not os.path.exists(file_path):
            raise FFmpegError(f"File not found: {file_path}")
        
        cmd = [
            self.ffprobe_path,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise FFmpegError(f"FFprobe command failed: {stderr.decode()}")
            
            return json.loads(stdout.decode())
        except Exception as e:
            raise FFmpegError(f"Failed to get media info: {str(e)}")
    
    async def extract_audio(self, video_path: str, output_path: Optional[str] = None) -> str:
        """Extract audio from a video file.
        
        Args:
            video_path: Path to the input video file.
            output_path: Path for the output audio file. If None, a temporary file is created.
            
        Returns:
            Path to the extracted audio file.
            
        Raises:
            FFmpegError: If FFmpeg command fails or input file doesn't exist.
        """
        if not os.path.exists(video_path):
            raise FFmpegError(f"Video file not found: {video_path}")
        
        if output_path is None:
            output_path = os.path.join(
                self.temp_dir, 
                f"{os.path.splitext(os.path.basename(video_path))[0]}_audio.wav"
            )
        
        cmd = [
            self.ffmpeg_path,
            '-i', video_path,
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # PCM 16-bit little-endian format
            '-ar', '44100',  # 44.1kHz sample rate
            '-y',  # Overwrite output file if it exists
            output_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise FFmpegError(f"FFmpeg audio extraction failed: {stderr.decode()}")
            
            return output_path
        except Exception as e:
            raise FFmpegError(f"Failed to extract audio: {str(e)}")

    def sanitize_filter_chain(self, filter_chain: str) -> str:
        """Sanitize a filter chain string by removing redundant parts.

        Args:
            filter_chain: The filter chain string to sanitize.

        Returns:
            A sanitized filter chain string.
        """
        # Remove empty filter chains
        if not filter_chain or not filter_chain.strip():
            return ""

        chain = filter_chain.strip()

        # Skip chains that are just input/output labels without actual filters
        if chain.count('[') >= 2 and ']' in chain and not any(op in chain for op in 
                                                             ['=', 'filter', 'scale', 'overlay', 
                                                              'drawtext', 'movie', 'color']):
            return ""

        return chain

    def build_complex_filter(self, filter_chains: List[str]) -> str:
        """Build a complex filtergraph string that properly chains filters.

        Args:
            filter_chains: List of filter chain strings.

        Returns:
            A complete complex filtergraph string.

        Raises:
            FFmpegError: If filter chains cannot be properly connected.
        """
        # If there are no filter chains, return an empty string
        if not filter_chains:
            return ""

        # Filter out empty chains and properly clean each chain
        valid_chains = [self.sanitize_filter_chain(chain) for chain in filter_chains]
        valid_chains = [chain for chain in valid_chains if chain]

        # If there are no valid chains after cleaning, return an empty string
        if not valid_chains:
            return ""

        # Prepare the initial format filter to establish the main input
        # This standardizes the input format and establishes [main] as our starting point
        result = ["[0:v]format=yuv420p,setpts=PTS-STARTPTS[main]"]

        # If we only have one filter chain, it needs to start with [main] and end with [out]
        if len(valid_chains) == 1:
            chain = valid_chains[0]
            
            # Extract the filter part (remove input/output labels if present)
            filter_parts = chain.split(']')
            if len(filter_parts) > 1 and '[' in filter_parts[0]:
                # This chain has input/output labels, so we need to adjust them
                filter_content = filter_parts[-1].strip()
                # Only append if there's actual filter content
                if filter_content:
                    result.append(f"[main]{filter_content}[out]")
            else:
                # No labels, so wrap the filter content with [main] and [out]
                result.append(f"[main]{chain}[out]")
        else:
            # For multiple chains, we need to create a sequence of labeled inputs/outputs
            current_input = "main"
            
            for i, chain in enumerate(valid_chains):
                # Determine the output label for this filter
                output_label = "out" if i == len(valid_chains) - 1 else f"tmp{i}"
                
                # Extract filter content (remove input/output labels if present)
                filter_parts = chain.split(']')
                if len(filter_parts) > 1 and '[' in filter_parts[0]:
                    # This chain has input/output labels, so we extract just the filter content
                    filter_content = filter_parts[-1].strip()
                    # Only append if there's actual filter content
                    if filter_content:
                        result.append(f"[{current_input}]{filter_content}[{output_label}]")
                        current_input = output_label
                else:
                    # No labels, so use the whole chain as filter content
                    result.append(f"[{current_input}]{chain}[{output_label}]")
                    current_input = output_label

        # Join all filter parts with semicolons
        return ";".join(result)
    
    def build_overlay_filter(self,
                           main_input: str,
                           overlay_input: str,
                           x: Union[int, str],
                           y: Union[int, str],
                           when: Optional[str] = None) -> str:
        """Build a filter string for overlaying one video on another.
        
        Args:
            main_input: Label for the main input stream.
            overlay_input: Label for the overlay input stream.
            x: X-coordinate for overlay position.
            y: Y-coordinate for overlay position.
            when: Optional expression for conditional overlay.
            
        Returns:
            Filter string for overlay operation.
        """
        overlay = f"[{main_input}][{overlay_input}]overlay=x={x}:y={y}"
        if when:
            overlay += f":enable='{when}'"
        return overlay
    
    async def run_ffmpeg_command(self, command: List[str]) -> None:
        """Execute an FFmpeg command with the given arguments.
        
        Args:
            command: List of command arguments (excluding the FFmpeg executable).
            
        Raises:
            FFmpegError: If FFmpeg command fails.
        """
        full_command = [self.ffmpeg_path] + command
        logger.info(f"Running FFmpeg command: {shlex.join(full_command)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise FFmpegError(f"FFmpeg command failed: {stderr.decode()}")
        except Exception as e:
            raise FFmpegError(f"Failed to execute FFmpeg command: {str(e)}")
    
    async def apply_effects(self,
                         input_path: str,
                         output_path: str,
                         complex_filter: str,
                         audio_options: Optional[List[str]] = None,
                         video_options: Optional[List[str]] = None) -> None:
        """Apply a complex filter to process a video with effects.
        
        Args:
            input_path: Path to the input video file.
            output_path: Path for the output processed video.
            complex_filter: Complex filtergraph string.
            audio_options: List of audio encoding options.
            video_options: List of video encoding options.
            
        Raises:
            FFmpegError: If FFmpeg command fails or input file doesn't exist.
        """
        if not os.path.exists(input_path):
            raise FFmpegError(f"Input file not found: {input_path}")
        
        cmd = ['-i', input_path]
        
        # Add complex filter
        cmd.extend(['-filter_complex', complex_filter])
        
        # Add audio options if provided
        if audio_options:
            cmd.extend(audio_options)
        
        # Add video options if provided
        if video_options:
            cmd.extend(video_options)
        
        # Output file
        cmd.extend(['-y', output_path])
        
        await self.run_ffmpeg_command(cmd)
    
    async def create_text_overlay(self, 
                            text: str, 
                            font_path: str,
                            font_size: int,
                            font_color: str,
                            output_path: str,
                            width: int,
                            height: int,
                            bg_color: Optional[str] = None,
                            box_opacity: float = 0.0) -> str:
        """Create a transparent PNG with text for overlay.
        
        Args:
            text: Text to display.
            font_path: Path to TTF font file.
            font_size: Font size in points.
            font_color: Font color in hexadecimal format (#RRGGBB).
            output_path: Path for the output image.
            width: Width of the output image.
            height: Height of the output image.
            bg_color: Optional background color.
            box_opacity: Opacity for the background box (0.0-1.0).
            
        Returns:
            Path to the created text overlay image.
            
        Raises:
            FFmpegError: If FFmpeg command fails.
        """
        # Ensure font path exists
        if not os.path.exists(font_path):
            raise FFmpegError(f"Font file not found: {font_path}")
        
        # Prepare filter for text
        filter_text = f"color=s={width}x{height}:color=black@0"
        
        # Add background box if needed
        if bg_color and box_opacity > 0:
            # Calculate box dimensions based on text
            box_padding = font_size // 2
            box_w = width - (box_padding * 2)
            box_h = font_size + box_padding
            box_x = box_padding
            box_y = (height - box_h) // 2
            box_color = f"{bg_color}@{box_opacity}"
            
            filter_text += f",drawbox=x={box_x}:y={box_y}:w={box_w}:h={box_h}:color={box_color}:t=fill"
        
        # Add text
        filter_text += (f",drawtext=text='{text}':fontfile='{font_path}':fontsize={font_size}:"
                      f"fontcolor={font_color}:x=(w-text_w)/2:y=(h-text_h)/2")
        
        cmd = [
            '-f', 'lavfi',
            '-i', filter_text,
            '-frames:v', '1',
            '-y',
            output_path
        ]
        
        await self.run_ffmpeg_command(cmd)
        return output_path
    
    def cleanup_temp_files(self, file_paths: List[str]) -> None:
        """Clean up temporary files created during processing.
        
        Args:
            file_paths: List of file paths to remove.
        """
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Removed temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {file_path}: {str(e)}")