# FFmpeg Filter Graph Builders

from typing import Dict, Any, Optional, Tuple, List, Union
import logging

logger = logging.getLogger(__name__)


class FilterGraphBuilder:
    """Helper class for building common filter graph patterns."""
    
    @staticmethod
    def create_logo_overlay(graph, 
                           logo_path: str, 
                           position: Tuple[Union[int, str], Union[int, str]] = (10, 10), 
                           scale: Optional[Union[float, Tuple[Union[int, str], Union[int, str]]]] = None, 
                           opacity: float = 1.0,
                           rotation: Optional[float] = None):
        """Create a logo overlay filter chain.
        
        Args:
            graph: The FilterGraph to add nodes to
            logo_path: Path to the logo image file
            position: (x, y) position for the logo
            scale: Scale factor or (width, height) for the logo
            opacity: Opacity factor (0.0 to 1.0)
            rotation: Optional rotation angle in degrees
            
        Returns:
            Tuple of (input_node, output_node) representing the start and end of the chain
        """
        # Create a movie source node for the logo
        movie_node = graph.create_node('movie', 'logo_source', {
            'filename': logo_path,
        })
        
        current_node = movie_node
        
        # Scale if needed
        if scale is not None:
            scale_params = {}
            if isinstance(scale, (int, float)):
                scale_params['width'] = f"iw*{scale}"
                scale_params['height'] = f"ih*{scale}"
            else:  # assuming tuple of width, height
                scale_params['width'] = scale[0]
                scale_params['height'] = scale[1]
                
            scale_node = graph.create_node('scale', 'logo_scale', scale_params)
            graph.connect(current_node, scale_node)
            current_node = scale_node
        
        # Rotate if needed
        if rotation is not None:
            rotate_node = graph.create_node('rotate', 'logo_rotate', {
                'angle': rotation * 3.14159 / 180  # Convert to radians
            })
            graph.connect(current_node, rotate_node)
            current_node = rotate_node
        
        # Set opacity if needed
        if opacity < 1.0:
            alpha_node = graph.create_node('colorchannelmixer', 'logo_opacity', {
                'aa': opacity
            })
            graph.connect(current_node, alpha_node)
            current_node = alpha_node
        
        # Create the format filter for the main video
        format_node = graph.create_node('format', 'main_format', {
            'pix_fmt': 'yuva420p'
        })
        
        # Create the overlay node
        overlay_node = graph.create_node('overlay', 'logo_overlay', {
            'x': position[0],
            'y': position[1],
            'format': 'rgb',
            'shortest': 1,
        })
        
        # Connect nodes
        graph.connect(format_node, overlay_node, 0, 0)  # Main video to first input
        graph.connect(current_node, overlay_node, 0, 1)  # Logo to second input
        
        return format_node, overlay_node
    
    @staticmethod
    def create_text_overlay(graph, 
                           text: str,
                           font_path: Optional[str] = None,
                           position: Tuple[Union[int, str], Union[int, str]] = (10, 10),
                           size: int = 24,
                           color: str = 'white',
                           box: bool = False,
                           box_color: str = 'black',
                           shadow: Optional[Tuple[int, int]] = None,
                           shadow_color: str = 'black'):
        """Create a text overlay filter chain.
        
        Args:
            graph: The FilterGraph to add nodes to
            text: The text to display
            font_path: Path to the font file (optional)
            position: (x, y) position for the text
            size: Font size
            color: Font color
            box: Whether to draw a box behind the text
            box_color: Box color if box is enabled
            shadow: (x, y) shadow offset or None for no shadow
            shadow_color: Shadow color
            
        Returns:
            Tuple of (input_node, output_node) representing the start and end of the chain
        """
        # Create the format filter for the main video
        format_node = graph.create_node('format', 'text_format', {
            'pix_fmt': 'yuva420p'
        })
        
        # Create the drawtext filter
        params = {
            'text': text,
            'fontsize': size,
            'fontcolor': color,
            'x': position[0],
            'y': position[1],
        }
        
        if font_path:
            params['fontfile'] = font_path
            
        if box:
            params['box'] = 1
            params['boxcolor'] = box_color
            
        if shadow:
            params['shadowx'] = shadow[0]
            params['shadowy'] = shadow[1]
            params['shadowcolor'] = shadow_color
            
        drawtext_node = graph.create_node('drawtext', 'text_overlay', params)
        
        # Connect nodes
        graph.connect(format_node, drawtext_node)
        
        return format_node, drawtext_node
    
    @staticmethod
    def create_spectrum_visualization(graph, 
                                     width: int = 640, 
                                     height: int = 480,
                                     mode: str = 'bar',  # 'bar', 'line', 'dot'
                                     colors: str = 'intensity'):
        """Create a spectrum visualization filter chain.
        
        Args:
            graph: The FilterGraph to add nodes to
            width: Width of the visualization
            height: Height of the visualization
            mode: Visualization mode ('bar', 'line', 'dot')
            colors: Color scheme
            
        Returns:
            Tuple of (input_node, output_node) representing the start and end of the chain
        """
        # This is a placeholder implementation
        # In a real implementation, this would create a showspectrum filter chain
        
        # Create the audio split filter to extract audio for analysis
        split_node = graph.create_node('asplit', 'audio_split', {})
        
        # Create the showspectrum filter
        spectrum_params = {
            'size': f"{width}x{height}",
            'mode': mode,
            'colors': colors,
        }
        spectrum_node = graph.create_node('showspectrum', 'spectrum', spectrum_params)
        
        # Connect audio to the spectrum filter
        graph.connect(split_node, spectrum_node)
        
        # Create a format filter
        format_node = graph.create_node('format', 'spectrum_format', {
            'pix_fmt': 'yuva420p'
        })
        graph.connect(spectrum_node, format_node)
        
        return split_node, format_node