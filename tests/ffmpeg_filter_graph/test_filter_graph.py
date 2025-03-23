import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add necessary path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from audiovisualizer.ffmpeg_filter_graph.core import FilterNode, FilterGraph
from audiovisualizer.ffmpeg_filter_graph.converters import FilterGraphConverter


@pytest.mark.unit
class TestFilterGraph:
    """
    Test suite for the FilterGraph class.
    """

    def test_graph_creation_and_node_addition(self):
        """Test creating a graph and adding nodes."""
        # Create an empty graph
        graph = FilterGraph()
        assert len(graph.nodes) == 0
        assert graph.inputs == {}
        assert graph.outputs == {}
        
        # Add a node using add_node
        node1 = FilterNode('format', 'fmt', {'pix_fmt': 'yuv420p'})
        result = graph.add_node(node1)
        
        assert len(graph.nodes) == 1
        assert graph.nodes[0] == node1
        assert result == node1  # Should return the added node
        
        # Add another node
        node2 = FilterNode('scale', 'scl', {'width': 1280, 'height': 720})
        graph.add_node(node2)
        
        assert len(graph.nodes) == 2
        assert graph.nodes[1] == node2

    def test_creating_nodes_with_create_node(self):
        """Test creating nodes with the create_node method."""
        graph = FilterGraph()
        
        # Create a node with the create_node method
        node = graph.create_node('overlay', 'ovl', {'x': 10, 'y': 20})
        
        # Verify node was created and added to the graph
        assert len(graph.nodes) == 1
        assert graph.nodes[0] == node
        assert node.filter_type == 'overlay'
        assert node.label == 'ovl'
        assert node.params == {'x': 10, 'y': 20}
        
        # Create another node without label and params
        node2 = graph.create_node('null')
        
        assert len(graph.nodes) == 2
        assert graph.nodes[1] == node2
        assert node2.filter_type == 'null'
        assert node2.label.startswith('null_')
        assert node2.params == {}

    def test_node_reference_tracking(self):
        """Test that node references are properly tracked in the graph."""
        graph = FilterGraph()
        
        # Create several nodes
        format_node = graph.create_node('format', 'fmt')
        scale_node = graph.create_node('scale', 'scl')
        overlay_node = graph.create_node('overlay', 'ovl')
        
        # Verify all nodes are tracked
        assert len(graph.nodes) == 3
        assert format_node in graph.nodes
        assert scale_node in graph.nodes
        assert overlay_node in graph.nodes
        
        # Verify node order is maintained
        assert graph.nodes.index(format_node) == 0
        assert graph.nodes.index(scale_node) == 1
        assert graph.nodes.index(overlay_node) == 2

    def test_connect_method(self):
        """Test the connect method for creating connections between nodes."""
        graph = FilterGraph()
        
        # Create nodes
        node1 = graph.create_node('format', 'fmt')
        node2 = graph.create_node('scale', 'scl')
        
        # Connect the nodes
        result = graph.connect(node1, node2)
        
        # Verify connection was made
        assert len(node2.inputs) == 1
        assert node2.inputs[0] == (node1, 0)
        assert len(node1.outputs) == 1
        assert node1.outputs[0] == (node2, 0)
        
        # Verify method returns the graph for chaining
        assert result == graph
        
        # Test with custom pad indices
        node3 = graph.create_node('overlay', 'ovl')
        graph.connect(node2, node3, source_pad=1, target_pad=2)
        
        assert len(node3.inputs) == 1
        assert node3.inputs[0] == (node2, 2)
        assert len(node2.outputs) == 1
        assert node2.outputs[0] == (node3, 1)

    def test_multiple_connections_between_nodes(self):
        """Test creating multiple connections between nodes."""
        graph = FilterGraph()
        
        # Create nodes
        node1 = graph.create_node('split', 'splitter', {'outputs': 2})
        node2 = graph.create_node('overlay', 'overlay')
        
        # Create multiple connections from node1 to node2
        graph.connect(node1, node2, source_pad=0, target_pad=0)
        graph.connect(node1, node2, source_pad=1, target_pad=1)
        
        # Verify connections
        assert len(node2.inputs) == 2
        assert node2.inputs[0] == (node1, 0)
        assert node2.inputs[1] == (node1, 1)
        
        assert len(node1.outputs) == 2
        assert node1.outputs[0] == (node2, 0)
        assert node1.outputs[1] == (node2, 1)

    def test_complex_graph_structure_building(self):
        """Test building a complex graph structure."""
        graph = FilterGraph()
        
        # Create a more complex graph with multiple paths:
        # input -> split -> [scale_1, scale_2] -> overlay -> output
        
        # Create nodes
        input_node = graph.create_node('movie', 'input', {'filename': 'input.mp4'})
        split_node = graph.create_node('split', 'splitter', {'outputs': 2})
        scale1_node = graph.create_node('scale', 'scale1', {'width': 640, 'height': 360})
        scale2_node = graph.create_node('scale', 'scale2', {'width': 1280, 'height': 720})
        overlay_node = graph.create_node('overlay', 'overlay', {'x': 10, 'y': 10})
        
        # Build connections
        graph.connect(input_node, split_node)
        graph.connect(split_node, scale1_node, source_pad=0)
        graph.connect(split_node, scale2_node, source_pad=1)
        graph.connect(scale1_node, overlay_node, target_pad=0)
        graph.connect(scale2_node, overlay_node, target_pad=1)
        
        # Verify structure
        # input -> split
        assert split_node.inputs[0] == (input_node, 0)
        
        # split -> scale1, split -> scale2
        assert scale1_node.inputs[0] == (split_node, 0)
        assert scale2_node.inputs[0] == (split_node, 1)
        
        # scale1 -> overlay (pad 0), scale2 -> overlay (pad 1)
        assert overlay_node.inputs[0] == (scale1_node, 0)
        assert overlay_node.inputs[1] == (scale2_node, 1)

    def test_set_input_and_input_mapping(self):
        """Test set_input method and input mapping."""
        graph = FilterGraph()
        
        # Create a node
        node = graph.create_node('scale', 'scl')
        
        # Set an external input
        result = graph.set_input('video', node)
        
        # Verify input mapping
        assert 'video' in graph.inputs
        assert graph.inputs['video'] == (node, 0)
        assert node.input_labels[0] == 'video'
        
        # Verify method returns the graph for chaining
        assert result == graph
        
        # Test with a specific pad index
        node2 = graph.create_node('overlay', 'ovl')
        graph.set_input('background', node2, pad=1)
        
        assert graph.inputs['background'] == (node2, 1)
        assert node2.input_labels[1] == 'background'

    def test_set_output_and_output_mapping(self):
        """Test set_output method and output mapping."""
        graph = FilterGraph()
        
        # Create a node
        node = graph.create_node('scale', 'scl')
        
        # Set an external output
        result = graph.set_output('video_out', node)
        
        # Verify output mapping
        assert 'video_out' in graph.outputs
        assert graph.outputs['video_out'] == (node, 0)
        assert node.output_labels[0] == 'video_out'
        
        # Verify method returns the graph for chaining
        assert result == graph
        
        # Test with a specific pad index
        node2 = graph.create_node('split', 'spl')
        graph.set_output('second_output', node2, pad=1)
        
        assert graph.outputs['second_output'] == (node2, 1)
        assert node2.output_labels[1] == 'second_output'

    def test_relationship_between_external_connections_and_node_labels(self):
        """Test relationship between external connections and node labels."""
        graph = FilterGraph()
        
        # Create some nodes
        input_node = graph.create_node('buffer', 'buf')
        process_node = graph.create_node('scale', 'scl')
        output_node = graph.create_node('format', 'fmt')
        
        # Connect the nodes
        graph.connect(input_node, process_node)
        graph.connect(process_node, output_node)
        
        # Set external input and output
        graph.set_input('in', input_node)
        graph.set_output('out', output_node)
        
        # Verify labels
        assert input_node.input_labels[0] == 'in'
        assert output_node.output_labels[0] == 'out'
        
        # Test the input/output label inheritance
        # When we generate a filter string, process_node would be connected to input_node's output
        # and process_node's output would be connected to output_node's input
        assert process_node.get_input_label(0) == input_node.get_output_label(0)

    @patch.object(FilterGraph, 'validate')
    def test_valid_graph_validation(self, mock_validate):
        """Test validation of a valid graph."""
        # Setup mock to return no errors
        mock_validate.return_value = []
        
        graph = FilterGraph()
        
        # Create a simple valid graph
        input_node = graph.create_node('movie', 'in', {'filename': 'input.mp4'})
        output_node = graph.create_node('format', 'out', {'pix_fmt': 'yuv420p'})
        graph.connect(input_node, output_node)
        
        # Call to_filter_string, which calls validate
        with patch.object(FilterGraphConverter, 'to_string', return_value='dummy_string'):
            filter_str = graph.to_filter_string()
            
            # Verify validation was called
            mock_validate.assert_called_once()
            assert filter_str == 'dummy_string'

    def test_detection_of_cycles_in_graph(self):
        """Test detection of cycles in the graph during validation."""
        graph = FilterGraph()
        
        # Create a simple cycle: A -> B -> C -> A
        nodeA = graph.create_node('format', 'A')
        nodeB = graph.create_node('scale', 'B')
        nodeC = graph.create_node('overlay', 'C')
        
        graph.connect(nodeA, nodeB)
        graph.connect(nodeB, nodeC)
        graph.connect(nodeC, nodeA)  # This creates the cycle
        
        # Validation should detect the cycle
        errors = graph._validate_structure()
        
        # Check that at least one error is about cycles
        assert any('cycle' in error.lower() for error in errors)

    def test_disconnected_node_detection(self):
        """Test detection of disconnected nodes during validation."""
        graph = FilterGraph()
        
        # Create nodes but don't connect them all
        node1 = graph.create_node('movie', 'in', {'filename': 'input.mp4'})
        node2 = graph.create_node('overlay', 'ov')  # This needs inputs but has none
        
        # Mock the registry to indicate overlay requires inputs
        with patch.object(graph.registry, 'get_filter_metadata') as mock_metadata:
            mock_metadata.return_value = {'min_inputs': 1}  # Overlay requires at least 1 input
            
            # Validation should detect the disconnected node
            errors = graph._validate_structure()
            
            # Check that at least one error is about the disconnected node
            assert any('has no inputs' in error for error in errors)
            assert any('ov' in error for error in errors)

    def test_validation_of_missing_inputs(self):
        """Test validation of missing inputs for nodes requiring them."""
        graph = FilterGraph()
        
        # Create a node that requires multiple inputs but only connect one
        background = graph.create_node('movie', 'bg', {'filename': 'bg.mp4'})
        overlay = graph.create_node('overlay', 'ov')  # Overlay typically needs 2 inputs
        
        # Connect only one input
        graph.connect(background, overlay)
        
        # Mock validation at the node level
        with patch.object(overlay, 'validate') as mock_node_validate:
            mock_node_validate.return_value = [
                "Filter 'overlay' requires at least 2 inputs, got 1"
            ]
            
            # Run full graph validation
            errors = graph.validate()
            
            # Check that the input validation error is included
            assert any('requires at least 2 inputs' in error for error in errors)

    @patch.object(FilterGraphConverter, 'to_string')
    def test_to_filter_string_for_simple_graphs(self, mock_to_string):
        """Test to_filter_string for simple graphs."""
        # Setup mock
        expected_string = "[in]format=pix_fmt=yuv420p[out]"
        mock_to_string.return_value = expected_string
        
        # Create a simple graph
        graph = FilterGraph()
        node = graph.create_node('format', 'fmt', {'pix_fmt': 'yuv420p'})
        graph.set_input('in', node)
        graph.set_output('out', node)
        
        # Mock validation to return no errors
        with patch.object(graph, 'validate', return_value=[]):
            filter_str = graph.to_filter_string()
            
            # Verify converter was called and returned the expected string
            mock_to_string.assert_called_once_with(graph)
            assert filter_str == expected_string

    @patch.object(FilterGraphConverter, 'to_string')
    def test_to_filter_string_for_complex_graphs(self, mock_to_string):
        """Test to_filter_string for complex graphs."""
        # Setup mock
        expected_string = "[in]split[split1][split2];[split1]scale=w=640:h=360[small];[split2]scale=w=1280:h=720[large];[small][large]overlay=x=10:y=10[out]"
        mock_to_string.return_value = expected_string
        
        # Create a more complex graph
        graph = FilterGraph()
        input_node = graph.create_node('split', 'split')
        scale1 = graph.create_node('scale', 'scale1', {'w': 640, 'h': 360})
        scale2 = graph.create_node('scale', 'scale2', {'w': 1280, 'h': 720})
        overlay = graph.create_node('overlay', 'overlay', {'x': 10, 'y': 10})
        
        graph.set_input('in', input_node)
        graph.connect(input_node, scale1, source_pad=0)
        graph.connect(input_node, scale2, source_pad=1)
        graph.connect(scale1, overlay, target_pad=0)
        graph.connect(scale2, overlay, target_pad=1)
        graph.set_output('out', overlay)
        
        # Mock validation to return no errors
        with patch.object(graph, 'validate', return_value=[]):
            filter_str = graph.to_filter_string()
            
            # Verify converter was called and returned the expected string
            mock_to_string.assert_called_once_with(graph)
            assert filter_str == expected_string

    def test_handling_of_empty_graphs(self):
        """Test to_filter_string handling of empty graphs."""
        graph = FilterGraph()
        
        # An empty graph should return an empty string
        assert graph.to_filter_string() == ""

    def test_validation_errors_during_string_generation(self):
        """Test validation errors during string generation."""
        graph = FilterGraph()
        
        # Create an invalid graph (overlay with no inputs)
        overlay = graph.create_node('overlay', 'ov')
        
        # Mock validation to return errors
        with patch.object(graph, 'validate', return_value=["Node 'ov' has no inputs and is not connected to an external input"]):
            # Attempt to generate filter string
            with pytest.raises(ValueError) as excinfo:
                graph.to_filter_string()
            
            # Verify error contains validation message
            assert "Invalid filter graph" in str(excinfo.value)
            assert "Node 'ov' has no inputs" in str(excinfo.value)