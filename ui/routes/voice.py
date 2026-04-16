"""
ui/routes/voice.py - Voice API endpoints

POST /api/voice/transcribe  — browser sends raw audio, returns text
POST /api/voice/speak       — text → TTS audio bytes
GET  /api/voice/status      — STT/TTS status
"""

import logging
import tempfile
import os
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse, Response

router = APIRouter()
logger = logging.getLogger("jarvis.ui.voice")


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    """
    Receive audio from browser (WAV/WebM), return transcription.
    Browser orb sends audio blobs here for Whisper STT.
    """
    try:
        from core.jarvis import jarvis
        if not jarvis.ears or not jarvis.ears._model:
            return JSONResponse({"error": "STT not available"}, status_code=503)

        import numpy as np
        import io

        # Save to temp file
        audio_bytes = await file.read()
        suffix = ".wav" if file.filename.endswith(".wav") else ".webm"

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            # Load audio with soundfile or ffmpeg fallback
            try:
                import soundfile as sf
                audio_data, sr = sf.read(tmp_path, dtype="float32", always_2d=False)
                # Resample to 16kHz if needed
                if sr != 16000:
                    import scipy.signal
                    audio_data = scipy.signal.resample(
                        audio_data, int(len(audio_data) * 16000 / sr)
                    )
            except Exception:
                # Fallback: use librosa or pydub
                try:
                    import librosa
                    audio_data, _ = librosa.load(tmp_path, sr=16000, mono=True)
                except Exception:
                    return JSONResponse({"error": "Audio decode failed"}, status_code=400)

            # Ensure mono float32
            if len(audio_data.shape) > 1:
                audio_data = audio_data.mean(axis=1)
            audio_data = audio_data.astype(np.float32)

            # Transcribe
            text = jarvis.ears.transcribe(audio_data)
            logger.info(f"Transcribed: '{text}'")

            # Broadcast state
            from ui.routes.state import set_state_sync
            set_state_sync("thinking")

            return {"text": text, "success": True}

        finally:
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Transcribe error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/speak")
async def speak(body: dict):
    """
    Synthesize text to audio and return WAV bytes.
    Browser orb calls this to play JARVIS's voice.
    """
    text = body.get("text", "").strip()
    if not text:
        return JSONResponse({"error": "No text provided"}, status_code=400)

    try:
        import asyncio
        import edge_tts
        import tempfile
        import os
        from core.config_manager import config

        voice = config.get("voice.tts_voice", "en-GB-RyanNeural")
        rate = config.get("voice.tts_rate", "+0%")
        pitch = config.get("voice.tts_pitch", "+0Hz")

        communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name

        await communicate.save(tmp_path)

        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()
        os.unlink(tmp_path)

        # Broadcast speaking state
        from ui.routes.state import set_state_sync
        set_state_sync("speaking")

        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=speech.mp3"}
        )

    except ImportError:
        return JSONResponse({"error": "edge-tts not installed"}, status_code=503)
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/status")
async def voice_status():
    from core.jarvis import jarvis
    return {
        "stt": {
            "available": jarvis.ears is not None,
            "model": jarvis.ears.model_size if jarvis.ears else None,
            "device": jarvis.ears.device if jarvis.ears else None,
        },
        "tts": {
            "available": jarvis.voice is not None,
            "voice": jarvis.voice.voice if jarvis.voice else None,
        },
        "wake": {
            "available": jarvis.wake is not None,
            "running": jarvis.wake._running if jarvis.wake else False,
        }
    }
