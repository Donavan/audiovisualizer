"""Visual effects for audio visualization.

This module provides a collection of visual effects that can be applied to videos
based on audio features. Effects include overlays, filters, and animations.
"""

import os
import tempfile
import json
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Any, Callable

class BaseEffect:
    """Base class for all visual effects.
    
    This class defines the interface for visual effects and provides common
    functionality for synchronizing with audio features.
    
    Attributes:
        name (str): Unique name for the effect.
        order (int): Execution order priority (lower numbers execute first).
        enabled (bool): Whether the effect is enabled.
    """
    
    def __init__(self, name: str, order: int = 0):
        """Initialize BaseEffect.
        
        Args:
            name: Unique name for the effect.
            order: Execution order priority (lower numbers execute first).
        """
        self.name = name
        self.order = order
        self.enabled = True
        self._audio_feature = None
        self._feature_source = None
        self._feature_transform = None
    
    def set_audio_feature(
        self, 
        feature: str, 
        source: str = 'amplitude',
        transform: Optional[Callable[[np.ndarray], np.ndarray]] = None
    ) -> 'BaseEffect':
        """Set the audio feature to synchronize with.
        
        Args:
            feature: Name of the feature to use (e.g., 'amplitude', 'freq_bands.bass').
            source: Source of the feature ('amplitude', 'freq_bands', 'beats', etc.).
            transform: Optional function to transform the feature values.
            
        Returns:
            Self for method chaining.
        """
        self._audio_feature = feature
        self._feature_source = source
        self._feature_transform = transform
        return self
    
    def get_feature_data(self, sync_data: Dict[str, Any]) -> np.ndarray:
        """Extract relevant feature data from sync_data.
        
        Args:
            sync_data: Dictionary containing synchronized audio features.
            
        Returns:
            Numpy array of feature values for each frame.
        """
        if not self._audio_feature:
            # Return a flat array of 1s if no feature is specified
            return np.ones(sync_data['n_frames'])
        
        # Parse the feature path (e.g., 'freq_bands.bass')
        parts = self._audio_feature.split('.')
        
        # Navigate to the correct feature
        data = sync_data['features']
        for part in parts:
            data = data.get(part, None)
            if data is None:
                raise ValueError(f"Feature not found: {self._audio_feature}")
        
        # Apply transform if provided
        if self._feature_transform and callable(self._feature_transform):
            data = self._feature_transform(data)
        
        return data
    
    def generate_filter_commands(self, sync_data: Dict[str, Any]) -> List[str]:
        """Generate FFmpeg filter commands for this effect.
        
        Args:
            sync_data: Dictionary containing synchronized audio features.
            
        Returns:
            List of FFmpeg filter strings.
            
        Note:
            This method must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement generate_filter_commands()")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert effect configuration to a dictionary.
        
        Returns:
            Dictionary representation of the effect configuration.
        """
        return {
            'name': self.name,
            'type': self.__class__.__name__,
            'order': self.order,
            'enabled': self.enabled,
            'audio_feature': self._audio_feature,
            'feature_source': self._feature_source
        }
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'BaseEffect':
        """Create an effect instance from a configuration dictionary.
        
        Args:
            config: Dictionary containing effect configuration.
            
        Returns:
            Instantiated effect object.
            
        Note:
            This method should be implemented by subclasses.
        """
        effect = cls(config['name'], config.get('order', 0))
        effect.enabled = config.get('enabled', True)
        if config.get('audio_feature'):
            effect.set_audio_feature(
                config['audio_feature'],
                config.get('feature_source', 'amplitude')
            )
        return effect


class LogoOverlayEffect(BaseEffect):
    """Effect for adding a reactive logo overlay.
    
    This effect adds a logo image overlay that can react to audio features
    through scaling, rotation, opacity, and position changes.
    
    Attributes:
        logo_path (str): Path to the logo image file.
        position (tuple): Position coordinates (x, y) or named position.
        scale (float): Base scale factor for the logo.
        opacity (float): Base opacity value (0.0-1.0).
    """
    
    NAMED_POSITIONS = {
        'top-left': (10, 10),
        'top-center': ('(w-overlay_w)/2', 10),
        'top-right': ('(w-overlay_w-10)', 10),
        'center-left': (10, '(h-overlay_h)/2'),
        'center': ('(w-overlay_w)/2', '(h-overlay_h)/2'),
        'center-right': ('(w-overlay_w-10)', '(h-overlay_h)/2'),
        'bottom-left': (10, '(h-overlay_h-10)'),
        'bottom-center': ('(w-overlay_w)/2', '(h-overlay_h-10)'),
        'bottom-right': ('(w-overlay_w-10)', '(h-overlay_h-10)')
    }
    
    def __init__(self, 
                 name: str, 
                 logo_path: str,
                 position: Union[Tuple[Union[int, str], Union[int, str]], str] = 'top-left',
                 scale: float = 1.0,
                 opacity: float = 1.0,
                 order: int = 10):
        """Initialize LogoOverlayEffect.
        
        Args:
            name: Unique name for the effect.
            logo_path: Path to the logo image file.
            position: Position coordinates (x, y) or named position.
            scale: Base scale factor for the logo.
            opacity: Base opacity value (0.0-1.0).
            order: Execution order priority.
        """
        super().__init__(name, order)
        self.logo_path = logo_path
        
        # Handle named positions
        if isinstance(position, str) and position in self.NAMED_POSITIONS:
            self.position = self.NAMED_POSITIONS[position]
        else:
            self.position = position
        
        self.scale = scale
        self.opacity = opacity
        
        # Effect modifiers
        self._scale_min = scale
        self._scale_max = scale
        self._opacity_min = opacity
        self._opacity_max = opacity
        self._rotation = False
        self._rotation_speed = 0
    
    def set_scale_range(self, min_scale: float, max_scale: float) -> 'LogoOverlayEffect':
        """Set the scale range for audio reactivity.
        
        Args:
            min_scale: Minimum scale factor.
            max_scale: Maximum scale factor.
            
        Returns:
            Self for method chaining.
        """
        self._scale_min = min_scale
        self._scale_max = max_scale
        return self
    
    def set_opacity_range(self, min_opacity: float, max_opacity: float) -> 'LogoOverlayEffect':
        """Set the opacity range for audio reactivity.
        
        Args:
            min_opacity: Minimum opacity value (0.0-1.0).
            max_opacity: Maximum opacity value (0.0-1.0).
            
        Returns:
            Self for method chaining.
        """
        self._opacity_min = max(0.0, min(1.0, min_opacity))
        self._opacity_max = max(0.0, min(1.0, max_opacity))
        return self
    
    def enable_rotation(self, speed: float = 1.0) -> 'LogoOverlayEffect':
        """Enable rotation animation.
        
        Args:
            speed: Rotation speed factor.
            
        Returns:
            Self for method chaining.
        """
        self._rotation = True
        self._rotation_speed = speed
        return self
    
    def generate_filter_commands(self, sync_data: Dict[str, Any]) -> List[str]:
        """Generate FFmpeg filter commands for logo overlay effect.
        
        Args:
            sync_data: Dictionary containing synchronized audio features.
            
        Returns:
            List of FFmpeg filter strings.
        """
        if not os.path.exists(self.logo_path):
            raise ValueError(f"Logo file not found: {self.logo_path}")
        
        # Get feature data for reactivity
        feature_data = self.get_feature_data(sync_data)
        n_frames = sync_data['n_frames']
        
        # Create temporary data file for frame-by-frame parameters
        fd, data_file = tempfile.mkstemp(suffix='.txt')
        os.close(fd)
        
        # Generate frame data
        with open(data_file, 'w') as f:
            for frame in range(n_frames):
                # Calculate scale based on audio feature
                if self._scale_min != self._scale_max:
                    feature_val = feature_data[frame] if frame < len(feature_data) else 0
                    scale = self._scale_min + (self._scale_max - self._scale_min) * feature_val
                else:
                    scale = self._scale
                
                # Calculate opacity based on audio feature
                if self._opacity_min != self._opacity_max:
                    feature_val = feature_data[frame] if frame < len(feature_data) else 0
                    opacity = self._opacity_min + (self._opacity_max - self._opacity_min) * feature_val
                else:
                    opacity = self.opacity
                
                # Calculate rotation angle if enabled
                if self._rotation:
                    angle = (frame * self._rotation_speed) % 360
                else:
                    angle = 0
                
                # Write frame data
                f.write(f"{frame} {scale} {opacity} {angle}\n")
        
        # Generate filter commands
        filters = []
        
        # Input for logo
        filters.append(f"[0:v]" + \
                      f"[main];" + \
                      f"movie='{self.logo_path}'" + \
                      f"[logo]")
        
        # Setup sendcmd filter for frame-by-frame control
        filters.append(f"[logo]sendcmd=f='{data_file}':" + \
                      f"c='f=${frame} scale${scale} opacity${opacity} angle${angle}';" + \
                      f"scale=iw*${scale}:ih*${scale}," + \
                      f"rotate=${angle}*PI/180:c=0x00000000:ow=rotw(${angle}*PI/180):oh=roth(${angle}*PI/180)," + \
                      f"format=rgba,colorchannelmixer=aa=${opacity}" + \
                      f"[scaledlogo]")
        
        # Overlay logo on main video
        x, y = self.position
        filters.append(f"[main][scaledlogo]overlay={x}:{y}:" + \
                      f"shortest=1:format=rgb" + \
                      f"[out]")
        
        return filters
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert effect configuration to a dictionary.
        
        Returns:
            Dictionary representation of the effect configuration.
        """
        config = super().to_dict()
        config.update({
            'logo_path': self.logo_path,
            'position': self.position,
            'scale': self.scale,
            'opacity': self.opacity,
            'scale_min': self._scale_min,
            'scale_max': self._scale_max,
            'opacity_min': self._opacity_min,
            'opacity_max': self._opacity_max,
            'rotation': self._rotation,
            'rotation_speed': self._rotation_speed
        })
        return config
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'LogoOverlayEffect':
        """Create a LogoOverlayEffect instance from a configuration dictionary.
        
        Args:
            config: Dictionary containing effect configuration.
            
        Returns:
            Instantiated LogoOverlayEffect object.
        """
        effect = cls(
            config['name'],
            config['logo_path'],
            config.get('position', 'top-left'),
            config.get('scale', 1.0),
            config.get('opacity', 1.0),
            config.get('order', 10)
        )
        
        # Apply scale range if specified
        if 'scale_min' in config and 'scale_max' in config:
            effect.set_scale_range(config['scale_min'], config['scale_max'])
        
        # Apply opacity range if specified
        if 'opacity_min' in config and 'opacity_max' in config:
            effect.set_opacity_range(config['opacity_min'], config['opacity_max'])
        
        # Enable rotation if specified
        if config.get('rotation', False):
            effect.enable_rotation(config.get('rotation_speed', 1.0))
        
        # Set audio feature if specified
        if config.get('audio_feature'):
            effect.set_audio_feature(
                config['audio_feature'],
                config.get('feature_source', 'amplitude')
            )
        
        return effect


class TextOverlayEffect(BaseEffect):
    """Effect for adding reactive text overlay.
    
    This effect adds text overlay that can react to audio features through
    opacity, scale, and color changes.
    
    Attributes:
        text (str): The text to display.
        font_path (str): Path to the font file.
        position (tuple): Position coordinates (x, y) or named position.
        font_size (int): Base font size.
        font_color (str): Base font color in hex format (#RRGGBB).
        opacity (float): Base opacity value (0.0-1.0).
    """
    
    NAMED_POSITIONS = LogoOverlayEffect.NAMED_POSITIONS
    
    def __init__(self, 
                 name: str, 
                 text: str,
                 font_path: str,
                 position: Union[Tuple[Union[int, str], Union[int, str]], str] = 'bottom-center',
                 font_size: int = 32,
                 font_color: str = '#FFFFFF',
                 opacity: float = 1.0,
                 order: int = 20):
        """Initialize TextOverlayEffect.
        
        Args:
            name: Unique name for the effect.
            text: The text to display.
            font_path: Path to the font file.
            position: Position coordinates (x, y) or named position.
            font_size: Base font size.
            font_color: Base font color in hex format (#RRGGBB).
            opacity: Base opacity value (0.0-1.0).
            order: Execution order priority.
        """
        super().__init__(name, order)
        self.text = text
        self.font_path = font_path
        
        # Handle named positions
        if isinstance(position, str) and position in self.NAMED_POSITIONS:
            self.position = self.NAMED_POSITIONS[position]
        else:
            self.position = position
        
        self.font_size = font_size
        self.font_color = font_color
        self.opacity = opacity
        
        # Effect modifiers
        self._opacity_min = opacity
        self._opacity_max = opacity
        self._color_shift = False
        self._glow = False
        self._glow_color = '#00FFFF'
        self._bg_box = False
        self._bg_color = '#000000'
        self._bg_opacity = 0.5
    
    def set_opacity_range(self, min_opacity: float, max_opacity: float) -> 'TextOverlayEffect':
        """Set the opacity range for audio reactivity.
        
        Args:
            min_opacity: Minimum opacity value (0.0-1.0).
            max_opacity: Maximum opacity value (0.0-1.0).
            
        Returns:
            Self for method chaining.
        """
        self._opacity_min = max(0.0, min(1.0, min_opacity))
        self._opacity_max = max(0.0, min(1.0, max_opacity))
        return self
    
    def enable_color_shift(self) -> 'TextOverlayEffect':
        """Enable color shifting effect based on audio intensity.
        
        Returns:
            Self for method chaining.
        """
        self._color_shift = True
        return self
    
    def enable_glow(self, glow_color: str = '#00FFFF') -> 'TextOverlayEffect':
        """Enable glow effect around text.
        
        Args:
            glow_color: Color for the glow effect in hex format (#RRGGBB).
            
        Returns:
            Self for method chaining.
        """
        self._glow = True
        self._glow_color = glow_color
        return self
    
    def enable_background_box(self, 
                             bg_color: str = '#000000', 
                             bg_opacity: float = 0.5) -> 'TextOverlayEffect':
        """Enable background box behind text.
        
        Args:
            bg_color: Background color in hex format (#RRGGBB).
            bg_opacity: Background opacity (0.0-1.0).
            
        Returns:
            Self for method chaining.
        """
        self._bg_box = True
        self._bg_color = bg_color
        self._bg_opacity = max(0.0, min(1.0, bg_opacity))
        return self
    
    def generate_filter_commands(self, sync_data: Dict[str, Any]) -> List[str]:
        """Generate FFmpeg filter commands for text overlay effect.
        
        Args:
            sync_data: Dictionary containing synchronized audio features.
            
        Returns:
            List of FFmpeg filter strings.
        """
        if not os.path.exists(self.font_path):
            raise ValueError(f"Font file not found: {self.font_path}")
        
        # Get feature data for reactivity
        feature_data = self.get_feature_data(sync_data)
        n_frames = sync_data['n_frames']
        
        # Create temporary data file for frame-by-frame parameters
        fd, data_file = tempfile.mkstemp(suffix='.txt')
        os.close(fd)
        
        # Generate frame data
        with open(data_file, 'w') as f:
            for frame in range(n_frames):
                # Calculate opacity based on audio feature
                if self._opacity_min != self._opacity_max:
                    feature_val = feature_data[frame] if frame < len(feature_data) else 0
                    opacity = self._opacity_min + (self._opacity_max - self._opacity_min) * feature_val
                else:
                    opacity = self.opacity
                
                # Calculate color if color shift is enabled
                if self._color_shift:
                    feature_val = feature_data[frame] if frame < len(feature_data) else 0
                    # Shift from white to red based on intensity
                    r = 255
                    g = max(0, int(255 * (1 - feature_val)))
                    b = max(0, int(255 * (1 - feature_val)))
                    color = f"#{r:02x}{g:02x}{b:02x}"
                else:
                    color = self.font_color
                
                # Write frame data
                f.write(f"{frame} {opacity} {color}\n")
        
        # Generate filter commands
        filters = []
        
        # Main video input
        filters.append(f"[0:v][main]")
        
        # Create text overlay
        text_filter = f"drawtext=text='{self.text}':" + \
                      f"fontfile='{self.font_path}':" + \
                      f"fontsize={self.font_size}:" + \
                      f"fontcolor=${{color}}@${{opacity}}:"
        
        # Add position parameters
        x, y = self.position
        text_filter += f"x={x}:y={y}:"
        
        # Add background box if enabled
        if self._bg_box:
            text_filter += f"box=1:" + \
                          f"boxcolor={self._bg_color}@{self._bg_opacity}:" + \
                          f"boxborderw=5:"
        
        # Add glow if enabled
        if self._glow:
            # Add a shadow with the glow color
            text_filter += f"shadowcolor={self._glow_color}@0.5:" + \
                          f"shadowx=2:shadowy=2:"
        
        # Add sendcmd for frame-by-frame control
        text_filter += f"sendcmd=f='{data_file}':" + \
                      f"c='f=${frame} opacity=${opacity} color=${color}'"        
        
        filters.append(f"[main]{text_filter}[out]")
        
        return filters
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert effect configuration to a dictionary.
        
        Returns:
            Dictionary representation of the effect configuration.
        """
        config = super().to_dict()
        config.update({
            'text': self.text,
            'font_path': self.font_path,
            'position': self.position,
            'font_size': self.font_size,
            'font_color': self.font_color,
            'opacity': self.opacity,
            'opacity_min': self._opacity_min,
            'opacity_max': self._opacity_max,
            'color_shift': self._color_shift,
            'glow': self._glow,
            'glow_color': self._glow_color,
            'bg_box': self._bg_box,
            'bg_color': self._bg_color,
            'bg_opacity': self._bg_opacity
        })
        return config
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'TextOverlayEffect':
        """Create a TextOverlayEffect instance from a configuration dictionary.
        
        Args:
            config: Dictionary containing effect configuration.
            
        Returns:
            Instantiated TextOverlayEffect object.
        """
        effect = cls(
            config['name'],
            config['text'],
            config['font_path'],
            config.get('position', 'bottom-center'),
            config.get('font_size', 32),
            config.get('font_color', '#FFFFFF'),
            config.get('opacity', 1.0),
            config.get('order', 20)
        )
        
        # Apply opacity range if specified
        if 'opacity_min' in config and 'opacity_max' in config:
            effect.set_opacity_range(config['opacity_min'], config['opacity_max'])
        
        # Enable color shift if specified
        if config.get('color_shift', False):
            effect.enable_color_shift()
        
        # Enable glow if specified
        if config.get('glow', False):
            effect.enable_glow(config.get('glow_color', '#00FFFF'))
        
        # Enable background box if specified
        if config.get('bg_box', False):
            effect.enable_background_box(
                config.get('bg_color', '#000000'),
                config.get('bg_opacity', 0.5)
            )
        
        # Set audio feature if specified
        if config.get('audio_feature'):
            effect.set_audio_feature(
                config['audio_feature'],
                config.get('feature_source', 'amplitude')
            )
        
        return effect


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


# Register all effect classes for easy access
EFFECT_REGISTRY = {
    'LogoOverlayEffect': LogoOverlayEffect,
    'TextOverlayEffect': TextOverlayEffect,
    'SpectrumVisualizerEffect': SpectrumVisualizerEffect
}


def create_effect(effect_type: str, *args, **kwargs) -> BaseEffect:
    """Create an effect instance by type name.
    
    Args:
        effect_type: Name of the effect class to create.
        *args: Positional arguments to pass to the effect constructor.
        **kwargs: Keyword arguments to pass to the effect constructor.
        
    Returns:
        Instantiated effect object.
        
    Raises:
        ValueError: If effect_type is not registered.
    """
    if effect_type not in EFFECT_REGISTRY:
        raise ValueError(f"Unknown effect type: {effect_type}")
    
    return EFFECT_REGISTRY[effect_type](*args, **kwargs)


def effect_from_dict(config: Dict[str, Any]) -> BaseEffect:
    """Create an effect instance from a configuration dictionary.
    
    Args:
        config: Dictionary containing effect configuration.
        
    Returns:
        Instantiated effect object.
        
    Raises:
        ValueError: If effect type is not registered.
    """
    effect_type = config.get('type')
    if not effect_type or effect_type not in EFFECT_REGISTRY:
        raise ValueError(f"Unknown or missing effect type: {effect_type}")
    
    return EFFECT_REGISTRY[effect_type].from_dict(config)