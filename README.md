# CiteAgent

**CiteAgent** is a production-grade, privacy-first agentic AI system that automatically converts research papers into correct journal formatting. Researchers upload a manuscript (DOCX, PDF, or TXT); the system parses it, detects structure, extracts formatting rules, applies journal formatting, validates citations, and generates a formatted DOCX. All formatting decisions are explainable.

---

## Features

- **Privacy-first**: Default **Private Mode** runs everything locally with Ollama (Phi3 + Llama3). Your manuscript never leaves your machine.
- **Cloud optional**: Switch to **Cloud Mode** (Groq, Llama3-70B) when you want faster formatting.
- **Modular agents**: Parser → Structure → Rule Extraction → Formatting → Citation Engine → Validation.
- **Explainable**: Every formatting change is listed with a reason in the Corrections panel.
- **Supported styles**: APA, MLA, Chicago, IEEE, Vancouver, and custom templates.

---

## Project structure

```
citeagent/
├── frontend/          # Next.js + Tailwind + Shadcn UI + Framer Motion
│   ├── app/
│   ├── components/
│   └── lib/
├── backend/
│   ├── agents/        # Parser, Structure, Rule, Format, Citation, Validation
│   ├── llm/           # Ollama + Groq clients
│   ├── utils/         # DOCX/PDF/TXT parsing and formatting
│   ├── main.py
│   └── requirements.txt
└── README.md
```

---

## Backend setup

**Python**: 3.10 or 3.11 recommended (3.13 may require prebuilt wheels for some deps).

### 1. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

Optional: `pip install pymupdf` for PDF fallback parsing (needs build tools on Windows).

### 2. Environment

Copy the example env and edit as needed:

```bash
cp .env.example .env
```

Variables:

- `AI_MODE=local`
- `OLLAMA_BASE_URL=http://localhost:11434`
- `OLLAMA_MODEL_FAST=phi3`
- `OLLAMA_MODEL_REASONING=llama3`
- `GROQ_API_KEY=your_key_here` (optional, for Cloud Mode)
- `GROQ_MODEL=llama3-70b-8192`
- `SERVER_PORT=8000`

### 3. Start Ollama (for Private Mode)

Install [Ollama](https://ollama.ai), then:

```bash
ollama pull phi3
ollama pull llama3
```

### 4. Run the backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API: `http://localhost:8000`. Docs: `http://localhost:8000/docs`.

---

## Frontend setup

### 1. Install dependencies

```bash
cd frontend
npm install
```

### 2. Environment

```bash
cp .env.local.example .env.local
```

Set:

- `NEXT_PUBLIC_API_LOCAL=http://localhost:8000`
- `NEXT_PUBLIC_API_TUNNEL=https://your-ngrok-url.ngrok.io` (optional)
- `NEXT_PUBLIC_API_CLOUD=https://your-railway-url.up.railway.app` (optional, for Cloud Mode)

### 3. Run the frontend

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

If the dev server starts then exits immediately (common on Windows):
- Run `npm install` to ensure `cross-env` and deps are installed, then try `npm run dev` again.
- If it still exits, run `npm i --force` (fixes SWC install issues on Windows) or run `npm run dev` from an **external** PowerShell/CMD window.

---

## Local hosting with Ngrok

To expose your local backend to the internet (e.g. for demos or mobile):

1. Install [Ngrok](https://ngrok.com).
2. Authenticate: `ngrok config add-authtoken YOUR_TOKEN`
3. Run the backend: `uvicorn main:app --host 0.0.0.0 --port 8000`
4. Start a tunnel: `ngrok http 8000`
5. Copy the HTTPS URL (e.g. `https://abc123.ngrok.io`) into `frontend/.env.local` as `NEXT_PUBLIC_API_TUNNEL`.

---

## Cloud mode hosting

- **Backend**: Deploy to Railway or Render. Set `AI_MODE=cloud` and `GROQ_API_KEY`.
- **Frontend**: Deploy to Vercel. Set `NEXT_PUBLIC_API_CLOUD` to your deployed backend URL.

---

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload-manuscript` | Upload DOCX/PDF/TXT |
| POST | `/parse` | Parse manuscript (no LLM) |
| POST | `/analyze-structure` | Detect structure (Phi3/Llama3-70B) |
| POST | `/extract-rules` | Extract formatting rules (Phi3) |
| POST | `/format-document` | Apply formatting (Llama3) |
| POST | `/validate-citations` | Citation checks (no LLM) |
| POST | `/validate-format` | Format compliance (Llama3) |
| GET | `/download?job_id=...` | Download formatted DOCX |
| GET | `/job/{job_id}` | Get job status and results |
| GET | `/health` | Health check |

---

## Tech stack

- **Frontend**: React, Next.js 14, TailwindCSS, Shadcn UI (Radix), Lucide React, Framer Motion, next-themes (dark/light).
- **Backend**: Python 3.10+, FastAPI, python-docx, pdfplumber, PyMuPDF, httpx, Groq SDK.
- **AI**: Ollama (Phi3, Llama3) for private mode; Groq (Llama3-70B) for cloud mode.

---

## License

MIT.
