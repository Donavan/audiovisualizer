#!/usr/bin/env python3
"""
Federation Records Demo for AudioVisualizer

This example demonstrates a Star Trek-themed audio visualization
with elements positioned to be compatible with video shorts format.
"""

import os
import sys
from audiovisualizer import AudioVisualOverlay

# Base path for resources (fixes path issues)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to your video and assets with corrected paths
VIDEO_PATH = os.path.join(BASE_DIR, "examples/test_assets/input_video.mp4")
LOGO_PATH = os.path.join(BASE_DIR, "examples/test_assets/logo.png")
OUTPUT_PATH = os.path.join(BASE_DIR, "/output/federation_records_demo.mp4")

# Federation font paths with corrected paths


def main():
    FEDERATION_FONT = os.path.join(BASE_DIR, "fonts", "examples/test_assets/Federation.ttf")
    FEDERATION_BOLD_FONT = os.path.join(BASE_DIR, "fonts", "examples/test_assets/FederationBold.ttf")
    # Check if files exist
    if not os.path.exists(VIDEO_PATH):
        print(f"Error: Video file not found: {VIDEO_PATH}")
        print("Please update the VIDEO_PATH variable to point to a valid video file.")
        return
        
    if not os.path.exists(LOGO_PATH):
        print(f"Error: Logo file not found: {LOGO_PATH}")
        print("Please update the LOGO_PATH variable to point to a valid image file.")
        print("Continuing without logo element...")
    
    # Check font paths
    if not os.path.exists(FEDERATION_FONT):
        print(f"Error: Federation font not found: {FEDERATION_FONT}")
        print("Please make sure the Federation.ttf font is in the fonts folder.")
        return
        
    if not os.path.exists(FEDERATION_BOLD_FONT):
        print(f"Error: Federation Bold font not found: {FEDERATION_BOLD_FONT}")
        print("Please make sure the FederationBold.ttf font is in the fonts folder.")
        print("Will use regular Federation font as fallback.")
        FEDERATION_BOLD_FONT = FEDERATION_FONT
    
    # Create an overlay processor with the input video
    print("Creating overlay processor...")
    overlay = AudioVisualOverlay(VIDEO_PATH)
    
    # Extract audio features for reactivity
    print("Extracting audio features...")
    overlay.extract_audio_features()
    
    # Add a logo with multiple reactions (if logo exists)
    if os.path.exists(LOGO_PATH):
        print("Adding Federation Records logo...")
        # Using bottom-right position to ensure visibility in shorts format
        logo = overlay.add_logo(
            logo_path=LOGO_PATH, 
            position="bottom-right", 
            size=0.15,
            margin=20  # Add some margin from the edges
        )
        
        if logo:
            print("Adding reactions to logo...")
            # Add scale reaction - logo pulses with the beat
            logo.add_reaction(
                reaction_type="scale",
                feature="onsets",  # reacts to beats
                params={
                    "intensity": 0.4,
                    "min_scale": 1.0,
                    "max_scale": 1.3,
                    "smoothing": 0.15  # responsive to beats
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
    
    # Add main text element - positioned in top-right for shorts compatibility
    print("Adding text elements...")
    main_text = overlay.add_text(
        text="FEDERATION RECORDS",
        position="top-right",
        fontsize=42,
        color="#FFD700",  # Star Trek gold
        font_path=FEDERATION_BOLD_FONT,
        margin=20  # Distance from the edges
    )
    
    # Check if text element was created successfully
    if main_text:
        print("Adding reactions to main text...")
        # Text opacity reaction - fades with bass
        main_text.add_reaction(
            reaction_type="opacity",
            feature="onsets",  # reacts to note onsets/beats
            params={
                "min_opacity": 0.6,
                "max_opacity": 1.0,
                "smoothing": 0.2
            }
        )
        
        # Text position reaction - subtle bounce with the beat
        main_text.add_reaction(
            reaction_type="position",
            feature="rms",
            params={
                "type": "bounce",
                "intensity": 10  # pixels
            }
        )
    else:
        print("Failed to create main text element. Check font path.")
    
    # Add subtitle text - also in top-right but below main text
    subtitle = overlay.add_text(
        text="OFFICIAL TRANSMISSION",
        position="top-right",
        fontsize=26,
        color="#CCCCCC",  # Light silver
        font_path=FEDERATION_FONT,
        margin=70  # Positioned below the main text
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
                    (0.0, "#3366CC"),  # Starfleet blue for low values
                    (0.5, "#FFFFFF"),  # white for mid values
                    (1.0, "#CC3366")   # pink/red for high values
                ]
            }
        )
    else:
        print("Failed to create subtitle text element. Check font path.")
    
    # Add stardate text (extra element)
    stardate = overlay.add_text(
        text="STARDATE 47634.44",
        position="top-right",
        fontsize=22,
        color="#AAA9AD",  # Silver/metallic
        font_path=FEDERATION_FONT,
        margin=110  # Position below subtitle
    )
    
    if stardate:
        # Subtle brightness pulsing
        stardate.add_reaction(
            reaction_type="color",
            feature="rms",
            params={
                "type": "brightness",
                "min_value": 0.8,
                "max_value": 1.2
            }
        )
    
    # Process the video with all elements and reactions
    print("Processing video...")
    overlay.process()
    
    # Export the final video
    print(f"Exporting video to: {OUTPUT_PATH}")
    output_file = overlay.export(OUTPUT_PATH)
    print(f"Export complete: {output_file}")

if __name__ == "__main__":
    main()