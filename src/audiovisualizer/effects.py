"""Visual effects for audio visualization - re-exports from effects package.

This module re-exports all classes and functions from the effects package for backward
compatibility. New code should import directly from the effects package.
"""

# Re-export everything from the effects package
from .effects import (
    BaseEffect, 
    LogoOverlayEffect, 
    TextOverlayEffect, 
    SpectrumVisualizerEffect,
    EFFECT_REGISTRY, 
    create_effect, 
    effect_from_dict
)

__all__ = [
    'BaseEffect', 
    'LogoOverlayEffect', 
    'TextOverlayEffect', 
    'SpectrumVisualizerEffect',
    'EFFECT_REGISTRY',
    'create_effect', 
    'effect_from_dict'
]