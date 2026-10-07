// Thin fetch wrapper around the FastAPI backend. Kept in one file so the
// HTTP contract between frontend and backend is easy to see in one place.

import { AskResponse, DocumentItem } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // response body wasn't JSON; fall back to statusText
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export async function listDocuments(): Promise<DocumentItem[]> {
  const response = await fetch(`${API_URL}/api/documents`, { cache: "no-store" });
  const data = await handleResponse<{ documents: DocumentItem[] }>(response);
  return data.documents;
}

export async function uploadDocuments(files: File[]): Promise<DocumentItem[]> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  const response = await fetch(`${API_URL}/api/documents/upload`, {
    method: "POST",
    body: formData,
  });
  const data = await handleResponse<{ documents: DocumentItem[] }>(response);
  return data.documents;
}

export async function deleteDocument(documentId: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/documents/${documentId}`, {
    method: "DELETE",
  });
  await handleResponse(response);
}

export async function askQuestion(question: string): Promise<AskResponse> {
  const response = await fetch(`${API_URL}/api/chat/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  return handleResponse<AskResponse>(response);
}
