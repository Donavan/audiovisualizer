# AudioVisualizer Testing Strategy

## Overview

This document outlines the testing approach for the AudioVisualizer package, detailing the structure, types of tests, and tools used to ensure code quality and reliability.

## Test Structure

The tests are organized to mirror the package structure, making it easy to locate tests for specific components:

```
tests/
├── __init__.py
├── conftest.py                      # Shared fixtures
├── test_ffmpeg_utils.py             # Tests for ffmpeg_utils.py
├── test_visualizer.py               # Tests for visualizer.py
├── test_ffmpeg_effect_mapper.py     # Tests for ffmpeg_effect_mapper.py
├── ffmpeg_filter_graph/             # Tests for the filter graph module
│   ├── __init__.py
│   ├── test_builders.py
│   ├── test_converters.py
│   ├── test_core.py
│   ├── test_registry.py
│   ├── test_validators.py
│   └── test_visualizers.py
└── integration/                     # Integration tests
    ├── __init__.py
    └── test_end_to_end.py
```

## Test Categories

### Unit Tests

Unit tests focus on testing individual components in isolation, with dependencies mocked as needed. The key unit tests include:

1. **FFmpeg Utils Tests** - Test the FFmpeg command execution and media info extraction, with subprocess calls mocked.

2. **Filter Graph Core Tests** - Test the core filter graph functionality, including node creation, connections, and filter string generation.

3. **Visualizer Tests** - Test the main AudioVisualizer class, verifying that it correctly orchestrates the processing pipeline.

### Integration Tests

Integration tests verify that components work together correctly. These tests require real media files and a working FFmpeg installation.

1. **End-to-End Tests** - Process an actual video with effects and verify the output is created correctly.

## Test Fixtures

Common test fixtures are defined in `conftest.py`:

1. **sample_audio_data** - Generates synthetic audio data for testing.

2. **temp_output_dir** - Creates a temporary directory for test outputs.

3. **test_assets_dir** - Provides access to test media files.

4. **sample_video_path**, **sample_logo_path**, **sample_font_path** - Paths to specific test assets.

5. **mock_media_info_json** - Sample FFprobe media info output for testing.

## Test Markers

Test markers are defined in `pyproject.toml` to categorize tests:

- **unit** - Mark unit tests that can run without external dependencies.

- **integration** - Mark integration tests that require FFmpeg and real media files.

## Mocking Strategy

The tests use strategic mocking to isolate components and avoid external dependencies:

1. **Subprocess Calls** - FFmpeg/FFprobe calls are mocked to avoid actual command execution.

2. **File Operations** - File existence checks and I/O operations are mocked when appropriate.

3. **Filter Graph Components** - Some filter graph dependencies are mocked to focus on the component being tested.

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run tests with coverage report
pytest --cov=src/audiovisualizer --cov-report=term-missing
```

### Test Environment

The test environment should include:

1. All development dependencies installed: `pip install -e ".[dev]"`

2. Test media files in the `examples/test_assets/` directory.

3. FFmpeg and FFprobe installed for integration tests.

## Future Improvements

1. **CI Integration** - Set up GitHub Actions or similar CI to run tests on commits and PRs.

2. **Code Coverage Targets** - Establish a coverage target (aim for 80%+ over time).

3. **Property-Based Testing** - Add property-based tests for complex data transformations.

4. **Visual Regression Tests** - Add tests that compare generated video frames to expected output.

5. **Performance Tests** - Add tests to monitor the performance of key processing functions.

## Conclusion

This testing strategy provides a comprehensive approach to ensuring the quality and reliability of the AudioVisualizer package. By combining unit tests, integration tests, and strategic mocking, we can verify that the code works as expected without making tests slow or brittle.