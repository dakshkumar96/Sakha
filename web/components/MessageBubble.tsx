"use client";

import type { StoredMessage } from "@/lib/session";
import CrisisBanner from "./CrisisBanner";
import VerseCard from "./VerseCard";

export default function MessageBubble({ message }: { message: StoredMessage }) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end animate-fade-up">
        <div
          className="max-w-[82%] rounded-2xl rounded-br-md border border-white/10 bg-black/40
                     px-4 py-2.5 text-[0.95rem] leading-relaxed text-ink/90 shadow-lg backdrop-blur-md"
        >
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start animate-fade-up">
      <div className="max-w-[88%]">
        {message.isCrisis && <CrisisBanner />}
        <div
          className={`whitespace-pre-wrap text-[1rem] leading-[1.75] presence-readout ${
            message.isCrisis ? "text-crisis" : "text-ink/95"
          }`}
        >
          {message.content}
        </div>

        {message.citations && message.citations.length > 0 && (
          <div className="mt-3 space-y-2">
            {message.citations.map((c) => (
              <VerseCard key={c.id} citation={c} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
