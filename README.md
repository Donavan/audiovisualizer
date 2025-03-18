# AudioVisualizer

A Python package for creating reactive audio-visual overlays for videos.

## Features

- Add logos and text overlays to videos
- Flexible audio-reactive effects system
- Multiple reaction types: scale, opacity, color, position
- Independent control of each reaction aspect
- React to audio features (amplitude, spectral features, etc.)
- GPU-accelerated video export (when available)

## Installation

```bash
pip install audiovisualizer
```

## Quick Start

```python
from audiovisualizer import AudioVisualOverlay

# Create the overlay processor with input video
overlay = AudioVisualOverlay("my_video.mp4")

# Extract audio features for reactive elements
overlay.extract_audio_features()

# Add a logo and make it react to the beat
logo = overlay.add_logo(
    logo_path="examples/test_assets/logo.png",
    position="top-right",
    size=0.15
)

# Add scale reaction - logo pulses with the beat
logo.add_reaction(
    reaction_type="scale",
    feature="rms",  # reacts to overall volume
    params={
        "intensity": 0.3,
        "min_scale": 1.0,
        "max_scale": 1.3,
        "smoothing": 0.2
    }
)

# Add a text element with different reactions
text = overlay.add_text(
    text="AUDIO REACTIVE",
    position="bottom-center",
    fontsize=40,
    color="white"
)

# Text opacity reaction - fades with audio
text.add_reaction(
    reaction_type="opacity",
    feature="onsets",  # reacts to note onsets/beats
    params={
        "min_opacity": 0.3,
        "max_opacity": 1.0
    }
)

# Text color reaction - changes color with frequency content
text.add_reaction(
    reaction_type="color",
    feature="spectral_centroid",
    params={
        "color_map": [
            (0.0, "#3366CC"),  # blue for low values
            (0.5, "#FFFFFF"),  # white for mid values
            (1.0, "#CC3366")  # pink for high values
        ]
    }
)

# Process the video with all elements and reactions
overlay.process()

# Export the final video
overlay.export("output_video.mp4")
```

## Reaction Types

The new flexible reactivity system allows you to add multiple reactions to each element:

### Scale Reaction
Makes elements grow/shrink based on audio features:
```python
element.add_reaction(
    reaction_type="scale",
    feature="rms",
    params={
        "min_scale": 1.0,
        "max_scale": 1.5,
        "smoothing": 0.3
    }
)
```

### Opacity Reaction
Changes element transparency based on audio features:
```python
element.add_reaction(
    reaction_type="opacity",
    feature="onsets",
    params={
        "min_opacity": 0.3,
        "max_opacity": 1.0,
        "smoothing": 0.4
    }
)
```

### Color Reaction
Changes element color/saturation based on audio features:
```python
element.add_reaction(
    reaction_type="color",
    feature="spectral_centroid",
    params={
        "type": "saturation",  # or "contrast" for logos
        "min_value": 0.8,
        "max_value": 1.5
    }
)

# For text, you can use color mapping:
text.add_reaction(
    reaction_type="color",
    feature="spectral_centroid",
    params={
        "color_map": [
            (0.0, "blue"),
            (0.5, "white"),
            (1.0, "red")
        ]
    }
)
```

### Position Reaction
Makes elements move based on audio features:
```python
element.add_reaction(
    reaction_type="position",
    feature="rms",
    params={
        "type": "bounce",  # or "shake" 
        "intensity": 15  # pixels
    }
)
```

## Audio Features

The following audio features can be used for reactive elements:

- `rms`: Root mean square energy (amplitude/volume)
- `onsets`: Onset strength (beat detection)
- `spectral_centroid`: Brightness of sound (frequency content)
- `mfcc`: Mel-frequency cepstral coefficients (timbre)

## License

MIT License