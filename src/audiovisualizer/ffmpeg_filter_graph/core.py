# FFmpeg Filter Graph - Core Components

import uuid
from typing import List, Dict, Tuple, Optional, Any, Union
from .registry import FilterRegistry


def _escape_param(value: Any) -> str:
    """Escape a parameter value for FFmpeg filter string."""
    if isinstance(value, (int, float)):
        return str(value)
    
    value_str = str(value)
    # Escape special characters
    if any(c in value_str for c in [':', ',', '[', ']', '\\']):
        # Escape backslashes first, then other special chars
        value_str = value_str.replace('\\', '\\\\')
        value_str = value_str.replace(':', '\\:')
        value_str = value_str.replace(',', '\\,')
        value_str = value_str.replace('[', '\\[')
        value_str = value_str.replace(']', '\\]')
        return f"'{value_str}'"
    return value_str


class FilterNode:
    """Represents a single filter in the filter graph."""

    def __init__(self, filter_type: str, label: Optional[str] = None, params: Optional[Dict[str, Any]] = None):
        """
        Initialize a filter node.

        Args:
            filter_type: The FFmpeg filter type (e.g., 'overlay', 'drawtext')
            label: Custom label for this node. If None, auto-generated.
            params: Filter parameters.
        """
        self.filter_type = filter_type
        self.label = label or f"{filter_type}_{uuid.uuid4().hex[:8]}"
        self.params = params or {}
        self.inputs: List[Tuple['FilterNode', int]] = []    # List of (source_node, pad_index) tuples
        self.outputs: List[Tuple['FilterNode', int]] = []   # List of (target_node, pad_index) tuples
        self.input_labels: Dict[int, str] = {}  # Map of pad_index to custom input label
        self.output_labels: Dict[int, str] = {} # Map of pad_index to custom output label

    def add_input(self, source: Optional['FilterNode'], pad_index: int = 0, source_pad: int = 0) -> 'FilterNode':
        """Connect an input to this node."""
        if source:
            # Store the correct pad indices for inputs and outputs
            self.inputs.append((source, source_pad))
            source.outputs.append((self, pad_index))
        else:
            # Handle external inputs (None source)
            self.inputs.append((None, pad_index))

        return self

    def set_input_label(self, pad_index: int, label: str) -> 'FilterNode':
        """Set a custom label for an input pad."""
        self.input_labels[pad_index] = label
        return self

    def set_output_label(self, pad_index: int, label: str) -> 'FilterNode':
        """Set a custom label for an output pad."""
        self.output_labels[pad_index] = label
        return self

    def get_input_label(self, pad_index: int) -> Optional[str]:
        """Get the label for an input pad."""
        if pad_index in self.input_labels:
            return self.input_labels[pad_index]
        if pad_index < len(self.inputs):
            source, source_pad = self.inputs[pad_index]
            if source:
                return source.get_output_label(source_pad)
        return None

    def get_output_label(self, pad_index: int = 0) -> str:
        """Get the label for an output pad."""
        if pad_index in self.output_labels:
            return self.output_labels[pad_index]
        return f"{self.label}_out{pad_index}" if pad_index > 0 else self.label

    def to_filter_string(self) -> str:
        """Convert this node to an FFmpeg filter string."""
        # Convert parameters to filter string format
        param_str = ':'.join(f"{k}={_escape_param(v)}" for k, v in self.params.items())
        return f"{self.filter_type}={param_str}" if param_str else self.filter_type

    def validate(self) -> List[str]:
        """Validate this node's configuration."""
        # Validate using the filter registry
        registry = FilterRegistry.get_instance()
        return registry.validate_filter(self)


class FilterGraph:
    """Represents a complete FFmpeg filter graph."""

    def __init__(self):
        """Initialize an empty filter graph."""
        self.nodes: List[FilterNode] = []  # All nodes in the graph
        self.inputs: Dict[str, Tuple[FilterNode, int]] = {}  # External input labels mapped to first node using them
        self.outputs: Dict[str, Tuple[FilterNode, int]] = {}  # External output labels mapped to last node producing them
        self.registry = FilterRegistry.get_instance()

    def add_node(self, node: FilterNode) -> FilterNode:
        """Add a node to the graph."""
        self.nodes.append(node)
        return node

    def create_node(self, filter_type: str, label: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> FilterNode:
        """Create and add a new filter node."""
        node = FilterNode(filter_type, label, params)
        return self.add_node(node)

    def connect(self, source: FilterNode, target: FilterNode, source_pad: int = 0, target_pad: int = 0) -> 'FilterGraph':
        """Connect two nodes in the graph."""
        target.add_input(source, target_pad, source_pad)
        return self

    def set_input(self, label: str, node: FilterNode, pad: int = 0) -> 'FilterGraph':
        """Set an external input connection."""
        self.inputs[label] = (node, pad)
        node.set_input_label(pad, label)
        return self

    def set_output(self, label: str, node: FilterNode, pad: int = 0) -> 'FilterGraph':
        """Set an external output connection."""
        self.outputs[label] = (node, pad)
        node.set_output_label(pad, label)
        return self

    def validate(self) -> List[str]:
        """Validate the entire filter graph."""
        errors = []

        # Validate each node
        for node in self.nodes:
            node_errors = node.validate()
            if node_errors:
                errors.extend(node_errors)

        # Validate graph structure (no cycles, all inputs connected, etc.)
        structure_errors = self._validate_structure()
        if structure_errors:
            errors.extend(structure_errors)

        return errors
    
    def to_filter_string(self) -> str:
        """Convert the graph to an FFmpeg filtergraph string."""
        if not self.nodes:
            return ""

        errors = self.validate()
        if errors:
            raise ValueError(f"Invalid filter graph: {'; '.join(errors)}")

        # Use the converter to build the filter string
        from .converters import FilterGraphConverter
        return FilterGraphConverter.to_string(self)

    def _validate_structure(self) -> List[str]:
        """Validate the overall graph structure."""
        errors = []
        # Check for cycles (would happen during topological sort if present)
        try:
            from .converters import FilterGraphConverter
            FilterGraphConverter._topological_sort(self)
        except ValueError as e:
            errors.append(str(e))

        # Check that all nodes have at least one input or are connected to an external input
        for node in self.nodes:
            metadata = self.registry.get_filter_metadata(node.filter_type) or {}
            min_inputs = metadata.get('min_inputs', 0)

            if min_inputs > 0 and not node.inputs and not any(node == input_node for input_node, _ in self.inputs.values()):
                errors.append(f"Node '{node.label}' has no inputs and is not connected to an external input")

            # Check that nodes with maximum inputs don't exceed it
            max_inputs = metadata.get('max_inputs', float('inf'))

            if len(node.inputs) > max_inputs:
                errors.append(f"Node '{node.label}' has {len(node.inputs)} inputs but max allowed is {max_inputs}")

        return errors