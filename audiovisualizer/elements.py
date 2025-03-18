import logging
import numpy as np
from PIL import Image, ImageEnhance
from moviepy.video.VideoClip import ImageClip, TextClip
import os

logger = logging.getLogger(__name__)

class ElementManager:
    """Base class for visual element managers"""
    
    def __init__(self):
        self.base_video = None
        self.audio_features = None
        
    def set_base_video(self, video):
        """Set the base video to overlay elements on"""
        self.base_video = video
        
    def set_audio_features(self, features):
        """Set audio features for reactive elements"""
        self.audio_features = features
        
    def _calculate_position(self, element_size, position, margin):
        """Calculate x, y coordinates based on position hint and margin"""
        if not self.base_video:
            return 0, 0
            
        video_w, video_h = self.base_video.size
        element_w, element_h = element_size
        
        x_pos, y_pos = 0, 0
        
        # Horizontal position
        if position[0] == 'left':
            x_pos = margin
        elif position[0] == 'center':
            x_pos = (video_w - element_w) // 2
        elif position[0] == 'right':
            x_pos = video_w - element_w - margin
        
        # Vertical position
        if position[1] == 'top':
            y_pos = margin
        elif position[1] == 'center':
            y_pos = (video_h - element_h) // 2
        elif position[1] == 'bottom':
            y_pos = video_h - element_h - margin
            
        return x_pos, y_pos
        
    def _get_feature_values(self, react_to):
        """Get the specified audio feature values or fall back to RMS"""
        if not self.audio_features or react_to not in self.audio_features:
            logger.warning(f"Audio feature {react_to} not available. Using 'rms' instead.")
            react_to = 'rms'
            
            # If still not available, return None
            if react_to not in self.audio_features:
                return None
                
        return self.audio_features[react_to]

    def _smooth_transition(self, curr_value, prev_value, smoothing_factor=0.3):
        """Apply smoothing to transitions to avoid flickering"""
        if prev_value is None:
            return curr_value
        return prev_value + smoothing_factor * (curr_value - prev_value)


class LogoManager(ElementManager):
    """Manages logo overlays (static and reactive)"""
    
    def create_static_logo(self, logo_path, position=('right', 'top'), margin=20, size=0.15):
        """Create a static logo overlay"""
        if not self.base_video:
            logger.error("No base video set")
            return None
            
        try:
            if not os.path.exists(logo_path):
                logger.error(f"Logo file not found: {logo_path}")
                return None
                
            logo = ImageClip(logo_path)
            
            # Set the duration to match the background video
            logo = logo.with_duration(self.base_video.duration)
            
            # Calculate the size based on the video dimensions
            video_w, video_h = self.base_video.size
            if isinstance(size, float):
                logo_w = int(video_w * size)
                logo = logo.resized(width=logo_w)
                
            # Determine position
            x_pos, y_pos = self._calculate_position(logo.size, position, margin)
            
            # Return the positioned logo clip
            return logo.with_position((x_pos, y_pos))
            
        except Exception as e:
            logger.error(f"Error creating static logo: {e}")
            return None
            
    def create_reactive_logo(self, logo_path, position=('right', 'top'), margin=20, 
                             base_size=0.15, react_to='rms', intensity=0.3):
        """Create a logo that reacts to audio features"""
        if not self.base_video:
            logger.error("No base video set")
            return None
            
        if not self.audio_features:
            logger.error("No audio features available")
            return None
            
        if not os.path.exists(logo_path):
            logger.error(f"Logo file not found: {logo_path}")
            return None
            
        feature_values = self._get_feature_values(react_to)
        if feature_values is None:
            return None
            
        try:
            # Base logo calculations
            video_w, video_h = self.base_video.size
            base_logo_w = int(video_w * base_size)
            base_logo = ImageClip(logo_path).resized(width=base_logo_w)
            base_logo_w, base_logo_h = base_logo.size
            
            # Base position
            base_x, base_y = self._calculate_position((base_logo_w, base_logo_h), position, margin)
            
            # Create a sequence of frames at appropriate times
            logo_clips = []
            frame_duration = 1.0 / self.base_video.fps
            total_duration = self.base_video.duration
            
            # For smoothing transitions
            prev_scale = None
            prev_brightness = None
            min_visibility = 0.1  # Ensure elements are never completely hidden
            
            for t in np.arange(0, total_duration, frame_duration):
                frame_idx = min(int(t * self.base_video.fps), len(feature_values) - 1)
                value = feature_values[frame_idx]
                
                # Apply smoothing to scale and brightness transitions
                scale_factor = 1.0 + (value * intensity)
                scale_factor = self._smooth_transition(scale_factor, prev_scale)
                prev_scale = scale_factor
                
                brightness_factor = 0.8 + (value * 0.4)
                brightness_factor = self._smooth_transition(brightness_factor, prev_brightness)
                prev_brightness = brightness_factor
                
                # Ensure minimum visibility (never fully hide elements)
                if "hide" in react_to and scale_factor < min_visibility:
                    scale_factor = min_visibility
                if "hide" in react_to and brightness_factor < min_visibility:
                    brightness_factor = min_visibility
                
                # Get the original logo image
                logo_img = np.array(Image.open(logo_path))
                
                # Convert to PIL Image for processing
                pil_img = Image.fromarray(logo_img)
                
                # Calculate new dimensions
                new_w = int(base_logo_w * scale_factor)
                new_h = int(base_logo_h * scale_factor)
                
                # Resize image
                pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)
                
                # Enhance brightness based on audio feature
                enhancer = ImageEnhance.Brightness(pil_img)
                pil_img = enhancer.enhance(brightness_factor)
                
                # Create ImageClip for this frame with the exact duration of one frame
                img_clip = ImageClip(np.array(pil_img))
                img_clip = img_clip.with_duration(frame_duration)
                
                # Calculate position to keep logo centered at original position
                width_diff = int((new_w - base_logo_w) / 2)
                height_diff = int((new_h - base_logo_h) / 2)
                pos = (base_x - width_diff, base_y - height_diff)
                
                # Add to list with correct position and start time
                logo_clips.append(img_clip.with_position(pos).with_start(t))
                
            return logo_clips
                
        except Exception as e:
            logger.error(f"Error creating reactive logo: {e}")
            return None


class TextManager(ElementManager):
    """Manages text overlays (static and reactive)"""
    
    def create_static_text(self, text, position=('center', 'bottom'), margin=30,
                          fontsize=30, color='white', font_path=None, duration=None):
        """Create a static text overlay"""
        if not self.base_video:
            logger.error("No base video set")
            return None
            
        try:
            # Create the text clip with font_path instead of font name
            kwargs = {
                'text': text,
                'font_size': fontsize,
                'color': color
            }
            
            if font_path and os.path.exists(font_path):
                kwargs['font'] = font_path
                
            text_clip = TextClip(**kwargs)
            
            # Set duration
            if duration:
                text_clip = text_clip.with_duration(duration)
            else:
                text_clip = text_clip.with_duration(self.base_video.duration)
                
            # Determine position
            x_pos, y_pos = self._calculate_position(text_clip.size, position, margin)
            
            # Return the positioned text clip
            return text_clip.with_position((x_pos, y_pos))
            
        except Exception as e:
            logger.error(f"Error creating static text: {e}")
            return None
            
    def create_reactive_text(self, text, position=('center', 'bottom'), margin=30,
                             base_fontsize=30, color='white', font_path=None,
                             react_to='rms', intensity=0.3):
        """Create text that reacts to audio features"""
        if not self.base_video:
            logger.error("No base video set")
            return None
            
        if not self.audio_features:
            logger.error("No audio features available")
            return None
            
        feature_values = self._get_feature_values(react_to)
        if feature_values is None:
            return None
            
        try:
            # Create a temporary text clip to estimate dimensions
            kwargs = {
                'text': text,
                'font_size': base_fontsize,
                'color': color
            }
            
            if font_path and os.path.exists(font_path):
                kwargs['font'] = font_path
                
            temp_clip = TextClip(**kwargs)
            base_text_w, base_text_h = temp_clip.size
            temp_clip.close()
            
            # Base position
            base_x, base_y = self._calculate_position((base_text_w, base_text_h), position, margin)
            
            # Create a sequence of frames at appropriate times
            text_clips = []
            frame_duration = 1.0 / self.base_video.fps
            total_duration = self.base_video.duration
            
            # For smoothing transitions
            prev_fontsize = None
            min_visibility = 0.1  # Ensure elements are never completely hidden
            
            for t in np.arange(0, total_duration, frame_duration):
                frame_idx = min(int(t * self.base_video.fps), len(feature_values) - 1)
                value = feature_values[frame_idx]
                
                # Apply smoothing to fontsize transitions
                scale_factor = 1.0 + (value * intensity)
                scale_factor = self._smooth_transition(scale_factor, prev_fontsize)
                prev_fontsize = scale_factor
                
                # Ensure minimum visibility (never fully hide elements)
                if "hide" in react_to and scale_factor < min_visibility:
                    scale_factor = min_visibility
                
                # Scale fontsize based on the audio feature
                fontsize = int(base_fontsize * scale_factor)
                
                # Create a TextClip with the appropriate size for this frame
                kwargs['font_size'] = fontsize
                frame_clip = TextClip(**kwargs)
                frame_clip = frame_clip.with_duration(frame_duration)
                
                # Calculate new dimensions
                new_w, new_h = frame_clip.size
                
                # Calculate position to keep text centered at original position
                width_diff = int((new_w - base_text_w) / 2)
                height_diff = int((new_h - base_text_h) / 2)
                pos = (base_x - width_diff, base_y - height_diff)
                
                # Add to list with correct position and start time
                text_clips.append(frame_clip.with_position(pos).with_start(t))
                
            return text_clips
                
        except Exception as e:
            logger.error(f"Error creating reactive text: {e}")
            return None