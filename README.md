# AudioVisualizer

A Python package for creating reactive audio-visual overlays for videos.

## Features

- Add static and reactive logos to videos
- Add static and reactive text overlays
- React to audio features (amplitude, spectral features, etc.)
- GPU-accelerated video export (when available)

## Installation

```bash
pip install audiovisualizer
```

## Quick Start

```python
from audiovisualizer import AudioVisualOverlay

# Create and configure the overlay processor
overlay = AudioVisualOverlay()

# Load video file
overlay.load_files("my_video.mp4")

# Extract audio features for reactive elements
overlay.extract_audio_features()

# Add a static logo
overlay.add_static_logo(
    logo_path="logo.png",
    position=('right', 'top'),
    margin=20,
    size=0.15
)

# Add a reactive logo
overlay.add_reactive_logo(
    logo_path="logo.png",
    position=('left', 'top'),
    margin=20,
    base_size=0.15,
    react_to='rms',
    intensity=0.3
)

# Add static text
overlay.add_text_overlay(
    text="Demo Video",
    position=('center', 'bottom'),
    margin=30,
    fontsize=30,
    color='white',
    font_path="my_font.ttf"  # Optional custom font
)

# Add reactive text
overlay.add_reactive_text(
    text="Powered by Python",
    position=('center', 'top'),
    margin=30,
    base_fontsize=24,
    color='yellow',
    font_path="my_font.ttf",  # Optional custom font
    react_to='spectral_contrast',
    intensity=0.5
)

# Export the result
overlay.export("output_video.mp4")
```

## Audio Features

The following audio features can be used for reactive elements:

- `rms`: Root mean square energy (amplitude/volume)
- `onsets`: Onset strength (beat detection)
- `spectral_centroid`: Brightness of sound
- `mfcc`: Mel-frequency cepstral coefficients (timbre)

## License

MIT License