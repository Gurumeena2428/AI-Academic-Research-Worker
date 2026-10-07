"""API endpoint for the autonomous research-task worker."""

from fastapi import APIRouter, HTTPException

from backend.agent.service import run_agent
from backend.models.agent_schemas import AgentRequest, AgentResponse, AgentStepOut

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/run", response_model=AgentResponse)
def run_research_agent(request: AgentRequest):
    try:
        result = run_agent(request.task, document_ids=request.document_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {exc}") from exc

    return AgentResponse(
        run_id=result.run_id,
        task=result.task,
        status=result.status,
        report=result.report,
        plan=result.plan,
        steps=[AgentStepOut(**step.__dict__) for step in result.steps],
        sources=result.sources,
        verified=result.verified,
        retries=result.retries,
    )
