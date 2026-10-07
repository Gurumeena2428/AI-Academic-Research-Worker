"use client";

import { BookOpenText } from "lucide-react";
import { DocumentItem } from "@/lib/types";
import UploadZone from "./UploadZone";
import DocumentList from "./DocumentList";

interface SidebarProps {
  documents: DocumentItem[];
  onUpload: (files: File[]) => Promise<void>;
  onDelete: (id: string) => void;
  deletingId: string | null;
}

export default function Sidebar({ documents, onUpload, onDelete, deletingId }: SidebarProps) {
  return (
    <aside className="flex h-full w-full max-w-xs flex-col border-r border-slate-200 bg-slate-50 p-4">
      <div className="mb-4 flex items-center gap-2">
        <BookOpenText className="h-6 w-6 text-brand-600" />
        <h1 className="text-base font-semibold text-slate-800">Research Workspace</h1>
      </div>

      <UploadZone onUpload={onUpload} />

      <div className="mt-2 flex items-center justify-between px-1">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
          Your Documents
        </h2>
        <span className="text-xs text-slate-400">{documents.length}</span>
      </div>

      <div className="flex-1 overflow-y-auto pr-1">
        <DocumentList documents={documents} onDelete={onDelete} deletingId={deletingId} />
      </div>
    </aside>
  );
}
