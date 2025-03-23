# FFmpeg Utilities
# Handles FFmpeg command execution and filter chain generation

import subprocess
import os
import json
import tempfile
import logging
from typing import List, Dict, Any, Optional, Union, Tuple

from .ffmpeg_filter_graph import FilterGraph
from .ffmpeg_effect_mapper import EffectFilterMapper

logger = logging.getLogger(__name__)


class FFmpegProcessor:
    """Handles FFmpeg command execution and filter chain generation."""
    
    def __init__(self, visualizer, ffmpeg_path='ffmpeg', ffprobe_path='ffprobe'):
        """Initialize the FFmpeg processor.
        
        Args:
            visualizer: The AudioVisualizer instance
            ffmpeg_path: Path to FFmpeg executable
            ffprobe_path: Path to FFprobe executable
        """
        self.visualizer = visualizer
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self.mapper = None
    
    def build_complex_filter(self, effects: List) -> str:
        """Build a complex filter chain from a list of effects.

        Args:
            effects: List of Effect objects.

        Returns:
            A properly formatted FFmpeg filtergraph string.
        """
        self.mapper = EffectFilterMapper(self.visualizer)

        for effect in effects:
            self.mapper.add_effect(effect)

        return self.mapper.build_filter_chain()
    
    def build_complex_filter_from_strings(self, filter_chains: List[str]) -> str:
        """Build a complex filter chain from a list of filter strings (legacy method).

        Args:
            filter_chains: List of filter chain strings.

        Returns:
            A properly formatted FFmpeg filtergraph string.
        """
        from .ffmpeg_filter_graph.converters import FilterGraphParser
        
        # Parse the filter strings and create a FilterGraph
        graph = FilterGraphParser.parse_filter_chains(filter_chains)

        # Return the properly formatted string
        return graph.to_filter_string()
    
    def get_media_info(self, media_path: str) -> Dict[str, Any]:
        """Get information about a media file.
        
        Args:
            media_path: Path to the media file
            
        Returns:
            Dictionary containing media information
        """
        cmd = [
            self.ffprobe_path,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            media_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting media info: {e}")
            logger.error(f"FFprobe stderr: {e.stderr}")
            raise ValueError(f"Could not get media info for {media_path}: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing media info: {e}")
            raise ValueError(f"Could not parse media info for {media_path}: {e}")
    
    def extract_audio(self, video_path: str, output_path: Optional[str] = None) -> str:
        """Extract audio from a video file.
        
        Args:
            video_path: Path to the video file
            output_path: Optional path for the output audio file
            
        Returns:
            Path to the extracted audio file
        """
        if output_path is None:
            # Generate temporary file path with .wav extension
            output_path = tempfile.mktemp(suffix='.wav')
            
        cmd = [
            self.ffmpeg_path,
            '-i', video_path,
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # PCM 16-bit LE audio codec
            '-ar', '44100',  # 44.1 kHz sample rate
            '-y',  # Overwrite output
            output_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Error extracting audio: {e}")
            logger.error(f"FFmpeg stderr: {e.stderr}")
            raise ValueError(f"Could not extract audio from {video_path}: {e}")
    
    def process_video(self, input_path: str, output_path: str, filter_chain: str, 
                      extra_args: Optional[List[str]] = None) -> None:
        """Process a video with a filter chain.
        
        Args:
            input_path: Path to the input video
            output_path: Path for the output video
            filter_chain: FFmpeg filter chain string
            extra_args: Optional extra FFmpeg arguments
        """
        cmd = [
            self.ffmpeg_path,
            '-i', input_path,
            '-filter_complex', filter_chain,
            '-map', '[out]',  # Map the output from the filter chain
            '-c:v', 'libx264',  # Use H.264 codec
            '-preset', 'medium',  # Medium preset for speed/quality balance
            '-crf', '23',  # Constant Rate Factor for quality
            '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
            '-y'  # Overwrite output
        ]
        
        if extra_args:
            cmd.extend(extra_args)
            
        cmd.append(output_path)
        
        try:
            logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            subprocess.run(cmd, capture_output=True, check=True)
            logger.info(f"Video processing complete: {output_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error processing video: {e}")
            logger.error(f"FFmpeg stderr: {e.stderr}")
            raise ValueError(f"Could not process video {input_path}: {e}")
    
    def create_filter_graph(self) -> FilterGraph:
        """Create a new filter graph.
        
        Returns:
            A new FilterGraph instance
        """
        return FilterGraph()