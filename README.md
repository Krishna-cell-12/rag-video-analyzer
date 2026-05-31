# 🎬 RAG Video Analyzer

> **An end-to-end AI platform that transcribes, indexes, and lets you have natural-language conversations with YouTube and Instagram video content — powered by Retrieval-Augmented Generation.**

<br>

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![LangChain](https://img.shields.io/badge/LangChain-LangGraph-1c3c3c?style=for-the-badge&logo=chainlink&logoColor=white)](https://langchain.com/)
[![Whisper](https://img.shields.io/badge/Whisper-Local_CPU-412991?style=for-the-badge&logo=openai&logoColor=white)](https://github.com/openai/whisper)

---

## 🚀 Project Overview

**RAG Video Analyzer** is a production-grade, end-to-end **Retrieval-Augmented Generation (RAG)** platform designed to bridge the gap between unstructured multimedia content and structured, queryable intelligence.

The system ingests video URLs from **YouTube** and **Instagram**, extracts and transcribes their audio entirely on-device using a **local Whisper model** (no external transcription API costs), vectorizes the resulting text through **Google Generative AI Embeddings**, and persists those vectors in a **pgvector-backed PostgreSQL** database. Users can then engage with the indexed content through a conversational AI interface powered by a **LangGraph stateful agent** — asking analytical questions, comparing creators, and extracting engagement insights in real time.

### Key Engineering Highlights

- 🧠 **Zero-cost transcription** — Whisper runs locally on CPU; no cloud transcription bills
- 🗂️ **Semantic chunking** — transcripts are split into overlapping chunks for precision retrieval
- ⚡ **Non-blocking ingestion** — vectorization runs as a FastAPI `BackgroundTask`, so the API responds instantly
- 🔐 **Anti-bot extraction** — `yt-dlp` with cookie-based authentication bypasses platform rate limiting
- 🤖 **Stateful RAG agent** — LangGraph orchestrates a multi-node workflow: routing → retrieval → generation

---

## 🛠️ Tech Stack Matrix

| Layer | Technology | Role |
|---|---|---|
| **Frontend** | Next.js 16 (Turbopack) | React framework with App Router |
| **Frontend** | TypeScript | Type-safe component development |
| **Frontend** | Tailwind CSS | Utility-first styling |
| **Backend** | FastAPI | Async REST API framework |
| **Backend** | Uvicorn (ASGI) | High-performance async server |
| **AI — Transcription** | Faster-Whisper (`base`, CPU) | Local audio-to-text transcription |
| **AI — Embeddings** | Google GenAI (`models/embedding-001`) | Text vectorization for semantic search |
| **AI — Orchestration** | LangGraph + LangChain | Stateful multi-node RAG agent |
| **AI — LLM** | Gemini 1.5 Pro | Conversational response generation |
| **Vector Storage** | PostgreSQL + pgvector | High-performance ANN similarity search |
| **Extraction** | yt-dlp + `cookies.txt` | Video audio download with auth bypass |
| **Infrastructure** | Docker Compose | PostgreSQL + pgvector containerization |

---

## 🏗️ Architecture & Data Flow

The system processes each video through a sequential, fault-tolerant pipeline before exposing it to the conversational interface.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         RAG VIDEO ANALYZER — DATA FLOW                  │
└─────────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐
  │  User UI     │  YouTube URL / Instagram URL
  │  (Next.js)   │
  └──────┬───────┘
         │  POST /api/extract
         ▼
  ┌──────────────────────┐
  │  FastAPI Backend     │  Validates & routes URL by platform
  └──────┬───────────────┘
         │
         ▼
  ┌──────────────────────┐
  │  yt-dlp Extractor    │  Downloads best-quality audio stream
  │  + cookies.txt Auth  │  Bypasses HTTP 429 / bot-detection
  └──────┬───────────────┘
         │  temp_audio.mp3
         ▼
  ┌──────────────────────┐
  │  Whisper Model       │  Local CPU transcription (beam_size=5)
  │  (faster-whisper)    │  Cleans up temp file post-transcription
  └──────┬───────────────┘
         │  Raw transcript text
         ▼
  ┌──────────────────────┐
  │  RecursiveText       │  chunk_size=400 / chunk_overlap=50
  │  Splitter            │  Attaches video metadata to each chunk
  └──────┬───────────────┘
         │  List[Document]
         ▼
  ┌──────────────────────┐
  │  Google GenAI        │  models/embedding-001
  │  Embeddings          │  Converts chunks → dense float vectors
  └──────┬───────────────┘
         │  Vector embeddings
         ▼
  ┌──────────────────────┐
  │  PostgreSQL          │  Persists vectors + metadata
  │  + pgvector          │  ANN similarity search at query time
  └──────┬───────────────┘
         │
         ▼
  ┌──────────────────────┐
  │  LangGraph Agent     │  Routes: metadata fetch OR transcript retrieval
  │  (Stateful Graph)    │  Constructs context window from top-k chunks
  └──────┬───────────────┘
         │  Augmented prompt
         ▼
  ┌──────────────────────┐
  │  Gemini 1.5 Pro LLM  │  Generates grounded, cited response
  └──────┬───────────────┘
         │
         ▼
  ┌──────────────────────┐
  │  User Chat UI        │  Streamed analyst response
  └──────────────────────┘
```

---

## 📁 Repository Structure

```
rag-video-analyzer/
│
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, route registration
│   │   ├── core/
│   │   │   └── config.py        # Pydantic settings — loads .env
│   │   ├── models/
│   │   │   └── video.py         # VideoMetadata, ExtractionRequest schemas
│   │   └── services/
│   │       ├── ingestion.py     # VideoExtractor — yt-dlp + Whisper pipeline
│   │       ├── vector_store.py  # VectorService — chunking + pgvector writes
│   │       └── chatbot.py       # VideoChatAgent — LangGraph RAG agent
│   │
│   ├── venv/                    # Python virtual environment (git-ignored)
│   ├── requirements.txt         # All Python dependencies
│   ├── cookies.txt              # yt-dlp Netscape cookie file (git-ignored)
│   └── .env                     # Secret keys (git-ignored)
│
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js App Router pages
│   │   ├── components/          # React UI components
│   │   └── ui/                  # Shared design system primitives
│   ├── package.json
│   ├── postcss.config.mjs       # PostCSS with autoprefixer
│   └── tailwind.config.ts       # Tailwind configuration
│
└── README.md
```

---

## ⚙️ Installation & Setup Guide

> **Environment:** WSL2 / Linux (Ubuntu 22.04+). Ensure `python3.12`, `node 20+`, `ffmpeg`, and `docker` are installed.

---

### Step 1 — Infrastructure: Start PostgreSQL + pgvector

```bash
# From the project root
cd backend
docker compose up -d
```

This spins up a PostgreSQL instance with the `pgvector` extension pre-enabled. Verify it's healthy:

```bash
docker compose ps
# Expected: Status = Up (healthy)
```

---

### Step 2 — Backend Setup

```bash
# Navigate to the backend directory
cd backend

# Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

**Configure environment variables:**

```bash
# Create the .env file
touch .env
```

Open `.env` and populate with your credentials:

```env
PROJECT_NAME="Video RAG API"
DATABASE_URL="postgresql://admin:adminpassword@localhost:5432/video_rag"
GEMINI_API_KEY="your_google_ai_studio_api_key_here"
OPENAI_API_KEY="your_openai_api_key_here"
```

> **Where to get keys:**
> - Gemini API Key → [Google AI Studio](https://aistudio.google.com/app/apikey)
> - OpenAI API Key → [OpenAI Platform](https://platform.openai.com/api-keys)

**Configure YouTube cookie authentication** *(required to avoid HTTP 429 blocks)*:

```bash
# Export cookies from your browser using a tool like:
# Chrome extension: "Get cookies.txt LOCALLY"
# Place the exported Netscape-format file at:
backend/cookies.txt
```

**Start the backend server:**

```bash
uvicorn app.main:app --port 8000 --reload
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

API documentation is auto-generated at: **`http://localhost:8000/docs`**

---

### Step 3 — Frontend Setup

Open a **new terminal tab** and run:

```bash
# Navigate to the frontend directory
cd frontend

# Install Node dependencies
npm install

# Start the development server (Turbopack)
npm run dev
```

The UI will be available at: **`http://localhost:3000`**

---

### Step 4 — Using the Application

1. Open **`http://localhost:3000`** in your browser
2. Paste a **YouTube URL** into the *Video A* field
3. Paste an **Instagram URL** (or second YouTube URL) into the *Video B* field
4. Click **Analyze Videos** — extraction and transcription will begin
5. Once complete, use the **Analyst Chat** panel to ask questions:
   - *"Compare the hooks used in the first 10 seconds of each video"*
   - *"Which creator has a higher engagement rate and why?"*
   - *"Summarize the key talking points of Video A"*

---

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check — returns server + DB status |
| `POST` | `/api/extract` | Trigger video extraction and vectorization |
| `POST` | `/api/chat` | Send a message to the RAG chat agent |

**`POST /api/extract` — Request Body:**
```json
{
  "url_a": "https://www.youtube.com/watch?v=VIDEO_ID",
  "url_b": "https://www.instagram.com/reel/REEL_ID/"
}
```

**`POST /api/chat` — Request Body:**
```json
{
  "messages": [
    { "role": "user", "content": "Compare the engagement of both videos" }
  ],
  "video_ids": ["VIDEO_ID_A", "VIDEO_ID_B"]
}
```

---

## 🛡️ Production & Troubleshooting Log

The following engineering issues were encountered and resolved during development. Documented here for future maintainability.

---

### 🔴 Issue A — PostCSS Configuration Cascade Failure

**Symptom:** Frontend build failed immediately on `npm run dev` with:
```
Error: Cannot find module 'autoprefixer'
PostCSS config mismatch — plugin resolution failure
```

**Root Cause:** Next.js 16 with Turbopack requires explicit `autoprefixer` registration in `postcss.config.mjs`. The default scaffold omits it when Tailwind is installed independently.

**Resolution:**
```bash
npm install autoprefixer --save-dev
```
`postcss.config.mjs` aligned to:
```js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

---

### 🔴 Issue B — Embedding Model 404 (API Version Mismatch)

**Symptom:** Background vectorization task crashed with:
```
google.genai.errors.ClientError: 404 NOT_FOUND
'models/text-embedding-004 is not found for API version v1beta'
```

**Root Cause:** The `langchain-google-genai` package internally routes embedding requests through the **`v1beta`** API surface. Google's `v1beta` endpoint does not support the newer `text-embedding-004` variant, causing a silent 404 on every vectorization call.

**Resolution:** Centralized all embedding calls — both ingest pipeline (`vector_store.py`) and retrieval layer (`chatbot.py`) — on the stable **`models/embedding-001`** infrastructure, which is fully supported across all API versions:

```python
# Both vector_store.py and chatbot.py use identical model config:
self.embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=settings.GEMINI_API_KEY
)
```

> **Critical:** Both services **must** use the same embedding model. Mismatched models produce vectors of different dimensionality or semantic space — similarity search will silently return incorrect results.

---

### 🔴 Issue C — YouTube HTTP 429 Rate Limiting / Bot Detection

**Symptom:** Every `yt-dlp` extraction attempt failed with:
```
ERROR: [youtube] Sign in to confirm you're not a bot.
WARNING: HTTP Error 429: Too Many Requests
```

**Root Cause:** YouTube's bot-detection system flags unauthenticated, headless download attempts — particularly from server environments and WSL2 network interfaces. Standard IP rotation is insufficient as YouTube also fingerprints request headers and session state.

**Resolution — Two-pronged approach:**

1. **Clean network routing** — Switching to a mobile hotspot network route bypasses IP-level throttling applied to residential/datacenter ranges that have exceeded YouTube's anonymous request quota.

2. **Cookie-based session authentication** — The `yt-dlp` initialization layer now loads a `cookies.txt` file (Netscape format) exported from a logged-in browser session. This passes a valid authenticated session to every request, making extraction indistinguishable from organic browser traffic:

```python
ydl_opts = {
    'cookiefile': 'cookies.txt',  # Authenticated session bypass
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ...'
    },
    'retries': 5,
    'sleep_interval': 3,
    ...
}
```

**To export cookies:**
- Install the **"Get cookies.txt LOCALLY"** Chrome extension
- Navigate to `youtube.com` while logged in
- Export → save as `backend/cookies.txt`
- Restart the backend server

> ⚠️ **Never commit `cookies.txt` to version control.** It contains your authenticated session tokens. Ensure it is listed in `.gitignore`.

---

## 🔒 Security & .gitignore Checklist

Ensure the following are **never committed** to your repository:

```gitignore
# backend/.gitignore
.env
cookies.txt
venv/
__pycache__/
*.pyc

# frontend/.gitignore
node_modules/
.next/
.env.local
```

---

## 📄 License

This project is licensed under the **MIT License**. See [`LICENSE`](./LICENSE) for details.

---

<div align="center">

**Built with precision. Engineered for scale.**

*RAG Video Analyzer — turning passive video content into active, queryable intelligence.*

</div>
