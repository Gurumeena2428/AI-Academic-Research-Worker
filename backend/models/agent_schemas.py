from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    task: str = Field(..., min_length=5, description="Natural-language task for the autonomous research worker")
    document_ids: Optional[List[str]] = None


class AgentStepOut(BaseModel):
    step: int
    action: str
    tool: str
    input: Dict[str, Any]
    observation: str
    success: bool
    retry: int = 0


class AgentResponse(BaseModel):
    run_id: str
    task: str
    status: str
    report: str
    plan: List[str]
    steps: List[AgentStepOut]
    sources: List[Dict[str, Any]]
    verified: bool
    retries: int
