import asyncio
import edge_tts
import sounddevice as sd
import soundfile as sf
import tempfile
import os

async def test_tts():
    print("Testing edge-tts...")
    text = "Good morning, sir. I am testing my vocal sub-routines."
    voice = "en-GB-RyanNeural"
    
    communicate = edge_tts.Communicate(text, voice)
    
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        print(f"Saving to {tmp_path}...")
        await communicate.save(tmp_path)
        
        print("Reading audio data...")
        data, samplerate = sf.read(tmp_path)
        
        print("Playing...")
        sd.play(data, samplerate)
        sd.wait()
        print("TTS test successful.")
    except Exception as e:
        print(f"TTS test failed: {e}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

if __name__ == "__main__":
    asyncio.run(test_tts())
