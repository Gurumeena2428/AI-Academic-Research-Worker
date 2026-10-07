"use client";

import { KeyboardEvent, useState } from "react";
import { Send } from "lucide-react";

interface ChatInputProps {
  onSend: (question: string) => void;
  disabled: boolean;
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");

  function submit() {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <div className="flex items-end gap-2 border-t border-slate-200 bg-white p-3">
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask a question about your uploaded documents…"
        rows={1}
        className="max-h-32 flex-1 resize-none rounded-xl border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
      />
      <button
        onClick={submit}
        disabled={disabled || !value.trim()}
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-white transition-colors hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-40"
        aria-label="Send question"
      >
        <Send className="h-4 w-4" />
      </button>
    </div>
  );
}
