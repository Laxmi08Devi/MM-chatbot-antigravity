# Multimodal AI Chatbot

A beginner-friendly, modular, full-stack Multimodal AI Chatbot built with **FastAPI**, **Streamlit**, and **PostgreSQL** (with **pgvector** support).

It supports multimodal input and output, live web search, Retrieval-Augmented Generation (RAG) with source attribution, document authoring and lifecycle management, and empathetic personal emotional assistance with safety boundaries.

---

## 📑 Table of Contents

- [Project Overview](#project-overview)
- [MVP Features & Limitations](#mvp-features--limitations)
- [Technology Stack](#technology-stack)
- [Architecture & Data Flow](#architecture--data-flow)
- [Project Folder Structure](#project-folder-structure)
- [Prerequisites](#prerequisites)
- [PostgreSQL & pgvector Setup](#postgresql--pgvector-setup)
- [Virtual Environment & Dependency Installation](#virtual-environment--dependency-installation)
- [Configuration (`.env`)](#configuration-env)
- [Running the Application](#running-the-application)
- [API Endpoint Overview](#api-endpoint-overview)
- [RAG Workflow Explained](#rag-workflow-explained)
- [Model & Provider Configuration](#model--provider-configuration)
- [Testing Instructions](#testing-instructions)
- [Common Errors & Troubleshooting](#common-errors--troubleshooting)
- [Security Considerations](#security-considerations)
- [Future Enhancements](#future-enhancements)

---

## Project Overview

This project implements a complete, minimum viable product (MVP) multimodal conversational AI system. It is designed to be:

- **Modular**: Model providers (OpenAI, Gemini), vector storage (pgvector or cosine fallback), web search, and UI layers are completely decoupled.
- **Resilient**: Graceful degradation when external API keys are not yet configured or when PostgreSQL is running without pgvector.
- **Beginner-Friendly**: Clear code structure, parameterized SQL queries, clean Pydantic schemas, and automated schema migrations.

---

## MVP Features & Limitations

### Core Features

1. **Multimodal Input**:
   - Text chat through an interactive Streamlit UI.
   - Image uploads (`.png`, `.jpg`, `.jpeg`, `.webp`) with vision model analysis.
   - Document uploads (`.pdf`, `.txt`, `.docx`, `.md`) with text extraction and automatic RAG indexing.
   - Audio file uploads (`.mp3`, `.wav`, `.m4a`, `.ogg`, `.webm`) with Whisper Speech-to-Text transcription.
   - Input validation for file types and maximum file size (default 10 MB).

2. **Multimodal Output**:
   - Structured markdown text responses.
   - Text-to-Speech (TTS) audio synthesis with in-browser audio player.
   - Image generation (DALL-E) from text prompts.
   - Clear and informative explanations when an API key is not configured.

3. **Live Web Search**:
   - Real search queries via Tavily API with zero-config DuckDuckGo live search fallback.
   - Source citations with titles, URLs, snippets, and dates.
   - Strict separation between sourced facts and AI reasoning.

4. **Retrieval-Augmented Generation (RAG)**:
   - Automated text cleaning and semantic chunking.
   - High-dimensional vector embeddings.
   - PostgreSQL/pgvector similarity search (with exact cosine similarity fallback).
   - Grounded context synthesis with document name and passage citations.
   - Clear fallback message when no relevant passages match.

5. **Document Lifecycle Management**:
   - Author new text documents directly in the UI.
   - View, edit, and update document content.
   - Automatic re-indexing and chunk invalidation upon editing.
   - Download stored documents.
   - Delete documents with chunk cleanup and file removal.

6. **Personal Emotional Assistance**:
   - Warm, empathetic active listening without judgment.
   - Practical grounding exercises (5-4-3-2-1 sensory grounding, 4-4-4-4 box breathing).
   - Reflective journaling prompts.
   - Strict safety disclaimers: AI is not a therapist or doctor.
   - Immediate crisis redirection (988 Lifeline, Crisis Text Line 741741) when self-harm or danger is detected.

### MVP Limitations

- Designed for local development and demonstration; does not include user authentication or role-based access control.
- Rate limits are governed by configured provider tiers (OpenAI / Gemini / Tavily).

---

## Technology Stack

- **Backend Framework:** FastAPI (Python 3.10+)
- **Frontend Framework:** Streamlit
- **Relational & Vector Database:** PostgreSQL with `pgvector` (with automatic fallback to local SQLite for zero-setup local dev/test)
- **ORM & Data Access:** SQLAlchemy 2.0
- **Data Validation:** Pydantic v2
- **Document Extractors:** `pypdf`, `python-docx`
- **AI & Model Providers:**
  - OpenAI API (`gpt-4o-mini`, `text-embedding-3-small`, `dall-e-3`, `whisper-1`, `tts-1`)
  - Google Gemini API (`gemini-1.5-flash`, `text-embedding-004`)
  - Speech synthesis fallback: `gTTS`
- **Web Search Providers:** Tavily API & DuckDuckGo Search
- **Test Suite:** `pytest`, `httpx`

---

## Architecture & Data Flow

```
┌────────────────────────────────────────────────────────┐
│                   Streamlit Frontend                   │
│   (Chat Hub, Document Management, Multimodal Studio)   │
└───────────────────────────┬────────────────────────────┘
                            │ REST API (JSON / Multipart)
                            ▼
┌────────────────────────────────────────────────────────┐
│                   FastAPI Backend                      │
│   (Pydantic Schemas, CORS, Static Media Mounting)      │
└───────────────────────────┬────────────────────────────┘
                            │ Service Orchestration
   ┌────────────────────────┼────────────────────────┐
   ▼                        ▼                        ▼
┌───────────────┐  ┌───────────────────┐  ┌─────────────────────┐
│  Chat Service │  │    RAG Service    │  │ Web Search Service  │
│(OpenAI/Gemini)│  │(Chunk, Embed, Sim)│  │ (Tavily/DuckDuckGo) │
└───────┬───────┘  └────────┬──────────┘  └─────────────────────┘
        │                   │
        ▼                   ▼
┌───────────────┐  ┌───────────────────────────────────────────┐
│ Multimodal &  │  │            SQLAlchemy Repository          │
│ Audio Service │  │  (Conversations, Messages, Documents,     │
│(Vision/DALL-E/│  │   Document Chunks & Vector Embeddings)    │
│ Whisper/TTS)  │  └─────────────────────┬─────────────────────┘
└───────────────┘                        │
                                         ▼
                            ┌────────────────────────┐
                            │ PostgreSQL + pgvector  │
                            │  (or SQLite fallback)  │
                            └────────────────────────┘
```

---

## Project Folder Structure

```
MM chatbot - antigravity/
├── backend/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application entrypoint
│   ├── api/                        # REST endpoint routers
│   │   ├── __init__.py
│   │   ├── health.py               # Health check and system status
│   │   ├── chat.py                 # Conversational messaging & sessions
│   │   ├── documents.py            # Document CRUD, upload & download
│   │   ├── rag.py                  # RAG grounded search & indexing
│   │   ├── search.py               # Live web search endpoint
│   │   ├── multimodal.py           # Vision analysis & image generation
│   │   └── audio.py                # Audio transcription & TTS
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py               # Environment configuration with Pydantic
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py           # Engine setup, session & fallback
│   │   ├── models.py               # SQLAlchemy ORM models
│   │   └── repository.py           # CRUD operations
│   ├── schemas/                    # Pydantic request & response models
│   │   ├── common.py
│   │   ├── chat.py
│   │   ├── document.py
│   │   ├── rag.py
│   │   ├── search.py
│   │   └── multimodal.py
│   └── services/                   # Business and AI logic
│       ├── __init__.py
│       ├── chat_service.py
│       ├── document_service.py
│       ├── extractor.py
│       ├── rag_service.py
│       ├── web_search_service.py
│       ├── multimodal_service.py
│       ├── audio_service.py
│       └── emotional_support_service.py
├── frontend/
│   ├── app.py                      # Main Streamlit web application
│   └── components/
│       ├── __init__.py
│       ├── chat_ui.py              # Message rendering, cards, audio players
│       ├── documents_ui.py         # Document manager UI (create/edit/delete)
│       ├── multimodal_ui.py        # Vision, DALL-E, Whisper, TTS controls
│       └── settings_ui.py          # System status pill & diagnostics
├── tests/                          # Automated Pytest suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_chat.py
│   ├── test_documents.py
│   ├── test_rag.py
│   ├── test_search.py
│   └── test_multimodal.py
│   └── test_emotional.py
├── .env.example                    # Sample environment variables
├── .env                            # Active environment configuration
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Prerequisites

- **Python:** Version 3.10 or higher.
- **Database:** PostgreSQL (v14+ recommended) with the `pgvector` extension.
  - *Note:* If PostgreSQL is not yet installed on your system, the application will automatically log a notice and fall back to local SQLite (`chatbot_local.db`) so you can test and explore immediately without installation blockers.
- **API Keys (Optional but recommended):**
  - OpenAI API Key (for GPT-4o, DALL-E, Whisper, TTS, Embeddings)
  - Tavily Search API Key (for advanced web search; DuckDuckGo works out of the box without keys)
  - Google Gemini API Key (if `AI_PROVIDER=gemini` is selected)

---

## PostgreSQL & pgvector Setup

### 1. Install PostgreSQL and pgvector
On Windows, you can install PostgreSQL from [postgresql.org](https://www.postgresql.org/download/windows/) and pgvector via:
```powershell
# Or using Docker:
docker run -d --name postgres-vector -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=multimodal_chatbot pgvector/pgvector:pg16
```

### 2. Enable pgvector Extension
Connect to your database in psql:
```sql
CREATE DATABASE multimodal_chatbot;
\c multimodal_chatbot;
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## Virtual Environment & Dependency Installation

1. **Create Virtual Environment:**
   ```powershell
   python -m venv venv
   ```

2. **Activate Environment:**
   ```powershell
   # Windows PowerShell
   .\venv\Scripts\Activate.ps1
   # Linux / macOS
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

---

## Configuration (`.env`)

Copy the example environment file:
```powershell
copy .env.example .env
```

Edit `.env` with your preferred settings and API credentials:
```env
# Application Settings
APP_NAME="Multimodal AI Chatbot"
DEBUG=true
PORT=8000
HOST=127.0.0.1
BACKEND_URL=http://127.0.0.1:8000

# Database Configuration (PostgreSQL)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/multimodal_chatbot

# AI Model Provider ("openai" or "gemini")
AI_PROVIDER=openai

# OpenAI Configuration
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_IMAGE_MODEL=dall-e-3
OPENAI_TTS_MODEL=tts-1
OPENAI_WHISPER_MODEL=whisper-1

# Optional Gemini Configuration
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-flash
GEMINI_EMBEDDING_MODEL=models/text-embedding-004

# Optional Tavily Search API (DuckDuckGo works as free fallback)
TAVILY_API_KEY=
```

---

## Running the Application

### 1. Start the FastAPI Backend
Open a terminal in the project root and run:
```powershell
.\venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive API Docs (Swagger UI): **http://127.0.0.1:8000/docs**
- Health status check: **http://127.0.0.1:8000/api/health**

### 2. Start the Streamlit Frontend
In a second terminal, run:
```powershell
.\venv\Scripts\python.exe -m streamlit run frontend/app.py
```
Streamlit will launch in your browser at **http://localhost:8501**.

---

## API Endpoint Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | System diagnostics, database type, and provider status |
| `POST` | `/api/chat/message` | Send message in a conversation session |
| `GET` | `/api/chat/conversations` | List recent conversation sessions |
| `GET` | `/api/chat/conversations/{id}` | Retrieve conversation message history |
| `DELETE` | `/api/chat/conversations/{id}/messages` | Clear messages in conversation |
| `DELETE` | `/api/chat/conversations/{id}` | Delete conversation and messages |
| `POST` | `/api/documents` | Create an editable text document |
| `POST` | `/api/documents/upload` | Upload `.pdf`, `.docx`, `.txt`, `.md` file |
| `GET` | `/api/documents` | List stored documents and chunk counts |
| `GET` | `/api/documents/{id}` | Get full document details |
| `PUT` | `/api/documents/{id}` | Update document title/content & re-index RAG |
| `DELETE` | `/api/documents/{id}` | Delete document, file, and embeddings |
| `GET` | `/api/documents/{id}/download` | Download document file |
| `POST` | `/api/rag/query` | Perform vector similarity search & grounded answer |
| `POST` | `/api/rag/index/{id}` | Trigger re-chunking and embedding generation |
| `POST` | `/api/search/query` | Live web search with sourced citations |
| `POST` | `/api/multimodal/vision` | Analyze uploaded image with vision AI |
| `POST` | `/api/multimodal/generate-image` | Generate image with DALL-E |
| `POST` | `/api/audio/transcribe` | Transcribe audio file to text with Whisper |
| `POST` | `/api/audio/tts` | Convert text to speech audio file |
| `POST` | `/api/emotional/respond` | Personal emotional assistance with safety checks |

---

## RAG Workflow Explained

1. **Ingestion & Extraction:** Uploaded `.pdf`, `.docx`, `.txt`, or `.md` files are parsed via `DocumentExtractor`, removing invalid characters and formatting whitespace.
2. **Chunking:** `RAGService.chunk_text` partitions text into overlapping segments (default 600 characters with 100 character overlap) to preserve sentence and paragraph context.
3. **Embeddings:** Each chunk is converted into an embedding vector via OpenAI (`text-embedding-3-small`) or Gemini (`text-embedding-004`).
4. **Storage:** Chunks and embeddings are stored with foreign keys to their parent document.
5. **Retrieval:** When a user queries in RAG mode, the query embedding is compared against stored chunks using vector similarity.
6. **Grounding:** The top relevant chunks are formatted into a strict system prompt instructing the model to answer using only verified passages.
7. **Attribution:** The response lists citations containing the document title, snippet, and similarity score.
8. **Invalidation:** Whenever a document is edited or deleted, old chunks are automatically purged and regenerated so RAG never serves stale data.

---

## Testing Instructions

The project includes an automated test suite covering all endpoints, database operations, RAG similarity math, and safety heuristics.

Run the full test suite:
```powershell
.\venv\Scripts\python.exe -m pytest tests/ -v
```

All 20 test cases will execute:
```
tests/test_chat.py::test_send_chat_message_creates_conversation PASSED
tests/test_chat.py::test_clear_and_delete_conversation PASSED
tests/test_documents.py::test_create_and_get_document PASSED
tests/test_documents.py::test_update_document_refreshes_chunks PASSED
tests/test_documents.py::test_upload_and_download_document PASSED
tests/test_documents.py::test_delete_document PASSED
tests/test_emotional.py::test_emotional_crisis_detection_heuristic PASSED
tests/test_emotional.py::test_emotional_crisis_intervention_endpoint PASSED
tests/test_emotional.py::test_everyday_emotional_support_endpoint PASSED
tests/test_health.py::test_health_check_endpoint PASSED
tests/test_multimodal.py::test_vision_endpoint_upload PASSED
tests/test_multimodal.py::test_image_generation_notice_without_key PASSED
tests/test_multimodal.py::test_audio_transcription_endpoint PASSED
tests/test_multimodal.py::test_text_to_speech_endpoint PASSED
tests/test_rag.py::test_chunking_logic PASSED
tests/test_rag.py::test_cosine_similarity PASSED
tests/test_rag.py::test_rag_query_fallback_when_empty PASSED
tests/test_rag.py::test_rag_indexing_and_retrieval_flow PASSED
tests/test_search.py::test_web_search_with_mocked_results PASSED
tests/test_search.py::test_web_search_empty_fallback PASSED
```

---

## Common Errors & Troubleshooting

1. **"PostgreSQL is unreachable / falling back to SQLite":**
   - Ensure the PostgreSQL service is running on `localhost:5432`.
   - Check username/password in `DATABASE_URL` in `.env`.
   - The app continues running safely on SQLite if PostgreSQL is not active.

2. **"OpenAI API key is not configured":**
   - Ensure you copied `.env.example` to `.env`.
   - Add your OpenAI API key starting with `sk-`.
   - Restart the FastAPI server so environment variables reload.

3. **"Directory './uploads' does not exist":**
   - The application automatically ensures `./uploads` and `./generated_media` directories exist upon startup.

4. **"pgvector extension is not available":**
   - If PostgreSQL does not have the `vector` extension compiled, the app automatically switches to numpy cosine similarity calculation without errors.

---

## Security Considerations

- **No Exposed Secrets:** API keys and connection strings remain strictly on the backend and in `.env`. They are never sent to the browser or frontend state.
- **Filename Sanitization:** Uploaded filenames are sanitized with regex to eliminate path traversal (`../`) vulnerabilities.
- **File Upload Limits:** File size is strictly enforced (10 MB maximum).
- **Untrusted Content Isolation:** RAG and Web Search content are clearly framed in delimiters so the LLM treats document content as data, not instruction.
- **Error Shielding:** Internal server exceptions return sanitized messages without leaking stack traces or connection credentials.

---

## Future Enhancements

- Real-time streaming responses via Server-Sent Events (SSE) or WebSockets.
- Support for additional vector engines (e.g., Qdrant, Pinecone).
- In-browser microphone audio recording using WebRTC / MediaStream API.
- Multi-user authentication and private per-user document workspaces.

