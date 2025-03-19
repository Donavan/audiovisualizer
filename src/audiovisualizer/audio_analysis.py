"""Audio analysis module for extracting and processing audio features.

This module provides utilities for analyzing audio data, including extracting
frequency bands, detecting beats, and calculating overall amplitude.
"""

import os
import numpy as np
import librosa
import logging
from typing import Dict, List, Optional, Tuple, Union, Any

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('audio_analysis')

class AudioAnalysisError(Exception):
    """Exception raised for errors in audio analysis operations."""
    pass

class AudioAnalyzer:
    """Analyzes audio data and extracts features for visualization.
    
    This class handles loading audio files, processing them with librosa,
    and extracting various features like frequency bands, beats, and amplitude.
    
    Attributes:
        hop_length (int): Number of samples between frames.
        n_fft (int): FFT window size.
        sr (int): Sample rate for analysis.
        features (dict): Dictionary to store computed features.
    """
    
    # Default frequency bands in Hz
    DEFAULT_FREQ_BANDS = {
        'sub_bass': (20, 60),
        'bass': (60, 250), 
        'low_mid': (250, 500),
        'mid': (500, 2000),
        'high_mid': (2000, 4000),
        'presence': (4000, 6000),
        'brilliance': (6000, 20000)
    }
    
    def __init__(self, 
                 hop_length: int = 512, 
                 n_fft: int = 2048,
                 sr: int = 44100):
        """Initialize AudioAnalyzer.
        
        Args:
            hop_length: Number of samples between frames. Defaults to 512.
            n_fft: FFT window size. Defaults to 2048.
            sr: Sample rate for analysis. Defaults to 44100.
        """
        self.hop_length = hop_length
        self.n_fft = n_fft
        self.sr = sr
        self.features = {}
    
    async def load_audio(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """Load audio file using librosa.
        
        Args:
            audio_path: Path to the audio file.
            
        Returns:
            Tuple of (audio_data, sample_rate).
            
        Raises:
            AudioAnalysisError: If audio file cannot be loaded.
        """
        if not os.path.exists(audio_path):
            raise AudioAnalysisError(f"Audio file not found: {audio_path}")
        
        try:
            audio_data, sr = librosa.load(audio_path, sr=self.sr)
            return audio_data, sr
        except Exception as e:
            raise AudioAnalysisError(f"Failed to load audio file: {str(e)}")
    
    async def analyze(self, 
                 audio_path: str, 
                 freq_bands: Optional[Dict[str, Tuple[int, int]]] = None,
                 beat_detection: bool = True,
                 onset_detection: bool = False) -> Dict[str, Any]:
        """Perform full analysis on audio file.
        
        Args:
            audio_path: Path to the audio file.
            freq_bands: Dictionary mapping band names to (min_freq, max_freq) tuples.
                       If None, default bands are used.
            beat_detection: Whether to perform beat detection.
            onset_detection: Whether to perform onset detection.
            
        Returns:
            Dictionary containing all extracted features.
            
        Raises:
            AudioAnalysisError: If analysis fails.
        """
        try:
            # Load audio data
            audio_data, sr = await self.load_audio(audio_path)
            
            # Calculate duration
            duration = librosa.get_duration(y=audio_data, sr=sr)
            
            # Extract features
            self.features = {
                'duration': duration,
                'sample_rate': sr,
                'n_samples': len(audio_data),
                'n_frames': 1 + int(len(audio_data) // self.hop_length),
                'times': librosa.times_like(audio_data, sr=sr, hop_length=self.hop_length)
            }
            
            # Calculate amplitude/volume over time
            self.features['amplitude'] = self._get_amplitude(audio_data)
            
            # Compute spectrogram
            stft = librosa.stft(audio_data, n_fft=self.n_fft, hop_length=self.hop_length)
            self.features['spectrogram'] = np.abs(stft)
            
            # Frequency bands
            bands_to_use = freq_bands or self.DEFAULT_FREQ_BANDS
            self.features['freq_bands'] = self._get_frequency_bands(stft, bands_to_use)
            
            # Beat detection
            if beat_detection:
                self.features['beats'] = self._detect_beats(audio_data)
            
            # Onset detection
            if onset_detection:
                self.features['onsets'] = self._detect_onsets(audio_data)
            
            return self.features
        
        except Exception as e:
            raise AudioAnalysisError(f"Audio analysis failed: {str(e)}")
    
    def _get_amplitude(self, audio_data: np.ndarray) -> np.ndarray:
        """Calculate amplitude/volume over time.
        
        Args:
            audio_data: Numpy array of audio samples.
            
        Returns:
            Numpy array of amplitude values over time.
        """
        # Calculate RMS energy in frames
        rms = librosa.feature.rms(y=audio_data, frame_length=self.n_fft, hop_length=self.hop_length)[0]
        
        # Normalize to 0-1 range
        rms_norm = rms / np.max(rms) if np.max(rms) > 0 else rms
        
        return rms_norm
    
    def _get_frequency_bands(self, 
                             stft: np.ndarray, 
                             freq_bands: Dict[str, Tuple[int, int]]) -> Dict[str, np.ndarray]:
        """Extract energy in specified frequency bands over time.
        
        Args:
            stft: Short-time Fourier transform data.
            freq_bands: Dictionary mapping band names to (min_freq, max_freq) tuples.
            
        Returns:
            Dictionary mapping band names to normalized energy arrays.
        """
        # Get frequency bins
        freqs = librosa.fft_frequencies(sr=self.sr, n_fft=self.n_fft)
        
        # Calculate energy in each band
        band_energies = {}
        
        for band_name, (min_freq, max_freq) in freq_bands.items():
            # Find indices for the frequency range
            idx_min = np.argmax(freqs >= min_freq) if np.any(freqs >= min_freq) else 0
            idx_max = np.argmax(freqs >= max_freq) if np.any(freqs >= max_freq) else len(freqs)
            
            # Sum energy in the band
            band_energy = np.sum(np.abs(stft[idx_min:idx_max, :]), axis=0)
            
            # Normalize to 0-1 range
            band_energy_norm = band_energy / np.max(band_energy) if np.max(band_energy) > 0 else band_energy
            
            band_energies[band_name] = band_energy_norm
        
        return band_energies
    
    def _detect_beats(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """Detect beats in audio.
        
        Args:
            audio_data: Numpy array of audio samples.
            
        Returns:
            Dictionary with beat information including timestamps and a beat envelope.
        """
        # Compute onset envelope
        onset_env = librosa.onset.onset_strength(y=audio_data, sr=self.sr, hop_length=self.hop_length)
        
        # Get beat frames
        tempo, beat_frames = librosa.beat.beat_track(onset_envelope=onset_env, sr=self.sr, hop_length=self.hop_length)
        
        # Convert to time
        beat_times = librosa.frames_to_time(beat_frames, sr=self.sr, hop_length=self.hop_length)
        
        # Create a beat envelope (a time series that peaks at beat locations)
        beat_envelope = np.zeros_like(onset_env)
        beat_envelope[beat_frames] = 1.0
        
        # Smooth the beat envelope slightly
        win_size = 3
        beat_envelope = np.convolve(beat_envelope, np.ones(win_size)/win_size, mode='same')
        
        return {
            'tempo': tempo,
            'beat_frames': beat_frames,
            'beat_times': beat_times,
            'beat_envelope': beat_envelope
        }
    
    def _detect_onsets(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """Detect note onsets in audio.
        
        Args:
            audio_data: Numpy array of audio samples.
            
        Returns:
            Dictionary with onset information including timestamps and an onset envelope.
        """
        # Compute onset envelope
        onset_env = librosa.onset.onset_strength(y=audio_data, sr=self.sr, hop_length=self.hop_length)
        
        # Get onset frames
        onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=self.sr, hop_length=self.hop_length)
        
        # Convert to time
        onset_times = librosa.frames_to_time(onset_frames, sr=self.sr, hop_length=self.hop_length)
        
        # Normalize onset envelope
        onset_env_norm = onset_env / np.max(onset_env) if np.max(onset_env) > 0 else onset_env
        
        return {
            'onset_frames': onset_frames,
            'onset_times': onset_times,
            'onset_envelope': onset_env_norm
        }
    
    def get_time_aligned_features(self, fps: float = 30.0) -> Dict[str, np.ndarray]:
        """Convert all time-based features to frame-based for video alignment.
        
        Args:
            fps: Frames per second of the target video.
            
        Returns:
            Dictionary of features aligned to video frames.
            
        Raises:
            AudioAnalysisError: If features haven't been extracted yet.
        """
        if not self.features:
            raise AudioAnalysisError("No features available. Run analyze() first.")
        
        # Calculate how many video frames we need
        duration = self.features['duration']
        n_video_frames = int(duration * fps)
        
        # Create time points for each video frame
        frame_times = np.linspace(0, duration, n_video_frames, endpoint=False)
        
        # Align features to video frames
        aligned_features = {'frame_times': frame_times}
        
        # Get audio time points - ensure this is always available
        audio_times = self.features['times']
        
        # Verify dimensions of features match with audio_times before interpolation
        # Align amplitude
        if 'amplitude' in self.features:
            amplitude = self.features['amplitude']
            
            # Ensure amplitude and audio_times have the same length
            if len(amplitude) > len(audio_times):
                amplitude = amplitude[:len(audio_times)]
            elif len(amplitude) < len(audio_times):
                # Pad amplitude with the last value
                amplitude = np.pad(amplitude, (0, len(audio_times) - len(amplitude)), 'edge')
                
            aligned_features['amplitude'] = np.interp(
                frame_times, 
                audio_times, 
                amplitude
            )
        
        # Align frequency bands
        if 'freq_bands' in self.features:
            aligned_bands = {}
            
            for band_name, band_energy in self.features['freq_bands'].items():
                # Ensure band_energy and audio_times have the same length
                if len(band_energy) > len(audio_times):
                    band_energy = band_energy[:len(audio_times)]
                elif len(band_energy) < len(audio_times):
                    # Pad band_energy with the last value
                    band_energy = np.pad(band_energy, (0, len(audio_times) - len(band_energy)), 'edge')
                    
                aligned_bands[band_name] = np.interp(
                    frame_times, 
                    audio_times, 
                    band_energy
                )
            
            aligned_features['freq_bands'] = aligned_bands
        
        # Align beat envelope
        if 'beats' in self.features and 'beat_envelope' in self.features['beats']:
            beat_envelope = self.features['beats']['beat_envelope']
            
            # Ensure beat_envelope and audio_times have the same length
            if len(beat_envelope) > len(audio_times):
                beat_envelope = beat_envelope[:len(audio_times)]
            elif len(beat_envelope) < len(audio_times):
                # Pad beat_envelope with zeros
                beat_envelope = np.pad(beat_envelope, (0, len(audio_times) - len(beat_envelope)), 'constant')
                
            aligned_features['beat_envelope'] = np.interp(
                frame_times, 
                audio_times, 
                beat_envelope
            )
        
        # Align onset envelope
        if 'onsets' in self.features and 'onset_envelope' in self.features['onsets']:
            onset_envelope = self.features['onsets']['onset_envelope']
            
            # Ensure onset_envelope and audio_times have the same length
            if len(onset_envelope) > len(audio_times):
                onset_envelope = onset_envelope[:len(audio_times)]
            elif len(onset_envelope) < len(audio_times):
                # Pad onset_envelope with zeros
                onset_envelope = np.pad(onset_envelope, (0, len(audio_times) - len(onset_envelope)), 'constant')
                
            aligned_features['onset_envelope'] = np.interp(
                frame_times, 
                audio_times, 
                onset_envelope
            )
        
        return aligned_features
    
    def get_synchronization_data(self, fps: float = 30.0) -> Dict[str, Any]:
        """Generate data needed for synchronizing effects with audio.
        
        Args:
            fps: Frames per second of the target video.
            
        Returns:
            Dictionary containing information for synchronizing effects.
            
        Raises:
            AudioAnalysisError: If features haven't been extracted yet.
        """
        if not self.features:
            raise AudioAnalysisError("No features available. Run analyze() first.")
        
        # Get frame-aligned features
        aligned_features = self.get_time_aligned_features(fps)
        
        # Create sync data structure
        sync_data = {
            'fps': fps,
            'duration': self.features['duration'],
            'n_frames': len(aligned_features['frame_times']),
            'features': aligned_features
        }
        
        return sync_data