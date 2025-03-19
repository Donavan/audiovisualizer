import os
import logging
from typing import Dict, List, Optional, Tuple, Union, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseEffect(ABC):
    """
    Abstract base class for all visual effects.
    """
    
    def __init__(self, **kwargs):
        self.params = kwargs
        self.requires_audio_analysis = False
    
    @abstractmethod
    def prepare(self, audio_analyzer) -> None:
        """
        Prepare the effect for rendering, potentially using audio analysis.
        
        Args:
            audio_analyzer: AudioAnalyzer instance with extracted features
        """
        pass
    
    @abstractmethod
    def get_filter_string(self) -> str:
        """
        Get the FFmpeg filter string for this effect.
        
        Returns:
            String containing the FFmpeg filter specification
        """
        pass


class TextEffect(BaseEffect):
    """
    Adds text overlay to video with optional audio reactivity.
    """
    
    def __init__(self, text: str, x: Union[int, str] = 10, y: Union[int, str] = 10, 
                 fontsize: int = 24, fontcolor: str = "white", fontfile: Optional[str] = None,
                 react_to: Optional[str] = None, **kwargs):
        """
        Initialize a text overlay effect.
        
        Args:
            text: The text to display
            x: X position (pixels or position keyword like "center")
            y: Y position (pixels or position keyword like "center")
            fontsize: Font size in pixels
            fontcolor: Font color
            fontfile: Path to a TrueType font file
            react_to: Audio feature to react to ("volume", "bass", etc)
            **kwargs: Additional parameters for text effect
        """
        super().__init__(**kwargs)
        self.text = text
        self.x = x
        self.y = y
        self.fontsize = fontsize
        self.fontcolor = fontcolor
        self.fontfile = fontfile
        self.react_to = react_to
        
        if react_to:
            self.requires_audio_analysis = True
    
    def prepare(self, audio_analyzer) -> None:
        """
        Prepare the text effect, potentially using audio analysis.
        
        Args:
            audio_analyzer: AudioAnalyzer instance with extracted features
        """
        if self.react_to and self.requires_audio_analysis:
            # Verify the requested audio feature exists
            if not audio_analyzer.get_feature(self.react_to):
                logger.warning(f"Audio feature '{self.react_to}' not available for text effect")
    
    def get_filter_string(self) -> str:
        """
        Get the FFmpeg filter string for text overlay.
        
        Returns:
            String containing the FFmpeg drawtext filter
        """
        # Basic drawtext parameters
        params = [f"text='{self.text}'"]
        
        # Handle position parameters
        if isinstance(self.x, str) and self.x == "center":
            params.append("x=(w-text_w)/2")
        else:
            params.append(f"x={self.x}")
            
        if isinstance(self.y, str) and self.y == "center":
            params.append("y=(h-text_h)/2")
        elif isinstance(self.y, str) and self.y == "bottom":
            params.append("y=h-text_h-10")
        else:
            params.append(f"y={self.y}")
        
        # Font parameters
        params.append(f"fontsize={self.fontsize}")
        params.append(f"fontcolor={self.fontcolor}")
        
        if self.fontfile and os.path.exists(self.fontfile):
            params.append(f"fontfile='{self.fontfile}'")
        
        # Additional parameters from kwargs
        for key, value in self.params.items():
            if key not in ['text', 'x', 'y', 'fontsize', 'fontcolor', 'fontfile', 'react_to']:
                params.append(f"{key}={value}")
        
        # If audio reactivity is desired, we'll need to handle it differently
        # Since FFmpeg doesn't directly support dynamic parameters based on audio,
        # we'd need to generate frame-by-frame commands or use expresions with sendcmd
        if self.react_to:
            # This is a simple example that could be expanded for true reactivity
            # For now, just adding an alpha blend effect as a placeholder
            params.append("alpha=0.8")
        
        return f"drawtext={':'.join(params)}"


class LogoEffect(BaseEffect):
    """
    Adds a logo/image overlay to video with optional audio reactivity.
    """
    
    def __init__(self, image_path: str, x: Union[int, str] = 10, y: Union[int, str] = 10,
                 width: Optional[int] = None, height: Optional[int] = None,
                 opacity: float = 1.0, react_to: Optional[str] = None, **kwargs):
        """
        Initialize a logo overlay effect.
        
        Args:
            image_path: Path to the image file
            x: X position (pixels or position keyword like "center")
            y: Y position (pixels or position keyword like "center")
            width: Optional width to resize image to
            height: Optional height to resize image to
            opacity: Opacity of the logo (0.0-1.0)
            react_to: Audio feature to react to ("volume", "bass", etc)
            **kwargs: Additional parameters for logo effect
        """
        super().__init__(**kwargs)
        self.image_path = image_path
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.opacity = opacity
        self.react_to = react_to
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Logo image not found: {image_path}")
            
        if react_to:
            self.requires_audio_analysis = True
    
    def prepare(self, audio_analyzer) -> None:
        """
        Prepare the logo effect, potentially using audio analysis.
        
        Args:
            audio_analyzer: AudioAnalyzer instance with extracted features
        """
        if self.react_to and self.requires_audio_analysis:
            # Verify the requested audio feature exists
            if not audio_analyzer.get_feature(self.react_to):
                logger.warning(f"Audio feature '{self.react_to}' not available for logo effect")
    
    def get_filter_string(self) -> str:
        """
        Get the FFmpeg filter string for logo overlay.
        
        Returns:
            String containing the FFmpeg overlay filter chain
        """
        # Prepare the overlay image
        # First create an input stream for the logo
        overlay_input = "movie='" + self.image_path.replace("'", "'\\'") + "'"
        
        # Apply any scaling if needed
        scale_params = []
        if self.width is not None:
            scale_params.append(f"width={self.width}")
        if self.height is not None:
            scale_params.append(f"height={self.height}")
        
        if scale_params:
            overlay_input += "[logo];[logo]scale=" + ":".

 class="""
            String containing the FFmpeg overlay filter chain
        """
        # Prepare the overlay image
        # First create an input stream for the logo
        overlay_input = "movie='" + self.image_path.replace("'", "'\\'") + "'"
        
        # Apply any scaling if needed
        scale_params = []
        if self.width is not None:
            scale_params.append(f"width={self.width}")
        if self.height is not None:
            scale_params.append(f"height={self.height}")
        
        if scale_params:
            overlay_input += "[logo];[logo]scale=" + ":".join(scale_params)
        
        # Handle opacity if not 1.0
        if self.opacity < 1.0:
            overlay_input += f"[scaled];[scaled]format=rgba,colorchannelmixer=aa={self.opacity}"
        
        # Position parameters for overlay
        position_params = []
        
        # Handle position parameters
        if isinstance(self.x, str) and self.x == "center":
            position_params.append("x=(main_w-overlay_w)/2")
        else:
            position_params.append(f"x={self.x}")
            
        if isinstance(self.y, str) and self.y == "center":
            position_params.append("y=(main_h-overlay_h)/2")
        elif isinstance(self.y, str) and self.y == "bottom":
            position_params.append("y=main_h-overlay_h-10")
        else:
            position_params.append(f"y={self.y}")
        
        # Final overlay filter
        overlay_filter = f"{overlay_input}[watermark];[in][watermark]overlay={':'.join(position_params)}"
        
        return overlay_filter


class WaveformEffect(BaseEffect):
    """
    Adds an audio waveform visualization to the video.
    """
    
    def __init__(self, x: int = 0, y: int = 0, width: int = 640, height: int = 120,
                 color: str = "white", **kwargs):
        """
        Initialize a waveform visualization effect.
        
        Args:
            x: X position of the waveform
            y: Y position of the waveform
            width: Width of the waveform
            height: Height of the waveform
            color: Color of the waveform
            **kwargs: Additional parameters for waveform effect
        """
        super().__init__(**kwargs)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        
        # Waveform effect always requires audio
        self.requires_audio_analysis = True
    
    def prepare(self, audio_analyzer) -> None:
        """
        Prepare the waveform effect.
        
        Args:
            audio_analyzer: AudioAnalyzer instance with extracted features
        """
        # Nothing to prepare specifically
        pass
    
    def get_filter_string(self) -> str:
        """
        Get the FFmpeg filter string for waveform visualization.
        
        Returns:
            String containing the FFmpeg showwaves filter
        """
        # Use FFmpeg's showwaves filter
        waveform_params = [
            f"s={self.width}x{self.height}",
            f"colors={self.color}",
            "mode=line",  # p2p, line, cline
            "draw=full",
            f"x={self.x}",
            f"y={self.y}"
        ]
        
        # Add additional parameters
        for key, value in self.params.items():
            if key not in ['x', 'y', 'width', 'height', 'color']:
                waveform_params.append(f"{key}={value}")
        
        # Create a split of the audio to visualize
        # Since this requires a more complex filter chain, we need to 
        # implement this differently in the main filter complex
        return f"[0:a]showwaves={':\\:'.join(waveform_params)}[waveform];[in][waveform]overlay=0:0:format=auto"


class SpectrumEffect(BaseEffect):
    """
    Adds an audio spectrum visualization to the video.
    """
    
    def __init__(self, x: int = 0, y: int = 0, width: int = 640, height: int = 120,
                 mode: str = "bar", **kwargs):
        """
        Initialize a spectrum visualization effect.
        
        Args:
            x: X position of the spectrum
            y: Y position of the spectrum
            width: Width of the spectrum
            height: Height of the spectrum
            mode: Visualization mode ("bar", "line", etc.)
            **kwargs: Additional parameters for spectrum effect
        """
        super().__init__(**kwargs)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.mode = mode
        
        # Spectrum effect always requires audio
        self.requires_audio_analysis = True
    
    def prepare(self, audio_analyzer) -> None:
        """
        Prepare the spectrum effect.
        
        Args:
            audio_analyzer: AudioAnalyzer instance with extracted features
        """
        # Nothing to prepare specifically
        pass
    
    def get_filter_string(self) -> str:
        """
        Get the FFmpeg filter string for spectrum visualization.
        
        Returns:
            String containing the FFmpeg showspectrum filter
        """
        # Use FFmpeg's showspectrum filter
        spectrum_params = [
            f"s={self.width}x{self.height}",
            f"mode={self.mode}",
            "color=intensity",
            "scale=log",
            f"x={self.x}",
            f"y={self.y}"
        ]
        
        # Add additional parameters
        for key, value in self.params.items():
            if key not in ['x', 'y', 'width', 'height', 'mode']:
                spectrum_params.append(f"{key}={value}")
        
        # Create a split of the audio to visualize
        return f"[0:a]showspectrum={':\\:'.join(spectrum_params)}[spectrum];[in][spectrum]overlay=0:0:format=auto"


class EffectRegistry:
    """
    Registry for all available visual effects.
    """
    
    def __init__(self):
        self.effects = {
            'text': TextEffect,
            'logo': LogoEffect,
            'waveform': WaveformEffect,
            'spectrum': SpectrumEffect
        }
    
    def register_effect(self, name: str, effect_class: type):
        """
        Register a new effect type.
        
        Args:
            name: Name to register the effect under
            effect_class: The effect class to register
        """
        if not issubclass(effect_class, BaseEffect):
            raise TypeError("Effect class must inherit from BaseEffect")
            
        self.effects[name] = effect_class
        logger.debug(f"Registered new effect type: {name}")
    
    def create_effect(self, effect_type: str, **kwargs) -> BaseEffect:
        """
        Create an instance of the specified effect type.
        
        Args:
            effect_type: Type of effect to create
            **kwargs: Parameters for the effect
            
        Returns:
            Instance of the requested effect
            
        Raises:
            ValueError: If the effect type is not registered
        """
        if effect_type not in self.effects:
            raise ValueError(f"Unknown effect type: {effect_type}")
            
        effect_class = self.effects[effect_type]
        return effect_class(**kwargs)
    
    def list_effects(self) -> List[str]:
        """
        List all registered effect types.
        
        Returns:
            List of registered effect type names
        """
        return list(self.effects.keys())