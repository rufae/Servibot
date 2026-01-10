"""
Voice API Endpoints
Handles speech-to-text (Whisper) and text-to-speech (pyttsx3/gTTS)
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
import os
import tempfile
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class TTSRequest(BaseModel):
    """Text-to-speech request model."""
    text: str
    language: Optional[str] = "es"  # Spanish by default
    engine: Optional[str] = "gtts"  # gtts or pyttsx3


class TranscriptionResponse(BaseModel):
    """Speech-to-text response model."""
    status: str
    text: str
    language: Optional[str] = None
    duration: Optional[float] = None
    message: Optional[str] = None


class TTSResponse(BaseModel):
    """Text-to-speech response model."""
    status: str
    audio_url: Optional[str] = None
    filename: Optional[str] = None
    message: Optional[str] = None


@router.post("/voice/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe audio file to text using Whisper.
    
    Args:
        file: Audio file (mp3, wav, m4a, etc.)
        
    Returns:
        Transcribed text
    """
    try:
        # Validate file type
        allowed_extensions = {'.mp3', '.wav', '.m4a', '.ogg', '.webm', '.flac'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {allowed_extensions}"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Use Whisper for transcription
            import whisper
            
            # Load model (base is a good balance between speed and accuracy)
            # Options: tiny, base, small, medium, large
            model = whisper.load_model("base")
            
            logger.info(f"Transcribing audio file: {file.filename}")
            result = model.transcribe(tmp_file_path, language="es")  # Spanish by default
            
            transcribed_text = result["text"].strip()
            detected_language = result.get("language", "es")
            
            logger.info(f"Transcription completed. Text length: {len(transcribed_text)}")
            
            return TranscriptionResponse(
                status="success",
                text=transcribed_text,
                language=detected_language,
                message="Audio transcribed successfully"
            )
            
        finally:
            # Clean up temp file
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
    
    except ImportError:
        logger.error("Whisper not installed")
        raise HTTPException(
            status_code=500,
            detail="Whisper library not installed. Run: pip install openai-whisper"
        )
    except Exception as e:
        logger.exception(f"Error transcribing audio: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )


@router.post("/voice/synthesize", response_model=TTSResponse)
async def synthesize_speech(request: TTSRequest):
    """
    Convert text to speech using TTS engine with automatic fallback.
    
    Tries gTTS first (better quality, requires internet), falls back to pyttsx3 (offline).
    
    Args:
        request: TTS request with text and options
        
    Returns:
        Audio file URL
    """
    try:
        if not request.text or len(request.text.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="Text is required"
            )
        
        # Create audio output directory
        audio_dir = os.path.join(os.getcwd(), "data", "audio")
        os.makedirs(audio_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tts_{timestamp}.mp3"
        file_path = os.path.join(audio_dir, filename)
        
        engine_used = None
        generation_error = None
        
        # Try requested engine first, then fallback
        engines_to_try = [request.engine]
        if request.engine == "gtts":
            engines_to_try.append("pyttsx3")  # Fallback
        elif request.engine == "pyttsx3":
            engines_to_try.append("gtts")  # Alternative fallback
        
        for engine_name in engines_to_try:
            try:
                if engine_name == "gtts":
                    # Use gTTS (Google Text-to-Speech) - requires internet
                    try:
                        from gtts import gTTS
                    except ImportError:
                        logger.warning("gTTS not installed, trying next engine")
                        generation_error = "gTTS not installed"
                        continue
                    
                    logger.info(f"🔊 Attempting TTS with gTTS for text: {request.text[:50]}...")
                    tts = gTTS(text=request.text, lang=request.language, slow=False)
                    tts.save(file_path)
                    engine_used = "gtts"
                    logger.info(f"✅ TTS audio generated with gTTS: {file_path}")
                    break  # Success, exit loop
                    
                elif engine_name == "pyttsx3":
                    # Use pyttsx3 (offline TTS) - works offline
                    try:
                        import pyttsx3
                    except ImportError:
                        logger.warning("pyttsx3 not installed, trying next engine")
                        generation_error = "pyttsx3 not installed"
                        continue
                    
                    logger.info(f"🔊 Attempting TTS with pyttsx3 for text: {request.text[:50]}...")
                    # pyttsx3 generates WAV by default, rename to .wav
                    filename_wav = filename.replace(".mp3", ".wav")
                    file_path_wav = os.path.join(audio_dir, filename_wav)
                    
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 150)  # Speed
                    engine.setProperty('volume', 0.9)  # Volume (0-1)
                    engine.save_to_file(request.text, file_path_wav)
                    engine.runAndWait()
                    
                    # Update filename to reflect actual format
                    filename = filename_wav
                    file_path = file_path_wav
                    engine_used = "pyttsx3"
                    logger.info(f"✅ TTS audio generated with pyttsx3: {file_path}")
                    break  # Success, exit loop
                    
            except Exception as engine_error:
                import traceback
                logger.warning(f"⚠️ TTS engine '{engine_name}' failed: {engine_error}")
                logger.debug(f"Traceback: {traceback.format_exc()}")
                generation_error = str(engine_error)
                # Continue to next engine
                continue
        
        # Check if any engine succeeded
        if not engine_used or not os.path.exists(file_path):
            error_msg = f"All TTS engines failed. Last error: {generation_error}"
            logger.error(f"❌ {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=error_msg
            )
        
        # Return audio URL (relative path for frontend)
        audio_url = f"/api/voice/audio/{filename}"
        
        return TTSResponse(
            status="success",
            audio_url=audio_url,
            filename=filename,
            message=f"Audio generated successfully with {engine_used}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"TTS generation failed: {str(e)}"
        logger.error(f"Error generating TTS: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )


@router.get("/voice/audio/{filename}")
async def get_audio_file(filename: str):
    """
    Serve generated audio file with proper CORS and caching headers.
    
    Args:
        filename: Audio filename
        
    Returns:
        Audio file with appropriate headers
    """
    from fastapi.responses import FileResponse
    
    audio_dir = os.path.join(os.getcwd(), "data", "audio")
    file_path = os.path.join(audio_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"Audio file not found: {filename}"
        )
    
    # Determine media type based on file extension
    media_type = "audio/mpeg"  # Default for .mp3
    if filename.endswith(".wav"):
        media_type = "audio/wav"
    elif filename.endswith(".ogg"):
        media_type = "audio/ogg"
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "*",
            "Accept-Ranges": "bytes"
        }
    )


@router.get("/voice/status")
async def get_voice_status():
    """
    Check which voice engines are available.
    
    Returns:
        Status of voice engines
    """
    status = {
        "whisper": False,
        "gtts": False,
        "pyttsx3": False
    }
    
    try:
        import whisper
        status["whisper"] = True
    except ImportError:
        pass
    
    try:
        from gtts import gTTS
        status["gtts"] = True
    except ImportError:
        pass
    
    try:
        import pyttsx3
        status["pyttsx3"] = True
    except ImportError:
        pass
    
    return {
        "status": "success",
        "engines": status,
        "available": any(status.values()),
        "message": "Voice engines status retrieved"
    }
