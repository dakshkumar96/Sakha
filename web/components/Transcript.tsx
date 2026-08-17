"use client";

import { useEffect, useRef } from "react";
import type { StoredMessage } from "@/lib/session";
import MessageBubble from "./MessageBubble";
import MindfulPause from "./MindfulPause";

export default function Transcript({
  messages,
  pausing,
}: {
  messages: StoredMessage[];
  pausing: boolean;
}) {
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length, pausing]);

  return (
    <div className="transcript-scroll flex-1 overflow-y-auto px-4 md:px-6">
      <div className="mx-auto flex w-full max-w-[680px] flex-col gap-6 pb-6 pt-2">
        {messages.map((m, i) => (
          <MessageBubble key={`${m.role}-${i}`} message={m} />
        ))}
        {pausing && <MindfulPause />}
        <div ref={endRef} />
      </div>
    </div>
  );
}
