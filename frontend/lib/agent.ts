import { AgentResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function runAgent(task: string, documentIds?: string[]): Promise<AgentResponse> {
  const response = await fetch(`${API_URL}/api/agent/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task, document_ids: documentIds?.length ? documentIds : undefined }),
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {}
    throw new Error(detail);
  }
  return response.json() as Promise<AgentResponse>;
}
