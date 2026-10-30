# System Specification: Multimodal AI Chatbot
**Module 3 Benchmark:** *Build a Multimodal Chatbot with Antigravity*  
**Document Version:** 1.0.0  
**Status:** Implemented & Verified with Automated Test Suite (26 Passing Tests)

---

## 1. Project Overview and Purpose

The **Multimodal AI Chatbot** is a beginner-friendly, modular, full-stack conversational application built with **FastAPI**, **Streamlit**, and **PostgreSQL** (with **pgvector** and a zero-config SQLite fallback).

The primary purpose of the application is to demonstrate end-to-end multimodal AI interaction:
1. Ingesting and processing multiple sensory inputs (**text**, **vision/images**, and **spoken audio**).
2. Synthesizing grounded, coherent responses (**text answers**, **audio speech playback**, and **generated images**).
3. Providing deep knowledge retrieval via **Retrieval-Augmented Generation (RAG)** and **live web searching**.
4. Providing supportive, non-clinical **personal emotional assistance** equipped with safety boundaries and crisis redirection.

---

## 2. Goals and Scope

### Goals
- **Full Multimodal Coverage:** Provide unified conversational support across text, images, and audio without fragile hacks.
- **Architectural Decoupling:** Keep frontend UI, REST API routing, business services, AI provider SDKs, and database storage in distinct layers.
- **Robust Pre-Save Validation:** Validate file extensions, reject empty files, and enforce size limits *before* committing data to disk.
- **Resilient Degradation:** Provide clear, human-readable instructions when external API keys or database extensions are unconfigured; never simulate fake successes or crash unhandled.

### Scope Distinction: Core Lab Requirements vs. MVP Extensions

| Capability | Category | Status & Implementation |
|---|---|---|
| **Text Chat** | **Module 3 Core** | Implemented via `/api/chat/message` with conversation session history. |
| **Image Vision Input** | **Module 3 Core** | Implemented via `/api/multimodal/vision` supporting `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`. |
| **Audio File Input (STT)** | **Module 3 Core** | Implemented via `/api/audio/transcribe` and `/api/audio/query` supporting `.mp3`, `.wav`, `.m4a`, `.ogg`, `.webm`. |
| **Text AI Response** | **Module 3 Core** | Implemented with OpenAI (`gpt-4o-mini`) and Gemini (`gemini-1.5-flash`) orchestration. |
| **Browser Live Mic Recording** | **Optional** | Marked as optional; audio file upload is the primary supported mechanism. |
| **Document RAG Pipeline** | Extended Feature | Implemented via `/api/rag/query` with semantic chunking and pgvector/cosine retrieval. |
| **Document Management** | Extended Feature | Implemented via `/api/documents` (CRUD, upload, edit, download, automatic re-indexing). |
| **Live Web Search** | Extended Feature | Implemented via `/api/search/query` using Tavily API with DuckDuckGo fallback. |
| **Text-to-Speech (TTS)** | Extended Feature | Implemented via `/api/audio/tts` with OpenAI TTS-1 and local zero-cost `gTTS` fallback. |
| **Image Generation** | Extended Feature | Implemented via `/api/multimodal/generate-image` using DALL-E 3. |
| **Emotional Assistance** | Extended Feature | Implemented via `/api/emotional/respond` with 988 Crisis Lifeline safety redirection. |

---

## 3. Target User and Main Use Cases

### Target User
Learners, developers, and everyday users who require an intuitive, transparent interface for interacting with multimodal AI models, managing local knowledge documents, and exploring real-time grounded search.

### Core Use Cases

- **UC-1: Standard Text Conversation**  
  *Actor:* User  
  *Flow:* User inputs text in Streamlit Chat Hub -> Backend checks whitespace -> AI generates context-aware answer -> Turn is saved in database.

- **UC-2: Image Understanding (Vision)**  
  *Actor:* User  
  *Flow:* User uploads image (`.png`, `.jpg`, etc.) + text prompt -> Backend validates extension and <= 10MB size before saving -> Vision model analyzes image features -> Analysis is displayed with thumbnail preview.

- **UC-3: Audio Voice Query (Speech-to-Text to Chatbot)**  
  *Actor:* User  
  *Flow:* User uploads spoken audio clip (`.wav`, `.mp3`, etc.) -> Backend validates size/format -> Whisper transcribes speech -> User reviews/edits transcript in UI -> Submits transcript to chatbot -> AI response is displayed and appended to conversation history without duplicate messages.

- **UC-4: Document-Grounded RAG**  
  *Actor:* User  
  *Flow:* User uploads PDF/DOCX/TXT/MD -> Backend extracts text, chunks, and indexes embeddings -> User asks question in RAG mode -> Cosine similarity finds matching passages -> LLM answers strictly using context with source attribution citations.

- **UC-5: Live Web Search**  
  *Actor:* User  
  *Flow:* User asks about current events -> Tavily/DuckDuckGo searches web -> Backend synthesizes answer citing source titles, URLs, and dates, distinguishing sourced facts from AI reasoning.

- **UC-6: Document Authoring, Editing, and Invalidation**  
  *Actor:* User  
  *Flow:* User authors or edits document in UI -> Backend updates record and immediately flushes stale chunks -> Re-indexes updated content so RAG never serves obsolete data.

- **UC-7: Personal Emotional Support with Safety Redirection**  
  *Actor:* User  
  *Flow:* User expresses stress, sadness, or journaling thoughts -> System provides active listening and grounding exercises (box breathing, 5-4-3-2-1 technique). If suicidal intent or self-harm keywords are detected, the system immediately diverts to the **988 Suicide & Crisis Lifeline** and **Crisis Text Line (741741)** without attempting amateur therapy.

---

## 4. Required Inputs and Outputs

### Supported Inputs
1. **Text Input:**
   - UTF-8 string input through Streamlit chat input or text areas.
   - Enforced validation: Non-empty, minimum length 1, whitespace-only messages strictly rejected.
2. **Image Input:**
   - Supported extensions: `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`.
   - File size ceiling: Enforced at maximum 10 MB.
   - Rejection: Empty (0-byte) files and unsupported extensions rejected with `400 Bad Request` before disk writes.
3. **Audio Input:**
   - Supported extensions: `.mp3`, `.wav`, `.m4a`, `.ogg`, `.webm`.
   - File size ceiling: Enforced at maximum 10 MB.
   - Rejection: Empty (0-byte) files and non-audio formats rejected with `400 Bad Request` before processing.
   - *Note on Browser Live Recording:* Browser-based WebRTC microphone capture is documented as an optional enhancement; audio file upload is the primary supported MVP mechanism.
4. **Document Input:**
   - Supported extensions: `.pdf`, `.docx`, `.txt`, `.md`.
   - File size ceiling: Enforced at maximum 10 MB.

### Supported Outputs
1. **Text Responses:** Markdown-formatted text responses with role avatars (🧑 User, 🤖 AI, 🌿 Emotional, 🔍 Search, 📚 RAG).
2. **Audio Output:** Text-to-Speech synthesized audio (`.mp3`) with embedded HTML5 browser playback controls.
3. **Image Output:** High-resolution image generation (DALL-E) saved locally and previewed in chat cards.
4. **Citations & Sources:** Expandable source cards displaying document titles, passage snippets, similarity scores, and web URLs with publish dates.
5. **Human-Readable Diagnostics:** Structured notifications guiding the user when external API keys (OpenAI, Gemini, Tavily) are absent.

---

## 5. Functional Requirements

- **FR-1 (Multimodal Routing):** The backend MUST route text, vision, and audio requests to isolated domain services.
- **FR-2 (Pre-Save File Validation):** File validation for format, emptiness, and file size MUST execute before files are written to disk or sent to external APIs.
- **FR-3 (Filename Sanitization):** All uploaded filenames MUST be stripped of directory traversal tokens (`../`) and dangerous characters using `sanitize_filename`.
- **FR-4 (Input Sanitation):** Empty or whitespace-only messages MUST be rejected by Pydantic validators (`422 Unprocessable Entity`) and intercepted by the frontend.
- **FR-5 (Audio-to-Chat Flow):** The application MUST allow transcribed audio text to be reviewed, edited, submitted to `/api/chat/message`, and rendered with the assistant's reply while preventing duplicate submissions.
- **FR-6 (RAG Pipeline Integrity):** Uploaded documents MUST be chunked recursively (600 characters, 100 character overlap), embedded, and queried using vector similarity. If no passages match the cutoff threshold, a friendly fallback message MUST be returned.
- **FR-7 (Document Invalidation):** Updating or deleting a document MUST automatically delete associated chunks and embeddings to eliminate stale RAG retrievals.
- **FR-8 (Web Search Grounding):** Web search queries MUST retrieve live snippets and produce answers citing titles, URLs, and dates while separating facts from AI conjecture.
- **FR-9 (Crisis Safety Guardrail):** Emotional assistance queries MUST be screened for self-harm keywords. Any detection MUST bypass standard LLM output and return verified crisis helpline contacts (988 Lifeline, 741741 Crisis Text Line).
- **FR-10 (Session Persistence):** All conversation turns, user inputs, assistant responses, citations, and media links MUST be persisted to the relational database.

---

## 6. Non-Functional Requirements

- **NFR-1 (Modularity):** Provider-specific logic (OpenAI, Gemini, Tavily, DuckDuckGo) MUST be decoupled in `backend/services/` so providers can be swapped without rewriting routers or UI.
- **NFR-2 (Resilience & Graceful Degradation):** Missing API keys or uninstalled database extensions MUST NOT crash the server. Informative warnings must be returned.
- **NFR-3 (Timeout Handling):** External API calls MUST enforce reasonable timeouts (30s for TTS, 45s for audio/vision, 60s for chat/RAG).
- **NFR-4 (Error Shielding):** Unhandled server exceptions MUST return sanitized JSON (`500 Internal Server Error`) to prevent leaking internal stack traces or database connection strings.
- **NFR-5 (Cross-Platform Execution):** The application MUST run cleanly on Python 3.10+ across Windows, macOS, and Linux.

---

## 7. Technology Stack and Architecture

```
┌────────────────────────────────────────────────────────┐
│                   Streamlit Frontend                   │
│   (Chat Hub, Document Management, Multimodal Studio)   │
└───────────────────────────┬────────────────────────────┘
                            │ REST API (HTTP JSON / Multipart)
                            ▼
┌────────────────────────────────────────────────────────┐
│                   FastAPI Backend                      │
│      (Pydantic v2 Schemas, CORS, Static Media)         │
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

- **Backend Framework:** FastAPI (`0.114.2`), Uvicorn (`0.31.1`)
- **Frontend Framework:** Streamlit (`1.39.1`)
- **Database & Vector Layer:** SQLAlchemy 2.0 with PostgreSQL/pgvector support (`psycopg2-binary`, `pgvector`) and local SQLite engine fallback.
- **Document Extractors:** `pypdf` (`6.21.4`), `python-docx` (`1.2.0`)
- **AI Providers:** OpenAI (`gpt-4o-mini`, `text-embedding-3-small`, `dall-e-3`, `whisper-1`, `tts-1`), Google Gemini (`gemini-1.5-flash`), `gTTS` fallback.
- **Search Providers:** `tavily-python`, `duckduckgo-search`
- **Testing:** `pytest` (`8.2.2`), `httpx` (`0.28.1`)

---

## 8. API Key and Secret Management

- **Server-Side Exclusivity:** All API keys (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `TAVILY_API_KEY`) and database credentials exist strictly on the backend via environment variables.
- **No Client Exposure:** API keys are never forwarded to the Streamlit UI, never stored in browser cookies/sessionStorage, and never included in HTTP response payloads.
- **Git Exclusion:**
  - `.env` is explicitly declared in `.gitignore` and verified untracked by `git ls-files .env`.
  - `.env.example` contains only blank placeholders without sensitive data.
  - Generated audio files and uploaded media are excluded from Git tracking.

---

## 9. File Upload Validation and Privacy

- **Pre-Storage Inspection:** Uploaded files are checked for allowed extensions and size limits before saving to disk.
- **Whitelist Enforcement:**
  - Images: `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`
  - Audio: `.mp3`, `.wav`, `.m4a`, `.ogg`, `.webm`
  - Documents: `.txt`, `.md`, `.pdf`, `.docx`
- **Size Limits:** Enforced at 10 MB (`MAX_UPLOAD_SIZE_MB = 10`). Violations immediately return `413 Payload Too Large`.
- **Emptiness Check:** 0-byte uploads return `400 Bad Request`.
- **Path Traversal Protection:** Filenames are sanitized via `sanitize_filename`, which strips directory traversal tokens (`../`) and illegal characters.
- **Privacy Boundary:** Sensitive personal expressions in **Emotional Assistance** mode are strictly kept in the local conversation container and are never forwarded to external search engines or third-party web scrapers.

---

## 10. Error Handling and User Feedback

- **Standard HTTP Codes:**
  - `400 Bad Request`: Unsupported file formats, empty files, or invalid requests.
  - `413 Payload Too Large`: Files exceeding the 10 MB ceiling.
  - `422 Unprocessable Entity`: Empty or whitespace-only messages.
  - `404 Not Found`: Non-existent conversations or documents.
  - `500 Internal Server Error`: Sanitized catch-all that logs details server-side while presenting a clean error to the client.
- **UI Alerts:** Streamlit visual feedback pills (`st.warning`, `st.error`, `st.info`) translate technical errors into actionable, plain-English instructions.
- **Missing Key Guidance:** If a user attempts to call OpenAI or Gemini without an active key, the system provides explicit setup instructions rather than throwing an unhandled exception.

---

## 11. Accessibility and Usability

- **Intuitive Visual Hierarchy:** Divided into three dedicated tabs: **Chat Hub**, **Document Management**, and **Multimodal Studio**.
- **Role Avatars & Badges:** Distinct avatars clarify the active persona (🧑 User, 🤖 AI, 🌿 Emotional, 🔍 Search, 📚 RAG).
- **Auditory Accessibility:** The integrated **Text-to-Speech (TTS)** engine provides an audio player allowing users to listen to AI responses aloud.
- **Clear Chat & Reset:** A one-click sidebar button allows users to immediately clear active chat sessions.

---

## 12. Testing and Acceptance Criteria

The system is validated through **26 automated pytest cases**:

| Test Group | Test Case Name | Verified Behavior |
|---|---|---|
| **Health** | `test_health_check_endpoint` | Verifies `/api/health` returns status, DB engine info, and provider readiness. |
| **Chat** | `test_send_chat_message_creates_conversation` | Verifies conversation creation and message persistence. |
| **Chat** | `test_clear_and_delete_conversation` | Verifies clearing messages and deleting conversation records. |
| **Chat** | `test_reject_empty_and_whitespace_chat_messages` | Verifies empty and spaces-only inputs are rejected with 422. |
| **Documents** | `test_create_and_get_document` | Verifies document authoring, persistence, and chunk indexing. |
| **Documents** | `test_update_document_refreshes_chunks` | Verifies content updates purge stale chunks and re-index. |
| **Documents** | `test_upload_and_download_document` | Verifies uploading `.txt` files and downloading exact bytes. |
| **Documents** | `test_delete_document` | Verifies document deletion cascades to chunks and disk files. |
| **RAG** | `test_chunking_logic` | Verifies text is split on semantic boundaries with overlap. |
| **RAG** | `test_cosine_similarity` | Verifies identical vectors return 1.0 and orthogonal return 0.0. |
| **RAG** | `test_rag_query_fallback_when_empty` | Verifies fallback notice when no documents match query. |
| **RAG** | `test_rag_indexing_and_retrieval_flow` | Verifies document retrieval and source attribution formatting. |
| **Search** | `test_web_search_with_mocked_results` | Verifies grounded answers with title, URL, and snippet citations. |
| **Search** | `test_web_search_empty_fallback` | Verifies graceful fallback message when search results are empty. |
| **Vision** | `test_vision_endpoint_upload` | Verifies image upload, file storage, and vision response schema. |
| **Vision** | `test_vision_validation_unsupported_empty_and_oversized` | Verifies rejection of `.py` (400), 0-byte (400), and >10MB (413). |
| **Vision** | `test_image_generation_notice_without_key` | Verifies clear informational notice when DALL-E key is absent. |
| **Audio** | `test_audio_transcription_endpoint` | Verifies audio upload and transcript structure. |
| **Audio** | `test_audio_validation_unsupported_empty_and_oversized` | Verifies rejection of `.pdf` (400), 0-byte (400), and >10MB (413). |
| **Audio** | `test_audio_query_endpoint_success_with_mock` | Verifies end-to-end audio transcribe -> chat reply -> DB turn persistence. |
| **Audio** | `test_audio_transcribe_then_chat_flow` | Verifies multi-step UI flow: audio upload -> transcript -> chat message. |
| **Audio** | `test_audio_query_endpoint_transcription_failure` | Verifies 400 error when transcription fails. |
| **Audio** | `test_text_to_speech_endpoint` | Verifies speech synthesis creates `.mp3` and returns playback URL. |
| **Emotional**| `test_emotional_crisis_detection_heuristic` | Verifies crisis keyword detection flags self-harm while passing stress. |
| **Emotional**| `test_emotional_crisis_intervention_endpoint` | Verifies immediate 988 Lifeline and Crisis Text Line redirect. |
| **Emotional**| `test_everyday_emotional_support_endpoint` | Verifies everyday stress receives empathetic non-crisis support. |

---

## 13. Known Limitations and Unverified Features

To maintain transparency, the following technical limitations and environment-dependent characteristics are documented:

1. **Live Paid API Provider Execution:**
   - Automated tests verify schemas, fallbacks, and mocked external provider responses.
   - Live end-to-end vision analysis, DALL-E image generation, Whisper transcription, and live LLM replies depend on inserting active paid API keys (`OPENAI_API_KEY` or `GEMINI_API_KEY`) into `.env`.
2. **PostgreSQL & pgvector Live Server Verification:**
   - The application has been verified against the local SQLite fallback engine.
   - Connection logic for PostgreSQL and pgvector is implemented in `connection.py` and `models.py`, but has not been verified against an active PostgreSQL instance on this host.
3. **Browser Live Audio Recording:**
   - Browser-based microphone capture (via WebRTC/MediaStream) is documented as an optional enhancement and is not currently implemented in the Streamlit UI. Audio file upload is the supported mechanism.
4. **Streaming Responses:**
   - The MVP uses standard request-response HTTP cycles. Token streaming (Server-Sent Events or WebSockets) is deferred to future releases.
5. **Single-User Scope:**
   - The system is architected as an MVP local workstation application. User authentication, login sessions, and multi-tenant access control are intentionally omitted per the project brief.

