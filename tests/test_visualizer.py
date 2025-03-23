import pytest
from unittest.mock import patch, MagicMock, call
import tempfile
import os
import json
import sys
from pathlib import Path

# Add necessary path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from audiovisualizer import AudioVisualizer


def test_load_media():
    """Test loading media file."""
    # Test with non-existent file
    visualizer = AudioVisualizer()
    with pytest.raises(ValueError, match="Input file does not exist"):
        visualizer.load_media('nonexistent.mp4')
    
    # Test with a valid file path (mocked)
    with patch('os.path.exists', return_value=True):
        result = visualizer.load_media('test.mp4')
        assert visualizer.input_path == 'test.mp4'
        assert result is visualizer  # Test method chaining


def test_add_effect():
    """Test adding effects to the visualizer."""
    visualizer = AudioVisualizer()
    
    # Add a logo effect
    result = visualizer.add_effect('logo', {
        'path': 'logo.png',
        'x': 20,
        'y': 20,
        'scale': (100, 100)
    })
    
    assert len(visualizer.effects) == 1
    assert visualizer.effects[0]['type'] == 'logo'
    assert visualizer.effects[0]['path'] == 'logo.png'
    assert visualizer.effects[0]['x'] == 20
    assert visualizer.effects[0]['y'] == 20
    assert visualizer.effects[0]['scale'] == (100, 100)
    assert result is visualizer  # Test method chaining
    
    # Add a text effect
    visualizer.add_effect('text', {
        'text': 'Hello World',
        'x': 50,
        'y': 50
    })
    
    assert len(visualizer.effects) == 2
    assert visualizer.effects[1]['type'] == 'text'
    assert visualizer.effects[1]['text'] == 'Hello World'


def test_process():
    """Test processing a video with effects."""
    visualizer = AudioVisualizer()
    
    # Mock os.path.exists to avoid file not found error
    with patch('os.path.exists', return_value=True):
        visualizer.load_media('input.mp4')
    
    # Add some effects
    visualizer.add_effect('logo', {'path': 'logo.png', 'x': 20, 'y': 20})
    
    # Mock the FFmpegProcessor methods
    with patch.object(visualizer.ffmpeg, 'build_complex_filter') as mock_build:
        with patch.object(visualizer.ffmpeg, 'process_video') as mock_process:
            # Configure mocks
            mock_build.return_value = "[0:v]overlay=x=20:y=20[out]"
            
            # Call the process method
            result = visualizer.process('output.mp4')
            
            # Verify method calls
            mock_build.assert_called_once_with(visualizer.effects)
            mock_process.assert_called_once_with(
                'input.mp4', 'output.mp4', "[0:v]overlay=x=20:y=20[out]", None
            )
            
            # Verify result
            assert result == 'output.mp4'


def test_process_with_filter_graph():
    """Test processing a video with a custom filter graph."""
    visualizer = AudioVisualizer()
    
    # Mock os.path.exists to avoid file not found error
    with patch('os.path.exists', return_value=True):
        visualizer.load_media('input.mp4')
    
    # Create a filter graph
    graph = visualizer.create_filter_graph()
    
    # Mock the filter graph and FFmpegProcessor methods
    with patch.object(graph, 'to_filter_string') as mock_to_string:
        with patch.object(visualizer.ffmpeg, 'process_video') as mock_process:
            # Configure mocks
            mock_to_string.return_value = "[0:v]overlay=x=30:y=30[out]"
            
            # Call the process method
            result = visualizer.process_with_filter_graph(graph, 'output.mp4')
            
            # Verify method calls
            mock_to_string.assert_called_once()
            mock_process.assert_called_once_with(
                'input.mp4', 'output.mp4', "[0:v]overlay=x=30:y=30[out]", None
            )
            
            # Verify result
            assert result == 'output.mp4'


def test_save_and_load_config():
    """Test saving and loading configuration."""
    visualizer = AudioVisualizer()
    
    # Mock os.path.exists to avoid file not found error
    with patch('os.path.exists', return_value=True):
        visualizer.load_media('input.mp4')
    
    visualizer.add_effect('logo', {'path': 'logo.png', 'x': 20, 'y': 20})
    
    # Create a temp file for config
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
        config_path = temp_file.name
    
    try:
        # Test saving config
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            visualizer.save_config(config_path)
            
            # Check that json.dump was called with the right data
            call_args = mock_file.write.call_args[0][0] 
            assert '"input_path": "input.mp4"' in call_args or \"'input_path': 'input.mp4'\" in call_args
            assert '"effects"' in call_args or "'effects'" in call_args
        
        # Test loading config
        mock_config = {
            'input_path': 'other_input.mp4',
            'effects': [
                {'type': 'text', 'text': 'Test Text', 'x': 50, 'y': 50}
            ]
        }
        
        with patch('builtins.open', create=True) as mock_open:
            with patch('json.load') as mock_json_load:
                mock_json_load.return_value = mock_config
                mock_open.return_value.__enter__.return_value = MagicMock()
                
                result = visualizer.load_config(config_path)
                
                # Verify the config was loaded
                assert visualizer.input_path == 'other_input.mp4'
                assert len(visualizer.effects) == 1
                assert visualizer.effects[0]['type'] == 'text'
                assert visualizer.effects[0]['text'] == 'Test Text'
                assert result is visualizer  # Test method chaining
    
    finally:
        # Clean up
        if os.path.exists(config_path):
            os.remove(config_path)


def test_cleanup():
    """Test cleanup of temporary files."""
    visualizer = AudioVisualizer()
    
    # Add some fake temp files
    visualizer.temp_files = ['temp1.mp4', 'temp2.wav']
    
    # Mock os.remove
    with patch('os.remove') as mock_remove:
        visualizer.cleanup()
        
        # Check that os.remove was called for each file
        assert mock_remove.call_count == 2
        mock_remove.assert_has_calls([
            call('temp1.mp4'),
            call('temp2.wav')
        ])
        
        # Check that temp_files list is empty
        assert visualizer.temp_files == []


def test_process_video_convenience_function():
    """Test the process_video convenience function."""
    from audiovisualizer import process_video
    
    # Define test parameters
    input_path = 'input.mp4'
    output_path = 'output.mp4'
    effects = [
        {'type': 'logo', 'path': 'logo.png', 'x': 20, 'y': 20},
        {'type': 'text', 'text': 'Hello World', 'x': 50, 'y': 50}
    ]
    
    # Create mocks
    with patch('audiovisualizer.visualizer.AudioVisualizer') as MockVisualizer:
        # Setup the mock instance
        mock_instance = MockVisualizer.return_value
        mock_instance.load_media.return_value = mock_instance
        mock_instance.add_effect.return_value = mock_instance
        mock_instance.process.return_value = output_path
        
        # Call the function
        result = process_video(input_path, output_path, effects)
        
        # Verify the AudioVisualizer was used correctly
        MockVisualizer.assert_called_once_with('ffmpeg', 'ffprobe')
        mock_instance.load_media.assert_called_once_with(input_path)
        
        # Check that add_effect was called for each effect
        assert mock_instance.add_effect.call_count == 2
        mock_instance.add_effect.assert_has_calls([
            call('logo', {'path': 'logo.png', 'x': 20, 'y': 20}),
            call('text', {'text': 'Hello World', 'x': 50, 'y': 50})
        ])
        
        mock_instance.process.assert_called_once_with(output_path)
        assert result == output_path