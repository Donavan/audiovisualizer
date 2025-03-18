import logging
import numpy as np
from PIL import Image, ImageEnhance
from moviepy.video.VideoClip import ImageClip, TextClip
import os
from typing import Dict, List, Tuple, Union, Callable, Optional, Any

logger = logging.getLogger(__name__)


class Element:
    """Base class for visual elements that can be overlaid on videos"""
    
    def __init__(self, clip, position: Tuple[int, int]):
        """Initialize the element with a clip and position
        
        Args:
            clip: The MoviePy clip (ImageClip, TextClip, etc.)
            position: The (x, y) position coordinates
        """
        self.clip = clip
        self.position = position
        self.original_size = clip.size
        self.reactions = {}
        self.audio_features = None
        
    def set_audio_features(self, features):
        """Set audio features for reactive behavior
        
        Args:
            features: Dictionary of audio features
        """
        self.audio_features = features
        return self
        
    def add_reaction(self, reaction_type: str, feature: str, params: Dict[str, Any]):
        """Add a reaction to this element
        
        Args:
            reaction_type: Type of reaction ("scale", "opacity", "color", "position", etc.)
            feature: Audio feature to react to ("rms", "bass", "mids", etc.)
            params: Parameters for this reaction (intensity, min_value, max_value, etc.)
            
        Returns:
            self: For method chaining
        """
        self.reactions[reaction_type] = {
            "feature": feature,
            "params": params
        }
        return self
        
    def render(self, video_fps: float, total_duration: float) -> List[ImageClip]:
        """Render this element with all its reactions
        
        Args:
            video_fps: Frames per second of the base video
            total_duration: Total duration of the video in seconds
            
        Returns:
            List of clips that represent this element over time
        """
        if not self.audio_features:
            # Return static clip if no audio features available
            return [self.clip.with_position(self.position).with_duration(total_duration)]
            
        # Create a sequence of frames at appropriate times
        element_clips = []
        frame_duration = 1.0 / video_fps
        
        # Previous values for smoothing
        prev_values = {reaction_type: None for reaction_type in self.reactions}
        
        for t in np.arange(0, total_duration, frame_duration):
            # Apply all reactions to create this frame
            frame = self._create_frame_at_time(t, frame_duration, video_fps, prev_values)
            if frame:
                element_clips.append(frame)
                
        return element_clips
    
    def _create_frame_at_time(self, time: float, frame_duration: float, 
                             video_fps: float, prev_values: Dict[str, Any]) -> Optional[ImageClip]:
        """Create a single frame with all reactions applied at the given time
        
        Args:
            time: Time position in the video
            frame_duration: Duration of a single frame
            video_fps: Video frames per second
            prev_values: Previous reaction values for smoothing
            
        Returns:
            ImageClip for this frame, or None if creation failed
        """
        # This will be implemented differently for each element type
        raise NotImplementedError("Subclasses must implement this method")

    def _smooth_transition(self, curr_value: float, prev_value: Optional[float], 
                         smoothing_factor: float = 0.3) -> float:
        """Apply smoothing to transitions to avoid flickering
        
        Args:
            curr_value: Current value
            prev_value: Previous value
            smoothing_factor: Amount of smoothing (0-1)
            
        Returns:
            Smoothed value
        """
        if prev_value is None:
            return curr_value
        return prev_value + smoothing_factor * (curr_value - prev_value)

    def _get_feature_value_at_time(self, feature: str, time: float, video_fps: float) -> float:
        """Get audio feature value at specific time
        
        Args:
            feature: Feature name
            time: Time in seconds
            video_fps: Video frames per second
            
        Returns:
            Feature value normalized between 0 and 1
        """
        if not self.audio_features or feature not in self.audio_features:
            logger.warning(f"Audio feature {feature} not available. Using default value.")
            return 0.5
            
        feature_values = self.audio_features[feature]
        frame_idx = min(int(time * video_fps), len(feature_values) - 1)
        return feature_values[frame_idx]


class LogoElement(Element):
    """Logo overlay element that can react to audio"""
    
    def __init__(self, logo_path: str, position: Tuple[int, int], 
                base_size: Optional[Union[float, Tuple[int, int]]] = None):
        """Initialize logo element
        
        Args:
            logo_path: Path to logo image file
            position: (x, y) position coordinates
            base_size: Base size as fraction of video or (width, height) tuple
        """
        self.logo_path = logo_path
        self.base_size = base_size
        
        # Load original logo image
        logo_clip = ImageClip(logo_path)
        
        super().__init__(logo_clip, position)
    
    def _create_frame_at_time(self, time: float, frame_duration: float, 
                             video_fps: float, prev_values: Dict[str, Any]) -> Optional[ImageClip]:
        """Create a single logo frame with all reactions applied
        
        Args:
            time: Time position in the video
            frame_duration: Duration of a single frame
            video_fps: Video frames per second
            prev_values: Previous reaction values for smoothing
            
        Returns:
            ImageClip for this frame
        """
        try:
            # Get the original logo image
            logo_img = np.array(Image.open(self.logo_path))
            
            # Convert to PIL Image for processing
            pil_img = Image.fromarray(logo_img)
            
            # Get base dimensions
            width, height = self.original_size
            pos_x, pos_y = self.position
            
            # Process different reaction types
            modified = False
            
            # Scale reaction processing
            if "scale" in self.reactions:
                reaction = self.reactions["scale"]
                feature = reaction["feature"]
                intensity = reaction["params"].get("intensity", 0.3)
                min_scale = reaction["params"].get("min_scale", 1.0)
                max_scale = reaction["params"].get("max_scale", 1.5)
                
                value = self._get_feature_value_at_time(feature, time, video_fps)
                scale_range = max_scale - min_scale
                scale_factor = min_scale + (value * scale_range)
                
                # Apply smoothing
                scale_factor = self._smooth_transition(
                    scale_factor, 
                    prev_values["scale"], 
                    reaction["params"].get("smoothing", 0.3)
                )
                prev_values["scale"] = scale_factor
                
                # Calculate new dimensions
                new_w = int(width * scale_factor)
                new_h = int(height * scale_factor)
                
                # Resize image
                pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)
                
                # Recalculate position to maintain center point
                width_diff = int((new_w - width) / 2)
                height_diff = int((new_h - height) / 2)
                pos_x = self.position[0] - width_diff
                pos_y = self.position[1] - height_diff
                
                modified = True
            
            # Opacity/brightness reaction processing
            if "opacity" in self.reactions:
                reaction = self.reactions["opacity"]
                feature = reaction["feature"]
                intensity = reaction["params"].get("intensity", 0.5)
                min_opacity = reaction["params"].get("min_opacity", 0.3)
                max_opacity = reaction["params"].get("max_opacity", 1.0)
                
                value = self._get_feature_value_at_time(feature, time, video_fps)
                opacity_range = max_opacity - min_opacity
                opacity = min_opacity + (value * opacity_range)
                
                # Apply smoothing
                opacity = self._smooth_transition(
                    opacity, 
                    prev_values["opacity"], 
                    reaction["params"].get("smoothing", 0.3)
                )
                prev_values["opacity"] = opacity
                
                # Enhance opacity (via brightness for PNG images with alpha)
                enhancer = ImageEnhance.Brightness(pil_img)
                pil_img = enhancer.enhance(opacity)
                
                modified = True
                
            # Color reaction processing (hue shift, saturation, etc.)
            if "color" in self.reactions:
                reaction = self.reactions["color"]
                feature = reaction["feature"]
                color_type = reaction["params"].get("type", "saturation")
                min_value = reaction["params"].get("min_value", 0.5)
                max_value = reaction["params"].get("max_value", 1.5)
                
                value = self._get_feature_value_at_time(feature, time, video_fps)
                value_range = max_value - min_value
                color_value = min_value + (value * value_range)
                
                # Apply smoothing
                color_value = self._smooth_transition(
                    color_value, 
                    prev_values["color"], 
                    reaction["params"].get("smoothing", 0.3)
                )
                prev_values["color"] = color_value
                
                # Apply color transformation based on type
                if color_type == "saturation":
                    enhancer = ImageEnhance.Color(pil_img)
                    pil_img = enhancer.enhance(color_value)
                elif color_type == "contrast":
                    enhancer = ImageEnhance.Contrast(pil_img)
                    pil_img = enhancer.enhance(color_value)
                    
                modified = True
                
            # Position reaction (bounce, shake, etc.) - advanced feature
            if "position" in self.reactions:
                reaction = self.reactions["position"]
                feature = reaction["feature"]
                movement_type = reaction["params"].get("type", "bounce")
                intensity = reaction["params"].get("intensity", 10)  # pixels
                
                value = self._get_feature_value_at_time(feature, time, video_fps)
                
                # Different movement patterns
                if movement_type == "bounce":
                    # Simple bounce effect based on audio value
                    offset_y = int(intensity * value)
                    pos_y = self.position[1] - offset_y
                elif movement_type == "shake":
                    # Random shake with intensity based on audio
                    shake_amount = int(intensity * value)
                    offset_x = np.random.randint(-shake_amount, shake_amount+1)
                    offset_y = np.random.randint(-shake_amount, shake_amount+1)
                    pos_x = self.position[0] + offset_x
                    pos_y = self.position[1] + offset_y
                    
                modified = True
            
            # Create ImageClip for this frame
            if modified:
                img_clip = ImageClip(np.array(pil_img))
                img_clip = img_clip.with_duration(frame_duration)
                img_clip = img_clip.with_position((pos_x, pos_y))
                img_clip = img_clip.with_start(time)
                return img_clip
            else:
                # If no modifications, return a simple clip with the original image
                return self.clip.with_position(self.position).with_start(time).with_duration(frame_duration)
                
        except Exception as e:
            logger.error(f"Error creating logo frame at {time}s: {e}")
            return None


class TextElement(Element):
    """Text overlay element that can react to audio"""
    
    def __init__(self, text: str, position: Tuple[int, int], 
                fontsize: int = 30, color: str = 'white', 
                font_path: Optional[str] = None):
        """Initialize text element
        
        Args:
            text: Text content
            position: (x, y) position coordinates
            fontsize: Base font size
            color: Text color
            font_path: Optional custom font file path
        """
        self.text = text
        self.fontsize = fontsize
        self.color = color
        self.font_path = font_path
        
        # Create kwargs for TextClip
        self.text_kwargs = {
            'text': text,
            'font_size': fontsize,
            'color': color
        }
        
        if font_path and os.path.exists(font_path):
            self.text_kwargs['font'] = font_path
            
        # Create base text clip
        text_clip = TextClip(**self.text_kwargs)
        
        super().__init__(text_clip, position)
    
    def _create_frame_at_time(self, time: float, frame_duration: float, 
                             video_fps: float, prev_values: Dict[str, Any]) -> Optional[TextClip]:
        """Create a single text frame with all reactions applied
        
        Args:
            time: Time position in the video
            frame_duration: Duration of a single frame
            video_fps: Video frames per second
            prev_values: Previous reaction values for smoothing
            
        Returns:
            TextClip for this frame
        """
        try:
            # Start with base text properties
            kwargs = self.text_kwargs.copy()
            pos_x, pos_y = self.position
            base_width, base_height = self.original_size
            color = self.color
            modified = False
            
            # Font size reaction
            if "scale" in self.reactions:
                reaction = self.reactions["scale"]
                feature = reaction["feature"]
                min_scale = reaction["params"].get("min_scale", 1.0)
                max_scale = reaction["params"].get("max_scale", 1.5)
                
                value = self._get_feature_value_at_time(feature, time, video_fps)
                scale_range = max_scale - min_scale
                scale_factor = min_scale + (value * scale_range)
                
                # Apply smoothing
                scale_factor = self._smooth_transition(
                    scale_factor, 
                    prev_values["scale"], 
                    reaction["params"].get("smoothing", 0.3)
                )
                prev_values["scale"] = scale_factor
                
                # Set new fontsize
                kwargs['font_size'] = int(self.fontsize * scale_factor)
                modified = True
            
            # Color reaction (color shift based on audio)
            if "color" in self.reactions:
                reaction = self.reactions["color"]
                feature = reaction["feature"]
                color_map = reaction["params"].get("color_map", [(0, "white"), (1, "red")])
                
                value = self._get_feature_value_at_time(feature, time, video_fps)
                
                # Find which color range we're in
                for i in range(len(color_map) - 1):
                    low_val, low_color = color_map[i]
                    high_val, high_color = color_map[i + 1]
                    
                    if low_val <= value <= high_val:
                        # Interpolate between colors
                        ratio = (value - low_val) / (high_val - low_val) if high_val > low_val else 0
                        color = self._interpolate_color(low_color, high_color, ratio)
                        break
                
                kwargs['color'] = color
                modified = True
                
            # Opacity reaction
            opacity = 1.0
            if "opacity" in self.reactions:
                reaction = self.reactions["opacity"]
                feature = reaction["feature"]
                min_opacity = reaction["params"].get("min_opacity", 0.0)
                max_opacity = reaction["params"].get("max_opacity", 1.0)
                
                value = self._get_feature_value_at_time(feature, time, video_fps)
                opacity_range = max_opacity - min_opacity
                opacity = min_opacity + (value * opacity_range)
                
                # Apply smoothing
                opacity = self._smooth_transition(
                    opacity, 
                    prev_values["opacity"], 
                    reaction["params"].get("smoothing", 0.3)
                )
                prev_values["opacity"] = opacity
                modified = True
            
            # Position reaction (bounce, shake, etc.)
            if "position" in self.reactions:
                reaction = self.reactions["position"]
                feature = reaction["feature"]
                movement_type = reaction["params"].get("type", "bounce")
                intensity = reaction["params"].get("intensity", 10)  # pixels
                
                value = self._get_feature_value_at_time(feature, time, video_fps)
                
                # Different movement patterns
                if movement_type == "bounce":
                    # Simple bounce effect based on audio value
                    offset_y = int(intensity * value)
                    pos_y = self.position[1] - offset_y
                elif movement_type == "shake":
                    # Random shake with intensity based on audio
                    shake_amount = int(intensity * value)
                    offset_x = np.random.randint(-shake_amount, shake_amount+1)
                    offset_y = np.random.randint(-shake_amount, shake_amount+1)
                    pos_x = self.position[0] + offset_x
                    pos_y = self.position[1] + offset_y
                    
                modified = True
                
            # Create the text clip for this frame
            if modified:
                frame_clip = TextClip(**kwargs)
                frame_clip = frame_clip.with_duration(frame_duration)
                
                # Handle centering if size changed
                if "scale" in self.reactions:
                    new_width, new_height = frame_clip.size
                    width_diff = int((new_width - base_width) / 2)
                    height_diff = int((new_height - base_height) / 2)
                    pos_x = self.position[0] - width_diff
                    pos_y = self.position[1] - height_diff
                
                frame_clip = frame_clip.with_position((pos_x, pos_y))
                frame_clip = frame_clip.with_start(time)
                
                # Apply opacity if needed
                if "opacity" in self.reactions:
                    frame_clip = frame_clip.with_opacity(opacity)
                    
                return frame_clip
            else:
                # If no modifications, return the base clip with position and time
                return self.clip.with_position(self.position).with_start(time).with_duration(frame_duration)
                
        except Exception as e:
            logger.error(f"Error creating text frame at {time}s: {e}")
            return None
    
    def _interpolate_color(self, color1: str, color2: str, ratio: float) -> str:
        """Interpolate between two colors
        
        Args:
            color1: First color (hex or name)
            color2: Second color (hex or name)
            ratio: Blend ratio (0-1)
            
        Returns:
            Interpolated color in hex format
        """
        # Convert named colors to RGB values
        # This is a simplified version - would need color name mapping for full support
        if color1.startswith('#'):
            r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        else:
            # Default white if not hex
            r1, g1, b1 = 255, 255, 255
            
        if color2.startswith('#'):
            r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        else:
            # Default white if not hex
            r2, g2, b2 = 255, 255, 255
        
        # Interpolate RGB values
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        
        # Return as hex string
        return f'#{r:02x}{g:02x}{b:02x}'


class ElementManager:
    """Manages visual elements and their positions"""
    
    def __init__(self):
        self.base_video = None
        self.audio_features = None
        self.elements = []
        
    def set_base_video(self, video):
        """Set the base video to overlay elements on"""
        self.base_video = video
        return self
        
    def set_audio_features(self, features):
        """Set audio features for reactive elements"""
        self.audio_features = features
        
        # Update all elements with these features
        for element in self.elements:
            element.set_audio_features(features)
            
        return self
    
    def add_element(self, element):
        """Add an element to be managed"""
        element.set_audio_features(self.audio_features)
        self.elements.append(element)
        return element  # Return the element for chaining
        
    def _calculate_position(self, element_size, position_hint, margin=20):
        """Calculate x, y coordinates based on position hint and margin"""
        if not self.base_video:
            return 0, 0
            
        video_w, video_h = self.base_video.size
        element_w, element_h = element_size
        
        # Handle string position hints
        if isinstance(position_hint, str):
            parts = position_hint.lower().split('-')
            vertical = parts[0] if parts[0] in ['top', 'center', 'bottom'] else 'center'
            horizontal = parts[1] if len(parts) > 1 and parts[1] in ['left', 'center', 'right'] else 'center'
            position_hint = (horizontal, vertical)
        
        x_pos, y_pos = 0, 0
        
        # Horizontal position
        if position_hint[0] == 'left':
            x_pos = margin
        elif position_hint[0] == 'center':
            x_pos = (video_w - element_w) // 2
        elif position_hint[0] == 'right':
            x_pos = video_w - element_w - margin
        
        # Vertical position
        if position_hint[1] == 'top':
            y_pos = margin
        elif position_hint[1] == 'center':
            y_pos = (video_h - element_h) // 2
        elif position_hint[1] == 'bottom':
            y_pos = video_h - element_h - margin
            
        return x_pos, y_pos
    
    def create_logo(self, logo_path, position=('right', 'top'), size=0.15, margin=20):
        """Create a logo element
        
        Args:
            logo_path: Path to logo image
            position: Position hint ('top-left', 'center-bottom', etc.)
            size: Size as a fraction of video width or (w, h) tuple
            margin: Margin from edges in pixels
            
        Returns:
            LogoElement instance for adding reactions
        """
        if not self.base_video:
            logger.error("No base video set")
            return None
            
        if not os.path.exists(logo_path):
            logger.error(f"Logo file not found: {logo_path}")
            return None
            
        try:
            # Load temporary logo to calculate size
            temp_logo = ImageClip(logo_path)
            
            # Calculate size based on video dimensions
            video_w, video_h = self.base_video.size
            if isinstance(size, float):
                logo_w = int(video_w * size)
                temp_logo = temp_logo.resized(width=logo_w)
                
            # Determine position
            pos = self._calculate_position(temp_logo.size, position, margin)
            
            # Create and return the logo element
            logo_element = LogoElement(logo_path, pos, base_size=size)
            self.add_element(logo_element)
            return logo_element
            
        except Exception as e:
            logger.error(f"Error creating logo element: {e}")
            return None
    
    def create_text(self, text, position=('center', 'bottom'), fontsize=30, 
                   color='white', font_path=None, margin=30):
        """Create a text element
        
        Args:
            text: Text content
            position: Position hint ('top-left', 'center-bottom', etc.)
            fontsize: Font size in pixels
            color: Text color
            font_path: Optional path to font file
            margin: Margin from edges in pixels
            
        Returns:
            TextElement instance for adding reactions
        """
        if not self.base_video:
            logger.error("No base video set")
            return None
            
        try:
            # Create temporary text clip to get dimensions
            kwargs = {
                'text': text,
                'font_size': fontsize,
                'color': color
            }
            
            if font_path and os.path.exists(font_path):
                kwargs['font'] = font_path
                
            temp_clip = TextClip(**kwargs)
            
            # Determine position
            pos = self._calculate_position(temp_clip.size, position, margin)
            temp_clip.close()
            
            # Create and return the text element
            text_element = TextElement(text, pos, fontsize, color, font_path)
            self.add_element(text_element)
            return text_element
            
        except Exception as e:
            logger.error(f"Error creating text element: {e}")
            return None
    
    def render_all(self):
        """Render all elements into clips for compositing
        
        Returns:
            List of all rendered element clips
        """
        if not self.base_video:
            logger.error("No base video set")
            return []
            
        all_clips = []
        fps = self.base_video.fps
        duration = self.base_video.duration
        
        for element in self.elements:
            element_clips = element.render(fps, duration)
            all_clips.extend(element_clips)
            
        return all_clips