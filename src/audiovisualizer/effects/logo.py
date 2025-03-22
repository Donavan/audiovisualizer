"""Logo overlay effect for audio visualization.

This module provides the LogoOverlayEffect class, which adds a logo image
overlay that can react to audio features through scaling, rotation, opacity, and
position changes.
"""

import os
from typing import Dict, List, Optional, Tuple, Union, Any
from .base import BaseEffect

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

        # Get feature data for reactivity - but we'll use a simple average now
        feature_data = self.get_feature_data(sync_data)
        avg_feature = sum(feature_data) / len(feature_data) if len(feature_data) > 0 else 0.5

        # Calculate an average scale and opacity based on the average feature value
        if self._scale_min != self._scale_max:
            scale = self._scale_min + (self._scale_max - self._scale_min) * avg_feature
        else:
            scale = self.scale

        if self._opacity_min != self._opacity_max:
            opacity = self._opacity_min + (self._opacity_max - self._opacity_min) * avg_feature
        else:
            opacity = self.opacity

        # Generate filter commands
        filters = []

        # Input for logo - let FFmpegProcessor handle the input/output labels
        logo_filter = f"movie='{self.logo_path}'[logo_{self.name}]"
        filters.append(logo_filter)

        # Transform logo with static parameters - no sendcmd
        transform_filter = f"[logo_{self.name}]scale=iw*{scale}:ih*{scale}"

        # Add rotation if enabled - simplified to a static angle
        if self._rotation:
            angle = 45 if self._rotation_speed > 0 else 0  # Just use a static rotation for now
            transform_filter += f",rotate={angle}*PI/180:c=0x00000000"

        # Add opacity
        transform_filter += f",format=rgba,colorchannelmixer=aa={opacity}[scaled_logo_{self.name}]"
        filters.append(transform_filter)

        # Overlay logo on main video - without hardcoding [main] or [out]
        # Let FFmpegProcessor handle proper chaining
        x, y = self.position
        overlay_filter = f"overlay={x}:{y}:shortest=1:format=rgb"
        
        # The FFmpegProcessor will wrap this with the appropriate input/output labels
        filters.append(f"[scaled_logo_{self.name}]{overlay_filter}")

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