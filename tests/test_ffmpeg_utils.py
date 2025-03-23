import pytest
from unittest.mock import patch, MagicMock
import json
import os
import tempfile
from pathlib import Path

# Add necessary path to import from src
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from audiovisualizer.ffmpeg_utils import FFmpegProcessor


def test_get_media_info(mock_media_info_json):
    """Test extracting media information from a file."""
    with patch('subprocess.run') as mock_run:
        # Setup the mock to return our sample JSON
        mock_process = MagicMock()
        mock_process.stdout = mock_media_info_json
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Create processor and call the function
        processor = FFmpegProcessor(None)
        result = processor.get_media_info('dummy.mp4')
        
        # Verify the subprocess call
        mock_run.assert_called_once()
        cmd_args = mock_run.call_args[0][0]
        assert cmd_args[0] == 'ffprobe'  # Check command
        assert 'dummy.mp4' in cmd_args   # Check input file
        
        # Verify results
        assert len(result['streams']) == 2
        video_stream = result['streams'][0]
        audio_stream = result['streams'][1]
        
        assert video_stream['codec_type'] == 'video'
        assert video_stream['width'] == 1920
        assert video_stream['height'] == 1080
        assert video_stream['r_frame_rate'] == '30/1'
        
        assert audio_stream['codec_type'] == 'audio'
        assert audio_stream['sample_rate'] == '44100'
        
        assert result['format']['duration'] == '10.5'


def test_extract_audio():
    """Test audio extraction from a video file."""
    with patch('subprocess.run') as mock_run:
        # Configure the mock
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Create processor and call the function
        processor = FFmpegProcessor(None)
        with tempfile.NamedTemporaryFile(suffix='.wav') as temp_file:
            output_path = temp_file.name
            result = processor.extract_audio('input.mp4', output_path)
            
            # Verify the subprocess call
            mock_run.assert_called_once()
            cmd_args = mock_run.call_args[0][0]
            assert cmd_args[0] == 'ffmpeg'  # Check command
            assert cmd_args[2] == 'input.mp4'  # Check input file
            assert cmd_args[-1] == output_path  # Check output file
            assert '-vn' in cmd_args  # Check for no-video option
            
            # Verify result
            assert result == output_path


def test_process_video():
    """Test video processing with a filter chain."""
    with patch('subprocess.run') as mock_run:
        # Configure the mock
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Create processor and call the function
        processor = FFmpegProcessor(None)
        filter_chain = "[0:v]format=yuva420p[formatted]; [formatted]drawtext=text='Test'[out]"
        processor.process_video('input.mp4', 'output.mp4', filter_chain)
        
        # Verify the subprocess call
        mock_run.assert_called_once()
        cmd_args = mock_run.call_args[0][0]
        assert cmd_args[0] == 'ffmpeg'  # Check command
        assert cmd_args[2] == 'input.mp4'  # Check input file
        assert cmd_args[-1] == 'output.mp4'  # Check output file
        assert '-filter_complex' in cmd_args  # Check for filter_complex option
        assert filter_chain in cmd_args  # Check for our filter chain


def test_create_filter_graph():
    """Test creating a filter graph."""
    processor = FFmpegProcessor(None)
    graph = processor.create_filter_graph()
    
    # Ensure we got a filter graph back
    assert graph is not None
    # Verify it's empty by checking the string conversion
    assert graph.to_filter_string() == ""