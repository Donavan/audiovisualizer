# Filter Graph Visualization Tools

This module provides tools for visualizing FFmpeg filter graphs to help with debugging, documentation, and understanding complex filter chains.

## Features

- Generate GraphViz DOT format representations of filter graphs
- Create visual diagrams in various formats (PNG, SVG, PDF)
- Export filter graphs as JSON for custom visualization tools
- Style customization for nodes and edges
- Display filter parameters and connections
- Support for both command-line and interactive environments

## Requirements

- Core functionality requires no external dependencies
- Visual output generation requires the `graphviz` Python package and the GraphViz system package

## Installation

To enable full visualization capabilities:

```bash
# Install the Python package
pip install graphviz

# On Debian/Ubuntu
apt-get install graphviz

# On macOS
brew install graphviz

# On Windows
# Download and install from https://graphviz.org/download/
```

## Basic Usage

### Visualizing a Filter Graph

```python
from audiovisualizer.ffmpeg_filter_graph.core import FilterGraph
from audiovisualizer.ffmpeg_filter_graph.visualizers import FilterGraphVisualizer

# Create a filter graph
graph = FilterGraph()
split = graph.create_node('split')
scale = graph.create_node('scale', params={'width': 640, 'height': 360})
graph.connect(split, scale)
graph.set_input('in', split)
graph.set_output('out', scale)

# Generate a visualization
FilterGraphVisualizer.visualize(graph, 'my_graph', format='png')
```

### Custom Styling

```python
# Define custom styles
custom_styles = {
    'node': {
        'fillcolor': 'lightblue',
        'fontname': 'Arial',
        'style': 'filled,rounded'
    },
    'edge': {
        'color': 'darkblue',
        'penwidth': '1.5'
    }
}

# Apply custom styles to the visualization
FilterGraphVisualizer.visualize(graph, 'styled_graph', format='svg', styles=custom_styles)
```

### JSON Export

```python
from audiovisualizer.ffmpeg_filter_graph.visualizers import JSONVisualizer

# Export the graph as JSON
json_str = JSONVisualizer.to_json(graph)
print(json_str)

# Save to a file
JSONVisualizer.save_json(graph, 'graph.json')
```

## HTML Integration

For web applications or Jupyter notebooks, you can generate HTML/SVG content:

```python
# Generate HTML with embedded SVG
html_content = FilterGraphVisualizer.generate_html_preview(graph)

# In a Jupyter notebook, display the result
from IPython.display import HTML
HTML(html_content)
```

## Output Formats

The visualizer supports all output formats supported by GraphViz:

- `png`: Portable Network Graphics (default)
- `svg`: Scalable Vector Graphics
- `pdf`: Portable Document Format
- `dot`: GraphViz DOT format
- `plain`: Plain text format

## Advanced Usage

### Working with Complex Graphs

For complex filter graphs, you can highlight specific paths or nodes by using custom styles:

```python
# Create a style that highlights a specific path
highlight_styles = {
    'node': {
        'fillcolor': 'lightgray',  # Default fill color
    },
    'edge': {
        'color': 'gray',  # Default edge color
    },
    # You can add custom node styles for specific nodes
    'node_styles': {
        'important_node': {
            'fillcolor': 'yellow',
            'penwidth': '2.0'
        }
    }
}

# Apply the styles when visualizing
FilterGraphVisualizer.visualize(graph, 'highlighted_path', styles=highlight_styles)
```

### Debugging with DOT Format

If you're having issues with GraphViz installation, you can still generate DOT files:

```python
# Generate DOT representation
dot_str = FilterGraphVisualizer.visualize(graph)

# Save to a file manually
with open('my_graph.dot', 'w') as f:
    f.write(dot_str)
```

You can then use online GraphViz tools to render the DOT file.

## Troubleshooting

- If you get an error about GraphViz not being found, make sure both the Python package and system package are installed.
- On Windows, you may need to add the GraphViz bin directory to your PATH.
- For large graphs, you may need to increase the graph size limit in GraphViz settings.