#!/usr/bin/env python
# Example demonstrating the new filter graph architecture

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from audiovisualizer import AudioVisualizer, FilterGraph
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main():
    # Path to the sample video
    video_path = os.path.join(os.path.dirname(__file__), 'test_assets', 'input_video.mp4')
    logo_path = os.path.join(os.path.dirname(__file__), 'test_assets', 'logo.png')
    font_path = os.path.join(os.path.dirname(__file__), 'test_assets', 'Federation.ttf')
    
    # Output file path
    output_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'filter_graph_demo.mp4')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Initialize the AudioVisualizer
    vis = AudioVisualizer()
    vis.load_media(video_path)
    
    # 1. Using the simplified API
    print("\n1. Using the simplified API:")
    vis.add_effect('logo', {
        'path': logo_path,
        'x': 20,
        'y': 20,
        'scale': (100, 100),
        'opacity': 0.8
    })
    
    vis.add_effect('text', {
        'text': 'Hello World',
        'font': font_path,
        'size': 36,
        'color': 'white',
        'x': 20,
        'y': 150,
        'box': True,
        'box_color': 'black@0.5'
    })
    
    vis.process(output_path.replace('.mp4', '_simple.mp4'))
    print(f"Output video saved to {output_path.replace('.mp4', '_simple.mp4')}")
    
    # 2. Using the filter graph API directly
    print("\n2. Using the filter graph API directly:")
    # Create a new visualizer
    vis = AudioVisualizer()
    vis.load_media(video_path)
    
    # Create a filter graph
    graph = vis.create_filter_graph()
    
    # Create the initial format filter
    format_node = graph.create_node('format', 'main_format', {'pix_fmt': 'yuva420p'})
    graph.set_input('0:v', format_node)  # Connect to video input
    
    # Create a movie source for the logo
    movie_node = graph.create_node('movie', 'logo_source', {
        'filename': logo_path
    })
    
    # Scale the logo
    scale_node = graph.create_node('scale', 'logo_scale', {
        'width': 100,
        'height': 100
    })
    graph.connect(movie_node, scale_node)
    
    # Set logo opacity
    alpha_node = graph.create_node('colorchannelmixer', 'logo_opacity', {
        'aa': 0.8
    })
    graph.connect(scale_node, alpha_node)
    
    # Create overlay for the logo
    overlay_node = graph.create_node('overlay', 'logo_overlay', {
        'x': 20,
        'y': 20,
        'format': 'rgb',
        'shortest': 1
    })
    graph.connect(format_node, overlay_node, 0, 0)  # Main video to input 0
    graph.connect(alpha_node, overlay_node, 0, 1)   # Logo to input 1
    
    # Add text overlay
    drawtext_node = graph.create_node('drawtext', 'text_overlay', {
        'text': 'Hello World',
        'fontfile': font_path,
        'fontsize': 36,
        'fontcolor': 'white',
        'x': 20,
        'y': 150,
        'box': 1,
        'boxcolor': 'black@0.5'
    })
    graph.connect(overlay_node, drawtext_node)
    
    # Set the output
    graph.set_output('out', drawtext_node)
    
    # Generate the filter chain
    filter_chain = graph.to_filter_string()
    print(f"Generated filter chain:\n{filter_chain}")
    
    # Process the video with the filter graph
    vis.process_with_filter_graph(graph, output_path)
    print(f"Output video saved to {output_path}")
    
    # 3. Visualize the filter graph (if graphviz is installed)
    print("\n3. Visualizing the filter graph:")
    try:
        from audiovisualizer.ffmpeg_filter_graph.visualizers import FilterGraphVisualizer
        dot_output = os.path.join(os.path.dirname(__file__), '..', 'output', 'filter_graph')
        dot = FilterGraphVisualizer.visualize(graph, dot_output)
        print(f"Filter graph visualization saved to {dot_output}.dot")
        print("If GraphViz is installed, a PNG file was also generated.")
    except ImportError:
        print("Could not import visualization module.")

if __name__ == '__main__':
    main()