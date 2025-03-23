# FFmpeg Filter Graph Validators

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class FilterValidator:
    """Validates filter configurations and connections."""
    
    @staticmethod
    def validate_filter_params(filter_type: str, params: Dict[str, Any], registry=None) -> List[str]:
        """Validate parameters for a specific filter type.
        
        Args:
            filter_type: The FFmpeg filter name
            params: Dictionary of parameter values
            registry: Optional filter registry instance
            
        Returns:
            List of validation error messages (empty if valid)
        """
        from .registry import FilterRegistry
        
        registry = registry or FilterRegistry.get_instance()
        metadata = registry.get_filter_metadata(filter_type)
        
        if not metadata:
            return [f"Unknown filter type: {filter_type}"]
            
        errors = []
        
        # Check required parameters
        for param in metadata.get('required_params', []):
            if param not in params:
                errors.append(f"Missing required parameter '{param}' for filter '{filter_type}'")
                
        # Check parameter types (if type info is available)
        param_types = metadata.get('param_types', {})
        for param, value in params.items():
            if param in param_types:
                expected_type = param_types[param]
                if not FilterValidator._check_type_compatibility(value, expected_type):
                    errors.append(f"Invalid type for parameter '{param}' in filter '{filter_type}'. "
                                 f"Expected {expected_type}, got {type(value).__name__}")
                    
        return errors
    
    @staticmethod
    def _check_type_compatibility(value: Any, expected_type: str) -> bool:
        """Check if a value is compatible with an expected type."""
        if expected_type == 'number':
            return isinstance(value, (int, float))
        elif expected_type == 'int':
            return isinstance(value, int)
        elif expected_type == 'float':
            return isinstance(value, float)
        elif expected_type == 'string':
            return isinstance(value, str)
        elif expected_type == 'bool':
            return isinstance(value, bool)
        elif expected_type == 'color':
            # Basic check for color strings
            if isinstance(value, str):
                # Check for hex color or named color
                return value.startswith('#') or value.lower() in {
                    'black', 'white', 'red', 'green', 'blue', 'yellow', 'cyan', 'magenta', 
                    'gray', 'grey', 'orange', 'purple', 'brown', 'pink', 'transparent'
                }
            return False
        # Add more type checks as needed
        return True