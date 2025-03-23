# FFmpeg Effect Mapper
# Maps high-level effects to filter graph nodes

from typing import List, Dict, Any, Optional
import logging
from .ffmpeg_filter_graph import FilterGraph, FilterNode

logger = logging.getLogger(__name__)


class EffectFilterMapper:
    """Maps high-level effects to filter graph nodes."""

    def __init__(self, visualizer):
        """Initialize the mapper with a reference to the AudioVisualizer instance.
        
        Args:
            visualizer: The AudioVisualizer instance
        """
        self.visualizer = visualizer
        self.graph = FilterGraph()

        # Create the initial format filter node
        self.format_node = self.graph.create_node('format', 'format', {'pix_fmt': 'yuva420p'})
        self.graph.set_input('0:v', self.format_node, 0)

        # Set the current node to the format node
        self.current_node = self.format_node

    def add_effect(self, effect) -> 'EffectFilterMapper':
        """Add an effect to the filter graph.
        
        Args:
            effect: The effect object to add
            
        Returns:
            Self for method chaining
        """
        effect_type = effect.type if hasattr(effect, 'type') else effect['type']
        
        if effect_type == 'logo':
            self._add_logo_effect(effect)
        elif effect_type == 'text':
            self._add_text_effect(effect)
        elif effect_type == 'spectrum':
            self._add_spectrum_effect(effect)
        else:
            logger.warning(f"Unknown effect type: {effect_type}")

        return self

    def build_filter_chain(self) -> str:
        """Build the complete filter chain string.
        
        Returns:
            FFmpeg filtergraph string
        """
        # Set the final node as the output
        self.graph.set_output('out', self.current_node)

        # Build and return the filter chain
        return self.graph.to_filter_string()

    def _add_logo_effect(self, effect) -> None:
        """Add a logo overlay effect to the graph.
        
        Args:
            effect: The logo effect object
        """
        # Get effect parameters
        if hasattr(effect, 'params'):
            params = effect.params
        else:
            params = effect
            
        effect_id = getattr(effect, 'id', id(effect))

        # Create a movie source node for the logo
        movie_node = self.graph.create_node('movie', f"logo_{effect_id}", {
            'filename': params.get('path'),
        })

        # Apply transformations to the logo
        logo_node = movie_node

        # Scale if needed
        if 'scale' in params:
            width, height = params['scale']
            scale_node = self.graph.create_node('scale', f"scale_{effect_id}", {
                'width': width,
                'height': height,
            })
            self.graph.connect(logo_node, scale_node)
            logo_node = scale_node

        # Set alpha/opacity if needed
        if 'opacity' in params:
            opacity = params['opacity']
            alpha_node = self.graph.create_node('colorchannelmixer', f"alpha_{effect_id}", {
                'aa': opacity,
            })
            self.graph.connect(logo_node, alpha_node)
            logo_node = alpha_node

        # Create the overlay node
        overlay_node = self.graph.create_node('overlay', f"overlay_{effect_id}", {
            'x': params.get('x', 10),
            'y': params.get('y', 10),
            'shortest': 1,
            'format': 'rgb',
        })

        # Connect the current video chain and the logo to the overlay
        self.graph.connect(self.current_node, overlay_node, 0, 0)  # Main video to input 0
        self.graph.connect(logo_node, overlay_node, 0, 1)  # Logo to input 1

        # Update the current node
        self.current_node = overlay_node

    def _add_text_effect(self, effect) -> None:
        """Add a text overlay effect to the graph.
        
        Args:
            effect: The text effect object
        """
        # Get effect parameters
        if hasattr(effect, 'params'):
            params = effect.params
        else:
            params = effect
            
        effect_id = getattr(effect, 'id', id(effect))

        # Create the drawtext node
        drawtext_node = self.graph.create_node('drawtext', f"text_{effect_id}", {
            'text': params.get('text', ''),
            'fontfile': params.get('font', ''),
            'fontsize': params.get('size', 24),
            'fontcolor': params.get('color', 'white'),
            'x': params.get('x', 10),
            'y': params.get('y', 10),
            # Add more parameters for box, shadow, etc.
            'box': 1 if params.get('box', False) else 0,
            'boxcolor': params.get('box_color', 'black@0.5'),
        })

        # Connect to the current video chain
        self.graph.connect(self.current_node, drawtext_node)

        # Update the current node
        self.current_node = drawtext_node

    def _add_spectrum_effect(self, effect) -> None:
        """Add a spectrum visualization effect to the graph.
        
        Args:
            effect: The spectrum effect object
        """
        # Get effect parameters
        if hasattr(effect, 'params'):
            params = effect.params
        else:
            params = effect
            
        effect_id = getattr(effect, 'id', id(effect))

        # Create a showspectrum filter
        # Note: This is just a basic implementation
        # A real implementation would be more complex and depend on the specific parameters
        
        # Extract audio stream
        self.graph.set_input('0:a', self.current_node, 0)
        
        # Create the showspectrum filter
        spectrum_node = self.graph.create_node('showspectrum', f"spectrum_{effect_id}", {
            'size': f"{params.get('width', 640)}x{params.get('height', 120)}",
            'mode': params.get('mode', 'combined'),
            'colors': params.get('colors', 'intensity'),
            'scale': params.get('scale', 'log'),
        })
        
        # Create an overlay filter to combine the spectrum with the video
        overlay_node = self.graph.create_node('overlay', f"spectrum_overlay_{effect_id}", {
            'x': params.get('x', 0),
            'y': params.get('y', 0),
            'shortest': 1,
        })
        
        # Connect the current video to the overlay's first input
        self.graph.connect(self.current_node, overlay_node, 0, 0)
        
        # Connect the spectrum to the overlay's second input
        self.graph.connect(spectrum_node, overlay_node, 0, 1)
        
        # Update the current node
        self.current_node = overlay_node