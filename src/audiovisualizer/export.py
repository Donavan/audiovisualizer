import os
import logging
import subprocess

logger = logging.getLogger(__name__)

class VideoExporter:
    """Handles video export with various quality settings and hardware acceleration options"""
    
    def __init__(self):
        self.video = None
        
    def set_video(self, video):
        """Set the video to be exported"""
        self.video = video
        
    def export_gpu_optimized(self, output_path, quality='balanced'):
        """
        Try to use GPU acceleration but fall back to CPU if needed.
        Simplified to work with older NVIDIA drivers.

        Parameters:
        - output_path: Path to save the output video
        - quality: 'speed', 'balanced', or 'quality' presets
        """
        if not self.video:
            logger.error("No video to export")
            return None
            
        # First, try to detect if we can use NVIDIA acceleration
        try:
            nvenc_available = False
            # Check if NVENC is available
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True, text=True, check=True
            )
            if "h264_nvenc" in result.stdout:
                nvenc_available = True
                logger.info("NVIDIA GPU encoding available")
            else:
                logger.info("NVIDIA GPU encoding not available, using CPU")
        except Exception as e:
            logger.warning(f"Could not check for NVENC: {e}")
            nvenc_available = False

        # Map quality to preset
        if nvenc_available:
            # NVENC presets
            if quality == 'speed':
                preset = 'fast'  # More compatible than p7
                bitrate = '6000k'
            elif quality == 'quality':
                preset = 'slow'  # More compatible than p1
                bitrate = '15000k'
            else:  # balanced
                preset = 'medium'  # More compatible than p2
                bitrate = '10000k'

            # Try GPU export with simpler parameters
            try:
                logger.info("Exporting with GPU acceleration...")
                self.video.write_videofile(
                    output_path,
                    codec="h264_nvenc",
                    preset=preset,
                    bitrate=bitrate,
                    audio_codec="aac",
                    audio_bitrate="192k",
                    ffmpeg_params=["-pix_fmt", "yuv420p"],
                    threads=4
                )
                logger.info(f"GPU-accelerated video exported to {output_path}")
                return self
            except Exception as e:
                logger.warning(f"GPU export failed: {e}")
                logger.info("Falling back to CPU encoding...")

        # If we get here, either NVENC wasn't available or it failed
        # CPU encoding fallback
        if quality == 'speed':
            preset = 'veryfast'
            bitrate = '6000k'
        elif quality == 'quality':
            preset = 'slow'
            bitrate = '15000k'
        else:  # balanced
            preset = 'medium'
            bitrate = '10000k'

        try:
            logger.info("Exporting with CPU encoding...")
            self.video.write_videofile(
                output_path,
                codec="libx264",
                preset=preset,
                bitrate=bitrate,
                audio_codec="aac",
                audio_bitrate="192k",
                ffmpeg_params=["-pix_fmt", "yuv420p"],
                threads=4
            )
            logger.info(f"Video exported to {output_path}")
        except Exception as e:
            logger.error(f"Export failed: {e}")
            logger.info("Try using the simple export method instead")

        return self
    
    def export(self, output_path, fps=None):
        """
        Simple and reliable export method that works on all systems.

        Parameters:
        - output_path: Path to save the output video
        - fps: Frame rate (if None, uses the same as source video)
        """
        if not self.video:
            logger.error("No video to export")
            return None
            
        if fps is None:
            fps = self.video.fps

        logger.info(f"Exporting video to {output_path}...")

        # Use the simplest possible parameters to ensure compatibility
        try:
            self.video.write_videofile(
                output_path,
                codec="libx264",  # Standard H.264 codec supported everywhere
                fps=fps,
                preset="medium",  # Balanced preset
                bitrate="8000k",
                audio_codec="aac",
                audio_bitrate="192k",
                threads=4,  # Use reasonable thread count
                ffmpeg_params=["-pix_fmt", "yuv420p"],  # Ensure compatibility
                logger=None  # Suppress excessive logging
            )
            logger.info(f"Video successfully exported to {output_path}")
        except Exception as e:
            logger.error(f"Export failed: {e}")
            
        return self