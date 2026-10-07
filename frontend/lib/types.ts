// Shared types, mirroring the Pydantic schemas in backend/models/schemas.py
// so the frontend and backend stay in sync.

export interface DocumentItem {
  id: string;
  filename: string;
  num_pages: number;
  num_chunks: number;
  uploaded_at: string;
  status: "processing" | "ready" | "failed";
}

export interface SourceChunk {
  document_id: string;
  filename: string;
  page_number: number;
  chunk_id: string;
  text: string;
  similarity_score: number;
}

export interface AskResponse {
  answer: string;
  sources: SourceChunk[];
  grounded: boolean;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceChunk[];
  grounded?: boolean;
  isError?: boolean;
}

export interface AgentStep {
  step: number;
  action: string;
  tool: string;
  input: Record<string, unknown>;
  observation: string;
  success: boolean;
  retry: number;
}

export interface AgentResponse {
  run_id: string;
  task: string;
  status: "completed" | "partial" | "failed";
  report: string;
  plan: string[];
  steps: AgentStep[];
  sources: SourceChunk[];
  verified: boolean;
  retries: number;
}
