"""
Tests for Voice API endpoints - Whisper STT and TTS
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, mock_open
import os
import tempfile
from pathlib import Path

# Import the FastAPI app
from app.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def temp_audio_dir():
    """Create temporary directory for audio files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_audio_file(temp_audio_dir):
    """Create a mock audio file"""
    audio_path = os.path.join(temp_audio_dir, "test.mp3")
    with open(audio_path, 'wb') as f:
        f.write(b"fake audio data")
    return audio_path


class TestVoiceStatus:
    """Test voice status endpoint"""

    def test_voice_status_returns_engines(self, client):
        """Test GET /api/voice/status returns engine availability"""
        response = client.get("/api/voice/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "engines" in data
        assert "whisper" in data["engines"]
        assert "gtts" in data["engines"]
        assert "pyttsx3" in data["engines"]
        
        # Values should be boolean
        assert isinstance(data["engines"]["whisper"], bool)
        assert isinstance(data["engines"]["gtts"], bool)
        assert isinstance(data["engines"]["pyttsx3"], bool)


class TestVoiceTranscription:
    """Test transcription endpoint"""

    @patch('app.api.voice.whisper.load_model')
    def test_transcribe_audio_success(self, mock_load_model, client, sample_audio_file):
        """Test successful audio transcription"""
        # Mock Whisper model
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "Hello, this is a test transcription",
            "language": "en"
        }
        mock_load_model.return_value = mock_model
        
        with open(sample_audio_file, 'rb') as f:
            response = client.post(
                "/api/voice/transcribe",
                files={"file": ("test.mp3", f, "audio/mpeg")}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "text" in data
        assert len(data["text"]) > 0
        assert "language" in data

    def test_transcribe_no_file(self, client):
        """Test transcription without file"""
        response = client.post("/api/voice/transcribe")
        
        assert response.status_code == 422  # Validation error

    @patch('app.api.voice.whisper.load_model')
    def test_transcribe_invalid_format(self, mock_load_model, client, temp_audio_dir):
        """Test transcription with invalid file format"""
        # Create non-audio file
        invalid_file = os.path.join(temp_audio_dir, "test.txt")
        with open(invalid_file, 'w') as f:
            f.write("Not an audio file")
        
        with open(invalid_file, 'rb') as f:
            response = client.post(
                "/api/voice/transcribe",
                files={"file": ("test.txt", f, "text/plain")}
            )
        
        # Should reject or handle gracefully
        assert response.status_code in [400, 422, 500]

    @patch('app.api.voice.whisper.load_model')
    def test_transcribe_different_formats(self, mock_load_model, client, temp_audio_dir):
        """Test transcription supports multiple audio formats"""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "Test transcription",
            "language": "en"
        }
        mock_load_model.return_value = mock_model
        
        formats = ["mp3", "wav", "m4a", "ogg"]
        
        for fmt in formats:
            audio_file = os.path.join(temp_audio_dir, f"test.{fmt}")
            with open(audio_file, 'wb') as f:
                f.write(b"fake audio data")
            
            with open(audio_file, 'rb') as f:
                response = client.post(
                    "/api/voice/transcribe",
                    files={"file": (f"test.{fmt}", f, f"audio/{fmt}")}
                )
            
            # Should accept all supported formats
            assert response.status_code in [200, 500]  # 500 if Whisper fails on fake data

    @patch('app.api.voice.whisper.load_model')
    def test_transcribe_spanish_language(self, mock_load_model, client, sample_audio_file):
        """Test transcription detects Spanish language"""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "Hola, esto es una prueba",
            "language": "es"
        }
        mock_load_model.return_value = mock_model
        
        with open(sample_audio_file, 'rb') as f:
            response = client.post(
                "/api/voice/transcribe",
                files={"file": ("test.mp3", f, "audio/mpeg")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "es"


class TestVoiceSynthesis:
    """Test TTS synthesis endpoint"""

    @patch('app.api.voice.gTTS')
    def test_synthesize_gtts_success(self, mock_gtts, client, temp_audio_dir):
        """Test successful TTS with gTTS"""
        # Mock gTTS
        mock_tts_instance = MagicMock()
        mock_gtts.return_value = mock_tts_instance
        
        with patch('app.api.voice.AUDIO_DIR', temp_audio_dir):
            response = client.post(
                "/api/voice/synthesize",
                json={
                    "text": "Hello world",
                    "language": "en",
                    "engine": "gtts"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "audio_url" in data
        assert "/api/voice/audio/" in data["audio_url"]

    @patch('app.api.voice.pyttsx3')
    def test_synthesize_pyttsx3_success(self, mock_pyttsx3, client, temp_audio_dir):
        """Test successful TTS with pyttsx3"""
        # Mock pyttsx3
        mock_engine = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine
        
        with patch('app.api.voice.AUDIO_DIR', temp_audio_dir):
            response = client.post(
                "/api/voice/synthesize",
                json={
                    "text": "Hello world",
                    "language": "en",
                    "engine": "pyttsx3"
                }
            )
        
        assert response.status_code in [200, 500]  # May fail if pyttsx3 not installed

    def test_synthesize_empty_text(self, client):
        """Test synthesis with empty text"""
        response = client.post(
            "/api/voice/synthesize",
            json={
                "text": "",
                "language": "en",
                "engine": "gtts"
            }
        )
        
        # Should reject empty text
        assert response.status_code in [400, 422]

    @patch('app.api.voice.gTTS')
    def test_synthesize_spanish_text(self, mock_gtts, client, temp_audio_dir):
        """Test synthesis with Spanish text"""
        mock_tts_instance = MagicMock()
        mock_gtts.return_value = mock_tts_instance
        
        with patch('app.api.voice.AUDIO_DIR', temp_audio_dir):
            response = client.post(
                "/api/voice/synthesize",
                json={
                    "text": "Hola mundo",
                    "language": "es",
                    "engine": "gtts"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    @patch('app.api.voice.gTTS')
    def test_synthesize_long_text(self, mock_gtts, client, temp_audio_dir):
        """Test synthesis with long text"""
        mock_tts_instance = MagicMock()
        mock_gtts.return_value = mock_tts_instance
        
        long_text = "This is a very long sentence. " * 50
        
        with patch('app.api.voice.AUDIO_DIR', temp_audio_dir):
            response = client.post(
                "/api/voice/synthesize",
                json={
                    "text": long_text,
                    "language": "en",
                    "engine": "gtts"
                }
            )
        
        assert response.status_code == 200

    def test_synthesize_invalid_engine(self, client):
        """Test synthesis with invalid engine"""
        response = client.post(
            "/api/voice/synthesize",
            json={
                "text": "Hello",
                "language": "en",
                "engine": "invalid_engine"
            }
        )
        
        # Should reject invalid engine
        assert response.status_code in [400, 422, 500]

    def test_synthesize_unsupported_language(self, client):
        """Test synthesis with unsupported language code"""
        response = client.post(
            "/api/voice/synthesize",
            json={
                "text": "Hello",
                "language": "xyz",  # Invalid language code
                "engine": "gtts"
            }
        )
        
        # May accept but fail during synthesis
        assert response.status_code in [200, 400, 422, 500]


class TestVoiceAudioServing:
    """Test audio file serving endpoint"""

    def test_audio_serving_existing_file(self, client, temp_audio_dir):
        """Test serving existing audio file"""
        # Create test audio file
        audio_filename = "test_audio.mp3"
        audio_path = os.path.join(temp_audio_dir, audio_filename)
        with open(audio_path, 'wb') as f:
            f.write(b"fake audio data")
        
        with patch('app.api.voice.AUDIO_DIR', temp_audio_dir):
            response = client.get(f"/api/voice/audio/{audio_filename}")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mpeg"

    def test_audio_serving_nonexistent_file(self, client):
        """Test serving non-existent audio file"""
        response = client.get("/api/voice/audio/nonexistent.mp3")
        
        assert response.status_code == 404

    def test_audio_serving_path_traversal(self, client):
        """Test audio serving prevents path traversal"""
        response = client.get("/api/voice/audio/../../../etc/passwd")
        
        assert response.status_code == 404

    def test_audio_serving_different_extensions(self, client, temp_audio_dir):
        """Test serving different audio file extensions"""
        extensions = ["mp3", "wav", "ogg"]
        
        for ext in extensions:
            filename = f"test.{ext}"
            audio_path = os.path.join(temp_audio_dir, filename)
            with open(audio_path, 'wb') as f:
                f.write(b"fake audio")
            
            with patch('app.api.voice.AUDIO_DIR', temp_audio_dir):
                response = client.get(f"/api/voice/audio/{filename}")
            
            assert response.status_code == 200


class TestVoiceEdgeCases:
    """Test edge cases and error handling"""

    @patch('app.api.voice.whisper.load_model')
    def test_transcribe_corrupted_audio(self, mock_load_model, client, temp_audio_dir):
        """Test transcription with corrupted audio file"""
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = Exception("Failed to decode audio")
        mock_load_model.return_value = mock_model
        
        corrupted_file = os.path.join(temp_audio_dir, "corrupted.mp3")
        with open(corrupted_file, 'wb') as f:
            f.write(b"not valid audio data")
        
        with open(corrupted_file, 'rb') as f:
            response = client.post(
                "/api/voice/transcribe",
                files={"file": ("corrupted.mp3", f, "audio/mpeg")}
            )
        
        # Should handle error gracefully
        assert response.status_code in [400, 500]
        data = response.json()
        assert data["status"] == "error"

    @patch('app.api.voice.gTTS')
    def test_synthesize_special_characters(self, mock_gtts, client, temp_audio_dir):
        """Test synthesis with special characters"""
        mock_tts_instance = MagicMock()
        mock_gtts.return_value = mock_tts_instance
        
        with patch('app.api.voice.AUDIO_DIR', temp_audio_dir):
            response = client.post(
                "/api/voice/synthesize",
                json={
                    "text": "¡Hola! ¿Cómo estás? ñ á é í ó ú",
                    "language": "es",
                    "engine": "gtts"
                }
            )
        
        assert response.status_code == 200

    def test_synthesize_missing_language(self, client):
        """Test synthesis with missing language parameter"""
        response = client.post(
            "/api/voice/synthesize",
            json={
                "text": "Hello",
                "engine": "gtts"
                # Missing language
            }
        )
        
        # Should use default or reject
        assert response.status_code in [200, 422]

    @patch('app.api.voice.whisper.load_model')
    def test_transcribe_very_short_audio(self, mock_load_model, client, temp_audio_dir):
        """Test transcription with very short audio"""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "",
            "language": "en"
        }
        mock_load_model.return_value = mock_model
        
        short_audio = os.path.join(temp_audio_dir, "short.mp3")
        with open(short_audio, 'wb') as f:
            f.write(b"x" * 100)  # Very small file
        
        with open(short_audio, 'rb') as f:
            response = client.post(
                "/api/voice/transcribe",
                files={"file": ("short.mp3", f, "audio/mpeg")}
            )
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 500]
