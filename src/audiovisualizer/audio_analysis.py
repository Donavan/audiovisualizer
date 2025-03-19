import os
import numpy as np
import subprocess
import tempfile
import json
import logging
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

class AudioAnalyzer:
    """
    Analyzes audio files to extract features like volume, frequency bands, and beats
    using FFmpeg's audio filters.
    """
    
    def __init__(self):
        self.audio_data = None
        self.sample_rate = None
        self.duration = None
        self.temp_files = []
        self.features = {}
    
    def analyze(self, media_path: str):
        """
        Analyze the audio from the provided media file.
        
        Args:
            media_path: Path to audio or video file
        """
        logger.info(f"Analyzing audio from {media_path}")
        
        # Extract audio data using FFmpeg
        self._extract_audio(media_path)
        
        # Calculate audio features
        self._analyze_volume()
        self._analyze_frequency_bands()
        self._detect_beats()
        
        # Clean up temporary files
        self._cleanup()
        
        logger.info("Audio analysis complete")
    
    def _extract_audio(self, media_path: str):
        """
        Extract audio data from the media file using FFmpeg.
        
        Args:
            media_path: Path to audio or video file
        """
        # Create temporary file for the extracted audio
        fd, audio_file = tempfile.mkstemp(suffix='.wav')
        os.close(fd)
        self.temp_files.append(audio_file)
        
        # Extract audio at 44.1kHz, mono
        cmd = [
            "ffmpeg", "-y",
            "-i", media_path,
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "44100", "-ac", "1",
            audio_file
        ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.debug(f"Audio extracted to {audio_file}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to extract audio: {e.stderr}")
            raise RuntimeError(f"Failed to extract audio: {e.stderr}") from e
            
        # Get audio duration and sample rate
        self._get_audio_info(audio_file)
        
        # Extract the actual audio data as numpy array for further processing
        self._load_audio_data(audio_file)
    
    def _get_audio_info(self, audio_file: str):
        """
        Get audio duration and sample rate using FFprobe.
        
        Args:
            audio_file: Path to the extracted audio file
        """
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            audio_file
        ]
        
        try:
            result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            info = json.loads(result.stdout)
            
            # Extract sample rate and duration
            for stream in info.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    self.sample_rate = int(stream.get('sample_rate', 44100))
                    break
            
            self.duration = float(info.get('format', {}).get('duration', 0))
            logger.debug(f"Audio info: {self.duration}s at {self.sample_rate}Hz")
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"Failed to get audio info: {e}")
            raise RuntimeError(f"Failed to get audio info: {e}") from e
    
    def _load_audio_data(self, audio_file: str):
        """
        Load audio data into a numpy array for analysis.
        
        Args:
            audio_file: Path to the extracted audio file
        """
        # Create a temporary file for the raw audio data
        fd, raw_file = tempfile.mkstemp(suffix='.raw')
        os.close(fd)
        self.temp_files.append(raw_file)
        
        # Extract raw PCM data
        cmd = [
            "ffmpeg", "-y",
            "-i", audio_file,
            "-f", "s16le",
            "-acodec", "pcm_s16le",
            raw_file
        ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # Load the raw audio data
            self.audio_data = np.fromfile(raw_file, dtype=np.int16)
            logger.debug(f"Loaded {len(self.audio_data)} audio samples")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to extract raw audio: {e.stderr}")
            raise RuntimeError(f"Failed to extract raw audio: {e.stderr}") from e
    
    def _analyze_volume(self):
        """
        Calculate volume/amplitude envelope over time.
        """
        if self.audio_data is None:
            logger.warning("No audio data available for volume analysis")
            return
        
        # Calculate number of samples per frame (assuming 30fps)
        fps = 30
        samples_per_frame = int(self.sample_rate / fps)
        
        # Calculate RMS volume for each frame
        num_frames = int(len(self.audio_data) / samples_per_frame)
        volume = np.zeros(num_frames)
        
        for i in range(num_frames):
            start = i * samples_per_frame
            end = min(start + samples_per_frame, len(self.audio_data))
            frame_data = self.audio_data[start:end].astype(np.float32)
            
            # Calculate RMS (root mean square)
            if len(frame_data) > 0:
                volume[i] = np.sqrt(np.mean(frame_data**2)) / 32768.0  # Normalize by max int16 value
        
        # Store the volume data
        self.features['volume'] = volume
        logger.debug(f"Volume analysis complete: {len(volume)} frames")
    
    def _analyze_frequency_bands(self, num_bands: int = 4):
        """
        Analyze frequency content over time and split into bands.
        
        Args:
            num_bands: Number of frequency bands to extract
        """
        if self.audio_data is None:
            logger.warning("No audio data available for frequency analysis")
            return
        
        # Define FFmpeg command for using the showcqt filter to analyze frequency content
        fd, spectrum_file = tempfile.mkstemp(suffix='.txt')
        os.close(fd)
        self.temp_files.append(spectrum_file)
        
        # Create temporary audio file from our numpy array
        fd, temp_audio = tempfile.mkstemp(suffix='.wav')
        os.close(fd)
        self.temp_files.append(temp_audio)
        
        # Write audio data to temp file
        with open(temp_audio, 'wb') as f:
            self.audio_data.tofile(f)
        
        # Use FFmpeg's ebur128 filter to get loudness information at different frequency bands
        bands = []
        band_names = ['bass', 'lowmid', 'highmid', 'highs']
        
        # Simplified frequency band analysis - for a more accurate version, we'd use FFT
        # This is a simplified version that uses simple filtering
        for i, band_name in enumerate(band_names[:num_bands]):
            # Different frequency range for each band
            if i == 0:  # Bass: 20-250 Hz
                cutoff_low, cutoff_high = 20, 250
            elif i == 1:  # Low mids: 250-2000 Hz
                cutoff_low, cutoff_high = 250, 2000
            elif i == 2:  # High mids: 2000-4000 Hz
                cutoff_low, cutoff_high = 2000, 4000
            else:  # Highs: 4000-20000 Hz
                cutoff_low, cutoff_high = 4000, 20000
            
            # Create bandpass filtered version
            fd, filtered_file = tempfile.mkstemp(suffix='.wav')
            os.close(fd)
            self.temp_files.append(filtered_file)
            
            bandpass_cmd = [
                "ffmpeg", "-y", 
                "-f", "s16le", "-ar", str(self.sample_rate), "-ac", "1",
                "-i", temp_audio,
                "-af", f"bandpass=f={cutoff_low + (cutoff_high-cutoff_low)/2}:width_type=h:width={cutoff_high-cutoff_low}",
                filtered_file
            ]
            
            subprocess.run(bandpass_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Load the filtered audio and calculate volume envelope
            filtered_data = np.fromfile(filtered_file, dtype=np.int16)
            
            # Calculate volume per frame
            fps = 30
            samples_per_frame = int(self.sample_rate / fps)
            num_frames = int(len(filtered_data) / samples_per_frame)
            band_volume = np.zeros(num_frames)
            
            for j in range(num_frames):
                start = j * samples_per_frame
                end = min(start + samples_per_frame, len(filtered_data))
                frame_data = filtered_data[start:end].astype(np.float32)
                
                if len(frame_data) > 0:
                    band_volume[j] = np.sqrt(np.mean(frame_data**2)) / 32768.0
            
            bands.append(band_volume)
            self.features[band_name] = band_volume
        
        logger.debug(f"Frequency band analysis complete: {num_bands} bands")
    
    def _detect_beats(self, threshold: float = 0.15, min_interval: float = 0.1):
        """
        Detect beats in the audio based on sudden increases in volume.
        
        Args:
            threshold: Threshold for beat detection
            min_interval: Minimum interval between beats in seconds
        """
        if 'volume' not in self.features:
            logger.warning("Volume data not available for beat detection")
            return
        
        volume = self.features['volume']
        fps = 30  # Assuming 30fps for frame conversion
        
        # First pass: find all potential beats (sudden increases in volume)
        beats = []
        min_frames = int(min_interval * fps)
        
        # Moving average for smoothing
        window_size = 5
        smoothed = np.convolve(volume, np.ones(window_size)/window_size, mode='same')
        
        # Beat detection using dynamic threshold
        for i in range(1, len(smoothed)):
            if i > window_size:
                local_avg = np.mean(smoothed[i-window_size:i])
                if smoothed[i] > local_avg + threshold and smoothed[i] > smoothed[i-1] * 1.1:
                    # Found potential beat
                    if not beats or i - beats[-1] >= min_frames:
                        beats.append(i)
        
        # Convert to seconds
        beat_times = [b / fps for b in beats]
        self.features['beats'] = beat_times
        logger.debug(f"Beat detection complete: {len(beat_times)} beats detected")
    
    def get_feature(self, feature_name: str) -> Optional[np.ndarray]:
        """
        Get a specific audio feature.
        
        Args:
            feature_name: Name of the feature to retrieve
            
        Returns:
            Numpy array containing the feature data, or None if not available
        """
        return self.features.get(feature_name)
    
    def _cleanup(self):
        """
        Clean up temporary files created during analysis.
        """
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {temp_file}: {e}")
                
        self.temp_files = []