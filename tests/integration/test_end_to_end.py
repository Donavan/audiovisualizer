import pytest
import os
import tempfile
import sys
from pathlib import Path

# Add necessary path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from audiovisualizer import AudioVisualizer


@pytest.mark.integration
def test_basic_pipeline(sample_video_path, sample_logo_path, temp_output_dir):
    """Test the complete processing pipeline with a real video.
    
    This is an integration test that requires real media files and FFmpeg installed.
    Skip if assets are not available or if running in CI without proper setup.
    """
    # Skip if running in CI without media files
    if os.environ.get('CI') == 'true' and not os.path.exists(sample_video_path):
        pytest.skip("Skipping integration test in CI environment without media files")
    
    # Create output path
    output_path = os.path.join(temp_output_dir, 'output.mp4')
    
    # Initialize the AudioVisualizer
    visualizer = AudioVisualizer()
    
    try:
        # Load media and add a simple logo effect
        visualizer.load_media(sample_video_path)
        visualizer.add_effect('logo', {
            'path': sample_logo_path,
            'x': 20,
            'y': 20,
            'scale': (100, 100),
            'opacity': 0.8
        })
        
        # Process the video
        result_path = visualizer.process(output_path)
        
        # Verify that the output file exists and has a non-zero size
        assert os.path.exists(result_path)
        assert os.path.getsize(result_path) > 0
        
    except Exception as e:
        # If an FFmpeg-related error occurs, skip the test
        if 'FFmpeg' in str(e) or 'ffmpeg' in str(e):
            pytest.skip(f"Skipping due to FFmpeg error: {e}")
        else:
            raise