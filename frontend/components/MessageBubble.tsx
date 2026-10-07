"use client";

import { Bot, TriangleAlert, User } from "lucide-react";
import { ChatMessage } from "@/lib/types";
import SourceList from "./SourceList";

export default function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
          isUser ? "bg-brand-600 text-white" : "bg-white text-brand-600 ring-1 ring-slate-200"
        }`}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      <div
        className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm shadow-sm ${
          isUser
            ? "rounded-tr-sm bg-brand-600 text-white"
            : message.isError
              ? "rounded-tl-sm bg-red-50 text-red-700 ring-1 ring-red-200"
              : "rounded-tl-sm bg-white text-slate-800 ring-1 ring-slate-200"
        }`}
      >
        {message.isError && (
          <div className="mb-1 flex items-center gap-1.5 text-xs font-semibold">
            <TriangleAlert className="h-3.5 w-3.5" /> Something went wrong
          </div>
        )}
        <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>

        {!isUser && !message.grounded && !message.isError && (
          <p className="mt-2 text-xs italic text-amber-600">
            No matching information was found in your uploaded documents.
          </p>
        )}

        {!isUser && message.sources && <SourceList sources={message.sources} />}
      </div>
    </div>
  );
}
