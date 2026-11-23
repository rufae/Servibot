# 🤖 ServiBot - Autonomous AI Assistant

[![CI](https://github.com/rufae/Servibot/actions/workflows/ci.yml/badge.svg)](https://github.com/rufae/Servibot/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-14-brightgreen.svg)](tests/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](backend/)

**ServiBot** is an autonomous multimodal AI agent that manages personal tasks through natural language, integrating RAG (Retrieval Augmented Generation), tool orchestration, voice interaction, and real automation capabilities.

## 🎯 Project Overview

This project is part of the AI Master's Capstone (2025), demonstrating advanced AI concepts including:

- 🧠 **Autonomous Agents** with Plan→Execute→Evaluate loop
- 📚 **RAG Pipeline** for context-aware responses
- 🎤 **Voice AI** (Whisper STT + ElevenLabs TTS)
- 🔧 **Tool Orchestration** (Calendar, Email, Notes, File Generation)
- 🖼️ **Multimodal Processing** (PDF, images with OCR)
- 🚀 **Production Deployment** (Vercel + Render/HF Spaces)

## 📅 Project Timeline

- **Start Date**: December 4, 2025
- **Concept Delivery**: December 17, 2025
- **Final Delivery**: January 27, 2026

## 🏗️ Architecture

```
Frontend (React + Tailwind)
    ↓ REST API
Backend (FastAPI)
    ├── Agent Engine (Planner/Executor/Evaluator)
    ├── RAG Pipeline (Chroma Vector DB)
    ├── Tool Layer (5+ tools)
    └── External APIs (OpenAI, ElevenLabs, Google)
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Git

### Backend Setup

```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy environment template
copy .env.example .env
# Edit .env with your API keys

# Run the server
python -m uvicorn app.main:app --reload
```

Backend will be available at `http://localhost:8000`  
API docs at `http://localhost:8000/api/docs`

### Frontend Setup

```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

### Running Tests

```powershell
# From project root
cd tests
pytest -v
```

## 📁 Project Structure

```
ServiBot/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── core/                # Config and utilities
│   │   ├── api/                 # API endpoints
│   │   │   ├── chat.py
│   │   │   ├── upload.py
│   │   │   └── health.py
│   │   ├── agent/               # Agent engine
│   │   │   ├── planner.py
│   │   │   ├── executor.py
│   │   │   └── evaluator.py
│   │   ├── rag/                 # RAG pipeline
│   │   ├── tools/               # Automation tools
│   │   └── models/              # Data models
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   │   ├── ChatInterface.jsx
│   │   │   ├── FileUpload.jsx
│   │   │   └── AgentTimeline.jsx
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── tailwind.config.js
├── tests/                       # Pytest test suite
├── docs/                        # Documentation
├── data/                        # Data storage
│   ├── uploads/
│   └── vector_db/
└── README.md
```

## 🔑 Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# API Keys
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key
HUGGINGFACE_API_KEY=your_hf_key

# Optional integrations
GOOGLE_CALENDAR_CREDENTIALS=path/to/credentials.json
GMAIL_CREDENTIALS=path/to/gmail_creds.json
NOTION_API_KEY=your_notion_key
TODOIST_API_KEY=your_todoist_key

# App settings
ENVIRONMENT=development
DEBUG=True
```

## 🎯 Current Features (MVP - Version B)

### ✅ Implemented
- [x] Backend FastAPI structure
- [x] Frontend React + Tailwind UI
- [x] Chat interface
- [x] File upload endpoint
- [x] Agent planner (basic)
- [x] Agent executor (basic)
- [x] Agent evaluator (basic)
- [x] Health monitoring

### ✅ Recently Implemented
- [x] RAG ingestion pipeline (ChromaDB + sentence-transformers)
- [x] Vector DB integration with automatic retry worker
- [x] **Voice AI**: Whisper STT (local) + gTTS/pyttsx3 TTS
- [x] **File Generation**: PDF (reportlab) + Excel (openpyxl)
- [x] **OCR Tool**: Tesseract with preprocessing and batch processing
- [x] **Agent-tool orchestration**: Executor routes to real tools
- [x] **Frontend Components**: VoiceRecorder, AudioPlayer, FileGenerator
- [x] **Test Suite**: 50+ tests for file_writer, OCR, voice APIs

### 🚧 In Progress
- [ ] Google Calendar integration
- [ ] Gmail integration
- [ ] Notion/Todoist integration
- [ ] Multi-user authentication
- [ ] Production deployment

### 📋 Planned
- [ ] ElevenLabs premium TTS
- [ ] Custom tool plugin system
- [ ] Memory system for conversation context
- [ ] Websockets for streaming responses
- [ ] Multi-language support beyond Spanish/English

## 🛠️ Available API Endpoints

### Health & Info
- `GET /` - Root info
- `GET /api/health` - Health check with system metrics

### Chat
- `POST /api/chat` - Send message to agent (RAG-enriched responses)
  ```json
  {"message": "¿Qué dice el documento sobre...?"}
  ```

### Upload & RAG
- `POST /api/upload` - Upload file (PDF, DOCX, TXT, images with OCR)
- `GET /api/upload/files` - List uploaded files
- `DELETE /api/upload/file/{filename}` - Delete file and embeddings
- `GET /api/rag/stats` - Vector database statistics
- `POST /api/rag/query` - Manual semantic search
- `POST /api/rag/clear` - Clear all ChromaDB data

### Voice AI 🎙️
- `POST /api/voice/transcribe` - Transcribe audio with Whisper
  ```
  multipart/form-data: file (mp3, wav, m4a, ogg, webm)
  ```
- `POST /api/voice/synthesize` - Generate TTS audio
  ```json
  {"text": "Hola", "language": "es", "engine": "gtts"}
  ```
- `GET /api/voice/status` - Check available engines (whisper, gtts, pyttsx3)
- `GET /api/voice/audio/{filename}` - Download generated audio

### File Generation 📄
- `POST /api/generate/pdf` - Generate formatted PDF
  ```json
  {"title": "Report", "content": "...", "metadata": {...}}
  ```
- `POST /api/generate/excel` - Generate multi-sheet Excel
  ```json
  {"filename": "data.xlsx", "sheets": {...}, "headers": {...}}
  ```
- `GET /api/generate/list` - List generated files
- `GET /api/generate/download/{filename}` - Download PDF/Excel

## 🧪 Testing

```powershell
# Run all tests
pytest

# Run with coverage
pytest --cov=backend/app

# Run specific test file
pytest tests/test_chat.py -v
```

## 📦 Deployment

### Backend (Render/HF Spaces)
```powershell
# Backend runs on port 8000
# Use Dockerfile or direct Python deployment
```

### Frontend (Vercel)
```powershell
# Build frontend
cd frontend
npm run build

# Deploy to Vercel
# Connect GitHub repo to Vercel dashboard
```

## 🎓 Academic Requirements Met

This project demonstrates mastery of:

- ✅ **Module 0**: Python programming
- ✅ **Module 1-8**: Exponential Programming (AI-assisted development)
- ✅ **Module 2**: AI fundamentals
- ✅ **Module 4**: Large Language Models
- ✅ **Module 5**: Prompt Engineering
- ✅ **Module 6**: RAG & Autonomous Agents
- ✅ **Module 7**: Multimodal AI (vision, audio, text)

## 📝 Development Log

### Week 1 (Dec 4-11, 2025)
- [x] Project structure created
- [x] Backend skeleton implemented (FastAPI + Pydantic)
- [x] Frontend skeleton implemented (React + Tailwind)
- [x] Basic API endpoints (health, chat, upload)
- [x] Test suite initialized

### Week 2 (Dec 10, 2025)
- [x] **RAG Pipeline Complete**: ChromaDB + sentence-transformers + automatic indexing
- [x] **Voice AI Implementation**: Whisper STT + gTTS/pyttsx3 TTS
- [x] **File Generation Tools**: reportlab PDF + openpyxl Excel
- [x] **OCR Enhancement**: Tesseract with preprocessing, batch, layout analysis
- [x] **Frontend Components**: VoiceRecorder (waveform visualization), AudioPlayer (advanced controls), FileGenerator (PDF/Excel export)
- [x] **Agent Tool Integration**: Executor routes to real file_writer and OCR tools
- [x] **Test Suite Expansion**: 50+ tests (file_writer, OCR, voice endpoints)
- [x] **Documentation**: Comprehensive README with API docs

### Next Steps (Dec 11-17, 2025)
- [ ] Frontend testing and bug fixes
- [ ] LM Studio integration optimization
- [ ] Google Calendar/Gmail API integration (optional)
- [ ] Concept document finalization
- [ ] Demo video recording

## 🤝 Contributing

This is a capstone project. For questions or collaboration:
- **Author**: Rafa Castaño
- **Institution**: AI Master's Program
- **Year**: 2025

## 📄 License

This project is for academic purposes.

## 🔗 Links

- **Backend API Docs**: http://localhost:8000/api/docs
- **Frontend**: http://localhost:3000
- **GitHub**: [Your repo URL]
- **Demo Video**: [To be added]

---

**Status**: 🚧 In Development  
**Version**: 0.1.0  
**Last Updated**: December 8, 2025
