# Architecture

## 1. High-level design

```text
                         Browser
                            |
             +--------------+--------------+
             |                             |
        Document Chat                 Research Worker
             |                             |
             +--------------+--------------+
                            |
                         FastAPI
                            |
       +--------------------+--------------------+
       |                    |                    |
   PDF service          RAG pipeline        Agent service
       |                    |                    |
   PyMuPDF             Embeddings             Planner
       |                    |                    |
   Chunking            ChromaDB             Search tool
                            |                 Evidence store
                            |                 Synthesis
                            |                 Verification
                            |                 Recovery
                            |
                      Language model
                         (Gemini)
```

## 2. Upload path

When a PDF is uploaded:

```text
PDF
 ↓
Save file
 ↓
Extract text page by page
 ↓
Split text into overlapping chunks
 ↓
Generate embeddings
 ↓
Store vectors + text + metadata in ChromaDB
 ↓
Store document metadata in SQLite
```

Each stored chunk keeps enough metadata to point back to the source:

- document id
- filename
- page number
- chunk id
- original text
- similarity score when retrieved

## 3. Question path

```text
Question
 ↓
Embed question
 ↓
Query ChromaDB
 ↓
Take top-k passages
 ↓
Apply similarity threshold
 ↓
Build context
 ↓
Generate answer
 ↓
Return answer + sources
```

The same retrieval code is reused by the research worker.

## 4. Research worker

The worker is implemented as a bounded loop in `backend/agent/service.py`.

The main tools are:

### `search_documents`

Searches the uploaded document collection and returns passages with page numbers and similarity scores.

If the best result is below the configured threshold, the search is marked unsuccessful so the worker has a reason to retry.

### `inspect_evidence`

Checks which documents and how many chunks have been collected so far.

### `synthesize_report`

Turns the collected evidence into a cited report. The prompt explicitly tells the report writer to use only the supplied evidence.

### `verify_report`

Checks whether the report answers the task, whether important claims are supported, and whether citations point to evidence collected during the run.

### Recovery

If retrieval is weak, the worker broadens the query. If verification identifies missing information, it performs a targeted search and can re-synthesize the report.

## 5. Retry handling

Temporary provider failures are handled inside `backend/services/llm_service.py`.

The wrapper retries common temporary errors such as 429, 500, 502, 503 and 504 responses with short delays.

The research worker also has higher-level fallbacks:

- planner failure -> deterministic research plan
- report generation failure -> evidence-only cited report
- verification failure -> result is marked for review rather than crashing the API

This keeps a temporary external-service problem from turning into an unhandled backend error.

## 6. Configuration

The project reads `.env` from the project root.

Important settings include:

```text
LLM_PROVIDER
a language-model provider name

GEMINI_API_KEY
local provider key

GEMINI_MODEL
model name used for generation

EMBEDDING_MODEL
embedding model used for documents and questions

CHUNK_SIZE
number of characters in each chunk

CHUNK_OVERLAP
overlap between adjacent chunks

TOP_K
number of passages retrieved for normal chat

MIN_RETRIEVAL_SIMILARITY
minimum similarity accepted by the research worker
```

## 7. Why ChromaDB

ChromaDB is embedded and persists locally. It fits this project because there is no need to run another database service just for vector search.

SQLite is used for document metadata and chat history.

## 8. Why the worker is bounded

A research task has a maximum number of actions and a maximum number of recovery attempts. This prevents a bad task or repeated weak searches from running forever.

Current limits:

```text
MAX_STEPS = 12
MAX_RETRIES = 2
```

These are deliberately small for the local demo.
