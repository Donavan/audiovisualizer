#!/usr/bin/env python3
"""
Flexible Reactivity Demo for AudioVisualizer

This example demonstrates the new flexible reactivity system that allows
adding different types of reactions to elements independently.
"""

import os
from audiovisualizer import AudioVisualOverlay

# Path to your video and assets
VIDEO_PATH = "input_video.mp4"  # replace with your video path
LOGO_PATH = "logo.png"  # replace with your logo path
OUTPUT_PATH = "output_with_flexible_reactivity.mp4"

def main():
    # Create an overlay processor with the input video
    overlay = AudioVisualOverlay(VIDEO_PATH)
    
    # Extract audio features for reactivity
    overlay.extract_audio_features()
    
    # Add a logo with multiple reactions
    logo = overlay.add_logo(
        logo_path=LOGO_PATH, 
        position="top-right", 
        size=0.15
    )
    
    # Add scale reaction - logo pulses with the beat
    logo.add_reaction(
        reaction_type="scale",
        feature="rms",  # reacts to overall volume
        params={
            "intensity": 0.3,
            "min_scale": 1.0,
            "max_scale": 1.3,
            "smoothing": 0.2  # lower = more responsive, higher = smoother
        }
    )
    
    # Add color reaction - logo changes saturation with mid frequencies
    logo.add_reaction(
        reaction_type="color",
        feature="spectral_centroid",  # reacts to frequency content
        params={
            "type": "saturation",
            "min_value": 0.8,
            "max_value": 1.5
        }
    )
    
    # Add a text element with different reactions
    text = overlay.add_text(
        text="AUDIO REACTIVE",
        position="bottom-center",
        fontsize=40,
        color="white"
    )
    
    # Text opacity reaction - fades with bass
    text.add_reaction(
        reaction_type="opacity",
        feature="onsets",  # reacts to note onsets/beats
        params={
            "min_opacity": 0.3,
            "max_opacity": 1.0,
            "smoothing": 0.3
        }
    )
    
    # Text position reaction - bounces with the beat
    text.add_reaction(
        reaction_type="position",
        feature="rms",
        params={
            "type": "bounce",
            "intensity": 15  # pixels
        }
    )
    
    # Add another text with different reactions
    subtitle = overlay.add_text(
        text="Flexible Reaction System",
        position="bottom-center",
        fontsize=24,
        color="#CCCCCC",
        margin=80  # more margin to position below main text
    )
    
    # Color reaction - changes between colors based on audio
    subtitle.add_reaction(
        reaction_type="color",
        feature="spectral_centroid",
        params={
            "color_map": [
                (0.0, "#3366CC"),  # blue for low values
                (0.5, "#FFFFFF"),  # white for mid values
                (1.0, "#CC3366")   # pink for high values
            ]
        }
    )
    
    # Process the video with all elements and reactions
    overlay.process()
    
    # Export the final video
    output_file = overlay.export(OUTPUT_PATH)
    print(f"Exported video to: {output_file}")

if __name__ == "__main__":
    main()