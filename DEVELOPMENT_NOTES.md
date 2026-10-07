# Development Notes

## Environment used

The project was developed and tested with:

- macOS
- Python 3.12
- Node.js / npm
- FastAPI
- Next.js
- ChromaDB
- Sentence Transformers
- PyMuPDF
- Gemini API

## Clean setup

From the project root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then add the local provider key to `.env`.

For the frontend:

```bash
cd frontend
npm install
```

## Development commands

Backend:

```bash
uvicorn backend.main:app --reload --reload-dir backend
```

Frontend:

```bash
cd frontend
npm run dev
```

Tests:

```bash
pytest -v
```

Frontend build:

```bash
cd frontend
npm run build
```

## Why `--reload-dir backend` is used

Without the directory restriction, the development server can watch folders such as `frontend/node_modules`. That can cause unnecessary reloads when Node packages change.

Restricting reload watching to `backend` keeps the backend development loop cleaner.

## Temporary provider errors

The provider wrapper now retries temporary errors such as 429 and 5xx responses. The research worker also has a deterministic planning fallback and an evidence-only report fallback.

The goal is simple: if the provider is temporarily unavailable, already collected document evidence should not be lost and the API should not fail with an unexplained server error.

## Local generated files

These should stay out of the repository:

```text
.env
.venv/
frontend/node_modules/
frontend/.next/
data/app.db
data/uploads/*
data/chroma/*
```

The `.gitignore` file already covers these paths.

## Before sharing the project

Run:

```bash
pytest -v
```

Then:

```bash
cd frontend
npm run build
```

Finally check that the archive does not contain:

- `.env`
- `.venv`
- `node_modules`
- `.next`
- local database files
- uploaded private documents
- API keys
