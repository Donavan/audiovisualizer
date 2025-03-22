"""Registry for effect classes.

This module provides a registry of available effect classes and helper functions
for creating effect instances from configuration.
"""

import os
import tempfile
import json
from typing import Dict, List, Optional, Tuple, Union, Any

# These imports look circular, but they'll be resolved when the package is imported
# through __init__.py, which ensures everything is already properly loaded
from .base import BaseEffect
from .logo import LogoOverlayEffect
from .text import TextOverlayEffect
from .spectrum import SpectrumVisualizerEffect

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