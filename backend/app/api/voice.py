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
    Convert text to speech using TTS engine.
    
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
        
        if request.engine == "gtts":
            # Use gTTS (Google Text-to-Speech) - requires internet
            try:
                from gtts import gTTS
                
                logger.info(f"Generating TTS with gTTS for text: {request.text[:50]}...")
                tts = gTTS(text=request.text, lang=request.language, slow=False)
                tts.save(file_path)
                
                logger.info(f"TTS audio generated with gTTS: {file_path}")
                
            except ImportError as ie:
                logger.error(f"gTTS import error: {ie}")
                raise HTTPException(
                    status_code=500,
                    detail="gTTS not installed. Run: pip install gTTS"
                )
            except Exception as gtts_err:
                import traceback
                logger.error(f"gTTS generation error: {gtts_err}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise HTTPException(
                    status_code=500,
                    detail=f"gTTS failed: {str(gtts_err)}. Try using pyttsx3 engine instead."
                )
        
        elif request.engine == "pyttsx3":
            # Use pyttsx3 (offline TTS) - works offline but voice quality varies
            try:
                import pyttsx3
                
                engine = pyttsx3.init()
                
                # Set properties
                engine.setProperty('rate', 150)  # Speed
                engine.setProperty('volume', 0.9)  # Volume (0-1)
                
                # Save to file
                engine.save_to_file(request.text, file_path)
                engine.runAndWait()
                
                logger.info(f"TTS audio generated with pyttsx3: {file_path}")
                
            except ImportError:
                raise HTTPException(
                    status_code=500,
                    detail="pyttsx3 not installed. Run: pip install pyttsx3"
                )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported engine: {request.engine}. Use 'gtts' or 'pyttsx3'"
            )
        
        # Return audio URL (relative path for frontend)
        audio_url = f"/api/voice/audio/{filename}"
        
        return TTSResponse(
            status="success",
            audio_url=audio_url,
            filename=filename,
            message="Audio generated successfully"
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
    Serve generated audio file.
    
    Args:
        filename: Audio filename
        
    Returns:
        Audio file
    """
    from fastapi.responses import FileResponse
    
    audio_dir = os.path.join(os.getcwd(), "data", "audio")
    file_path = os.path.join(audio_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"Audio file not found: {filename}"
        )
    
    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=filename
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
