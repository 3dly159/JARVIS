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
        import subprocess

        audio_bytes = await file.read()

        # Use ffmpeg to decode to wav 16kHz mono PCM
        try:
            # Run ffmpeg to decode any audio format to wav 16kHz mono
            # Input from pipe, output wav to pipe
            proc = subprocess.Popen(
                ['ffmpeg', '-i', 'pipe:0', '-f', 'wav', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', 'pipe:1'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )
            out, err = proc.communicate(input=audio_bytes, timeout=10)
            if proc.returncode != 0:
                raise subprocess.CalledProcessError(proc.returncode, 'ffmpeg')
            # Convert raw PCM s16le to float32 numpy array
            audio_data = np.frombuffer(out, dtype=np.int16).astype(np.float32) / 32768.0
            # Ensure it's mono (should be due to -ac 1)
            if len(audio_data.shape) > 1:
                audio_data = audio_data.mean(axis=1)
        except Exception as e:
            logger.error(f"FFmpeg audio decode failed: {e}")
            return JSONResponse({"error": "Audio decode failed"}, status_code=400)

        # Transcribe
        text = jarvis.ears.transcribe(audio_data)
        logger.info(f"Transcribed: '{text}'")

        # Broadcast state
        from ui.routes.state import set_state_sync
        set_state_sync("thinking")

        return {"text": text, "success": True}

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
