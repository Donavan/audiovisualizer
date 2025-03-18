from audiovisualizer import AudioVisualOverlay
import os

# Example usage
def main():
    # Path to your video and logo files
    video_path = "path/to/your/video.mp4"
    logo_path = "path/to/your/logo.png"
    font_path = "path/to/your/font.ttf"  # Path to font file
    
    # Create and configure the overlay processor
    overlay = AudioVisualOverlay()
    
    # Load video file
    overlay.load_files(video_path)
    
    # Extract audio features for reactive elements
    overlay.extract_audio_features()
    
    # Add a static logo
    overlay.add_static_logo(
        logo_path=logo_path,
        position=('right', 'top'),
        margin=20,
        size=0.15
    )
    
    # Add a reactive logo
    overlay.add_reactive_logo(
        logo_path=logo_path,
        position=('left', 'top'),
        margin=20,
        base_size=0.15,
        react_to='rms',
        intensity=0.3
    )
    
    # Add static text with font path
    overlay.add_text_overlay(
        text="Demo Video",
        position=('center', 'bottom'),
        margin=30,
        fontsize=30,
        color='white',
        font_path=font_path
    )
    
    # Add reactive text with font path
    overlay.add_reactive_text(
        text="Powered by Python",
        position=('center', 'top'),
        margin=30,
        base_fontsize=24,
        color='yellow',
        font_path=font_path,
        react_to='spectral_centroid',
        intensity=0.5
    )
    
    # Export the result
    output_path = "output_video.mp4"
    overlay.export(output_path)
    print(f"Video exported to {output_path}")

if __name__ == "__main__":
    main()