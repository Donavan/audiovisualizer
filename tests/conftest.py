import pytest
import os
import tempfile
import numpy as np
import json
from pathlib import Path

@pytest.fixture
def sample_audio_data():
    """Generate a synthetic audio signal for testing."""
    sr = 22050
    duration = 3  # seconds
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # Generate a sine wave at 440 Hz
    audio = 0.5 * np.sin(2 * np.pi * 440 * t)
    return audio, sr

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def test_assets_dir():
    """Return the path to the test assets directory."""
    # This assumes tests are being run from the package root
    base_dir = Path(__file__).parent.parent
    assets_dir = base_dir / 'examples' / 'test_assets'
    
    if not assets_dir.exists():
        pytest.skip(f"Test assets directory not found at {assets_dir}")
        
    return assets_dir

@pytest.fixture
def sample_video_path(test_assets_dir):
    """Return the path to a sample video file."""
    video_path = test_assets_dir / 'input_video.mp4'
    
    if not video_path.exists():
        pytest.skip(f"Sample video not found at {video_path}")
        
    return str(video_path)

@pytest.fixture
def sample_logo_path(test_assets_dir):
    """Return the path to a sample logo file."""
    logo_path = test_assets_dir / 'logo.png'
    
    if not logo_path.exists():
        pytest.skip(f"Sample logo not found at {logo_path}")
        
    return str(logo_path)

@pytest.fixture
def sample_font_path(test_assets_dir):
    """Return the path to a sample font file."""
    font_path = test_assets_dir / 'Federation.ttf'
    
    if not font_path.exists():
        pytest.skip(f"Sample font not found at {font_path}")
        
    return str(font_path)

@pytest.fixture
def mock_media_info_json():
    """Return a sample JSON response for media info."""
    return json.dumps({
        "streams": [
            {
                "codec_type": "video",
                "width": 1920,
                "height": 1080,
                "r_frame_rate": "30/1"
            },
            {
                "codec_type": "audio",
                "sample_rate": "44100"
            }
        ],
        "format": {
            "duration": "10.5"
        }
    })