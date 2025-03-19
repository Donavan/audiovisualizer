import os
import subprocess
import logging
import json
from typing import List, Dict, Optional, Union, Tuple

logger = logging.getLogger(__name__)

class FFmpegProcessor:
    """
    Handles FFmpeg command generation and execution for audio-reactive video processing.
    """
    
    def __init__(self):
        self.filter_complex = []
        self.input_path = None
        self.input_args = []
        self.output_args = []
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """
        Check if FFmpeg is installed and available.
        Raises RuntimeError if FFmpeg is not found.
        """
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            if result.returncode != 0:
                raise RuntimeError("FFmpeg is not properly installed or accessible")
            logger.debug("FFmpeg found and available")
        except FileNotFoundError:
            raise RuntimeError("FFmpeg is not installed or not in PATH")
    
    def build_filter_chain(self, input_path: str, effects: List):
        """
        Build the FFmpeg filter complex chain based on the input and effects.
        
        Args:
            input_path: Path to the input media file
            effects: List of effect objects to be applied
        """
        self.input_path = input_path
        self.filter_complex = []
        
        # Start with the input stream
        input_stream = "0:v"
        
        # Add each effect's filter to the chain
        for i, effect in enumerate(effects):
            filter_str = effect.get_filter_string()
            if filter_str:
                output_label = f"v{i+1}"
                self.filter_complex.append(f"[{input_stream}]{filter_str}[{output_label}]")
                input_stream = output_label
        
        logger.debug(f"Built filter chain with {len(effects)} effects")
    
    def execute(self, output_path: str, duration: Optional[float] = None, preview: bool = False, **kwargs):
        """
        Execute the FFmpeg command with the built filter chain.
        
        Args:
            output_path: Path where the output video will be saved
            duration: Optional duration limit for the output
            preview: Whether this is a preview render (lower quality/faster)
            **kwargs: Additional FFmpeg parameters
        
        Returns:
            subprocess.CompletedProcess object with the result of the FFmpeg execution
        """
        if not self.input_path or not self.filter_complex:
            raise ValueError("No input path or filter chain set")
        
        # Basic command structure
        cmd = ["ffmpeg", "-y"]
        
        # Add input file
        cmd.extend(["-i", self.input_path])
        
        # Add duration limit if specified
        if duration is not None:
            cmd.extend(["-t", str(duration)])
        
        # Add filter complex
        if self.filter_complex:
            filter_str = ";".join(self.filter_complex)
            cmd.extend(["-filter_complex", filter_str])
            # Map the last output to the video output stream
            last_output = self.filter_complex[-1].split(']')[-1].strip('[]')
            cmd.extend(["-map", f"[{last_output}]"])
        
        # Map audio stream from input if available
        cmd.extend(["-map", "0:a?"])
        
        # Set output codec options based on whether this is a preview
        if preview:
            # For preview: faster encoding, lower quality
            cmd.extend([
                "-c:v", "libx264", 
                "-preset", "ultrafast", 
                "-crf", "28"
            ])
        else:
            # For final output: better quality
            cmd.extend([
                "-c:v", "libx264", 
                "-preset", "medium", 
                "-crf", "23"
            ])
        
        # Add any custom output arguments from kwargs
        for key, value in kwargs.items():
            if key in ["codec", "c", "c:v"]:
                cmd.extend(["-c:v", value])
            elif key in ["preset"]:
                cmd.extend(["-preset", value])
            elif key in ["crf", "quality"]:
                cmd.extend(["-crf", str(value)])
            elif key in ["bitrate", "b", "b:v"]:
                cmd.extend(["-b:v", value])
        
        # Add output path
        cmd.append(output_path)
        
        # Execute the command
        logger.info(f"Executing FFmpeg command: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            logger.debug("FFmpeg execution complete")
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg execution failed: {e.stderr}")
            raise RuntimeError(f"FFmpeg execution failed: {e.stderr}") from e
    
    def get_media_info(self, media_path: str) -> Dict:
        """
        Get detailed information about a media file using FFprobe.
        
        Args:
            media_path: Path to the media file
            
        Returns:
            Dictionary containing the media file information
        """
        cmd = [
            "ffprobe", 
            "-v", "quiet", 
            "-print_format", "json", 
            "-show_format", 
            "-show_streams", 
            media_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"Failed to get media info: {e}")
            raise RuntimeError(f"Failed to get media info: {e}") from e