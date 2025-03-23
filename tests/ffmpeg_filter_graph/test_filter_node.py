import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
from uuid import uuid4

# Add necessary path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from audiovisualizer.ffmpeg_filter_graph.core import FilterNode, _escape_param
from audiovisualizer.ffmpeg_filter_graph.registry import FilterRegistry


@pytest.mark.unit
class TestFilterNode:
    """
    Test suite for the FilterNode class.
    """

    def test_node_initialization(self):
        """Test filter node initialization with various parameters."""
        # Test with minimal parameters
        node1 = FilterNode('overlay')
        assert node1.filter_type == 'overlay'
        assert node1.label.startswith('overlay_')
        assert node1.params == {}
        assert node1.inputs == []
        assert node1.outputs == []
        assert node1.input_labels == {}
        assert node1.output_labels == {}

        # Test with custom label
        node2 = FilterNode('scale', 'my_scale')
        assert node2.filter_type == 'scale'
        assert node2.label == 'my_scale'
        assert node2.params == {}

        # Test with parameters
        params = {'width': 1280, 'height': 720}
        node3 = FilterNode('scale', 'hd_scale', params)
        assert node3.filter_type == 'scale'
        assert node3.label == 'hd_scale'
        assert node3.params == params

    def test_node_label_generation(self):
        """Test automatic label generation when none is provided."""
        # Create multiple nodes of the same type
        node1 = FilterNode('format')
        node2 = FilterNode('format')

        # Verify they have different auto-generated labels
        assert node1.label != node2.label
        assert node1.label.startswith('format_')
        assert node2.label.startswith('format_')
        
        # Verify the label structure (should include a UUID part)
        assert len(node1.label.split('_')[1]) == 8

    def test_parameter_handling(self):
        """Test node parameter handling."""
        # Test with empty parameters
        node1 = FilterNode('null')
        assert node1.params == {}

        # Test with various parameter types
        params = {
            'x': 10,  # integer
            'y': 20.5,  # float
            'text': 'Hello',  # string
            'enable': True,  # boolean
        }
        node2 = FilterNode('drawtext', params=params)
        assert node2.params == params

        # Test updating parameters after creation
        node2.params['fontsize'] = 24
        assert node2.params['fontsize'] == 24
        assert len(node2.params) == 5

    def test_add_input_functionality(self):
        """Test the add_input method."""
        # Create nodes
        source = FilterNode('movie', 'source', {'filename': 'input.mp4'})
        target = FilterNode('scale', 'scaler', {'width': 1280, 'height': 720})

        # Connect source to target
        result = target.add_input(source)

        # Verify connections
        assert len(target.inputs) == 1
        assert target.inputs[0] == (source, 0)
        assert len(source.outputs) == 1
        assert source.outputs[0] == (target, 0)
        
        # Verify method returns the node for chaining
        assert result == target

        # Test with custom pad indices
        target2 = FilterNode('overlay', 'overlay')
        target2.add_input(source, pad_index=1, source_pad=0)
        
        assert len(target2.inputs) == 1
        assert target2.inputs[0] == (source, 1)
        assert len(source.outputs) == 2
        assert source.outputs[1] == (target2, 0)
        
        # Test with None source (external input)
        target3 = FilterNode('scale', 'ext_scale')
        target3.add_input(None, pad_index=0)
        assert len(target3.inputs) == 1
        assert target3.inputs[0] == (None, 0)

    def test_input_output_relationship_consistency(self):
        """Test consistency between inputs and outputs of connected nodes."""
        # Create a chain of nodes
        node1 = FilterNode('format', 'fmt')
        node2 = FilterNode('scale', 'scl')
        node3 = FilterNode('overlay', 'ovl')

        # Connect the chain: node1 -> node2 -> node3
        node2.add_input(node1)
        node3.add_input(node2)

        # Verify input-output relationship consistency
        # node1's outputs should match node2's inputs
        assert node1.outputs[0][0] == node2
        assert node2.inputs[0][0] == node1
        
        # node2's outputs should match node3's inputs
        assert node2.outputs[0][0] == node3
        assert node3.inputs[0][0] == node2

    def test_multi_pad_connections(self):
        """Test connections with multiple input/output pads."""
        # Create nodes for testing multi-pad connections
        # overlay takes two inputs: background and foreground
        background = FilterNode('movie', 'background', {'filename': 'bg.mp4'})
        foreground = FilterNode('movie', 'foreground', {'filename': 'fg.png'})
        overlay = FilterNode('overlay', 'combine')

        # Connect background to overlay's first input
        overlay.add_input(background, pad_index=0)
        
        # Connect foreground to overlay's second input
        overlay.add_input(foreground, pad_index=1)

        # Verify both connections
        assert len(overlay.inputs) == 2
        assert overlay.inputs[0] == (background, 0)
        assert overlay.inputs[1] == (foreground, 1)
        
        # Verify outputs on source nodes
        assert background.outputs[0] == (overlay, 0)
        assert foreground.outputs[0] == (overlay, 1)

    def test_circular_connections_detection(self):
        """Test detection of circular connections."""
        # This is typically detected during graph validation or topological sort
        # We'll create a simple circle: A -> B -> C -> A
        nodeA = FilterNode('format', 'A')
        nodeB = FilterNode('scale', 'B')
        nodeC = FilterNode('overlay', 'C')

        # Create the circle
        nodeB.add_input(nodeA)
        nodeC.add_input(nodeB)
        nodeA.add_input(nodeC)  # This creates the circle

        # The actual detection happens in the FilterGraph's _topological_sort method
        # We'll test that the connections are properly recorded
        assert nodeA.inputs[0][0] == nodeC
        assert nodeB.inputs[0][0] == nodeA
        assert nodeC.inputs[0][0] == nodeB
        
        assert nodeA.outputs[0][0] == nodeB
        assert nodeB.outputs[0][0] == nodeC
        assert nodeC.outputs[0][0] == nodeA

    def test_set_get_input_label(self):
        """Test setting and getting input labels."""
        node = FilterNode('scale', 'scaler')

        # Set input label
        node.set_input_label(0, 'main_input')
        
        # Verify label is set
        assert node.input_labels[0] == 'main_input'
        
        # Verify getter returns the label
        assert node.get_input_label(0) == 'main_input'
        
        # Test with another pad index
        node.set_input_label(1, 'secondary_input')
        assert node.get_input_label(1) == 'secondary_input'
        
        # Test getting a non-existent label
        assert node.get_input_label(2) is None
        
        # Test method chaining
        result = node.set_input_label(3, 'another_input')
        assert result == node
        assert node.get_input_label(3) == 'another_input'

    def test_set_get_output_label(self):
        """Test setting and getting output labels."""
        node = FilterNode('scale', 'scaler')

        # Set output label
        node.set_output_label(0, 'main_output')
        
        # Verify label is set
        assert node.output_labels[0] == 'main_output'
        
        # Verify getter returns the label
        assert node.get_output_label(0) == 'main_output'
        
        # Test with another pad index
        node.set_output_label(1, 'secondary_output')
        assert node.get_output_label(1) == 'secondary_output'
        
        # Test default behavior for unlabeled outputs
        # Should return node.label for pad 0 or node.label_outN for pad N>0
        unlabeled_node = FilterNode('format', 'fmt')
        assert unlabeled_node.get_output_label(0) == 'fmt'
        assert unlabeled_node.get_output_label(1) == 'fmt_out1'
        assert unlabeled_node.get_output_label(2) == 'fmt_out2'
        
        # Test method chaining
        result = node.set_output_label(3, 'another_output')
        assert result == node
        assert node.get_output_label(3) == 'another_output'

    def test_label_inheritance_from_connected_nodes(self):
        """Test label inheritance from connected nodes."""
        # Create nodes
        source = FilterNode('movie', 'source')
        target = FilterNode('scale', 'target')

        # Set output label on source
        source.set_output_label(0, 'source_output')
        
        # Connect source to target
        target.add_input(source)
        
        # Target should inherit input label from source's output
        assert target.get_input_label(0) == 'source_output'
        
        # Test with custom pad indices
        source2 = FilterNode('format', 'source2')
        target2 = FilterNode('overlay', 'target2')
        
        source2.set_output_label(1, 'special_output')
        target2.add_input(source2, pad_index=2, source_pad=1)
        
        assert target2.get_input_label(2) == 'special_output'

    def test_to_filter_string_with_various_params(self):
        """Test to_filter_string with various parameter types."""
        # Test with various parameter types
        params = {
            'width': 1280,              # Integer
            'height': 720,              # Integer
            'alpha': 0.5,               # Float
            'text': 'Hello, World!',    # String with special chars
            'enable': True,             # Boolean
            'font': '/path/to/font.ttf' # Path
        }
        node = FilterNode('complexfilter', params=params)
        
        # Generate filter string
        filter_str = node.to_filter_string()
        
        # Verify all parameters are included correctly
        assert 'complexfilter=' in filter_str
        assert 'width=1280' in filter_str
        assert 'height=720' in filter_str
        assert 'alpha=0.5' in filter_str
        assert "text='Hello\\, World!'" in filter_str
        assert 'enable=True' in filter_str
        assert 'font=/path/to/font.ttf' in filter_str
        
        # Test with no parameters
        empty_node = FilterNode('null')
        assert empty_node.to_filter_string() == 'null'

    def test_parameter_escaping_for_special_chars(self):
        """Test parameter escaping for special characters."""
        # Test with various special characters
        special_params = {
            'text1': 'Text with : colons',
            'text2': 'Text with , commas',
            'text3': 'Text with [brackets]',
            'text4': 'Text with \\ backslashes',
            'text5': 'Multiple:\\,[]\\special:chars',
        }
        node = FilterNode('drawtext', params=special_params)
        
        # Generate filter string
        filter_str = node.to_filter_string()
        
        # Verify escaping is correct
        assert "text1='Text with \\: colons'" in filter_str
        assert "text2='Text with \\, commas'" in filter_str
        assert "text3='Text with \\[brackets\\]'" in filter_str
        assert "text4='Text with \\\\ backslashes'" in filter_str
        assert "text5='Multiple\\:\\\\\\,\\[\\]\\\\special\\:chars'" in filter_str

    def test_empty_parameter_handling(self):
        """Test handling of empty parameters."""
        # Test with empty string parameter
        params = {'text': ''}
        node = FilterNode('drawtext', params=params)
        
        filter_str = node.to_filter_string()
        assert 'text=' in filter_str
        
        # Test with None parameter (should be converted to string)
        params = {'text': None}
        node = FilterNode('drawtext', params=params)
        
        filter_str = node.to_filter_string()
        assert 'text=None' in filter_str

    @patch.object(FilterRegistry, 'validate_filter')
    def test_validation_with_valid_config(self, mock_validate):
        """Test validation with valid configuration."""
        # Setup mock to return empty list (no errors)
        mock_validate.return_value = []
        
        # Create a node with valid configuration
        node = FilterNode('format', params={'pix_fmt': 'yuv420p'})
        
        # Validate
        errors = node.validate()
        
        # Verify validation was called and returned no errors
        mock_validate.assert_called_once_with(node)
        assert errors == []
        assert len(errors) == 0

    @patch.object(FilterRegistry, 'validate_filter')
    def test_validation_with_invalid_params(self, mock_validate):
        """Test validation with invalid parameters."""
        # Setup mock to return errors
        mock_validate.return_value = ["Missing required parameter 'text' for filter 'drawtext'"]
        
        # Create a node with invalid configuration
        node = FilterNode('drawtext', params={})
        
        # Validate
        errors = node.validate()
        
        # Verify validation was called and returned errors
        mock_validate.assert_called_once_with(node)
        assert len(errors) == 1
        assert "Missing required parameter 'text'" in errors[0]

    @patch.object(FilterRegistry, 'validate_filter')
    def test_validation_with_missing_required_params(self, mock_validate):
        """Test validation with missing required parameters."""
        # Setup mock to return errors for missing parameters
        mock_validate.return_value = [
            "Missing required parameter 'filename' for filter 'movie'"
        ]
        
        # Create a node with missing required parameters
        node = FilterNode('movie', params={})
        
        # Validate
        errors = node.validate()
        
        # Verify validation results
        mock_validate.assert_called_once_with(node)
        assert len(errors) == 1
        assert "Missing required parameter 'filename'" in errors[0]