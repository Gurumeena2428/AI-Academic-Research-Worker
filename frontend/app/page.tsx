"use client";

import { useCallback, useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import ChatWindow from "@/components/ChatWindow";
import AgentPanel from "@/components/AgentPanel";
import { askQuestion, deleteDocument, listDocuments, uploadDocuments } from "@/lib/api";
import { ChatMessage, DocumentItem } from "@/lib/types";

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export default function HomePage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isAsking, setIsAsking] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [mode, setMode] = useState<"chat" | "agent">("agent");

  const refreshDocuments = useCallback(async () => {
    try {
      const docs = await listDocuments();
      setDocuments(docs);
      setLoadError(null);
    } catch (err) {
      setLoadError(
        err instanceof Error
          ? `Could not reach the backend: ${err.message}`
          : "Could not reach the backend."
      );
    }
  }, []);

  useEffect(() => {
    refreshDocuments();
  }, [refreshDocuments]);

  async function handleUpload(files: File[]) {
    try {
      const docs = await uploadDocuments(files);
      setDocuments(docs);
      setLoadError(null);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Upload failed.");
    }
  }

  async function handleDelete(id: string) {
    setDeletingId(id);
    try {
      await deleteDocument(id);
      await refreshDocuments();
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Delete failed.");
    } finally {
      setDeletingId(null);
    }
  }

  async function handleSend(question: string) {
    const userMessage: ChatMessage = { id: generateId(), role: "user", content: question };
    setMessages((prev) => [...prev, userMessage]);
    setIsAsking(true);

    try {
      const response = await askQuestion(question);
      setMessages((prev) => [
        ...prev,
        {
          id: generateId(),
          role: "assistant",
          content: response.answer,
          sources: response.sources,
          grounded: response.grounded,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: generateId(),
          role: "assistant",
          content: err instanceof Error ? err.message : "Failed to get an answer.",
          isError: true,
        },
      ]);
    } finally {
      setIsAsking(false);
    }
  }

  return (
    <main className="flex h-screen w-screen overflow-hidden">
      <Sidebar
        documents={documents}
        onUpload={handleUpload}
        onDelete={handleDelete}
        deletingId={deletingId}
      />
      <div className="flex flex-1 flex-col">
        {loadError && (
          <div className="border-b border-red-200 bg-red-50 px-4 py-2 text-center text-xs text-red-600">
            {loadError}
          </div>
        )}
        <div className="flex items-center gap-1 border-b border-slate-200 bg-white px-4 py-2">
          <button onClick={() => setMode("agent")} className={`rounded-lg px-3 py-1.5 text-xs font-medium ${mode === "agent" ? "bg-brand-100 text-brand-700" : "text-slate-500 hover:bg-slate-100"}`}>Research Worker</button>
          <button onClick={() => setMode("chat")} className={`rounded-lg px-3 py-1.5 text-xs font-medium ${mode === "chat" ? "bg-brand-100 text-brand-700" : "text-slate-500 hover:bg-slate-100"}`}>Document Chat</button>
        </div>
        {mode === "agent" ? (
          <AgentPanel hasDocuments={documents.length > 0} />
        ) : (
          <ChatWindow
            messages={messages}
            onSend={handleSend}
            isAsking={isAsking}
            hasDocuments={documents.length > 0}
          />
        )}
      </div>
    </main>
  );
}
