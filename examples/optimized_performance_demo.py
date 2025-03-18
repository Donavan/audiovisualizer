#!/usr/bin/env python3
"""
Optimized Performance Demo for AudioVisualizer

This example demonstrates improved export performance with:
- Multithreaded rendering
- Hardware acceleration (when available)
- Quality/speed trade-off options
- Comprehensive timing metrics

Designed for systems with multiple cores and significant RAM.
"""

import os
import sys
import time
import argparse
import hashlib
import pickle
import multiprocessing
import psutil
import numpy as np
from PIL import Image
from audiovisualizer import AudioVisualOverlay

# Base path for resources (fixes path issues)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to your video and assets with corrected paths
VIDEO_PATH = os.path.join(BASE_DIR, "examples/test_assets/input_video.mp4")
LOGO_PATH = os.path.join(BASE_DIR, "examples/test_assets/logo.png")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Define cache directory for storing audio features
CACHE_DIR = os.path.join(BASE_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# Performance tracking
class PerformanceTracker:
    """Tracks execution time and system resource usage"""
    
    def __init__(self):
        self.start_time = time.time()
        self.checkpoints = {}
        self.current_checkpoint = None
    
    def start_checkpoint(self, name):
        """Start timing a specific section of code"""
        if self.current_checkpoint:
            self.end_checkpoint()
        
        self.current_checkpoint = name
        self.checkpoints[name] = {
            'start': time.time(),
            'memory_start': psutil.Process().memory_info().rss / (1024 * 1024),  # MB
            'end': None,
            'duration': None,
            'memory_end': None,
            'memory_diff': None
        }
        print(f"\n[{name}] Starting...")
        return self
    
    def end_checkpoint(self):
        """End timing the current checkpoint"""
        if not self.current_checkpoint:
            return
            
        name = self.current_checkpoint
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB
        
        self.checkpoints[name]['end'] = end_time
        self.checkpoints[name]['duration'] = end_time - self.checkpoints[name]['start']
        self.checkpoints[name]['memory_end'] = end_memory
        self.checkpoints[name]['memory_diff'] = end_memory - self.checkpoints[name]['memory_start']
        
        print(f"[{name}] Completed in {self.checkpoints[name]['duration']:.2f} seconds")
        print(f"[{name}] Memory change: {self.checkpoints[name]['memory_diff']:.2f} MB")
        
        self.current_checkpoint = None
        return self
    
    def get_total_time(self):
        """Get total execution time so far"""
        return time.time() - self.start_time
    
    def print_summary(self):
        """Print a summary of all checkpoints"""
        print("\n===== PERFORMANCE SUMMARY =====")
        print(f"Total execution time: {self.get_total_time():.2f} seconds ({self.get_total_time()/60:.2f} minutes)")
        print("\nCheckpoint breakdown:")
        
        for name, data in self.checkpoints.items():
            if data['duration'] is not None:
                print(f"  {name}: {data['duration']:.2f} seconds")
                if data['memory_diff'] is not None:
                    print(f"    Memory change: {data['memory_diff']:.2f} MB")
        
        cpu_count = multiprocessing.cpu_count()
        ram_gb = psutil.virtual_memory().total / (1024**3)
        print(f"\nSystem information:")
        print(f"  CPU cores: {cpu_count}")
        print(f"  Total RAM: {ram_gb:.1f} GB")
        print(f"  Current RAM usage: {psutil.virtual_memory().percent}%")

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

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Optimized performance demo for AudioVisualizer")
    parser.add_argument("--quality", choices=["speed", "balanced", "quality"], default="balanced",
                        help="Quality preset - speed (fastest), balanced, or quality (best)")
    parser.add_argument("--threads", type=int, default=min(16, multiprocessing.cpu_count()),
                        help="Number of threads to use for processing")
    parser.add_argument("--use-gpu", action="store_true", default=True,
                        help="Use GPU acceleration if available")
    parser.add_argument("--output", type=str, default=None,
                        help="Output file name (default: auto-generated based on settings)")
    args = parser.parse_args()
    
    # Configure output path
    if args.output:
        OUTPUT_PATH = os.path.join(OUTPUT_DIR, args.output)
    else:
        output_filename = f"optimized_demo_{args.quality}_{args.threads}threads"
        output_filename += "_gpu" if args.use_gpu else "_cpu"
        OUTPUT_PATH = os.path.join(OUTPUT_DIR, f"{output_filename}.mp4")
    
    # Initialize performance tracker
    tracker = PerformanceTracker()
    
    # Check if files exist
    tracker.start_checkpoint("Initialization")
    if not os.path.exists(VIDEO_PATH):
        print(f"Error: Video file not found: {VIDEO_PATH}")
        print("Please update the VIDEO_PATH variable to point to a valid video file.")
        return
    
    if not os.path.exists(LOGO_PATH):
        print(f"Error: Logo file not found: {LOGO_PATH}")
        print("Continuing without logo...")
    
    # Display configuration information
    print(f"Configuration:")
    print(f"  Quality preset: {args.quality}")
    print(f"  Threads: {args.threads}")
    print(f"  GPU acceleration: {'Enabled' if args.use_gpu else 'Disabled'}")
    print(f"  Output path: {OUTPUT_PATH}")
    tracker.end_checkpoint()
    
    # Create an overlay processor with the input video
    tracker.start_checkpoint("Creating overlay processor")
    overlay = AudioVisualOverlay(VIDEO_PATH)
    tracker.end_checkpoint()
    
    # Try to load cached audio features or extract if not available
    tracker.start_checkpoint("Audio feature processing")
    if not load_cached_audio_features(overlay):
        print("Extracting audio features (this may take a while)...")
        overlay.extract_audio_features()
        
        # Cache the features for future use
        cache_audio_features(overlay)
    tracker.end_checkpoint()
    
    # Add a logo with multiple reactions (if logo exists)
    tracker.start_checkpoint("Adding visual elements")
    if os.path.exists(LOGO_PATH):
        print(f"Adding logo from {LOGO_PATH}...")
        logo = overlay.add_logo(
            logo_path=LOGO_PATH, 
            position="bottom-right", 
            size=0.20,
            margin=25
        )
        
        if logo:
            print("Adding reactions to logo...")
            # Add scale reaction - logo pulses with the beat
            logo.add_reaction(
                reaction_type="scale",
                feature="onsets",
                params={
                    "intensity": 0.4,
                    "min_scale": 1.0,
                    "max_scale": 1.3,
                    "smoothing": 0.15
                }
            )
            
            # Add color reaction - logo changes saturation with mid frequencies
            logo.add_reaction(
                reaction_type="color",
                feature="spectral_centroid",
                params={
                    "type": "saturation",
                    "min_value": 0.8,
                    "max_value": 1.5
                }
            )
            
            # Add opacity reaction to ensure visibility
            logo.add_reaction(
                reaction_type="opacity",
                feature="rms",
                params={
                    "min_opacity": 0.8,
                    "max_opacity": 1.0,
                    "smoothing": 0.3
                }
            )
    
    # Add main title text
    main_text = overlay.add_text(
        text="OPTIMIZED PERFORMANCE DEMO",
        font_path="examples/test_assets/FederationBold.ttf",
        position="top-right",
        fontsize=42,
        color="#FF9900",  # Orange
        margin=20
    )
    
    if main_text:
        main_text.add_reaction(
            reaction_type="opacity",
            feature="onsets",
            params={
                "min_opacity": 0.6,
                "max_opacity": 1.0,
                "smoothing": 0.2
            }
        )
    
    # Add subtitle with quality setting
    subtitle = overlay.add_text(
        font_path="examples/test_assets/Federation.ttf",
        text=f"QUALITY: {args.quality.upper()}",
        position="top-right",
        fontsize=26,
        color="#CCCCCC",
        margin=70
    )
    
    if subtitle:
        subtitle.add_reaction(
            reaction_type="color",
            feature="spectral_centroid",
            params={
                "color_map": [
                    (0.0, "#3366CC"),  # Blue for low values
                    (0.5, "#FFFFFF"),  # White for mid values
                    (1.0, "#CC3366")   # Pink/red for high values
                ]
            }
        )
    
    # Add info text about thread count
    thread_info = overlay.add_text(
        text=f"THREADS: {args.threads}",
        font_path="examples/test_assets/Federation.ttf",
        position="top-right",
        fontsize=22,
        color="#AAA9AD",
        margin=110
    )
    
    if thread_info:
        thread_info.add_reaction(
            reaction_type="color",
            feature="rms",
            params={
                "type": "brightness",
                "min_value": 0.8,
                "max_value": 1.2
            }
        )
    tracker.end_checkpoint()
    
    # Process the video with all elements and reactions
    tracker.start_checkpoint("Video processing")
    overlay.process()
    tracker.end_checkpoint()
    
    # Export the final video with optimized settings
    tracker.start_checkpoint("Video export")
    print(f"Exporting video to: {OUTPUT_PATH}")
    
    # Custom implementation to maximize thread usage and GPU acceleration
    if args.use_gpu:
        overlay.export_gpu_optimized(OUTPUT_PATH, quality=args.quality)
    else:
        # Create a patched export function to use custom thread count
        from functools import partial
        from types import MethodType
        
        def custom_export(self, output_path, fps=None):
            """Export with custom thread count"""
            if not self.video:
                print("No video to export")
                return None
                
            if fps is None:
                fps = self.video.fps
    
            print(f"Exporting with {args.threads} threads...")
    
            # Quality settings mapping
            preset = {
                'speed': 'veryfast',
                'balanced': 'medium',
                'quality': 'slow'
            }.get(args.quality, 'medium')
            
            bitrate = {
                'speed': '6000k',
                'balanced': '10000k',
                'quality': '15000k'
            }.get(args.quality, '10000k')
    
            try:
                self.video.write_videofile(
                    output_path,
                    codec="libx264",
                    fps=fps,
                    preset=preset,
                    bitrate=bitrate,
                    audio_codec="aac",
                    audio_bitrate="192k",
                    threads=args.threads,  # Use specified thread count
                    ffmpeg_params=["-pix_fmt", "yuv420p"],
                    logger=None
                )
                print(f"Video successfully exported to {output_path}")
            except Exception as e:
                print(f"Export failed: {e}")
                
            return self
        
        # Patch the export method to use our custom function
        overlay.exporter.export = MethodType(custom_export, overlay.exporter)
        overlay.export(OUTPUT_PATH)
    
    tracker.end_checkpoint()
    
    # Print performance summary
    tracker.print_summary()
    print(f"\nExport complete: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()