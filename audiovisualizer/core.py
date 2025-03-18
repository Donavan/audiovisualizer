import os
import logging
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

from .audio_features import AudioFeatureExtractor
from .elements import LogoManager, TextManager
from .export import VideoExporter

logger = logging.getLogger(__name__)

class AudioVisualOverlay:
    """
    Main class for creating audio-visual overlays with reactive elements.
    Acts as a facade to the various specialized components.
    """
    def __init__(self):
        self.visualization_video = None
        self.logo_manager = LogoManager()
        self.text_manager = TextManager()
        self.audio_feature_extractor = AudioFeatureExtractor()
        self.exporter = VideoExporter()
        
    def load_files(self, visualization_path, logo_path=None):
        """Load the visualization video (with embedded audio) and optional logo."""
        self.visualization_video = VideoFileClip(visualization_path)
        
        # Initialize managers with the base video
        self._update_managers()
        return self
    
    def _update_managers(self):
        """Update all managers with current video properties"""
        if self.visualization_video:
            self.logo_manager.set_base_video(self.visualization_video)
            self.text_manager.set_base_video(self.visualization_video)
            self.exporter.set_video(self.visualization_video)
    
    def extract_audio_features(self, n_mfcc=13, hop_length=512):
        """Extract audio features for potential reactive elements from the video's audio."""
        if not self.visualization_video:
            logger.error("No visualization video loaded.")
            return self
            
        self.audio_feature_extractor.extract_from_video(
            self.visualization_video, 
            n_mfcc=n_mfcc, 
            hop_length=hop_length
        )
        
        # Share the extracted features with managers that need them
        self.logo_manager.set_audio_features(self.audio_feature_extractor.features)
        self.text_manager.set_audio_features(self.audio_feature_extractor.features)
        
        return self
    
    def add_static_logo(self, logo_path=None, position=('right', 'top'), margin=20, size=0.15):
        """Add a static logo overlay to the visualization."""
        if not logo_path:
            logger.warning("No logo file provided.")
            return self
            
        logo_clip = self.logo_manager.create_static_logo(
            logo_path=logo_path,
            position=position,
            margin=margin,
            size=size
        )
        
        # Update the main video with the logo added
        if logo_clip:
            self.visualization_video = CompositeVideoClip([
                self.visualization_video,
                logo_clip
            ])
            self._update_managers()
            
        return self
    
    def add_reactive_logo(self, logo_path=None, position=('right', 'top'), margin=20, base_size=0.15,
                          react_to='rms', intensity=0.3):
        """Add a logo that reacts to audio features like amplitude/beats."""
        if not logo_path:
            logger.warning("No logo file provided.")
            return self
            
        if not hasattr(self.audio_feature_extractor, 'features') or not self.audio_feature_extractor.features:
            logger.warning("Audio features not extracted. Call extract_audio_features() first.")
            return self
            
        logo_clips = self.logo_manager.create_reactive_logo(
            logo_path=logo_path,
            position=position,
            margin=margin,
            base_size=base_size,
            react_to=react_to,
            intensity=intensity
        )
        
        # Update the main video with the reactive logo elements
        if logo_clips:
            all_clips = [self.visualization_video] + logo_clips
            self.visualization_video = CompositeVideoClip(all_clips, size=self.visualization_video.size)
            self._update_managers()
            
        return self
    
    def add_text_overlay(self, text, position=('center', 'bottom'), margin=30,
                         fontsize=30, color='white', font_path=None, duration=None):
        """Add a text overlay to the visualization."""
        text_clip = self.text_manager.create_static_text(
            text=text,
            position=position,
            margin=margin,
            fontsize=fontsize,
            color=color,
            font_path=font_path,
            duration=duration
        )
        
        # Update the main video with the text element
        if text_clip:
            self.visualization_video = CompositeVideoClip([
                self.visualization_video,
                text_clip
            ])
            self._update_managers()
            
        return self
    
    def add_reactive_text(self, text, position=('center', 'bottom'), margin=30,
                          base_fontsize=30, color='white', font_path=None,
                          react_to='rms', intensity=0.3):
        """Add text that reacts to audio features like amplitude/beats."""
        if not hasattr(self.audio_feature_extractor, 'features') or not self.audio_feature_extractor.features:
            logger.warning("Audio features not extracted. Call extract_audio_features() first.")
            return self
            
        text_clips = self.text_manager.create_reactive_text(
            text=text,
            position=position,
            margin=margin,
            base_fontsize=base_fontsize,
            color=color,
            font_path=font_path,
            react_to=react_to,
            intensity=intensity
        )
        
        # Update the main video with the reactive text elements
        if text_clips:
            all_clips = [self.visualization_video] + text_clips
            self.visualization_video = CompositeVideoClip(all_clips, size=self.visualization_video.size)
            self._update_managers()
            
        return self
    
    def export_gpu_optimized(self, output_path, quality='balanced'):
        """Try to use GPU acceleration for export but fall back to CPU if needed."""
        return self.exporter.export_gpu_optimized(output_path, quality=quality)
    
    def export(self, output_path, fps=None):
        """Simple and reliable export method that works on all systems."""
        return self.exporter.export(output_path, fps=fps)