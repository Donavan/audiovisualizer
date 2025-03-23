import os
import pytest
import tempfile
from pathlib import Path

from audiovisualizer.ffmpeg_filter_graph.core import FilterGraph, FilterNode
from audiovisualizer.ffmpeg_filter_graph.visualizers import FilterGraphVisualizer, JSONVisualizer


@pytest.fixture
def simple_graph():
    """Create a simple filter graph for testing."""
    # Create a graph with split, overlay, and scale filters
    graph = FilterGraph()
    
    # Add nodes
    split = graph.create_node('split', 'split', {})
    scale1 = graph.create_node('scale', 'scale1', {'width': 640, 'height': 480})
    scale2 = graph.create_node('scale', 'scale2', {'width': 320, 'height': 240})
    overlay = graph.create_node('overlay', 'overlay', {'x': 10, 'y': 10})
    
    # Connect nodes
    graph.connect(split, scale1)
    graph.connect(split, scale2, source_pad=1)
    graph.connect(scale1, overlay)
    graph.connect(scale2, overlay, target_pad=1)
    
    # Set inputs and outputs
    graph.set_input('in', split)
    graph.set_output('out', overlay)
    
    return graph


@pytest.fixture
def complex_graph():
    """Create a more complex filter graph for testing."""
    graph = FilterGraph()
    
    # Add nodes for a complex audio-visual processing chain
    split = graph.create_node('split', 'split', {})
    
    # Video processing branch 1
    scale = graph.create_node('scale', 'scale', {'width': 720, 'height': 480})
    fade = graph.create_node('fade', 'fade', {'type': 'in', 'start_time': 0, 'duration': 2})
    
    # Video processing branch 2
    crop = graph.create_node('crop', 'crop', {'out_w': 640, 'out_h': 360, 'x': 40, 'y': 20})
    colorize = graph.create_node('colorize', 'colorize', {'hue': 180, 'saturation': 0.5})
    
    # Audio processing
    aecho = graph.create_node('aecho', 'aecho', {'in_gain': 0.6, 'out_gain': 0.3, 'delays': 1000, 'decays': 0.5})
    volume = graph.create_node('volume', 'volume', {'volume': 2.0})
    
    # Final mixing
    overlay = graph.create_node('overlay', 'overlay', {'x': 0, 'y': 0})
    
    # Connect nodes
    graph.connect(split, scale)
    graph.connect(split, crop, source_pad=1)
    graph.connect(scale, fade)
    graph.connect(crop, colorize)
    graph.connect(fade, overlay)
    graph.connect(colorize, overlay, target_pad=1)
    graph.connect(aecho, volume)
    
    # Set inputs and outputs
    graph.set_input('video', split)
    graph.set_input('audio', aecho)
    graph.set_output('video_out', overlay)
    graph.set_output('audio_out', volume)
    
    return graph


class TestFilterGraphVisualizer:
    
    def test_to_dot(self, simple_graph):
        """Test generating DOT representation of a filter graph."""
        dot = FilterGraphVisualizer._to_dot(simple_graph, FilterGraphVisualizer.DEFAULT_STYLES)
        
        # Check for basic structure elements
        assert 'digraph FilterGraph {' in dot
        assert 'rankdir=LR;' in dot
        
        # Check for nodes
        assert '"split"' in dot
        assert '"scale1"' in dot
        assert '"scale2"' in dot
        assert '"overlay"' in dot
        
        # Check for connections
        assert '"split" -> "scale1"' in dot
        assert '"split" -> "scale2"' in dot
        assert '"scale1" -> "overlay"' in dot
        assert '"scale2" -> "overlay"' in dot
        
        # Check for external inputs/outputs
        assert '"in"' in dot
        assert '"out_out"' in dot
        assert '"in" -> "split"' in dot
        assert '"overlay" -> "out_out"' in dot
    
    def test_visualize(self, simple_graph):
        """Test the main visualize method."""
        # Just test that it returns a string without errors
        dot = FilterGraphVisualizer.visualize(simple_graph)
        assert isinstance(dot, str)
        assert 'digraph FilterGraph {' in dot
    
    def test_save_visualization(self, simple_graph):
        """Test saving visualization to a file."""
        # Use a temporary file for the test
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'test_graph')
            
            try:
                # Try to use graphviz if available
                import graphviz
                
                # Generate DOT and save file
                dot = FilterGraphVisualizer._to_dot(simple_graph, FilterGraphVisualizer.DEFAULT_STYLES)
                result = FilterGraphVisualizer._save_visualization(dot, output_path, 'dot')
                
                # Check that file was created
                assert result is not None
                assert os.path.exists(result)
                
            except ImportError:
                # Skip the test if graphviz is not available
                pytest.skip("Graphviz package not installed")
    
    def test_custom_styles(self, simple_graph):
        """Test custom styling options."""
        custom_styles = {
            'node': {
                'fillcolor': 'lightgray',
                'fontname': 'Courier'
            },
            'edge': {
                'color': 'red'
            }
        }
        
        # Generate DOT with custom styles
        dot = FilterGraphVisualizer.visualize(simple_graph, styles=custom_styles)
        
        # Check that custom styles were applied
        assert 'fillcolor=lightgray' in dot
        assert 'fontname=Courier' in dot
        assert 'color=red' in dot
    
    def test_complex_graph(self, complex_graph):
        """Test visualization of a more complex graph."""
        dot = FilterGraphVisualizer.visualize(complex_graph)
        
        # Check for basic structure elements
        assert 'digraph FilterGraph {' in dot
        
        # Check for all nodes
        for node_name in ['split', 'scale', 'fade', 'crop', 'colorize', 'overlay', 'aecho', 'volume']:
            assert f'"{node_name}"' in dot
        
        # Check for external inputs/outputs
        assert '"video"' in dot
        assert '"audio"' in dot
        assert '"video_out_out"' in dot
        assert '"audio_out_out"' in dot


class TestJSONVisualizer:
    
    def test_to_json(self, simple_graph):
        """Test conversion to JSON format."""
        json_str = JSONVisualizer.to_json(simple_graph)
        
        # Check that it produces a valid JSON string
        import json
        data = json.loads(json_str)
        
        # Check structure
        assert 'nodes' in data
        assert 'edges' in data
        assert 'inputs' in data
        assert 'outputs' in data
        
        # Check content
        assert len(data['nodes']) == 4  # split, scale1, scale2, overlay
        assert len(data['edges']) == 4  # The connections between them
        assert len(data['inputs']) == 1  # 'in'
        assert len(data['outputs']) == 1  # 'out'
        
        # Check specific node data
        node_labels = [node['label'] for node in data['nodes']]
        assert 'split' in node_labels
        assert 'scale1' in node_labels
        assert 'scale2' in node_labels
        assert 'overlay' in node_labels
        
        # Check input/output
        assert data['inputs'][0]['label'] == 'in'
        assert data['outputs'][0]['label'] == 'out'
    
    def test_save_json(self, simple_graph):
        """Test saving JSON to a file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'test_graph.json')
            
            # Save the JSON file
            JSONVisualizer.save_json(simple_graph, output_path)
            
            # Check that file was created
            assert os.path.exists(output_path)
            
            # Check that it contains valid JSON
            with open(output_path, 'r') as f:
                content = f.read()
            
            import json
            data = json.loads(content)
            assert 'nodes' in data
            assert 'edges' in data