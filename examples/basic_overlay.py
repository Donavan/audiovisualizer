#!/usr/bin/env python3
"""Basic example script for AudioVisualizer.

This script demonstrates the basic usage of the AudioVisualizer package
with a logo pulsing to the beat and text fading with the volume.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the src directory to the path so we can import the package
src_dir = Path(__file__).resolve().parent.parent / 'src'
sys.path.insert(0, str(src_dir))

from audiovisualizer import AudioVisualizer

# Get paths to example assets
examples_dir = Path(__file__).resolve().parent
assets_dir = examples_dir / 'test_assets'

input_video = str(assets_dir / 'input_video.mp4')
logo_path = str(assets_dir / 'logo.png')
font_path = str(assets_dir / 'Federation.ttf')

# Output path
output_dir = Path.cwd()
output_video = str(output_dir / 'basic_overlay_output.mp4')

async def main():
    """Run the basic overlay example."""
    # Create the visualizer
    visualizer = AudioVisualizer(input_video, output_video)
    
    # Load media info
    await visualizer.load_media_info()
    
    # Analyze audio
    await visualizer.analyze_audio()
    
    # Add a logo that pulses to the beat
    logo = visualizer.add_logo(
        logo_path,
        position='top-right',
        scale=0.2,
        opacity=0.8
    )
    
    # Make the logo pulse with the beat
    logo.set_audio_feature('beat_envelope')
    logo.set_scale_range(0.18, 0.22)
    
    # Add text that fades with the volume
    text = visualizer.add_text(
        "AUDIO VISUALIZER",
        font_path,
        position='bottom-center',
        font_size=48,
        font_color='#FFFFFF',
        opacity=0.8
    )
    
    # Make the text opacity change with the volume
    text.set_audio_feature('amplitude')
    text.set_opacity_range(0.3, 1.0)
    
    # Process and export
    await visualizer.process()
    
    print(f"Video processing complete! Output saved to: {output_video}")

if __name__ == "__main__":
    asyncio.run(main())