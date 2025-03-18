import os
import logging
import numpy as np
import librosa

logger = logging.getLogger(__name__)

class AudioFeatureExtractor:
    """Handles extraction and processing of audio features from videos."""
    
    def __init__(self):
        self.features = None
        
    def extract_from_video(self, video_clip, n_mfcc=13, hop_length=512):
        """Extract audio features from a video clip's audio track."""
        # Extract audio from the video clip
        temp_audio_path = "temp_audio.wav"
        video_clip.audio.write_audiofile(temp_audio_path, fps=44100, logger=None)
        
        try:
            # Load the audio file with librosa
            y, sr = librosa.load(temp_audio_path)
            
            # Extract various audio features
            self.features = {
                'duration': librosa.get_duration(y=y, sr=sr),
                'tempo': librosa.beat.tempo(y=y, sr=sr)[0],
                'rms': librosa.feature.rms(y=y, hop_length=hop_length)[0],
                'onsets': librosa.onset.onset_strength(y=y, sr=sr),
                'mfcc': librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc),
                'spectral_centroid': librosa.feature.spectral_centroid(y=y, sr=sr)[0],
            }
            
            # Normalize and resize the features to match video frame count
            self._normalize_features(video_clip)
            
            logger.info("Audio features extracted successfully")
            return self.features
            
        except Exception as e:
            logger.error(f"Error extracting audio features: {e}")
            self.features = None
            return None
        finally:
            # Clean up the temporary audio file
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
    
    def _normalize_features(self, video_clip):
        """Normalize and resize features to match the video frame count."""
        if not self.features:
            return
            
        num_frames = int(video_clip.fps * video_clip.duration)
        
        for feature in ['rms', 'onsets', 'spectral_centroid']:
            # Resize to match frame count
            self.features[feature] = np.interp(
                np.linspace(0, len(self.features[feature]), num_frames),
                np.arange(len(self.features[feature])),
                self.features[feature]
            )
            
            # Normalize between 0 and 1
            if len(self.features[feature]) > 0:
                feature_min = self.features[feature].min()
                feature_max = self.features[feature].max()
                if feature_max > feature_min:
                    self.features[feature] = (self.features[feature] - feature_min) / (feature_max - feature_min)
                    
    def get_feature(self, feature_name, default=None):
        """Safe accessor for features with fallback"""
        if not self.features:
            return default
        return self.features.get(feature_name, default)