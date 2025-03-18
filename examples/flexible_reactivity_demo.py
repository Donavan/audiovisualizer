#!/usr/bin/env python3
"""
Flexible Reactivity Demo for AudioVisualizer

This example demonstrates the new flexible reactivity system that allows
adding different types of reactions to elements independently.
"""

import os
import sys
from audiovisualizer import AudioVisualOverlay

# Path to your video and assets
VIDEO_PATH = "input_video.mp4"  # replace with your video path
LOGO_PATH = "logo.png"  # replace with your logo path
OUTPUT_PATH = "output_with_flexible_reactivity.mp4"

# Default font path - try various system locations
# We'll try a few common system fonts
POSSIBLE_FONTS = [
    "C:\\Windows\\Fonts\\Arial.ttf",  # Windows
    "C:\\Windows\\Fonts\\Calibri.ttf",  # Windows
    "C:\\Windows\\Fonts\\Verdana.ttf",  # Windows
    "/Library/Fonts/Arial.ttf",  # macOS
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
]

def find_system_font():
    """Try to find a valid system font"""
    for font_path in POSSIBLE_FONTS:
        if os.path.exists(font_path):
            print(f"Using font: {font_path}")
            return font_path
            
    print("WARNING: Could not find a valid system font. Text elements will fail.")
    print("Please modify the POSSIBLE_FONTS list to include a font available on your system.")
    return None

def main():
    # Find a valid system font
    FONT_PATH = find_system_font()
    
    if not os.path.exists(VIDEO_PATH):
        print(f"Error: Video file not found: {VIDEO_PATH}")
        print("Please update the VIDEO_PATH variable to point to a valid video file.")
        return
        
    if not os.path.exists(LOGO_PATH):
        print(f"Error: Logo file not found: {LOGO_PATH}")
        print("Please update the LOGO_PATH variable to point to a valid image file.")
        print("Continuing without logo element...")
        
    # Create an overlay processor with the input video
    print("Creating overlay processor...")
    overlay = AudioVisualOverlay(VIDEO_PATH)
    
    # Extract audio features for reactivity
    print("Extracting audio features...")
    overlay.extract_audio_features()
    
    # Add a logo with multiple reactions (if logo exists)
    if os.path.exists(LOGO_PATH):
        print("Adding logo element...")
        logo = overlay.add_logo(
            logo_path=LOGO_PATH, 
            position="top-right", 
            size=0.15
        )
        
        if logo:
            print("Adding reactions to logo...")
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
        else:
            print("Failed to create logo element. Check logo path and format.")
    
    # Add a text element with different reactions (if font is available)
    if FONT_PATH:
        print("Adding text elements...")
        text = overlay.add_text(
            text="AUDIO REACTIVE",
            position="bottom-center",
            fontsize=40,
            color="white",
            font_path=FONT_PATH  # Using found font
        )
        
        # Check if text element was created successfully
        if text:
            print("Adding reactions to main text...")
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
        else:
            print("Failed to create main text element. Check font path.")
        
        # Add another text with different reactions
        subtitle = overlay.add_text(
            text="Flexible Reaction System",
            position="bottom-center",
            fontsize=24,
            color="#CCCCCC",
            font_path=FONT_PATH,  # Using found font
            margin=80  # more margin to position below main text
        )
        
        # Check if subtitle was created successfully
        if subtitle:
            print("Adding reactions to subtitle...")
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
        else:
            print("Failed to create subtitle text element. Check font path.")
    else:
        print("Skipping text elements due to missing font.")
    
    # Process the video with all elements and reactions
    print("Processing video...")
    overlay.process()
    
    # Export the final video
    print(f"Exporting video to: {OUTPUT_PATH}")
    output_file = overlay.export(OUTPUT_PATH)
    print(f"Export complete: {output_file}")

if __name__ == "__main__":
    main()