import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add necessary path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from audiovisualizer.ffmpeg_filter_graph.core import FilterNode, FilterGraph, _escape_param


@pytest.mark.unit
def test_escape_param():
    """Test parameter escaping for filter strings."""
    # Test numeric values
    assert _escape_param(100) == "100"
    assert _escape_param(3.14) == "3.14"
    
    # Test regular strings
    assert _escape_param("text") == "text"
    
    # Test strings with special characters
    assert _escape_param("text:with:colons") == "'text\\:with\\:colons'"
    assert _escape_param("comma,separated") == "'comma\\,separated'"
    assert _escape_param("[brackets]") == "'\\[brackets\\]'"
    assert _escape_param("backslash\\") == "'backslash\\\\'"


@pytest.mark.unit
def test_filter_node_creation():
    """Test creating a filter node."""
    # Test with minimal parameters
    node1 = FilterNode('overlay')
    assert node1.filter_type == 'overlay'
    assert node1.label.startswith('overlay_')
    assert node1.params == {}
    assert node1.inputs == []
    assert node1.outputs == []
    
    # Test with specified parameters
    params = {'x': 10, 'y': 20, 'format': 'rgb'}
    node2 = FilterNode('overlay', 'my_overlay', params)
    assert node2.filter_type == 'overlay'
    assert node2.label == 'my_overlay'
    assert node2.params == params


@pytest.mark.unit
def test_filter_node_connections():
    """Test connecting filter nodes."""
    # Create two nodes
    node1 = FilterNode('format', 'format1', {'pix_fmt': 'yuva420p'})
    node2 = FilterNode('overlay', 'overlay1', {'x': 10, 'y': 20})
    
    # Connect node1 to node2
    node2.add_input(node1)
    
    # Check connections
    assert len(node2.inputs) == 1
    assert node2.inputs[0] == (node1, 0)
    assert len(node1.outputs) == 1
    assert node1.outputs[0] == (node2, 0)
    
    # Test with specific pad indices
    node3 = FilterNode('overlay', 'overlay2', {'x': 30, 'y': 40})
    node3.add_input(node1, 1, 0)  # Connect node1 to node3's pad 1
    
    assert len(node3.inputs) == 1
    assert node3.inputs[0] == (node1, 1)
    assert len(node1.outputs) == 2
    assert node1.outputs[1] == (node3, 0)


@pytest.mark.unit
def test_filter_node_to_string():
    """Test converting filter node to string."""
    # Simple node
    node1 = FilterNode('format', params={'pix_fmt': 'yuva420p'})
    assert node1.to_filter_string() == "format=pix_fmt=yuva420p"
    
    # Node with no parameters
    node2 = FilterNode('null')
    assert node2.to_filter_string() == "null"
    
    # Node with special characters in parameters
    node3 = FilterNode('drawtext', params={
        'text': 'Hello, World!',
        'fontfile': '/path/to/font.ttf',
        'x': 10,
        'y': 20
    })
    # We expect commas to be escaped
    filter_str = node3.to_filter_string()
    assert 'drawtext=' in filter_str
    assert 'text=\'Hello\\, World!\'' in filter_str or "text='Hello\\, World!'" in filter_str
    assert 'fontfile=/path/to/font.ttf' in filter_str
    assert 'x=10' in filter_str
    assert 'y=20' in filter_str


@pytest.mark.unit
def test_filter_graph_creation_and_connection():
    """Test creating and connecting nodes in a filter graph."""
    graph = FilterGraph()
    
    # Create nodes
    format_node = graph.create_node('format', 'format1', {'pix_fmt': 'yuva420p'})
    overlay_node = graph.create_node('overlay', 'overlay1', {'x': 10, 'y': 20})
    
    # Connect nodes
    graph.connect(format_node, overlay_node)
    
    # Check graph state
    assert len(graph.nodes) == 2
    assert format_node in graph.nodes
    assert overlay_node in graph.nodes
    assert overlay_node.inputs[0] == (format_node, 0)
    
    # Set external input and output
    graph.set_input('0:v', format_node)
    graph.set_output('out', overlay_node)
    
    # Check external connections
    assert graph.inputs['0:v'] == (format_node, 0)
    assert graph.outputs['out'] == (overlay_node, 0)
    assert format_node.input_labels[0] == '0:v'
    assert overlay_node.output_labels[0] == 'out'


@pytest.mark.unit
def test_filter_graph_to_string():
    """Test converting filter graph to string."""
    # Create a simple graph
    graph = FilterGraph()
    
    # Create a basic chain: input -> format -> overlay -> output
    format_node = graph.create_node('format', 'format1', {'pix_fmt': 'yuva420p'})
    overlay_node = graph.create_node('overlay', 'overlay1', {'x': 10, 'y': 20})
    
    # Set external input/output
    graph.set_input('0:v', format_node)
    graph.connect(format_node, overlay_node)
    graph.set_output('out', overlay_node)
    
    # Mock the validation method to avoid registry dependencies
    with patch.object(FilterGraph, 'validate', return_value=[]):
        with patch('audiovisualizer.ffmpeg_filter_graph.converters.FilterGraphConverter.to_string') as mock_to_string:
            mock_to_string.return_value = "[0:v]format=pix_fmt=yuva420p[format1];[format1]overlay=x=10:y=20[out]"
            filter_str = graph.to_filter_string()
            
            # Check the result
            assert filter_str == "[0:v]format=pix_fmt=yuva420p[format1];[format1]overlay=x=10:y=20[out]"
            mock_to_string.assert_called_once_with(graph)


@pytest.mark.unit
def test_empty_filter_graph_to_string():
    """Test converting an empty filter graph to string."""
    graph = FilterGraph()
    assert graph.to_filter_string() == ""