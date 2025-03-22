"""Text overlay effect for audio visualization.

This module provides the TextOverlayEffect class, which adds text overlay
that can react to audio features through opacity, scale, and color changes.
"""

import os
from typing import Dict, List, Optional, Tuple, Union, Any
from .base import BaseEffect
from .logo import LogoOverlayEffect  # For NAMED_POSITIONS

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

        # Get feature data for reactivity - but we'll use a simple average now
        feature_data = self.get_feature_data(sync_data)
        avg_feature = sum(feature_data) / len(feature_data) if len(feature_data) > 0 else 0.5

        # Calculate an average opacity based on the average feature value
        if self._opacity_min != self._opacity_max:
            opacity = self._opacity_min + (self._opacity_max - self._opacity_min) * avg_feature
        else:
            opacity = self.opacity

        # Calculate color - simplified to a static color for now
        if self._color_shift:
            # Create a color based on the average feature
            r = 255
            g = max(0, int(255 * (1 - avg_feature)))
            b = max(0, int(255 * (1 - avg_feature)))
            color = f"#{r:02x}{g:02x}{b:02x}"
        else:
            color = self.font_color

        # Generate filter commands - return the filter without input/output labels
        # Let FFmpegProcessor handle proper chaining

        # Create text overlay filter - without hardcoding [main] or [out]
        # The filter parameters stay the same, we just don't add labels
        text_filter = f"drawtext=text='{self.text}':" + \
                     f"fontfile='{self.font_path}':" + \
                     f"fontsize={self.font_size}:" + \
                     f"fontcolor={color}@{opacity}:"

        # Add position parameters
        x, y = self.position
        text_filter += f"x={x}:y={y}"

        # Add background box if enabled
        if self._bg_box:
            text_filter += f":box=1:" + \
                          f"boxcolor={self._bg_color}@{self._bg_opacity}:" + \
                          f"boxborderw=5"

        # Add glow if enabled
        if self._glow:
            # Add a shadow with the glow color
            text_filter += f":shadowcolor={self._glow_color}@0.5:" + \
                          f"shadowx=2:shadowy=2"

        # Return the filter without input/output labels
        # Let FFmpegProcessor handle proper chaining
        return [text_filter]

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