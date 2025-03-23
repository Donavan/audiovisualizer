# AudioVisualizer

A Python package for creating audio-reactive visual effects for videos.

## Overview

AudioVisualizer extracts audio features (like frequency bands and amplitude) and uses them to dynamically modify visual elements in videos, creating engaging audio-reactive effects.

## Features

- Object-oriented FFmpeg filter graph representation
- Overlay logos, text, and spectrum visualizations that react to audio
- Clean builder API for creating complex filter graphs
- Validation to catch errors before execution
- Visualization tools for debugging filter graphs

## Installation

```bash
pip install audiovisualizer
```

## Quick Start

```python
from audiovisualizer import process_video

# Create a simple video with logo and text overlays
process_video(
    "input.mp4",
    "output.mp4",
    [
        {
            "type": "logo",
            "path": "logo.png",
            "x": 20,
            "y": 20,
            "scale": (100, 100),
            "opacity": 0.8
        },
        {
            "type": "text",
            "text": "Hello World",
            "font": "font.ttf",
            "size": 36,
            "color": "white",
            "x": 20,
            "y": 150
        }
    ]
)
```

## Using the Filter Graph API

The new filter graph API provides a clean, object-oriented way to work with FFmpeg filter graphs:

```python
from audiovisualizer import AudioVisualizer, FilterGraph

# Initialize the AudioVisualizer
vis = AudioVisualizer()
vis.load_media("input.mp4")

# Create a filter graph
graph = vis.create_filter_graph()

# Create the initial format filter
format_node = graph.create_node('format', 'main_format', {'pix_fmt': 'yuva420p'})
graph.set_input('0:v', format_node)  # Connect to video input

# Create a movie source for the logo
movie_node = graph.create_node('movie', 'logo_source', {
    'filename': 'logo.png'
})

# Scale the logo
scale_node = graph.create_node('scale', 'logo_scale', {
    'width': 100,
    'height': 100
})
graph.connect(movie_node, scale_node)

# Create overlay for the logo
overlay_node = graph.create_node('overlay', 'logo_overlay', {
    'x': 20,
    'y': 20,
    'format': 'rgb',
    'shortest': 1
})
graph.connect(format_node, overlay_node, 0, 0)  # Main video to input 0
graph.connect(scale_node, overlay_node, 0, 1)   # Logo to input 1

# Set the output
graph.set_output('out', overlay_node)

# Process the video with the filter graph
vis.process_with_filter_graph(graph, "output.mp4")
```

## Using the Filter Graph Builders

The package includes builder utilities for common filter patterns:

```python
from audiovisualizer import AudioVisualizer
from audiovisualizer.ffmpeg_filter_graph import FilterGraph
from audiovisualizer.ffmpeg_filter_graph.builders import FilterGraphBuilder

# Initialize
vis = AudioVisualizer()
vis.load_media("input.mp4")
graph = FilterGraph()

# Create a logo overlay
input_node, logo_output = FilterGraphBuilder.create_logo_overlay(
    graph,
    logo_path="logo.png",
    position=(20, 20),
    scale=0.2,
    opacity=0.8
)

# Add text overlay after the logo
text_input, text_output = FilterGraphBuilder.create_text_overlay(
    graph,
    text="Hello World",
    font_path="font.ttf",
    position=(20, 150),
    size=36,
    color="white"
)

# Connect the logo output to the text input
graph.connect(logo_output, text_input)

# Set up inputs and outputs
graph.set_input("0:v", input_node)
graph.set_output("out", text_output)

# Process the video
vis.process_with_filter_graph(graph, "output.mp4")
```

## Visualizing Filter Graphs

The package includes tools for visualizing filter graphs:

```python
from audiovisualizer.ffmpeg_filter_graph.visualizers import FilterGraphVisualizer

# Visualize the graph (requires graphviz package)
dot = FilterGraphVisualizer.visualize(graph, "filter_graph")
print(f"Graph visualization saved to filter_graph.dot")
```

## License

MIT License