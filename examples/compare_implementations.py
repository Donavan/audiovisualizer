#!/usr/bin/env python
# Example comparing the old string-based approach with the new filter graph architecture

import os
import sys
from pathlib import Path
import time
import logging

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from audiovisualizer import AudioVisualizer
from audiovisualizer.ffmpeg_filter_graph import FilterGraph
from audiovisualizer.ffmpeg_filter_graph.builders import FilterGraphBuilder

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def old_approach(video_path, logo_path, font_path):
    """Generate filter chain using the old string-based approach."""
    # In the old approach, we would manually construct filter chains as strings
    # This is a simplified example of what that might look like
    
    # Format filter
    filter_chain = "[0:v]format=pix_fmt=yuva420p[formatted];"
    
    # Logo overlay
    filter_chain += f"movie='{logo_path}',scale=100:100,colorchannelmixer=aa=0.8[logo];"
    filter_chain += "[formatted][logo]overlay=x=20:y=20:format=rgb:shortest=1[with_logo];"
    
    # Text overlay
    filter_chain += f"[with_logo]drawtext=text='Hello World':fontfile='{font_path}':fontsize=36"
    filter_chain += ":fontcolor=white:x=20:y=150:box=1:boxcolor=black@0.5[out]"
    
    return filter_chain

def new_approach(video_path, logo_path, font_path):
    """Generate filter chain using the new filter graph architecture."""
    graph = FilterGraph()
    
    # Use the builders to create the filter chains
    input_node, logo_output = FilterGraphBuilder.create_logo_overlay(
        graph,
        logo_path=logo_path,
        position=(20, 20),
        scale=(100, 100),
        opacity=0.8
    )
    
    text_input, text_output = FilterGraphBuilder.create_text_overlay(
        graph,
        text="Hello World",
        font_path=font_path,
        position=(20, 150),
        size=36,
        color="white",
        box=True,
        box_color="black@0.5"
    )
    
    # Connect the logo output to the text input
    graph.connect(logo_output, text_input)
    
    # Set up inputs and outputs
    graph.set_input("0:v", input_node)
    graph.set_output("out", text_output)
    
    return graph.to_filter_string()

def main():
    # Path to the sample video
    video_path = os.path.join(os.path.dirname(__file__), 'test_assets', 'input_video.mp4')
    logo_path = os.path.join(os.path.dirname(__file__), 'test_assets', 'logo.png')
    font_path = os.path.join(os.path.dirname(__file__), 'test_assets', 'Federation.ttf')
    
    # Compare outputs
    print("Comparing old and new approaches to filter chain generation:\n")
    
    # Measure time for old approach
    start_time = time.time()
    old_chain = old_approach(video_path, logo_path, font_path)
    old_time = time.time() - start_time
    
    print(f"Old approach ({old_time:.4f} seconds):\n{old_chain}\n")
    
    # Measure time for new approach
    start_time = time.time()
    new_chain = new_approach(video_path, logo_path, font_path)
    new_time = time.time() - start_time
    
    print(f"New approach ({new_time:.4f} seconds):\n{new_chain}\n")
    
    # Compare the results
    print(f"Filter chains match: {old_chain == new_chain}")
    
    # Process videos with both approaches for visual comparison
    old_output = os.path.join(os.path.dirname(__file__), '..', 'output', 'old_approach.mp4')
    new_output = os.path.join(os.path.dirname(__file__), '..', 'output', 'new_approach.mp4')
    os.makedirs(os.path.dirname(old_output), exist_ok=True)
    
    print("\nProcessing videos for visual comparison...")
    
    # Process with old approach
    vis = AudioVisualizer()
    vis.load_media(video_path)
    vis.ffmpeg.process_video(video_path, old_output, old_chain)
    
    # Process with new approach
    vis = AudioVisualizer()
    vis.load_media(video_path)
    vis.ffmpeg.process_video(video_path, new_output, new_chain)
    
    print(f"Videos saved to:\n{old_output}\n{new_output}")

if __name__ == '__main__':
    main()