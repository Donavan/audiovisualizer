#!/usr/bin/env python3
"""Advanced example script for AudioVisualizer.

This script demonstrates more advanced features of the AudioVisualizer package
including multiple effects reacting to different audio features.
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
font_path = str(assets_dir / 'FederationBold.ttf')

# Output path
output_dir = Path.cwd()
output_video = str(output_dir / 'advanced_effects_output.mp4')

# Custom frequency bands (in Hz)
CUSTOM_FREQ_BANDS = {
    'sub_bass': (20, 60),
    'bass': (60, 250),
    'low_mid': (250, 500),
    'mid': (500, 2000),
    'high_mid': (2000, 4000),
    'presence': (4000, 6000),
    'brilliance': (6000, 20000)
}

async def main():
    """Run the advanced effects example."""
    # Create the visualizer
    visualizer = AudioVisualizer(input_video, output_video)
    
    # Load media info
    await visualizer.load_media_info()
    
    # Analyze audio with custom frequency bands
    await visualizer.analyze_audio(
        freq_bands=CUSTOM_FREQ_BANDS,
        beat_detection=True,
        onset_detection=True
    )
    
    # Add a logo with both scaling and rotation
    logo = visualizer.add_logo(
        logo_path,
        position='center',
        scale=0.3,
        opacity=0.9,
        effect_name='pulsing_logo'
    )
    
    # Make the logo pulse with the bass and rotate
    logo.set_audio_feature('freq_bands.bass')
    logo.set_scale_range(0.25, 0.35)
    logo.enable_rotation(speed=0.5)
    
    # Add animated text with glow
    title_text = visualizer.add_text(
        "AUDIO VISUALIZER",
        font_path,
        position='top-center',
        font_size=72,
        font_color='#FFFFFF',
        opacity=1.0,
        effect_name='title_text'
    )
    
    # Make the text respond to mid-range frequencies
    title_text.set_audio_feature('freq_bands.mid')
    title_text.enable_glow('#00AAFF')  # Blue glow
    title_text.enable_color_shift()
    
    # Add a subtitle with background box
    subtitle_text = visualizer.add_text(
        "Advanced Effects Demo",
        font_path,
        position=('(w-text_w)/2', 150),  # Positioned below title
        font_size=36,
        font_color='#FFFFFF',
        opacity=0.8,
        effect_name='subtitle_text'
    )
    
    # Make the subtitle respond to high frequencies
    subtitle_text.set_audio_feature('freq_bands.brilliance')
    subtitle_text.set_opacity_range(0.5, 1.0)
    subtitle_text.enable_background_box('#000000', 0.7)
    
    # Add a spectrum visualizer
    spectrum = visualizer.add_spectrum(
        position='bottom-center',
        width=800,
        height=200,
        bands=64,
        mode='bars',
        color='#FFFFFF',
        opacity=0.8,
        effect_name='spectrum_viz'
    )
    
    # Customize the spectrum
    spectrum.enable_rainbow()
    spectrum.enable_mirror()
    spectrum.set_bar_style(width=10, gap=2)
    
    # Set custom video and audio options
    visualizer.set_video_options([
        '-c:v', 'libx264', 
        '-preset', 'slow',  # Better quality but slower encoding
        '-crf', '18'        # Higher quality (lower value)
    ])
    
    visualizer.set_audio_options([
        '-c:a', 'aac', 
        '-b:a', '320k'      # Higher bitrate audio
    ])
    
    # Save the project configuration for future reference
    visualizer.save_project(str(output_dir / 'advanced_project.json'))
    
    # Process and export
    await visualizer.process()
    
    print(f"Video processing complete! Output saved to: {output_video}")
    print(f"Project configuration saved to: {output_dir / 'advanced_project.json'}")

if __name__ == "__main__":
    asyncio.run(main())