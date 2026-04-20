import sounddevice as sd
import numpy as np
import time

def test_audio():
    print("Testing sounddevice...")
    fs = 44100
    duration = 1.0  # seconds
    t = np.linspace(0, duration, int(fs * duration))
    data = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440Hz sine wave
    
    try:
        sd.play(data, fs)
        sd.wait()
        print("Audio test successful.")
    except Exception as e:
        print(f"Audio test failed: {e}")

if __name__ == "__main__":
    test_audio()
