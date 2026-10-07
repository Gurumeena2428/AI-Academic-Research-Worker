"""Autonomous research worker over the uploaded-document workspace.

The worker is intentionally narrow and inspectable. It does not control a
browser, execute shell commands, or access third-party accounts. Its autonomy
comes from planning research subtasks, selecting search queries, observing
retrieval quality, retrying weak searches, and verifying the final report.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from backend.rag.pipeline import RetrievedChunk, retrieve_context
from backend.services import llm_service
from backend.utils.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

MAX_STEPS = 12
MAX_RETRIES = 2


@dataclass
class AgentStep:
    step: int
    action: str
    tool: str
    input: Dict[str, Any]
    observation: str
    success: bool
    retry: int = 0


@dataclass
class AgentResult:
    task: str
    status: str
    report: str
    plan: List[str]
    steps: List[AgentStep]
    sources: List[Dict[str, Any]]
    verified: bool
    retries: int
    run_id: str


class ResearchAgent:
    """Stateful, bounded research worker for uploaded academic PDFs."""

    def __init__(self, document_ids: Optional[List[str]] = None):
        self.document_ids = document_ids
        self.evidence: List[RetrievedChunk] = []
        self.steps: List[AgentStep] = []
        self.retries = 0

    def plan_task(self, task: str) -> List[str]:
        prompt = f"""You are the planning component of an autonomous academic research worker.

User task:
{task}

The worker has access only to uploaded academic PDFs. Create 2 to 5 concrete
research subtasks that can be answered by semantic search over those PDFs.

For comparison tasks, make sure the subtasks cover:
1. identifying relevant documents,
2. methodology/approach,
3. evaluation metrics/results,
4. similarities, differences, or limitations.

Do not invent document names or facts. Return ONLY a JSON object:
{{"steps": ["subtask 1", "subtask 2", "..."]}}
"""
        try:
            parsed = llm_service.generate_json(prompt)
            steps = parsed.get("steps", [])
            if isinstance(steps, list):
                clean = [str(item).strip() for item in steps if str(item).strip()]
                if 2 <= len(clean) <= 5:
                    return clean
        except Exception as exc:
            logger.warning("Planner failed; using deterministic fallback: %s", exc)

        return _fallback_plan(task)

    def tool_search_documents(self, query: str, top_k: int = 5) -> tuple[str, bool]:
        chunks = retrieve_context(
            query,
            top_k=max(1, min(top_k, 8)),
            document_ids=self.document_ids,
        )

        if not chunks:
            return (
                "No evidence was retrieved. The query should be broadened or retried.",
                False,
            )

        threshold = settings.MIN_RETRIEVAL_SIMILARITY
        usable = [chunk for chunk in chunks if chunk.similarity_score >= threshold]

        if not usable:
            best = max(chunk.similarity_score for chunk in chunks)
            return (
                f"Retrieved {len(chunks)} chunks, but the best similarity "
                f"({best:.3f}) is below the acceptance threshold ({threshold:.3f}). "
                "The query should be broadened or retried.",
                False,
            )

        seen = {chunk.chunk_id for chunk in self.evidence}
        added = 0
        for chunk in usable:
            if chunk.chunk_id not in seen:
                self.evidence.append(chunk)
                seen.add(chunk.chunk_id)
                added += 1

        lines = [
            f"Retrieved {len(chunks)} chunks; accepted {len(usable)}; "
            f"added {added} new evidence chunks."
        ]
        for chunk in usable:
            lines.append(
                f"- {chunk.filename}, page {chunk.page_number}, "
                f"similarity={chunk.similarity_score:.3f}: "
                f"{_compact(chunk.text, 280)}"
            )
        return "\n".join(lines), True

    def tool_inspect_evidence(self) -> str:
        if not self.evidence:
            return "Evidence store is empty."

        by_doc: Dict[str, int] = {}
        for chunk in self.evidence:
            by_doc[chunk.filename] = by_doc.get(chunk.filename, 0) + 1

        return "Evidence currently covers: " + ", ".join(
            f"{name} ({count} chunks)" for name, count in sorted(by_doc.items())
        )

    def tool_synthesize_report(self, task: str) -> str:
        if not self.evidence:
            return "Cannot synthesize: no supporting evidence was collected."

        prompt = f"""You are the report-writing component of an autonomous academic research worker.

TASK:
{task}

EVIDENCE:
{_evidence_block(self.evidence)}

Write a concise but useful report answering the task ONLY from the evidence.
Every substantive claim must be supported by one or more supplied evidence
items. Use citations exactly in this form:
[filename, p. 3]

If a requested point is not established by the evidence, explicitly say so.
Never invent paper names, methods, metrics, numbers, or conclusions.
"""
        try:
            return llm_service.generate_answer(prompt)
        except Exception as exc:
            logger.warning("Report generation failed; building an evidence-only report: %s", exc)
            return _fallback_report(task, self.evidence)

    def tool_verify_report(self, task: str, report: str) -> Dict[str, Any]:
        evidence = _unique_chunks(self.evidence)
        evidence_block = _evidence_block(evidence)
        allowed_citations = {
            (chunk.filename, chunk.page_number) for chunk in evidence
        }

        prompt = f"""You are the verification component of an autonomous research worker.

TASK:
{task}

DRAFT REPORT:
{report}

AVAILABLE EVIDENCE:
{evidence_block}

Check whether the report answers the task and whether its substantive claims
are supported by the available evidence. Return ONLY this JSON:
{{"verified": true, "issues": [], "missing": []}}

Set verified=false for unsupported claims, missing required comparisons,
or important claims without evidence. Do not require information that the
uploaded evidence does not contain.
"""
        try:
            result = llm_service.generate_json(prompt)
        except Exception as exc:
            return {
                "verified": False,
                "issues": [f"Verification model failed: {exc}"],
                "missing": [],
            }

        issues = [str(item) for item in result.get("issues", [])]
        missing = [str(item) for item in result.get("missing", [])]

        citations = _extract_citations(report)
        invalid_citations = [
            f"[{filename}, p. {page}]"
            for filename, page in citations
            if (filename, page) not in allowed_citations
        ]

        if not citations:
            issues.append("The report contains no source citations in the required format.")
        if invalid_citations:
            issues.append(
                "The report contains citations that do not map to collected evidence: "
                + ", ".join(invalid_citations)
            )

        return {
            "verified": bool(result.get("verified", False))
            and not issues
            and not invalid_citations
            and bool(citations),
            "issues": issues,
            "missing": missing,
        }

    def run(self, task: str) -> AgentResult:
        run_id = str(uuid.uuid4())
        plan = self.plan_task(task)
        report = ""
        verified = False

        for index, research_step in enumerate(plan, start=1):
            if len(self.steps) >= MAX_STEPS:
                break

            observation, success = self.tool_search_documents(research_step)
            self.steps.append(
                AgentStep(
                    step=len(self.steps) + 1,
                    action=f"Research subtask {index}: {research_step}",
                    tool="search_documents",
                    input={"query": research_step, "top_k": 5},
                    observation=observation,
                    success=success,
                )
            )

            if not success and self.retries < MAX_RETRIES:
                self.retries += 1
                fallback_query = _broaden_query(task, research_step)
                retry_observation, retry_success = self.tool_search_documents(
                    fallback_query, top_k=7
                )
                self.steps.append(
                    AgentStep(
                        step=len(self.steps) + 1,
                        action="Recover from weak retrieval with a broadened query",
                        tool="search_documents",
                        input={"query": fallback_query, "top_k": 7},
                        observation=retry_observation,
                        success=retry_success,
                        retry=self.retries,
                    )
                )

        inspect = self.tool_inspect_evidence()
        self.steps.append(
            AgentStep(
                step=len(self.steps) + 1,
                action="Inspect accumulated evidence before synthesis",
                tool="inspect_evidence",
                input={},
                observation=inspect,
                success=bool(self.evidence),
            )
        )

        if self.evidence:
            report = self.tool_synthesize_report(task)
            self.steps.append(
                AgentStep(
                    step=len(self.steps) + 1,
                    action="Synthesize a cited report from collected evidence",
                    tool="synthesize_report",
                    input={"evidence_chunks": len(self.evidence)},
                    observation=_compact(report, 1400),
                    success=True,
                )
            )

            verification = self.tool_verify_report(task, report)
            verified = verification["verified"]
            self.steps.append(
                AgentStep(
                    step=len(self.steps) + 1,
                    action="Verify report against the collected evidence",
                    tool="verify_report",
                    input={},
                    observation=json.dumps(verification),
                    success=verified,
                )
            )

            if not verified and self.retries < MAX_RETRIES:
                self.retries += 1
                gaps = verification.get("missing") or verification.get("issues")
                gaps = gaps or ["additional supporting evidence"]
                recovery_query = (
                    f"{task}. Find additional evidence specifically addressing: "
                    + "; ".join(gaps[:3])
                )
                recovery_observation, recovery_success = self.tool_search_documents(
                    recovery_query, top_k=8
                )
                self.steps.append(
                    AgentStep(
                        step=len(self.steps) + 1,
                        action="Recover from verification gaps with targeted search",
                        tool="search_documents",
                        input={"query": recovery_query, "top_k": 8},
                        observation=recovery_observation,
                        success=recovery_success,
                        retry=self.retries,
                    )
                )

                if recovery_success:
                    report = self.tool_synthesize_report(task)
                    verification = self.tool_verify_report(task, report)
                    verified = verification["verified"]
                    self.steps.append(
                        AgentStep(
                            step=len(self.steps) + 1,
                            action="Re-synthesize and re-verify after recovery",
                            tool="verify_report",
                            input={},
                            observation=json.dumps(verification),
                            success=verified,
                            retry=self.retries,
                        )
                    )
        else:
            report = (
                "I could not complete the task because no sufficiently relevant "
                "evidence was found in the uploaded documents."
            )

        status = "completed" if verified else ("partial" if self.evidence else "failed")
        sources = [_source_dict(chunk) for chunk in _unique_chunks(self.evidence)]

        return AgentResult(
            task=task,
            status=status,
            report=report,
            plan=plan,
            steps=self.steps,
            sources=sources,
            verified=verified,
            retries=self.retries,
            run_id=run_id,
        )


def run_agent(task: str, document_ids: Optional[List[str]] = None) -> AgentResult:
    if not task.strip():
        raise ValueError("Task cannot be empty.")
    return ResearchAgent(document_ids=document_ids).run(task.strip())


def _fallback_report(task: str, chunks: List[RetrievedChunk]) -> str:
    """Build a useful cited report when the provider is temporarily unavailable."""
    unique = _unique_chunks(chunks)
    lines = [
        "Research task",
        task,
        "",
        "Evidence collected",
        f"The search worker collected {len(unique)} supporting passages from the uploaded documents.",
        "",
    ]
    for index, chunk in enumerate(unique[:8], start=1):
        lines.append(
            f"{index}. {_compact(chunk.text, 650)} [{chunk.filename}, p. {chunk.page_number}]"
        )
    lines.extend([
        "",
        "Note: the report was assembled directly from the retrieved passages because the report-generation service was temporarily unavailable.",
    ])
    return "\n".join(lines)


def _fallback_plan(task: str) -> List[str]:
    lower = task.lower()
    if any(word in lower for word in ["compare", "comparison", "difference", "versus", "vs"]):
        return [
            f"Identify the relevant uploaded papers or documents for: {task}",
            f"Extract the methodology, approach, or system design for: {task}",
            f"Extract the evaluation metrics, experiments, and reported results for: {task}",
            f"Cross-check similarities, differences, and limitations for: {task}",
        ]
    return [
        f"Find the documents and passages relevant to: {task}",
        f"Extract the evidence needed to answer: {task}",
        f"Cross-check the collected evidence for completeness: {task}",
    ]


def _broaden_query(task: str, failed_step: str) -> str:
    terms = re.sub(r"[^a-zA-Z0-9 ]", " ", failed_step).strip()
    return f"{task} relevant evidence {terms} methodology results evaluation metrics"


def _evidence_block(chunks: List[RetrievedChunk]) -> str:
    return "\n\n---\n\n".join(
        f"[E{i}] {chunk.filename}, page {chunk.page_number}, "
        f"similarity {chunk.similarity_score:.3f}\n{chunk.text}"
        for i, chunk in enumerate(_unique_chunks(chunks), start=1)
    )


def _unique_chunks(chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
    seen = set()
    result = []
    for chunk in chunks:
        if chunk.chunk_id not in seen:
            seen.add(chunk.chunk_id)
            result.append(chunk)
    return result


def _source_dict(chunk: RetrievedChunk) -> Dict[str, Any]:
    return {
        "document_id": chunk.document_id,
        "filename": chunk.filename,
        "page_number": chunk.page_number,
        "chunk_id": chunk.chunk_id,
        "text": chunk.text,
        "similarity_score": chunk.similarity_score,
    }


def _extract_citations(report: str) -> list[tuple[str, int]]:
    pattern = re.compile(r"\[([^\],]+),\s*p\.?\s*(\d+)\]")
    return [(filename.strip(), int(page)) for filename, page in pattern.findall(report)]


def _parse_json(raw: str) -> Dict[str, Any]:
    """Parse a JSON object from an LLM response, tolerating code fences."""
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("LLM did not return a JSON object.")
    parsed = json.loads(cleaned[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("LLM JSON response must be an object.")
    return parsed


def _compact(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."
