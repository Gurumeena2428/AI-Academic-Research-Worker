"use client";

import { useEffect, useRef } from "react";
import { Loader2, MessageCircleQuestion } from "lucide-react";
import { ChatMessage } from "@/lib/types";
import MessageBubble from "./MessageBubble";
import ChatInput from "./ChatInput";

interface ChatWindowProps {
  messages: ChatMessage[];
  onSend: (question: string) => void;
  isAsking: boolean;
  hasDocuments: boolean;
}

export default function ChatWindow({ messages, onSend, isAsking, hasDocuments }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isAsking]);

  return (
    <section className="flex h-full flex-1 flex-col bg-slate-100">
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center text-slate-400">
            <MessageCircleQuestion className="mb-3 h-10 w-10" />
            <p className="text-sm font-medium">
              {hasDocuments
                ? "Ask anything about your uploaded documents."
                : "Upload a PDF on the left, then ask a question about it."}
            </p>
            <p className="mt-1 text-xs">
              Example: &ldquo;What is the difference between TCP and UDP?&rdquo;
            </p>
          </div>
        ) : (
          <div className="mx-auto flex max-w-3xl flex-col gap-5">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {isAsking && (
              <div className="flex items-center gap-2 pl-11 text-sm text-slate-400">
                <Loader2 className="h-4 w-4 animate-spin" />
                Thinking&hellip;
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="mx-auto w-full max-w-3xl">
        <ChatInput onSend={onSend} disabled={isAsking} />
      </div>
    </section>
  );
}
