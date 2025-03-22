"""Spectrum visualizer effect for audio visualization.

This module provides the SpectrumVisualizerEffect class, which adds an audio spectrum
visualizer that shows frequency bands as a bar graph or waveform.
"""

from typing import Dict, List, Optional, Tuple, Union, Any
from .base import BaseEffect
from .logo import LogoOverlayEffect  # For NAMED_POSITIONS

class SpectrumVisualizerEffect(BaseEffect):
    """Effect for adding a spectrum visualizer.
    
    This effect adds an audio spectrum visualizer that shows frequency bands
    as a bar graph or waveform.
    
    Attributes:
        position (tuple): Position coordinates (x, y).
        width (int): Width of the visualizer.
        height (int): Height of the visualizer.
        bands (int): Number of frequency bands to display.
        mode (str): Visualization mode ('bars' or 'wave').
        color (str): Base color in hex format (#RRGGBB).
    """
    
    NAMED_POSITIONS = LogoOverlayEffect.NAMED_POSITIONS
    
    def __init__(self, 
                 name: str, 
                 position: Union[Tuple[Union[int, str], Union[int, str]], str] = 'bottom-center',
                 width: int = 640,
                 height: int = 120,
                 bands: int = 32,
                 mode: str = 'bars',
                 color: str = '#FFFFFF',
                 opacity: float = 0.8,
                 order: int = 30):
        """Initialize SpectrumVisualizerEffect.
        
        Args:
            name: Unique name for the effect.
            position: Position coordinates (x, y) or named position.
            width: Width of the visualizer.
            height: Height of the visualizer.
            bands: Number of frequency bands to display.
            mode: Visualization mode ('bars' or 'wave').
            color: Base color in hex format (#RRGGBB).
            opacity: Base opacity value (0.0-1.0).
            order: Execution order priority.
        """
        super().__init__(name, order)
        
        # Handle named positions
        if isinstance(position, str) and position in self.NAMED_POSITIONS:
            self.position = self.NAMED_POSITIONS[position]
        else:
            self.position = position
        
        self.width = width
        self.height = height
        self.bands = bands
        self.mode = mode
        self.color = color
        self.opacity = opacity
        
        # Effect modifiers
        self._rainbow = False
        self._mirror = False
        self._bar_width = width // bands
        self._bar_gap = 1
    
    def enable_rainbow(self) -> 'SpectrumVisualizerEffect':
        """Enable rainbow color effect.
        
        Returns:
            Self for method chaining.
        """
        self._rainbow = True
        return self
    
    def enable_mirror(self) -> 'SpectrumVisualizerEffect':
        """Enable mirrored visualization.
        
        Returns:
            Self for method chaining.
        """
        self._mirror = True
        return self
    
    def set_bar_style(self, width: int, gap: int) -> 'SpectrumVisualizerEffect':
        """Set the bar style for bar mode.
        
        Args:
            width: Width of each bar.
            gap: Gap between bars.
            
        Returns:
            Self for method chaining.
        """
        self._bar_width = width
        self._bar_gap = gap
        return self
    
    def generate_filter_commands(self, sync_data: Dict[str, Any]) -> List[str]:
        """Generate FFmpeg filter commands for spectrum visualizer effect.
        
        Args:
            sync_data: Dictionary containing synchronized audio features.
            
        Returns:
            List of FFmpeg filter strings.
        """
        # Check if we have frequency bands data
        if 'freq_bands' not in sync_data['features']:
            raise ValueError("Frequency bands data required for spectrum visualizer")
        
        # Generate filter commands
        filters = []
        
        # Main video input
        filters.append(f"[0:v][main]")
        
        # Create a transparent background for the visualizer
        filters.append(f"color=s={self.width}x{self.height}:c=#00000000,format=rgba[spectrum_bg]")
        
        # Select appropriate FFmpeg filter based on mode
        if self.mode == 'bars':
            # Use showspectrum filter for bars
            spectrum_filter = f"showspectrum=s={self.width}x{self.height}:" + \
                            f"mode=bar:color={self.color}:scale=lin:" + \
                            f"slide=replace:saturation=1:opacity={self.opacity}"
            
            if self._rainbow:
                spectrum_filter += f":color=rainbow"
            
            if self._mirror:
                spectrum_filter += f":mirror=1"
        
        elif self.mode == 'wave':
            # Use showwaves filter for waveform
            spectrum_filter = f"showwaves=s={self.width}x{self.height}:" + \
                            f"mode=line:n={self.bands}:scale=sqrt:" + \
                            f"colors={self.color}:opacity={self.opacity}"
            
            if self._mirror:
                spectrum_filter += f":mirror=1"
        
        else:
            raise ValueError(f"Unsupported visualization mode: {self.mode}")
        
        # Apply spectrum filter to audio
        filters.append(f"[0:a]{spectrum_filter}[spectrum]")
        
        # Overlay spectrum on main video
        x, y = self.position
        filters.append(f"[main][spectrum]overlay={x}:{y}[out]")
        
        return filters
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert effect configuration to a dictionary.
        
        Returns:
            Dictionary representation of the effect configuration.
        """
        config = super().to_dict()
        config.update({
            'position': self.position,
            'width': self.width,
            'height': self.height,
            'bands': self.bands,
            'mode': self.mode,
            'color': self.color,
            'opacity': self.opacity,
            'rainbow': self._rainbow,
            'mirror': self._mirror,
            'bar_width': self._bar_width,
            'bar_gap': self._bar_gap
        })
        return config
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'SpectrumVisualizerEffect':
        """Create a SpectrumVisualizerEffect instance from a configuration dictionary.
        
        Args:
            config: Dictionary containing effect configuration.
            
        Returns:
            Instantiated SpectrumVisualizerEffect object.
        """
        effect = cls(
            config['name'],
            config.get('position', 'bottom-center'),
            config.get('width', 640),
            config.get('height', 120),
            config.get('bands', 32),
            config.get('mode', 'bars'),
            config.get('color', '#FFFFFF'),
            config.get('opacity', 0.8),
            config.get('order', 30)
        )
        
        # Enable rainbow if specified
        if config.get('rainbow', False):
            effect.enable_rainbow()
        
        # Enable mirror if specified
        if config.get('mirror', False):
            effect.enable_mirror()
        
        # Set bar style if specified
        if 'bar_width' in config and 'bar_gap' in config:
            effect.set_bar_style(config['bar_width'], config['bar_gap'])
        
        # Set audio feature if specified
        if config.get('audio_feature'):
            effect.set_audio_feature(
                config['audio_feature'],
                config.get('feature_source', 'amplitude')
            )
        
        return effect