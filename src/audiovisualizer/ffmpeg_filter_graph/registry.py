# FFmpeg Filter Registry

from typing import Dict, Any, List, Optional


class FilterRegistry:
    """Registry of supported FFmpeg filters with metadata."""

    _instance = None

    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initialize the registry."""
        self.filters: Dict[str, Dict[str, Any]] = {}
        self._register_builtin_filters()

    def register_filter(self, filter_type: str, metadata: Dict[str, Any]) -> None:
        """Register a filter type with metadata.
        
        Args:
            filter_type: The FFmpeg filter name
            metadata: Dictionary containing filter metadata such as:
                - min_inputs: Minimum number of inputs required
                - max_inputs: Maximum number of inputs allowed
                - required_params: List of required parameters
                - optional_params: List of optional parameters
        """
        self.filters[filter_type] = metadata

    def get_filter_metadata(self, filter_type: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a filter type."""
        return self.filters.get(filter_type)

    def validate_filter(self, node) -> List[str]:
        """Validate a filter node against its metadata."""
        from .core import FilterNode
        if not isinstance(node, FilterNode):
            return ["Not a valid FilterNode instance"]
            
        metadata = self.get_filter_metadata(node.filter_type)
        if not metadata:
            return [f"Unknown filter type: {node.filter_type}"]

        errors = []

        # Check required parameters
        for param in metadata.get('required_params', []):
            if param not in node.params:
                errors.append(f"Missing required parameter '{param}' for filter '{node.filter_type}'")

        # Check input/output connections
        min_inputs = metadata.get('min_inputs', 0)
        if len(node.inputs) < min_inputs:
            errors.append(f"Filter '{node.filter_type}' requires at least {min_inputs} inputs, got {len(node.inputs)}")

        max_inputs = metadata.get('max_inputs', float('inf'))
        if len(node.inputs) > max_inputs:
            errors.append(f"Filter '{node.filter_type}' accepts at most {max_inputs} inputs, got {len(node.inputs)}")

        return errors

    def _register_builtin_filters(self) -> None:
        """Register built-in FFmpeg filters."""
        # Register buffer_src as a special source filter (required for input streams)
        self.register_filter('buffer_src', {
            'min_inputs': 0,
            'max_inputs': 0,
            'min_outputs': 1,
            'max_outputs': 1,
            'required_params': [],
            'optional_params': [],
        })
        
        # Common video filters
        self.register_filter('format', {
            'min_inputs': 1,
            'max_inputs': 1,
            'required_params': ['pix_fmt'],
            'optional_params': [],
        })
        
        self.register_filter('overlay', {
            'min_inputs': 2,
            'max_inputs': 2,
            'required_params': [],
            'optional_params': ['x', 'y', 'format', 'shortest', 'repeatlast'],
        })

        self.register_filter('drawtext', {
            'min_inputs': 1,
            'max_inputs': 1,
            'required_params': ['text'],
            'optional_params': ['fontfile', 'fontsize', 'fontcolor', 'x', 'y', 'alpha', 'box', 
                               'boxcolor', 'shadowx', 'shadowy', 'shadowcolor'],
        })
        
        self.register_filter('scale', {
            'min_inputs': 1,
            'max_inputs': 1,
            'required_params': [],
            'optional_params': ['width', 'height', 'flags', 'interl', 'in_color_matrix', 
                               'out_color_matrix', 'force_original_aspect_ratio'],
        })
        
        self.register_filter('movie', {
            'min_inputs': 0,
            'max_inputs': 0,
            'required_params': ['filename'],
            'optional_params': ['format', 'seek_point', 'stream_index'],
        })
        
        self.register_filter('colorchannelmixer', {
            'min_inputs': 1,
            'max_inputs': 1,
            'required_params': [],
            'optional_params': ['rr', 'rg', 'rb', 'ra', 'gr', 'gg', 'gb', 'ga', 'br', 'bg', 'bb', 'ba', 'ar', 'ag', 'ab', 'aa'],
        })
        
        self.register_filter('rotate', {
            'min_inputs': 1,
            'max_inputs': 1,
            'required_params': [],
            'optional_params': ['angle', 'out_w', 'out_h', 'fillcolor'],
        })
        
        self.register_filter('fade', {
            'min_inputs': 1,
            'max_inputs': 1,
            'required_params': ['type'],
            'optional_params': ['start_frame', 'nb_frames', 'alpha', 'start_time', 'duration'],
        })
        
        self.register_filter('fps', {
            'min_inputs': 1,
            'max_inputs': 1,
            'required_params': [],
            'optional_params': ['fps', 'round', 'eof_action'],
        })
        
        self.register_filter('setpts', {
            'min_inputs': 1,
            'max_inputs': 1,
            'required_params': ['expr'],
            'optional_params': [],
        })
        
        # Add more filters as needed