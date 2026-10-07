"use client";

import { FileText, Loader2, Trash2, CircleAlert } from "lucide-react";
import { DocumentItem } from "@/lib/types";

interface DocumentListProps {
  documents: DocumentItem[];
  onDelete: (id: string) => void;
  deletingId: string | null;
}

function StatusBadge({ status }: { status: DocumentItem["status"] }) {
  if (status === "processing") {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-amber-600">
        <Loader2 className="h-3 w-3 animate-spin" /> processing
      </span>
    );
  }
  if (status === "failed") {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-red-600">
        <CircleAlert className="h-3 w-3" /> failed
      </span>
    );
  }
  return <span className="text-xs text-emerald-600">ready</span>;
}

export default function DocumentList({ documents, onDelete, deletingId }: DocumentListProps) {
  if (documents.length === 0) {
    return (
      <p className="mt-4 text-center text-sm text-slate-400">
        No documents uploaded yet.
      </p>
    );
  }

  return (
    <ul className="mt-4 flex flex-col gap-2">
      {documents.map((doc) => (
        <li
          key={doc.id}
          className="group flex items-start gap-3 rounded-lg border border-slate-200 bg-white p-3 shadow-sm"
        >
          <FileText className="mt-0.5 h-5 w-5 shrink-0 text-brand-600" />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-slate-800" title={doc.filename}>
              {doc.filename}
            </p>
            <div className="mt-0.5 flex items-center gap-2 text-xs text-slate-400">
              <span>{doc.num_pages} pages</span>
              <span>&middot;</span>
              <span>{doc.num_chunks} chunks</span>
              <span>&middot;</span>
              <StatusBadge status={doc.status} />
            </div>
          </div>
          <button
            onClick={() => onDelete(doc.id)}
            disabled={deletingId === doc.id}
            aria-label={`Delete ${doc.filename}`}
            className="shrink-0 rounded-md p-1.5 text-slate-400 opacity-0 transition-opacity hover:bg-red-50 hover:text-red-600 group-hover:opacity-100 disabled:opacity-50"
          >
            {deletingId === doc.id ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Trash2 className="h-4 w-4" />
            )}
          </button>
        </li>
      ))}
    </ul>
  );
}
