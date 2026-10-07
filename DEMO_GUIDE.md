# Demo Guide

This is the sequence I use to demonstrate the project from a clean start.

## 1. Start the backend

Terminal 1:

```bash
cd ~/Downloads/Autonomous-Academic-Research-Worker
source .venv/bin/activate
uvicorn backend.main:app --reload --reload-dir backend
```

Expected:

```text
Uvicorn running on http://127.0.0.1:8000
Application startup complete.
```

## 2. Start the frontend

Terminal 2:

```bash
cd ~/Downloads/Autonomous-Academic-Research-Worker/frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

## 3. Upload a document

Use the PDF upload area and select an academic PDF.

Wait until the document card says:

```text
ready
```

The card should also show the page and chunk counts.

## 4. Test direct document questions

Open **Document Chat** and ask a question whose answer is clearly present in the document.

Example:

```text
How many pillars are described in the document?
```

The useful part of the result is not only the answer. The source list should show the filename and page number.

## 5. Test the research worker

Open **Research Worker**.

Use:

```text
Compare the methodology and evaluation metrics of the most relevant papers in my uploaded documents and prepare a cited comparison.
```

Click **Run autonomous task**.

## 6. What to look for

The result page should show:

- task status
- retry count
- verification state
- generated research plan
- execution trace
- search actions
- observations from each action
- final report
- source count

The strongest part of the demo is the execution trace. It shows that the worker did more than one fixed retrieval call.

## 7. Recovery demo

A useful way to demonstrate recovery is to give a task that is related to the uploaded document but uses wording that is unlikely to match the document exactly.

The search tool can mark weak retrieval and create a broader follow-up query.

In the execution trace, look for an action similar to:

```text
Recover from weak retrieval with a broadened query
```

## 8. Provider failure demo

Temporary provider errors should no longer make `/api/agent/run` crash immediately.

The model wrapper retries temporary errors. If report generation still fails, the worker keeps the collected evidence and creates a cited evidence-only report.

This is useful because a temporary external-service problem should not destroy all of the work already done during the run.

## 9. Screenshots I would keep

For a short project demo, I would capture:

1. The uploaded PDF showing `ready`.
2. A successful Document Chat answer with page sources.
3. The Research Worker task before execution.
4. The execution trace after the run.
5. The final cited report.

## 10. If the demo fails

Check the backend terminal first.

### Backend not running

```bash
lsof -i :8000
```

Then restart:

```bash
uvicorn backend.main:app --reload --reload-dir backend
```

### Frontend not running

```bash
cd frontend
npm install
npm run dev
```

### API key error

Check `.env` in the project root and restart the backend.

### Port 3000 is already in use

```bash
lsof -i :3000
```

Stop the old process and run `npm run dev` again.
