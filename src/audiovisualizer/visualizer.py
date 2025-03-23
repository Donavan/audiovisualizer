# AudioVisualizer - Main Class
# Orchestrates audio analysis and video processing with effects

import os
import tempfile
import json
import logging
from typing import List, Dict, Any, Optional, Union, Tuple

from .ffmpeg_utils import FFmpegProcessor
from .ffmpeg_filter_graph import FilterGraph

logger = logging.getLogger(__name__)


class AudioVisualizer:
    """Main class for audio-reactive video processing."""
    
    def __init__(self, ffmpeg_path: str = 'ffmpeg', ffprobe_path: str = 'ffprobe'):
        """Initialize the AudioVisualizer.
        
        Args:
            ffmpeg_path: Path to FFmpeg executable
            ffprobe_path: Path to FFprobe executable
        """
        self.ffmpeg = FFmpegProcessor(self, ffmpeg_path, ffprobe_path)
        self.input_path = None
        self.effects = []
        self.audio_analyzer = None  # Will implement later
        self.temp_files = []
        
    def load_media(self, path: str) -> 'AudioVisualizer':
        """Load a media file for processing.
        
        Args:
            path: Path to the media file
            
        Returns:
            Self for method chaining
        """
        if not os.path.exists(path):
            raise ValueError(f"Input file does not exist: {path}")
            
        self.input_path = path
        return self
    
    def add_effect(self, effect_type: str, effect_params: Dict[str, Any]) -> 'AudioVisualizer':
        """Add an effect to the processing pipeline.
        
        Args:
            effect_type: Type of effect ('logo', 'text', 'spectrum', etc.)
            effect_params: Parameters for the effect
            
        Returns:
            Self for method chaining
        """
        # Create a simple effect dictionary
        # In a real implementation, this would create proper Effect objects
        effect = {
            'type': effect_type,
            **effect_params
        }
        
        self.effects.append(effect)
        return self
    
    def process(self, output_path: str, extra_args: Optional[List[str]] = None) -> str:
        """Process the input media with all added effects.
        
        Args:
            output_path: Path for the output video
            extra_args: Optional extra FFmpeg arguments
            
        Returns:
            Path to the output video
        """
        if not self.input_path:
            raise ValueError("No input media loaded. Call load_media() first.")
            
        # Build the filter chain
        filter_chain = self.ffmpeg.build_complex_filter(self.effects)
        logger.debug(f"Generated filter chain: {filter_chain}")
        
        # Process the video
        self.ffmpeg.process_video(self.input_path, output_path, filter_chain, extra_args)
        
        return output_path
    
    def create_filter_graph(self) -> FilterGraph:
        """Create a new filter graph for manual configuration.
        
        Returns:
            A new FilterGraph instance
        """
        return self.ffmpeg.create_filter_graph()
    
    def process_with_filter_graph(self, graph: FilterGraph, output_path: str, 
                                extra_args: Optional[List[str]] = None) -> str:
        """Process the input media with a custom filter graph.
        
        Args:
            graph: The FilterGraph to use
            output_path: Path for the output video
            extra_args: Optional extra FFmpeg arguments
            
        Returns:
            Path to the output video
        """
        if not self.input_path:
            raise ValueError("No input media loaded. Call load_media() first.")
            
        # Convert the graph to a filter chain string
        filter_chain = graph.to_filter_string()
        logger.debug(f"Using custom filter chain: {filter_chain}")
        
        # Process the video
        self.ffmpeg.process_video(self.input_path, output_path, filter_chain, extra_args)
        
        return output_path

    def save_config(self, path: str) -> None:
        """Save the current configuration to a file.

        Args:
            path: Path to save the configuration
        """
        config = {
            'input_path': self.input_path,
            'effects': self.effects,
        }

        with open(path, 'w') as f:
            json_str = json.dumps(config, indent=2)
            f.write(json_str)

        logger.info(f"Configuration saved to {path}")
    
    def load_config(self, path: str) -> 'AudioVisualizer':
        """Load configuration from a file.
        
        Args:
            path: Path to the configuration file
            
        Returns:
            Self for method chaining
        """
        with open(path, 'r') as f:
            config = json.load(f)
            
        self.input_path = config.get('input_path')
        self.effects = config.get('effects', [])
        
        logger.info(f"Configuration loaded from {path}")
        return self
    
    def cleanup(self) -> None:
        """Clean up temporary files."""
        for file_path in self.temp_files:
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Could not remove temporary file {file_path}: {e}")
                
        self.temp_files = []
        
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()


def process_video(input_path: str, output_path: str, effects: List[Dict[str, Any]], 
                 ffmpeg_path: str = 'ffmpeg', ffprobe_path: str = 'ffprobe') -> str:
    """Convenience function to process a video with effects.
    
    Args:
        input_path: Path to the input video
        output_path: Path for the output video
        effects: List of effect dictionaries
        ffmpeg_path: Path to FFmpeg executable
        ffprobe_path: Path to FFprobe executable
        
    Returns:
        Path to the output video
    """
    visualizer = AudioVisualizer(ffmpeg_path, ffprobe_path)
    visualizer.load_media(input_path)
    
    for effect in effects:
        effect_type = effect.pop('type')
        visualizer.add_effect(effect_type, effect)
    
    return visualizer.process(output_path)