#!/usr/bin/env python3
"""
Enhanced Federation Records Demo for AudioVisualizer

This example demonstrates a Star Trek-themed audio visualization
with properly handled transparent logo and caching for faster renders.
"""

import os
import sys
import json
import time
import hashlib
import pickle
import numpy as np
from PIL import Image
from audiovisualizer import AudioVisualOverlay

# Base path for resources (fixes path issues)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to your video and assets with corrected paths
VIDEO_PATH = os.path.join(BASE_DIR, "examples/test_assets/input_video.mp4")
LOGO_PATH = os.path.join(BASE_DIR, "examples/test_assets/logo.png")
OUTPUT_PATH = os.path.join(BASE_DIR, "/output/federation_records_demo.mp4")

# Define cache directory for storing audio features
CACHE_DIR = os.path.join(BASE_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# Cache helper functions
def get_file_hash(file_path):
    """Generate a hash from a file to use as a cache key"""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        buf = f.read(65536)  # Read in 64k chunks
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()

def get_cache_path(video_path):
    """Get cache file path for audio features"""
    video_hash = get_file_hash(video_path)
    return os.path.join(CACHE_DIR, f"{video_hash}_features.pkl")

def cache_audio_features(overlay):
    """Save extracted audio features to cache"""
    if not overlay.audio_feature_extractor.features:
        print("No audio features to cache")
        return False
    
    cache_path = get_cache_path(VIDEO_PATH)
    try:
        # Convert numpy arrays to lists for serialization
        features_copy = {}
        for key, value in overlay.audio_feature_extractor.features.items():
            if isinstance(value, np.ndarray):
                features_copy[key] = value.tolist()
            else:
                features_copy[key] = value
                
        with open(cache_path, 'wb') as f:
            pickle.dump(features_copy, f)
        print(f"Audio features cached to {cache_path}")
        return True
    except Exception as e:
        print(f"Error caching audio features: {e}")
        return False

def load_cached_audio_features(overlay):
    """Load cached audio features if available"""
    cache_path = get_cache_path(VIDEO_PATH)
    if not os.path.exists(cache_path):
        print("No cached audio features found")
        return False
    
    try:
        with open(cache_path, 'rb') as f:
            features = pickle.load(f)
        
        # Convert lists back to numpy arrays
        for key, value in features.items():
            if isinstance(value, list):
                features[key] = np.array(value)
        
        # Apply cached features directly
        overlay.audio_feature_extractor.features = features
        overlay.element_manager.set_audio_features(features)
        print(f"Loaded cached audio features from {cache_path}")
        return True
    except Exception as e:
        print(f"Error loading cached audio features: {e}")
        return False

# Function to check and fix transparent logo
def verify_and_fix_logo(logo_path):
    """Verify and fix logo transparency issues"""
    try:
        # Check if logo exists
        if not os.path.exists(logo_path):
            print(f"Error: Logo file not found at {logo_path}")
            return False
            
        # Open and analyze the logo
        img = Image.open(logo_path)
        print(f"Logo format: {img.format}, Mode: {img.mode}, Size: {img.size}")
        
        # Ensure the image has an alpha channel for transparency
        if img.mode != 'RGBA':
            print(f"Converting logo from {img.mode} to RGBA for transparency support")
            img = img.convert('RGBA')
            
            # Save the converted image
            fixed_logo_path = os.path.join(os.path.dirname(logo_path), "fixed_logo.png")
            img.save(fixed_logo_path, 'PNG')
            print(f"Saved fixed logo to {fixed_logo_path}")
            return fixed_logo_path
        
        # Check if transparency is working as expected
        transparent_pixels = 0
        total_pixels = img.width * img.height
        
        # Sample some pixels to check for transparency
        for x in range(0, img.width, 10):
            for y in range(0, img.height, 10):
                pixel = img.getpixel((x, y))
                if pixel[3] < 255:  # Alpha channel value less than 255 indicates transparency
                    transparent_pixels += 1
        
        # If no transparency detected but image is RGBA, might need to adjust
        if transparent_pixels == 0 and img.mode == 'RGBA':
            print("Warning: Image is RGBA but no transparent pixels detected")
            # This is not necessarily an error, as the logo might be fully opaque
        
        return logo_path  # Original path is fine
        
    except Exception as e:
        print(f"Error verifying logo: {e}")
        return logo_path  # Return original path as fallback

def main():
    FEDERATION_FONT = "examples/test_assets/Federation.ttf"
    FEDERATION_BOLD_FONT =  "examples/test_assets/FederationBold.ttf"
    
    # Start timing for performance monitoring
    start_time = time.time()
    
    # Check if files exist
    if not os.path.exists(VIDEO_PATH):
        print(f"Error: Video file not found: {VIDEO_PATH}")
        print("Please update the VIDEO_PATH variable to point to a valid video file.")
        return
    
    # Verify logo and fix if needed
    verified_logo_path = verify_and_fix_logo(LOGO_PATH)
    if not verified_logo_path:
        print("Continuing without logo...")
    
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
    
    # Try to load cached audio features or extract if not available
    if not load_cached_audio_features(overlay):
        print("Extracting audio features (this may take a while)...")
        extract_start = time.time()
        overlay.extract_audio_features()
        print(f"Audio extraction took {time.time() - extract_start:.2f} seconds")
        
        # Cache the features for future use
        cache_audio_features(overlay)
    
    # Add a logo with multiple reactions (if logo exists)
    if verified_logo_path:
        print(f"Adding Federation Records logo from {verified_logo_path}...")
        # Using bottom-right position to ensure visibility in shorts format
        # Increased size for better visibility
        logo = overlay.add_logo(
            logo_path=verified_logo_path, 
            position="bottom-right", 
            size=0.20,  # Slightly larger for better visibility
            margin=25   # Add some margin from the edges
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
            
            # Add opacity reaction to ensure visibility
            logo.add_reaction(
                reaction_type="opacity",
                feature="rms",  # overall volume
                params={
                    "min_opacity": 0.8,  # Never fully transparent
                    "max_opacity": 1.0,
                    "smoothing": 0.3
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
    process_start = time.time()
    overlay.process()
    print(f"Video processing took {time.time() - process_start:.2f} seconds")
    
    # Export the final video
    print(f"Exporting video to: {OUTPUT_PATH}")
    export_start = time.time()
    output_file = overlay.export(OUTPUT_PATH)
    print(f"Video export took {time.time() - export_start:.2f} seconds")
    
    # Print total processing time
    total_time = time.time() - start_time
    print(f"\nTotal processing time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
    print(f"Export complete: {output_file}")

if __name__ == "__main__":
    main()