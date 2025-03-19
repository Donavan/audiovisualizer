import os
import logging
import tempfile
from typing import Optional, Dict, List, Tuple, Union

from .ffmpeg_utils import FFmpegProcessor
from .audio_analysis import AudioAnalyzer
from .effects import EffectRegistry

logger = logging.getLogger(__name__)

class AudioVisualizer:
    """
    Main class for creating audio-reactive video overlays using FFmpeg.
    This class orchestrates the process of analyzing audio and applying visual effects.
    """
    
    def __init__(self, input_path: str):
        """
        Initialize the AudioVisualizer with an input media file.
        
        Args:
            input_path: Path to the input audio or video file
        """
        self.input_path = input_path
        self.output_path = None
        self.effects = []
        self.temp_files = []
        self.ffmpeg = FFmpegProcessor()
        self.audio_analyzer = AudioAnalyzer()
        self.effect_registry = EffectRegistry()
        
        # Validate input file exists
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
            
        logger.info(f"Initialized AudioVisualizer with input: {input_path}")
    
    def add_effect(self, effect_type: str, **kwargs):
        """
        Add a visual effect to be applied to the video.
        
        Args:
            effect_type: Type of effect to add (e.g., 'text', 'logo', 'waveform')
            **kwargs: Effect-specific parameters
        
        Returns:
            self for method chaining
        """
        effect = self.effect_registry.create_effect(effect_type, **kwargs)
        self.effects.append(effect)
        logger.debug(f"Added {effect_type} effect")
        return self
    
    def process(self):
        """
        Process the input media and prepare all effects for rendering.
        This analyzes the audio and prepares the FFmpeg filter chain.
        
        Returns:
            self for method chaining
        """
        # Extract audio features if we have effects that require them
        if any(effect.requires_audio_analysis for effect in self.effects):
            self.audio_analyzer.analyze(self.input_path)
            
        # Prepare each effect
        for effect in self.effects:
            effect.prepare(self.audio_analyzer)
            
        # Build the FFmpeg filter chain
        self.ffmpeg.build_filter_chain(self.input_path, self.effects)
        
        logger.info("Processing complete, ready for export")
        return self
    
    def export(self, output_path: str, **kwargs):
        """
        Export the processed video to the specified output path.
        
        Args:
            output_path: Path where the output video will be saved
            **kwargs: Export parameters like codec, bitrate, etc.
            
        Returns:
            Path to the exported file
        """
        self.output_path = output_path
        
        # Execute the FFmpeg command
        self.ffmpeg.execute(output_path, **kwargs)
        
        # Clean up any temporary files
        self._cleanup()
        
        logger.info(f"Export complete: {output_path}")
        return output_path
    
    def preview(self, duration: Optional[float] = 10.0):
        """
        Generate a preview of the video with the current effects.
        
        Args:
            duration: Duration of the preview in seconds
            
        Returns:
            Path to the temporary preview file
        """
        # Create a temporary file for the preview
        fd, preview_path = tempfile.mkstemp(suffix='.mp4')
        os.close(fd)
        self.temp_files.append(preview_path)
        
        # Generate a shorter preview using the same filter chain
        self.ffmpeg.execute(preview_path, duration=duration, preview=True)
        
        logger.info(f"Preview generated: {preview_path}")
        return preview_path
    
    def _cleanup(self):
        """
        Clean up temporary files created during processing.
        """
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {temp_file}: {e}")
                
        self.temp_files = []
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup()