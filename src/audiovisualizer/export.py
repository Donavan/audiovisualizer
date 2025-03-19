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

    def export(self, output_path, quality='balanced', use_gpu=True, fps=None, threads=None):
        """
        Unified export method with optimized GPU acceleration for modern NVIDIA GPUs.

        Parameters:
        - output_path: Path to save the output video
        - quality: 'speed', 'balanced', or 'quality' presets
        - use_gpu: Whether to attempt GPU acceleration (default: True)
        - fps: Frame rate (if None, uses the same as source video)
        - threads: Number of CPU threads to use for processing (default: auto-detect)

        Returns:
        - self for method chaining
        """
        if not self.video:
            logger.error("No video to export")
            return None

        # Configure FPS
        if fps is None:
            fps = self.video.fps

        # Configure thread count
        if threads is None:
            import multiprocessing
            threads = min(16, multiprocessing.cpu_count())

        logger.info(f"Using {threads} threads for export")

        # Check for GPU acceleration if requested
        nvenc_available = False
        if use_gpu:
            try:
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

        # Configure encoding parameters based on quality and available hardware
        if nvenc_available:
            # GPU encoding with NVENC
            codec = "h264_nvenc"

            # Map quality to appropriate settings for NVENC
            if quality == 'speed':
                preset = 'fast'  # Use standard preset names for compatibility
                bitrate = '6000k'
            elif quality == 'quality':
                preset = 'slow'
                bitrate = '15000k'
            else:  # balanced
                preset = 'medium'
                bitrate = '10000k'

            # Optimize for modern NVIDIA GPUs like the 3090
            try:
                # Calculate derived bitrate values
                max_bitrate = f"{int(float(bitrate.rstrip('k')) * 1.5)}k"  # 1.5x target
                buffer_size = f"{int(float(bitrate.rstrip('k')) * 2)}k"  # 2x target

                # Advanced parameters for modern NVIDIA GPUs (3090)
                ffmpeg_params = [
                    "-pix_fmt", "yuv420p",
                    "-b:v", bitrate,  # Target bitrate
                    "-maxrate", max_bitrate,  # Maximum bitrate
                    "-bufsize", buffer_size,  # Buffer size
                    "-profile:v", "high",  # High profile for better quality
                    "-level", "5.1",  # Supports high resolutions and framerates
                    "-tune", "hq",  # High quality tuning
                    "-rc", "vbr",  # Variable bitrate for better quality
                    "-gpu", "0"  # Use primary GPU
                ]

                logger.info(f"Exporting with optimized GPU acceleration...")
                self.video.write_videofile(
                    output_path,
                    codec=codec,
                    preset=preset,
                    bitrate=bitrate,
                    fps=fps,
                    audio_codec="aac",
                    audio_bitrate="192k",
                    threads=threads,
                    ffmpeg_params=ffmpeg_params
                )
                logger.info(f"GPU-accelerated video exported to {output_path}")
                return self
            except Exception as e:
                logger.warning(f"Advanced GPU export failed: {e}")
                logger.info("Trying with simpler GPU parameters...")

                # Fallback to simpler NVENC parameters
                try:
                    # Simple GPU parameters for better compatibility
                    self.video.write_videofile(
                        output_path,
                        codec="h264_nvenc",
                        preset=preset,
                        bitrate=bitrate,
                        fps=fps,
                        audio_codec="aac",
                        audio_bitrate="192k",
                        ffmpeg_params=["-pix_fmt", "yuv420p"],
                        threads=threads,
                        logger=None
                    )
                    logger.info(f"GPU-accelerated video exported to {output_path}")
                    return self
                except Exception as e2:
                    logger.warning(f"Simple GPU export also failed: {e2}")
                    logger.info("Falling back to CPU encoding...")

        # CPU encoding (either as fallback or primary method)
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
                fps=fps,
                audio_codec="aac",
                audio_bitrate="192k",
                ffmpeg_params=["-pix_fmt", "yuv420p"],
                threads=threads,
                logger=None
            )
            logger.info(f"Video exported to {output_path}")
        except Exception as e:
            logger.error(f"Export failed: {e}")
            logger.info("Try adjusting export parameters or checking your video source")

        return self