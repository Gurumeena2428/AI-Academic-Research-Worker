# Project Study Guide

This is the set of points I would use to explain the project in a technical discussion.

## 1. What problem does the project solve?

A normal document chat application is good for individual questions, but it does not naturally handle a larger research objective. My worker breaks the objective into smaller searches, checks the returned evidence, retries weak searches, and then produces a report with citations.

## 2. What happens when I upload a PDF?

The backend saves the PDF, extracts text page by page with PyMuPDF, splits the text into overlapping chunks, creates embeddings for the chunks, and stores the embeddings and metadata in ChromaDB. SQLite stores the document-level metadata used by the application.

## 3. Why chunk the document?

A complete PDF can be much larger than the useful context for one question. Chunking lets the system search for the small parts that are relevant to the current question.

The project uses an 800-character chunk size with 150 characters of overlap. The overlap helps when an important sentence falls close to a chunk boundary.

## 4. Why use embeddings?

A question and the document passage may use different words but still mean the same thing. Embeddings turn both into vectors so the system can compare semantic similarity rather than relying only on exact keyword matches.

## 5. Why ChromaDB?

It can run locally and persist the vector collection to disk. That is enough for the size of this project and avoids adding another server just for vector search.

## 6. How does normal Document Chat work?

```text
question
 ↓
question embedding
 ↓
ChromaDB search
 ↓
top relevant chunks
 ↓
context construction
 ↓
language model
 ↓
answer + source pages
```

The answer is generated from the retrieved context instead of sending the complete document every time.

## 7. How is the Research Worker different?

The worker has state during a run. It keeps:

- the current plan
- previous actions
- retrieved evidence
- retry count
- verification result

That lets it use the result of one action when deciding what to do next.

## 8. How does it decide that retrieval is weak?

Each retrieved chunk has a similarity score. The worker compares the score with `MIN_RETRIEVAL_SIMILARITY`.

If the retrieved chunks do not cross the threshold, the search is marked unsuccessful and the worker creates a broader query.

## 9. Why have deterministic fallback planning?

The planner is useful when the task is open-ended, but the whole application should not stop just because one planning request fails. For common task types such as comparisons, the code has a small fallback plan covering relevant documents, methodology, evaluation, and differences.

## 10. What happens if the language-model service returns 503?

The provider wrapper retries temporary errors with short delays. If the report-generation call still fails, the worker does not discard the evidence. It creates a cited evidence-only report from the passages already collected.

This is better than returning an unhandled 500 error after the worker has already completed the expensive retrieval work.

## 11. How is the report checked?

The report checker receives the task, the draft report, and the collected evidence. It checks whether the report answers the task and whether its claims are supported.

The code also checks citations directly. A citation must match a filename and page number from the evidence collected during that run.

## 12. Why use a bounded loop?

Autonomous systems need limits. Otherwise a poor query can cause repeated searches forever. This project limits the run to 12 actions and 2 recovery attempts.

## 13. What would I improve?

I would add a proper evaluation set with known questions and expected source pages, better ranking across multiple documents, resumable research sessions, and optional external connectors with explicit permissions.

## 14. Questions I should be ready for

### Why not send the whole PDF to the model?

It would waste context and make retrieval less precise. Searching first lets the system send only the passages that matter.

### Why not use many workers?

For this project one bounded worker is easier to debug and explain. More workers would add coordination overhead without being necessary for the current task.

### What is the biggest weakness?

Retrieval quality is still important. If the right evidence is not retrieved, the later report step cannot recover information that was never found. Provider availability is another external dependency, which is why retry and fallback handling is included.

### How do I know the citations are real?

The citation checker compares the filename and page number in the report with the evidence actually collected during that run. It does not accept an arbitrary page reference.
