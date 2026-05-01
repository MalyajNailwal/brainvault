# 🧠 BrainVault

A local-first, personal knowledge graph powered by **RAG-Anything** and **LightRAG**. Drop documents into a folder on your Desktop and watch an interactive knowledge graph build in real time. Ask questions about your documents via chat — all running locally on your machine.

![Architecture](https://raw.githubusercontent.com/HKUDS/RAG-Anything/main/assets/rag_anything_framework.png)

---

## ✨ Features

- **📁 Auto-watching Vault** — Drop files into `~/Desktop/BrainVault` and they auto-process
- **🧠 Live Knowledge Graph** — Visualize entities and relationships in an interactive force graph
- **💬 Multimodal Chat** — Ask questions about text, images, tables, and equations
- **🔌 Real-time Updates** — WebSocket pushes graph changes instantly to the UI
- **🚫 No Database** — JSON file registry for deduplication, localStorage for chat history
- **🪟 Cross-platform** — Works on **macOS** and **Windows**

---

## 🏗️ Architecture

```
┌─────────────┐     WebSocket      ┌─────────────────┐
│  React UI   │ ◄────────────────► │  FastAPI        │
│  (3 panels) │                    │  + Watchdog     │
└─────────────┘                    └─────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    ▼                    ▼                    ▼
              ┌─────────┐        ┌─────────────┐      ┌──────────┐
              │  Vault  │        │ RAG-Anything│      │  Graph   │
              │  Folder │        │  + LightRAG │      │  Storage │
              └─────────┘        └─────────────┘      └──────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python** 3.10+
- **Node.js** 18+ (for frontend)
- **LibreOffice** (for Office document support)

#### Install LibreOffice

**macOS:**
```bash
brew install --cask libreoffice
```

**Windows:**
Download and install from [libreoffice.org](https://www.libreoffice.org/download/download/)

---

### 1. Clone & Enter Project

```bash
git clone <your-repo-url>
cd brainvault
```

---

### 2. Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate
# macOS / Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Configure API Keys

```bash
# Edit the .env file
nano .env        # macOS / Linux
notepad .env     # Windows
```

Fill in your keys:
```env
# OpenRouter (for LLM + Vision)
OPENROUTER_API_KEY=sk-or-v1-your-key-here
LLM_MODEL=google/gemini-flash-1.5
VISION_MODEL=google/gemini-flash-1.5

# OpenAI (for Embeddings ONLY — OpenRouter has no embedding endpoint)
OPENAI_API_KEY=sk-your-openai-key-here
```

> **Where to get keys:**
> - OpenRouter: https://openrouter.ai/keys
> - OpenAI: https://platform.openai.com/api-keys

#### Start Backend Server

```bash
uvicorn main:app --reload --port 8000
```

You should see:
```
BrainVault ready. Vault: /Users/You/Desktop/BrainVault
```

---

### 3. Frontend Setup

Open a **new terminal** (keep the backend running):

```bash
cd brainvault/frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Open your browser to: **http://localhost:5173**

---

## 📂 How to Use

1. **The Vault folder** is auto-created at:
   - **macOS:** `~/Desktop/BrainVault/`
   - **Windows:** `C:\Users\You\Desktop\BrainVault\`

2. **Add documents** by either:
   - Dragging files into the left panel in the web UI
   - Copying files directly into the Desktop folder

3. **Watch the graph build** in the center panel as files are processed

4. **Chat on the right** — ask questions about your documents

### Supported File Types

| Type | Extensions |
|------|-----------|
| PDF | `.pdf` |
| Office | `.docx`, `.doc`, `.pptx`, `.ppt`, `.xlsx`, `.xls` |
| Images | `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`, `.bmp`, `.tiff` |
| Text | `.txt`, `.md` |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Server health + vault status |
| GET | `/vault/info` | List files in vault |
| POST | `/upload` | Upload files via UI |
| GET | `/graph` | Get current knowledge graph |
| POST | `/chat` | Ask a question |
| WS | `/ws` | WebSocket for live updates |

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** — REST API + native WebSocket
- **RAG-Anything** — Multimodal document parsing + knowledge graph
- **LightRAG** — Vector + graph retrieval
- **Watchdog** — File system monitoring
- **OpenRouter** — LLM + Vision models
- **OpenAI** — Text embeddings

### Frontend
- **React 18** + **Vite** + **TypeScript**
- **Tailwind CSS** — Styling
- **react-force-graph-2d** — Knowledge graph visualization
- **react-dropzone** — File drag & drop

---

## 🔧 Customization

### Change the LLM Model

Edit `backend/.env`:
```env
# Any OpenRouter model ID
LLM_MODEL=anthropic/claude-3.5-sonnet
VISION_MODEL=anthropic/claude-3.5-sonnet
```

Popular options:
- `google/gemini-flash-1.5` — Fast, cheap, multimodal
- `anthropic/claude-3.5-sonnet` — High quality reasoning
- `openai/gpt-4o-mini` — Balanced cost/quality

### Use Local Embeddings (Ollama)

```env
OPENAI_API_KEY=your-ollama-key-or-dummy
EMBED_BASE_URL=http://localhost:11434/v1
EMBED_MODEL=nomic-embed-text
EMBED_DIM=768
```

---

## 📁 Project Structure

```
brainvault/
├── backend/
│   ├── main.py              # FastAPI app + WebSocket
│   ├── config.py            # Paths, API keys, settings
│   ├── rag_engine.py        # RAG-Anything wrapper (CORRECT API)
│   ├── watcher.py           # Watchdog folder monitor
│   ├── graph_utils.py       # Read graph from LightRAG storage
│   ├── registry.py          # JSON deduplication registry
│   ├── requirements.txt
│   └── .env                 # API keys (edit this!)
└── frontend/
    ├── src/
    │   ├── App.tsx          # 3-panel layout
    │   ├── api/client.ts    # Axios instance
    │   ├── hooks/useSocket.ts   # Native WebSocket hook
    │   ├── components/
    │   │   ├── VaultPanel.tsx   # Left: file list + dropzone
    │   │   ├── BrainGraph.tsx   # Center: force graph
    │   │   └── ChatPanel.tsx    # Right: Q&A chat
    │   └── index.css        # Tailwind + custom styles
    ├── index.html
    ├── package.json
    ├── vite.config.ts
    └── tailwind.config.js
```

---

## ⚠️ Important Notes

1. **OpenRouter does NOT serve embeddings.** You MUST use OpenAI (or another OpenAI-compatible provider) for embeddings. We use `text-embedding-3-small` by default.

2. **First document processing is slow** because MinerU downloads AI models on first use (~1-2 GB). Subsequent runs are much faster.

3. **LibreOffice is required** for `.doc`, `.docx`, `.pptx`, `.xlsx` files. Without it, these files will fail to process.

4. **No database** — everything is file-based:
   - Vault files live on your Desktop
   - RAG storage lives in `~/.brainvault/rag_storage/`
   - Deduplication registry is `~/.brainvault/processed_files.json`

---

## 🐛 Troubleshooting

### "Missing API keys" warning
Fill in `OPENROUTER_API_KEY` and `OPENAI_API_KEY` in `backend/.env`

### Files not processing
- Check that the file extension is supported
- Check backend logs for errors
- Ensure LibreOffice is installed for Office documents

### Graph is empty
- The graph builds after document processing completes
- Try the `/graph` API endpoint directly to verify

### WebSocket not connecting
- Ensure backend is running on port 8000
- Check browser console for CORS errors
- The frontend proxy in `vite.config.ts` handles this automatically

---

## 📄 License

MIT License — built with ❤️ using RAG-Anything and LightRAG.
