"""Visual effects for audio visualization.

This module provides a collection of visual effects that can be applied to videos
based on audio features. Effects include overlays, filters, and animations.
"""

# Import all effect classes for easy access
from .base import BaseEffect
from .logo import LogoOverlayEffect
from .text import TextOverlayEffect
from .spectrum import SpectrumVisualizerEffect
from .registry import EFFECT_REGISTRY, create_effect, effect_from_dict

__all__ = [
    'BaseEffect',
    'LogoOverlayEffect',
    'TextOverlayEffect',
    'SpectrumVisualizerEffect',
    'EFFECT_REGISTRY',
    'create_effect',
    'effect_from_dict'
]