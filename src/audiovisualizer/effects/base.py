"""Base class for all visual effects.

This module defines the BaseEffect class that all other effects inherit from,
providing common functionality for audio synchronization and configuration.
"""

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