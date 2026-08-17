"use client";

import type { StoredMessage } from "@/lib/session";
import Transcript from "./Transcript";

/** Full-screen transcript — replaces the presence stage entirely. */
export default function FullChatView({
  messages,
  onBack,
}: {
  messages: StoredMessage[];
  onBack: () => void;
}) {
  return (
    <div
      className="relative flex h-full min-h-0 min-w-0 flex-1 flex-col overflow-hidden
                    rounded-none md:rounded-2xl"
      style={{ background: "rgba(5, 13, 26, 0.9)" }}
    >
      <div className="glass-strong flex shrink-0 items-center justify-between border-b border-white/10
                      px-4 py-3 md:px-5">
        <button
          type="button"
          onClick={onBack}
          className="flex items-center gap-2 rounded-full border border-white/15 px-3 py-1.5
                     text-[0.78rem] tracking-wide text-ink-dim transition-colors hover:text-gold"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M15 18l-6-6 6-6" />
          </svg>
          Back to presence
        </button>
        <span className="font-body text-[0.78rem] uppercase tracking-[0.18em] text-ink-dim">
          Full chat
        </span>
      </div>

      <div
        className="flex min-h-0 flex-1 flex-col"
        style={{
          background:
            "linear-gradient(to bottom, rgba(10, 24, 48, 0.8), rgba(5, 13, 26, 0.9))",
        }}
      >
        <Transcript messages={messages} pausing={false} />
      </div>
    </div>
  );
}
