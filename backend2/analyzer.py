import librosa
import numpy as np
from typing import Dict, Any, Optional

class AudioAnalyzer:
    def __init__(self):
        pass

    def analyze(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Loads the WAV file and performs analysis using librosa.
        Returns a dictionary with features.
        """
        try:
            # Load audio file (librosa handles common formats, but WAV is safest)
            # y is the audio time series, sr is the sampling rate
            y, sr = librosa.load(file_path, sr=None)
            
            # 1. Basic properties
            duration = librosa.get_duration(y=y, sr=sr)
            
            # 2. Tempo and Beats
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            # In librosa 0.10+, beat_track returns (tempo, beats) or (tempo, beats, frames) depending on version
            # ensuring we get a float
            if isinstance(tempo, np.ndarray):
                tempo = float(tempo[0])
            else:
                tempo = float(tempo)

            # 3. Spectral features (Centroid)
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            avg_spectral_centroid = float(np.mean(spectral_centroids))

            # 4. Energy (RMS)
            rms = librosa.feature.rms(y=y)[0]
            avg_rms = float(np.mean(rms))

            return {
                "duration_seconds": round(duration, 2),
                "tempo_bpm": round(tempo, 2),
                "avg_spectral_centroid": round(avg_spectral_centroid, 2),
                "avg_rms_energy": round(avg_rms, 4),
                "status": "success"
            }

        except Exception as e:
            print(f"Librosa analysis error: {e}")
            return None

if __name__ == "__main__":
    # Test
    analyzer = AudioAnalyzer()
    # result = analyzer.analyze("test.wav")
    # print(result)
