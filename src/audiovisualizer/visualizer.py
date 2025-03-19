"""Main AudioVisualizer module for creating audio-reactive visual effects.

This module provides the main AudioVisualizer class that orchestrates the
process of creating audio-reactive visual effects for videos.
"""

import os
import tempfile
import json
import asyncio
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple, Union, Any, Callable

from .ffmpeg_utils import FFmpegProcessor, FFmpegError
from .audio_analysis import AudioAnalyzer, AudioAnalysisError
from .effects import BaseEffect, create_effect, effect_from_dict

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('audiovisualizer')

class AudioVisualizer:
    """Main class for creating audio-reactive visual effects.
    
    This class orchestrates the process of analyzing audio, applying visual effects,
    and generating the final output video with effects synchronized to audio features.
    
    Attributes:
        input_path (str): Path to the input video file.
        output_path (str): Path for the output processed video.
        temp_dir (str): Directory for temporary files.
        effects (list): List of visual effects to apply.
        fps (float): Frames per second of the video.
        width (int): Width of the video.
        height (int): Height of the video.
    """
    
    def __init__(self, 
                 input_path: str, 
                 output_path: Optional[str] = None,
                 temp_dir: Optional[str] = None,
                 ffmpeg_path: str = 'ffmpeg',
                 ffprobe_path: str = 'ffprobe'):
        """Initialize AudioVisualizer.
        
        Args:
            input_path: Path to the input video file.
            output_path: Path for the output processed video. If None, one is generated.
            temp_dir: Directory for temporary files. If None, system temp directory is used.
            ffmpeg_path: Path to the FFmpeg executable. Defaults to 'ffmpeg'.
            ffprobe_path: Path to the FFprobe executable. Defaults to 'ffprobe'.
            
        Raises:
            ValueError: If input file doesn't exist.
        """
        if not os.path.exists(input_path):
            raise ValueError(f"Input file not found: {input_path}")
        
        self.input_path = input_path
        self.output_path = output_path or self._generate_output_path(input_path)
        self.temp_dir = temp_dir or tempfile.gettempdir()
        
        # Initialize processors
        self.ffmpeg = FFmpegProcessor(ffmpeg_path, ffprobe_path, self.temp_dir)
        self.audio_analyzer = AudioAnalyzer()
        
        # Video properties
        self.fps = 30.0
        self.width = 1280
        self.height = 720
        self.duration = 0.0
        
        # List of effects to apply
        self.effects: List[BaseEffect] = []
        
        # Temporary files to clean up
        self._temp_files = []
        
        # Sync data for effects
        self._sync_data = None
        
        # Video and audio encoding options
        self.video_options = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '23']
        self.audio_options = ['-c:a', 'aac', '-b:a', '192k']
    
    def _generate_output_path(self, input_path: str) -> str:
        """Generate an output path based on the input path.
        
        Args:
            input_path: Path to the input file.
            
        Returns:
            Generated output path.
        """
        input_file = Path(input_path)
        output_file = input_file.with_stem(f"{input_file.stem}_visualized")
        return str(output_file)
    
    async def load_media_info(self) -> Dict[str, Any]:
        """Load media information from the input file.
        
        Returns:
            Dictionary containing media information.
            
        Raises:
            FFmpegError: If FFprobe command fails.
        """
        media_info = await self.ffmpeg.get_media_info(self.input_path)
        
        # Extract video properties
        for stream in media_info.get('streams', []):
            if stream.get('codec_type') == 'video':
                self.width = int(stream.get('width', self.width))
                self.height = int(stream.get('height', self.height))
                
                # Extract frame rate
                if 'avg_frame_rate' in stream:
                    fps_parts = stream['avg_frame_rate'].split('/')
                    if len(fps_parts) == 2 and int(fps_parts[1]) != 0:
                        self.fps = float(int(fps_parts[0]) / int(fps_parts[1]))
                
                break
        
        # Extract duration
        if 'format' in media_info and 'duration' in media_info['format']:
            self.duration = float(media_info['format']['duration'])
        
        logger.info(f"Media info: {self.width}x{self.height} @ {self.fps} fps, {self.duration:.2f} seconds")
        return media_info
    
    async def analyze_audio(self, 
                       freq_bands: Optional[Dict[str, Tuple[int, int]]] = None,
                       beat_detection: bool = True,
                       onset_detection: bool = False) -> Dict[str, Any]:
        """Analyze audio from the input file.
        
        Args:
            freq_bands: Dictionary mapping band names to (min_freq, max_freq) tuples.
                       If None, default bands are used.
            beat_detection: Whether to perform beat detection.
            onset_detection: Whether to perform onset detection.
            
        Returns:
            Dictionary containing audio features.
            
        Raises:
            FFmpegError: If audio extraction fails.
            AudioAnalysisError: If audio analysis fails.
        """
        # Extract audio to a temporary file
        audio_path = await self.ffmpeg.extract_audio(self.input_path)
        self._temp_files.append(audio_path)
        
        # Analyze the audio
        features = await self.audio_analyzer.analyze(
            audio_path, 
            freq_bands=freq_bands,
            beat_detection=beat_detection,
            onset_detection=onset_detection
        )
        
        # Generate frame-aligned features
        self._sync_data = self.audio_analyzer.get_synchronization_data(self.fps)
        
        return features
    
    def add_effect(self, effect: BaseEffect) -> 'AudioVisualizer':
        """Add a visual effect to be applied.
        
        Args:
            effect: The effect to add.
            
        Returns:
            Self for method chaining.
        """
        self.effects.append(effect)
        return self
    
    def add_logo(self, 
                logo_path: str, 
                position: Union[Tuple[Union[int, str], Union[int, str]], str] = 'top-left',
                scale: float = 1.0,
                opacity: float = 1.0,
                effect_name: Optional[str] = None) -> 'BaseEffect':
        """Add a logo overlay effect.
        
        Args:
            logo_path: Path to the logo image file.
            position: Position coordinates (x, y) or named position.
            scale: Base scale factor for the logo.
            opacity: Base opacity value (0.0-1.0).
            effect_name: Optional name for the effect. If None, one is generated.
            
        Returns:
            The created effect for further customization.
        """
        effect_name = effect_name or f"logo_{len(self.effects)}"
        effect = create_effect(
            'LogoOverlayEffect',
            effect_name,
            logo_path,
            position,
            scale,
            opacity
        )
        self.add_effect(effect)
        return effect
    
    def add_text(self, 
                text: str, 
                font_path: str,
                position: Union[Tuple[Union[int, str], Union[int, str]], str] = 'bottom-center',
                font_size: int = 32,
                font_color: str = '#FFFFFF',
                opacity: float = 1.0,
                effect_name: Optional[str] = None) -> 'BaseEffect':
        """Add a text overlay effect.
        
        Args:
            text: The text to display.
            font_path: Path to the font file.
            position: Position coordinates (x, y) or named position.
            font_size: Base font size.
            font_color: Base font color in hex format (#RRGGBB).
            opacity: Base opacity value (0.0-1.0).
            effect_name: Optional name for the effect. If None, one is generated.
            
        Returns:
            The created effect for further customization.
        """
        effect_name = effect_name or f"text_{len(self.effects)}"
        effect = create_effect(
            'TextOverlayEffect',
            effect_name,
            text,
            font_path,
            position,
            font_size,
            font_color,
            opacity
        )
        self.add_effect(effect)
        return effect
    
    def add_spectrum(self, 
                    position: Union[Tuple[Union[int, str], Union[int, str]], str] = 'bottom-center',
                    width: int = 640,
                    height: int = 120,
                    bands: int = 32,
                    mode: str = 'bars',
                    color: str = '#FFFFFF',
                    opacity: float = 0.8,
                    effect_name: Optional[str] = None) -> 'BaseEffect':
        """Add a spectrum visualizer effect.
        
        Args:
            position: Position coordinates (x, y) or named position.
            width: Width of the visualizer.
            height: Height of the visualizer.
            bands: Number of frequency bands to display.
            mode: Visualization mode ('bars' or 'wave').
            color: Base color in hex format (#RRGGBB).
            opacity: Base opacity value (0.0-1.0).
            effect_name: Optional name for the effect. If None, one is generated.
            
        Returns:
            The created effect for further customization.
        """
        effect_name = effect_name or f"spectrum_{len(self.effects)}"
        effect = create_effect(
            'SpectrumVisualizerEffect',
            effect_name,
            position,
            width,
            height,
            bands,
            mode,
            color,
            opacity
        )
        self.add_effect(effect)
        return effect
    
    def set_video_options(self, options: List[str]) -> 'AudioVisualizer':
        """Set video encoding options.
        
        Args:
            options: List of FFmpeg video encoding options.
            
        Returns:
            Self for method chaining.
        """
        self.video_options = options
        return self
    
    def set_audio_options(self, options: List[str]) -> 'AudioVisualizer':
        """Set audio encoding options.
        
        Args:
            options: List of FFmpeg audio encoding options.
            
        Returns:
            Self for method chaining.
        """
        self.audio_options = options
        return self
    
    def _sort_effects(self) -> List[BaseEffect]:
        """Sort effects by their order property.
        
        Returns:
            Sorted list of enabled effects.
        """
        return sorted([e for e in self.effects if e.enabled], key=lambda e: e.order)
    
    def save_project(self, filepath: str) -> None:
        """Save project configuration to a JSON file.
        
        Args:
            filepath: Path to save the project file.
        """
        project_data = {
            'input_path': self.input_path,
            'output_path': self.output_path,
            'fps': self.fps,
            'width': self.width,
            'height': self.height,
            'duration': self.duration,
            'video_options': self.video_options,
            'audio_options': self.audio_options,
            'effects': [effect.to_dict() for effect in self.effects]
        }
        
        with open(filepath, 'w') as f:
            json.dump(project_data, f, indent=2)
    
    @classmethod
    def load_project(cls, 
                    filepath: str, 
                    ffmpeg_path: str = 'ffmpeg',
                    ffprobe_path: str = 'ffprobe') -> 'AudioVisualizer':
        """Load project configuration from a JSON file.
        
        Args:
            filepath: Path to the project file.
            ffmpeg_path: Path to the FFmpeg executable.
            ffprobe_path: Path to the FFprobe executable.
            
        Returns:
            Instantiated AudioVisualizer with loaded configuration.
        """
        with open(filepath, 'r') as f:
            project_data = json.load(f)
        
        # Create visualizer instance
        visualizer = cls(
            project_data['input_path'],
            project_data.get('output_path'),
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path
        )
        
        # Set properties
        visualizer.fps = project_data.get('fps', 30.0)
        visualizer.width = project_data.get('width', 1280)
        visualizer.height = project_data.get('height', 720)
        visualizer.duration = project_data.get('duration', 0.0)
        
        # Set encoding options
        if 'video_options' in project_data:
            visualizer.video_options = project_data['video_options']
        if 'audio_options' in project_data:
            visualizer.audio_options = project_data['audio_options']
        
        # Load effects
        for effect_data in project_data.get('effects', []):
            effect = effect_from_dict(effect_data)
            visualizer.add_effect(effect)
        
        return visualizer
    
    async def process(self) -> None:
        """Process the input video and generate the output with effects.
        
        This method orchestrates the entire process of loading media info,
        analyzing audio, generating filter commands from effects, and
        applying them to create the final output video.
        
        Raises:
            FFmpegError: If FFmpeg operations fail.
            AudioAnalysisError: If audio analysis fails.
            ValueError: If effects generate invalid filter commands.
        """
        try:
            # Load media info
            await self.load_media_info()
            
            # Analyze audio if not already done
            if not self._sync_data:
                await self.analyze_audio()
            
            # No effects, just copy the file
            if not self.effects:
                logger.warning("No effects added, copying input to output")
                await self.ffmpeg.run_ffmpeg_command([
                    '-i', self.input_path,
                    '-c', 'copy',
                    '-y', self.output_path
                ])
                return
            
            # Sort effects by order
            sorted_effects = self._sort_effects()
            logger.info(f"Processing {len(sorted_effects)} effects")
            
            # Generate filter commands from each effect
            filter_chains = []
            
            for i, effect in enumerate(sorted_effects):
                try:
                    effect_filters = effect.generate_filter_commands(self._sync_data)
                    filter_chains.extend(effect_filters)
                    logger.info(f"Generated filters for effect: {effect.name}")
                except Exception as e:
                    logger.error(f"Error generating filters for effect {effect.name}: {str(e)}")
                    raise
            
            # Build the complex filter string
            complex_filter = self.ffmpeg.build_complex_filter(filter_chains)
            
            # Apply effects and generate output
            await self.ffmpeg.apply_effects(
                self.input_path,
                self.output_path,
                complex_filter,
                self.audio_options,
                self.video_options
            )
            
            logger.info(f"Processing complete, output saved to {self.output_path}")
        
        finally:
            # Clean up temporary files
            self._cleanup()
    
    def _cleanup(self) -> None:
        """Clean up temporary files."""
        if self._temp_files:
            self.ffmpeg.cleanup_temp_files(self._temp_files)
            self._temp_files = []


async def process_video(input_path: str, 
                    output_path: Optional[str] = None,
                    effects_config: Optional[List[Dict[str, Any]]] = None) -> str:
    """Process a video with audio-reactive effects.
    
    This is a convenience function for simple processing tasks.
    
    Args:
        input_path: Path to the input video file.
        output_path: Path for the output processed video. If None, one is generated.
        effects_config: List of effect configurations as dictionaries.
        
    Returns:
        Path to the output video file.
        
    Raises:
        FFmpegError: If FFmpeg operations fail.
        AudioAnalysisError: If audio analysis fails.
    """
    # Create visualizer
    visualizer = AudioVisualizer(input_path, output_path)
    
    # Load media info and analyze audio
    await visualizer.load_media_info()
    await visualizer.analyze_audio()
    
    # Add effects from configuration
    if effects_config:
        for effect_config in effects_config:
            effect = effect_from_dict(effect_config)
            visualizer.add_effect(effect)
    
    # Process the video
    await visualizer.process()
    
    return visualizer.output_path