# Project Overview

## Project name

**Autonomous Academic Research Worker**

## Why I built it

I already had a document question-answering application, but a normal chat flow only reacts to one question at a time. For this version I wanted the system to handle a larger research objective by deciding what information it needs, searching for that information, and checking the result before finishing.

I kept the scope around uploaded academic PDFs so that the whole workflow can be tested locally.

## Example task

> Compare the methodology and evaluation metrics of the most relevant papers in my uploaded documents and prepare a cited comparison.

## What happens during a run

1. The user gives a research objective.
2. The worker creates a short research plan.
3. Each research step becomes a document search.
4. Retrieval quality is checked using the similarity score.
5. Weak searches are retried with a broader query.
6. Useful passages are added to an evidence store.
7. The evidence is inspected before writing.
8. A cited report is generated from the collected evidence.
9. The report is checked against the evidence and its citations.
10. If important information is missing, the worker can search again and re-run the report step.
11. The frontend shows the plan, actions, observations, retries, sources and final report.

## Main files

| File | Purpose |
|---|---|
| `backend/agent/service.py` | Research planning, search loop, recovery and verification |
| `backend/rag/pipeline.py` | Retrieval and grounded question answering |
| `backend/services/llm_service.py` | Provider wrapper and temporary-failure retry handling |
| `backend/services/pdf_service.py` | PDF text extraction |
| `backend/services/chunking_service.py` | Text chunking |
| `backend/services/embedding_service.py` | Embedding generation |
| `backend/services/vector_store_service.py` | ChromaDB storage and search |
| `backend/routes/agent.py` | Research worker API |
| `backend/routes/chat.py` | Document chat API |
| `backend/routes/documents.py` | Upload and document APIs |
| `frontend/components/AgentPanel.tsx` | Research worker interface |
| `frontend/components/DocumentChat.tsx` | Document chat interface |

## Design choice

I deliberately did not add a large orchestration framework or multiple independent workers. There is one bounded research loop with a small set of tools. This makes the execution trace easy to inspect and keeps the project practical for a local demo.
