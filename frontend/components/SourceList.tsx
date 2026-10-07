"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, FileText } from "lucide-react";
import { SourceChunk } from "@/lib/types";

export default function SourceList({ sources }: { sources: SourceChunk[] }) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (sources.length === 0) return null;

  return (
    <div className="mt-3 border-t border-slate-200 pt-2">
      <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
        Sources
      </p>
      <ul className="flex flex-col gap-1">
        {sources.map((source) => {
          const isOpen = expandedId === source.chunk_id;
          return (
            <li key={source.chunk_id} className="rounded-md bg-slate-50 px-2 py-1.5">
              <button
                className="flex w-full items-center justify-between gap-2 text-left"
                onClick={() => setExpandedId(isOpen ? null : source.chunk_id)}
              >
                <span className="flex min-w-0 items-center gap-1.5 text-xs text-slate-600">
                  <FileText className="h-3.5 w-3.5 shrink-0 text-brand-600" />
                  <span className="truncate">
                    {source.filename} &mdash; Page {source.page_number}
                  </span>
                </span>
                <span className="flex shrink-0 items-center gap-1 text-[10px] text-slate-400">
                  {Math.round(source.similarity_score * 100)}% match
                  {isOpen ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                </span>
              </button>
              {isOpen && (
                <p className="mt-1.5 whitespace-pre-wrap text-xs leading-relaxed text-slate-600">
                  {source.text}
                </p>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
