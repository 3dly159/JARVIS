import sounddevice as sd
import numpy as np
import time

def test_duplex():
    print("Testing simultaneous Playback and Recording (Duplex)...")
    fs = 16000
    duration = 3.0
    
    # Generate a tone to play
    t = np.linspace(0, duration, int(fs * duration))
    play_data = 0.3 * np.sin(2 * np.pi * 440 * t)
    
    recorded_data = []

    def callback(indata, frames, time, status):
        if status:
            print(f"Status: {status}")
        recorded_data.append(indata.copy())

    try:
        print("Starting playback...")
        sd.play(play_data, fs)
        
        print("Starting recording...")
        with sd.InputStream(samplerate=fs, channels=1, callback=callback):
            sd.wait() # wait for playback to finish
            
        print("Test complete.")
        if recorded_data:
            print(f"Successfully recorded {len(recorded_data)} blocks during playback.")
        else:
            print("Failed to record any data.")
            
    except Exception as e:
        print(f"Duplex test failed: {e}")

if __name__ == "__main__":
    test_duplex()
