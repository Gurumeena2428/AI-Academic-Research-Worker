"""
The RAG pipeline: this file is the "spine" of the whole project.

    question
      -> embed_query()                (embedding_service)
      -> vector_store.query()         (vector_store_service)
      -> build_prompt()               (this file)
      -> generate_answer()            (llm_service)
      -> AskResponse (answer + sources)

Everything here is plain, sequential Python on purpose -- no hidden
framework magic -- so each of the 8 steps described in the project brief
maps to one clearly-named function call below.
"""

from dataclasses import dataclass
from typing import List, Optional

from backend.services import embedding_service, llm_service, vector_store_service
from backend.utils.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------
# Hallucination control
# ---------------------------------------------------------------------
#
# WHY THIS PROMPT IS USED
# The model is instructed to answer *only* from the retrieved context and
# to explicitly say when the answer isn't there, instead of falling back
# on its own general knowledge. Without this instruction, a model will
# happily answer from what it learned during pretraining, which defeats
# the purpose of RAG: the user wants an answer grounded in THEIR uploaded
# document, not a generic answer that might not match their course's
# notation, textbook edition, or lecture content.
#
# HOW GROUNDING WORKS
# "Grounding" means every claim in the answer must be traceable back to a
# piece of retrieved text. We enforce this at the prompt level (telling
# the model what it may and may not use) and support it structurally by
# always returning the retrieved chunks alongside the answer as citations,
# so a human can verify the answer against the source text themselves.
#
# WHY RAG DOES NOT COMPLETELY ELIMINATE HALLUCINATIONS
# RAG reduces hallucination risk but cannot remove it entirely, because:
#   1. Retrieval can fail -- if the top-k chunks don't actually contain
#      the answer (e.g. bad chunking, ambiguous phrasing), the model is
#      working with irrelevant context and may still guess.
#   2. The LLM can still ignore instructions ("instruction following" is
#      not perfect) and blend in outside knowledge, especially for
#      well-known topics.
#   3. The model can misread or over-generalize the retrieved text even
#      when the right chunk WAS retrieved (e.g. summarizing "some cases"
#      as "all cases").
# This is why source citations are shown for every answer: they let the
# user verify the claim against the original document instead of trusting
# the model blindly.
SYSTEM_INSTRUCTION = (
    "You are an academic assistant that answers questions using ONLY the "
    "context provided below, which was retrieved from the user's own "
    "uploaded documents. "
    "If the answer cannot be found in the provided context, clearly state "
    "that the information was not found in the uploaded documents. "
    "Do not invent facts, and do not use outside knowledge beyond what is "
    "given in the context. Keep the answer concise and directly relevant "
    "to the question."
)

NOT_FOUND_MARKER = "the information was not found in the uploaded documents"


@dataclass
class RetrievedChunk:
    document_id: str
    filename: str
    page_number: int
    chunk_id: str
    text: str
    similarity_score: float


@dataclass
class RagResult:
    answer: str
    sources: List[RetrievedChunk]
    grounded: bool


def retrieve_context(
    question: str,
    top_k: Optional[int] = None,
    document_ids: Optional[List[str]] = None,
) -> List[RetrievedChunk]:
    """Steps 1-3 of the pipeline: embed the question, search Chroma, return top-k chunks."""
    top_k = top_k or settings.TOP_K

    # Step 1: question -> embedding
    query_vector = embedding_service.embed_query(question)

    # Step 2 + 3: similarity search in ChromaDB, retrieve top-k chunks
    raw_results = vector_store_service.query(query_vector, top_k=top_k, document_ids=document_ids)

    chunks: List[RetrievedChunk] = []
    if not raw_results["ids"] or not raw_results["ids"][0]:
        return chunks

    ids = raw_results["ids"][0]
    documents = raw_results["documents"][0]
    metadatas = raw_results["metadatas"][0]
    distances = raw_results["distances"][0]

    for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
        # Chroma returns cosine *distance* (0 = identical). We convert to a
        # more intuitive similarity score (1 = identical, 0 = unrelated).
        similarity = max(0.0, 1.0 - distance)
        chunks.append(
            RetrievedChunk(
                document_id=metadata["document_id"],
                filename=metadata["filename"],
                page_number=metadata["page_number"],
                chunk_id=chunk_id,
                text=text,
                similarity_score=round(similarity, 4),
            )
        )
    return chunks


def build_prompt(question: str, chunks: List[RetrievedChunk]) -> str:
    """Step 4-5: combine retrieved chunks into context, construct the final prompt."""
    if not chunks:
        context_block = "(No relevant context was retrieved from the uploaded documents.)"
    else:
        context_parts = []
        for chunk in chunks:
            context_parts.append(
                f"[Source: {chunk.filename}, Page {chunk.page_number}]\n{chunk.text}"
            )
        context_block = "\n\n---\n\n".join(context_parts)

    prompt = (
        f"{SYSTEM_INSTRUCTION}\n\n"
        f"CONTEXT:\n{context_block}\n\n"
        f"QUESTION:\n{question}\n\n"
        f"ANSWER:"
    )
    return prompt


def answer_question(
    question: str,
    top_k: Optional[int] = None,
    document_ids: Optional[List[str]] = None,
) -> RagResult:
    """Run the full RAG pipeline end-to-end and return the answer + sources."""
    logger.info("RAG query: %s", question)

    # Steps 1-3: retrieve relevant chunks
    chunks = retrieve_context(question, top_k=top_k, document_ids=document_ids)

    if not chunks:
        # No documents uploaded yet, or nothing matched at all.
        return RagResult(
            answer=(
                "The information was not found in the uploaded documents. "
                "Please upload a relevant PDF and try again."
            ),
            sources=[],
            grounded=False,
        )

    # Steps 4-5: build context + prompt
    prompt = build_prompt(question, chunks)

    # Steps 6-7: send to LLM, generate answer
    answer_text = llm_service.generate_answer(prompt)

    # Step 8: package answer + sources for the API response
    grounded = NOT_FOUND_MARKER not in answer_text.lower()

    return RagResult(answer=answer_text, sources=chunks, grounded=grounded)
