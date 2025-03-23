# AudioVisualizer Package
# Creates audio-reactive visual effects for videos

from .visualizer import AudioVisualizer, process_video
from .ffmpeg_filter_graph import FilterGraph, FilterNode

__version__ = '0.2.0'

__all__ = [
    'AudioVisualizer',
    'process_video',
    'FilterGraph',
    'FilterNode',
]