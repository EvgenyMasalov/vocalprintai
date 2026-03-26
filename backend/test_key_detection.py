import librosa
import numpy as np
from utils import estimate_key

def test_key_detection():
    print("Testing Key Detection Algorithm...")
    
    # Generate a simple C Major chord (C, E, G)
    # C=0, E=4, G=7 in chroma
    sr = 22050
    duration = 2.0
    t = np.linspace(0, duration, int(sr * duration))
    
    # Frequencies for C4, E4, G4
    c4 = 261.63
    e4 = 329.63
    g4 = 392.00
    
    y = np.sin(2 * np.pi * c4 * t) + np.sin(2 * np.pi * e4 * t) + np.sin(2 * np.pi * g4 * t)
    
    key = estimate_key(y, sr)
    print(f"Generated C Major chord -> Detected Key: {key}")
    
    # Generate A Minor chord (A, C, E)
    # A=9, C=0, E=4
    a3 = 220.00
    y_minor = np.sin(2 * np.pi * a3 * t) + np.sin(2 * np.pi * c4 * t) + np.sin(2 * np.pi * e4 * t)
    
    key_minor = estimate_key(y_minor, sr)
    print(f"Generated A Minor chord -> Detected Key: {key_minor}")

if __name__ == "__main__":
    test_key_detection()
