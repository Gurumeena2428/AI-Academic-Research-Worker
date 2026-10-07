# Autonomous Academic Research Worker

I built this project as a document research workspace. The main use case is simple: I upload academic PDFs, ask questions about them, or give the application a larger research task and let it work through the uploaded documents step by step.

The project has two modes:

1. **Document Chat** - ask a direct question and get an answer with page-level sources.
2. **Research Worker** - give a larger objective, let the worker create smaller research steps, search the documents, retry weak searches, collect evidence, prepare a report, and check the report before returning it.

The worker is intentionally limited to the uploaded documents. It does not browse the internet, control a desktop, or access personal accounts.

---

## 1. What I built

The normal question-answering flow is:

```text
PDF
 ↓
Text extraction
 ↓
Chunking
 ↓
Embeddings
 ↓
ChromaDB
 ↓
Similarity search
 ↓
Relevant passages
 ↓
Gemini
 ↓
Answer + sources
```

The research worker adds a control loop on top of the same document search:

```text
Research task
 ↓
Create research plan
 ↓
Search documents
 ↓
Check retrieval quality
 ↓
Retry / broaden weak searches
 ↓
Collect evidence
 ↓
Prepare report
 ↓
Check report and citations
 ↓
Recover if a gap is found
 ↓
Final report + execution trace
```

The important part is that the next search is not fixed in advance. The worker observes the result of each search and can decide that it needs another query.

---

## 2. Main features

- PDF upload
- Page-by-page PDF text extraction
- Overlapping text chunks
- Local sentence embeddings
- Persistent ChromaDB storage
- SQLite metadata storage
- Document question answering
- Page-level source information
- Natural-language research tasks
- LLM-based planning with deterministic fallback planning
- Retrieval quality threshold
- Automatic query broadening when retrieval is weak
- Evidence collection and deduplication
- Cited report generation
- Report checking
- Recovery after verification gaps
- Execution trace in the frontend
- Provider retry handling for temporary service failures
- Pytest test suite

---

## 3. Tech stack

| Part | Technology |
|---|---|
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI |
| Language model | Google Gemini API |
| Embeddings | Sentence Transformers - `all-MiniLM-L6-v2` |
| Vector store | ChromaDB |
| PDF processing | PyMuPDF |
| Metadata | SQLite |
| Testing | Pytest |

---

## 4. Project structure

```text
Autonomous-Academic-Research-Worker/
│
├── backend/
│   ├── agent/                 Research worker and control loop
│   ├── models/                Request, response and database models
│   ├── rag/                   Document retrieval pipeline
│   ├── routes/                FastAPI endpoints
│   ├── services/              PDF, embedding, vector store and model services
│   └── utils/                 Configuration and logging
│
├── frontend/
│   ├── app/                   Next.js pages
│   ├── components/            Main UI components
│   └── lib/                   Frontend API functions and types
│
├── data/
│   ├── uploads/               Uploaded PDFs
│   └── chroma/                Local vector database
│
├── tests/                     Backend tests
├── README.md                  This file
├── ARCHITECTURE.md            System design notes
├── DEMO_GUIDE.md              Demo steps
├── PROJECT_OVERVIEW.md        Short project overview
├── PROJECT_STUDY_GUIDE.md     Technical notes for explaining the project
├── DEVELOPMENT_NOTES.md       Development and troubleshooting notes
├── requirements.txt           Python dependencies
├── start_project.py           Optional one-command launcher
└── .env.example               Environment variable template
```

---

# 5. Running the project

## Requirements

I used:

- Python 3.12
- Node.js and npm
- A Gemini API key

Python 3.12 is recommended because it is the version I used for the backend dependencies.

### Step 1 - Open the project

```bash
cd ~/Downloads/Autonomous-Academic-Research-Worker
```

If the folder is somewhere else, use that path instead.

### Step 2 - Create the Python environment

```bash
python3.12 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Check the version:

```bash
python --version
```

It should show Python 3.12.x.

### Step 3 - Install backend packages

```bash
pip install -r requirements.txt
```

### Step 4 - Create `.env`

```bash
cp .env.example .env
```

Open it:

```bash
code .env
```

Set at least:

```text
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.8-flash
```

Do not commit `.env` to GitHub. The real key belongs only in the local `.env` file.

---

## 6. Start the backend

From the project root:

```bash
source .venv/bin/activate
uvicorn backend.main:app --reload --reload-dir backend
```

The backend should be available at:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/api/health
```

Leave this terminal running.

---

## 7. Start the frontend

Open a second terminal.

```bash
cd ~/Downloads/Autonomous-Academic-Research-Worker/frontend
```

Install frontend packages the first time:

```bash
npm install
```

Then start Next.js:

```bash
npm run dev
```

Open:

```text
http://localhost:3000
```

The frontend is normally on port 3000. If another process is already using that port, Next.js may move to 3001. In that case, stop the old process on port 3000 and start the frontend again so that the frontend and the configured backend origin match.

---

# 8. Run everything with the launcher

After the Python environment and frontend dependencies have been installed, the project can also be started with:

```bash
cd ~/Downloads/Autonomous-Academic-Research-Worker
source .venv/bin/activate
python start_project.py
```

The launcher starts the backend on port 8000 and the frontend on port 3000, then opens the browser.

For debugging, I prefer the two-terminal method because the backend and frontend logs are easier to see separately.

---

# 9. First test

After opening the website:

1. Upload a PDF.
2. Wait until the document shows `ready`.
3. Open **Document Chat**.
4. Ask a simple question that is clearly answered by the PDF.
5. Check that the answer includes source pages.
6. Open **Research Worker**.
7. Give it a multi-step task.

For the included networking document, a simple first question is:

```text
How many pillars are described in the document?
```

A good research-worker test is:

```text
Compare the methodology and evaluation metrics of the most relevant papers in my uploaded documents and prepare a cited comparison.
```

---

# 10. Useful commands

### Backend

```bash
cd ~/Downloads/Autonomous-Academic-Research-Worker
source .venv/bin/activate
uvicorn backend.main:app --reload --reload-dir backend
```

### Frontend

```bash
cd ~/Downloads/Autonomous-Academic-Research-Worker/frontend
npm install
npm run dev
```

### Run backend tests

From the project root:

```bash
pytest -v
```

### Build the frontend

```bash
cd frontend
npm run build
```

### Check which process uses port 8000

```bash
lsof -i :8000
```

### Check which process uses port 3000

```bash
lsof -i :3000
```

### Stop a process when its PID is known

```bash
kill PID
```

For example, if the PID shown by `lsof` is `15723`:

```bash
kill 15723
```

Do not type the word `PID`; replace it with the number shown by the terminal.

---

# 11. Common problems

## `sh: next: command not found`

The frontend packages are not installed.

```bash
cd frontend
npm install
npm run dev
```

## `Address already in use` on port 8000

Another backend process is already running.

```bash
lsof -i :8000
```

Stop the actual PID shown by that command and start Uvicorn again.

## `Port 3000 is in use ... using 3001 instead`

The frontend has moved to port 3001. The project is configured for port 3000 by default, so the safest fix is to stop the process using port 3000 and run:

```bash
npm run dev
```

again.

## `Could not reach the backend: Failed to fetch`

Check both terminals.

Backend:

```bash
uvicorn backend.main:app --reload --reload-dir backend
```

Frontend:

```bash
npm run dev
```

Also check that the browser is using `http://localhost:3000` and that port 8000 is running.

## `GEMINI_API_KEY is not set`

Make sure `.env` exists in the project root:

```bash
ls -la .env
```

Then check the line in `.env` without sharing it anywhere:

```text
GEMINI_API_KEY=...
```

Restart the backend after changing `.env`.

## The research worker shows a 503 service error

A temporary provider failure should now be retried automatically. If all retries fail, the worker keeps the retrieved evidence and builds an evidence-based fallback report instead of turning the whole request into an unhandled 500 error.

Try the task again after a short wait if the external service is busy.

## Chroma telemetry warnings appear in the terminal

Messages such as:

```text
Failed to send telemetry event ...
```

are warnings from the local Chroma installation. They do not mean that document retrieval failed. The useful check is whether the request itself succeeds and whether chunks are being retrieved.

---

# 12. Security notes

- Keep the real API key in `.env` only.
- Never commit `.env`.
- Never put a real key in `.env.example`.
- Do not include `.env` in the final ZIP.
- Do not paste API keys into screenshots, README files, GitHub issues, or chat messages.

The repository already ignores `.env` and local generated data.

---

# 13. Current limitations

This is a focused local research tool, not a general-purpose work automation system.

Current limitations include:

- It works only with uploaded documents.
- It does not browse external websites.
- It does not operate desktop applications.
- It does not connect to external company systems.
- It is designed for local/small-scale document collections.
- Authentication and multi-user access are not included.
- The quality of the final report still depends on retrieval quality and the selected language model.
- Temporary provider outages can reduce the quality of planning, synthesis, or verification, although the worker now has retry and fallback handling.

These limitations are deliberate so the project stays small enough to understand and demonstrate end to end.

---

# 14. What I would improve next

If I continue this project, I would work on:

1. Better document-level ranking before research starts.
2. More structured citation checking.
3. Persistent research sessions so a task can be resumed.
4. A small evaluation set for measuring retrieval and report quality.
5. Better handling of multiple related documents and duplicate passages.
6. A background job queue for larger document collections.
7. Optional connectors for external sources while keeping permissions explicit.

---

## 15. Short project summary

I built this as a full-stack research workspace around uploaded academic PDFs. The interesting part is not only answering a question; the research worker decides what evidence it needs, searches for it, notices when a search is weak, retries with a broader query, collects the useful passages, prepares a cited report, and checks the result before returning it. The rest of the system is intentionally simple so I can explain every major component and run the complete project locally.
