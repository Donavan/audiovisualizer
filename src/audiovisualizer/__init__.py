"""AudioVisualizer package for creating audio-reactive visual effects.

This package provides tools for creating audio-reactive visual overlays for videos.
It extracts audio features and uses them to drive visual effects that are
synchronized with the audio content.
"""

__version__ = '0.2.0'

from .visualizer import AudioVisualizer, process_video
from .effects import (
    BaseEffect, 
    LogoOverlayEffect, 
    TextOverlayEffect, 
    SpectrumVisualizerEffect,
    create_effect, 
    effect_from_dict
)

__all__ = [
    'AudioVisualizer',
    'process_video',
    'BaseEffect', 
    'LogoOverlayEffect', 
    'TextOverlayEffect', 
    'SpectrumVisualizerEffect',
    'create_effect', 
    'effect_from_dict'
]