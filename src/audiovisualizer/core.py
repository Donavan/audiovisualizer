import os
import logging
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from typing import Dict, List, Tuple, Union, Optional, Any

from .audio_features import AudioFeatureExtractor
from .elements import ElementManager, LogoElement, TextElement
from .export import VideoExporter

logger = logging.getLogger(__name__)

class AudioVisualOverlay:
    """
    Main class for creating audio-visual overlays with reactive elements.
    Acts as a facade to the various specialized components.
    """
    def __init__(self, video_path=None):
        """
        Initialize the audio visual overlay processor
        
        Args:
            video_path: Optional path to video file to load immediately
        """
        self.video = None
        self.element_manager = ElementManager()
        self.audio_feature_extractor = AudioFeatureExtractor()
        self.exporter = VideoExporter()
        
        if video_path:
            self.load_video(video_path)
        
    def load_video(self, video_path):
        """Load a video file for processing
        
        Args:
            video_path: Path to the video file
            
        Returns:
            self: For method chaining
        """
        self.video = VideoFileClip(video_path)
        
        # Initialize managers with the base video
        self.element_manager.set_base_video(self.video)
        self.exporter.set_video(self.video)
        
        return self
    
    def extract_audio_features(self, n_mfcc=13, hop_length=512):
        """Extract audio features for reactive elements
        
        Args:
            n_mfcc: Number of MFCC coefficients to extract
            hop_length: Hop length for feature extraction
            
        Returns:
            self: For method chaining
        """
        if not self.video:
            logger.error("No video loaded.")
            return self
            
        self.audio_feature_extractor.extract_from_video(
            self.video, 
            n_mfcc=n_mfcc, 
            hop_length=hop_length
        )
        
        # Share the extracted features with the element manager
        self.element_manager.set_audio_features(self.audio_feature_extractor.features)
        
        return self
    
    def add_logo(self, logo_path, position="top-right", size=0.15, margin=20):
        """Add a logo element to the video
        
        Args:
            logo_path: Path to logo image file
            position: Position hint ("top-right", "center", etc.)
            size: Size as fraction of video width or (w, h) tuple
            margin: Margin from edges in pixels
            
        Returns:
            LogoElement: The created logo element for adding reactions
        """
        if not self.video:
            logger.error("No video loaded.")
            return None
            
        # Create the logo element
        logo = self.element_manager.create_logo(
            logo_path=logo_path,
            position=position,
            size=size,
            margin=margin
        )
        
        return logo
    
    def add_text(self, text, position="bottom-center", fontsize=30, 
                color="white", font_path=None, margin=30):
        """Add a text element to the video
        
        Args:
            text: Text content
            position: Position hint ("bottom-center", "top-left", etc.)
            fontsize: Font size in pixels
            color: Text color
            font_path: Optional path to font file
            margin: Margin from edges in pixels
            
        Returns:
            TextElement: The created text element for adding reactions
        """
        if not self.video:
            logger.error("No video loaded.")
            return None
            
        # Create the text element
        text_elem = self.element_manager.create_text(
            text=text,
            position=position,
            fontsize=fontsize,
            color=color,
            font_path=font_path,
            margin=margin
        )
        
        return text_elem
    
    def process(self):
        """Process the video with all elements and their reactions
        
        Returns:
            self: For method chaining
        """
        if not self.video:
            logger.error("No video loaded.")
            return self
            
        # Render all elements
        element_clips = self.element_manager.render_all()
        
        # Create the final composite video
        if element_clips:
            all_clips = [self.video] + element_clips
            self.video = CompositeVideoClip(all_clips, size=self.video.size)
            
            # Update the exporter with the new video
            self.exporter.set_video(self.video)
            
        return self
    
    def export(self, output_path, fps=None, threads=None):
        """Export the processed video
        
        Args:
            output_path: Path to save the output video
            fps: Frames per second (optional)
            threads: Number of CPU threads to use for processing (default: auto-detect)
            
        Returns:
            str: Path to the exported video
        """
        if not self.video:
            logger.error("No video loaded.")
            return None
            
        return self.exporter.export(output_path, fps=fps, threads=threads)
    
    def export_gpu_optimized(self, output_path, quality='balanced', threads=None):
        """Export using GPU acceleration if available
        
        Args:
            output_path: Path to save the output video
            quality: Quality preset ('speed', 'balanced', 'quality')
            threads: Number of CPU threads to use for processing (default: auto-detect)
            
        Returns:
            str: Path to the exported video
        """
        if not self.video:
            logger.error("No video loaded.")
            return None
            
        return self.exporter.export_gpu_optimized(output_path, quality=quality, threads=threads)