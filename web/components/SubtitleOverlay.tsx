"use client";

import type { VerseCitation } from "@/lib/api";
import VerseCard from "./VerseCard";

export type CaptionFrame = {
  /** Single subtitle row (advances with speech). */
  text: string;
};

/**
 * Movie-style subtitles over presence.
 * One row at a time — no multi-line dump, no word-by-word flash.
 */
export default function SubtitleOverlay({
  caption,
  crisisText,
  crisisActive,
  onDismissCrisis,
  citations,
  citeOpen,
  onToggleCite,
}: {
  caption: CaptionFrame | null;
  crisisText: string | null;
  crisisActive: boolean;
  onDismissCrisis?: () => void;
  citations?: VerseCitation[];
  citeOpen: boolean;
  onToggleCite: () => void;
}) {
  if (crisisActive && crisisText) {
    return (
      <div className="mb-4 flex w-full max-w-[36rem] flex-col items-center gap-3">
        <div
          className="glass-strong w-full rounded-2xl px-5 py-4 text-left"
          role="alert"
        >
          <p className="whitespace-pre-wrap font-body text-[1rem] leading-[1.7] text-crisis">
            {crisisText}
          </p>
          {onDismissCrisis && (
            <button
              type="button"
              onClick={onDismissCrisis}
              className="mt-3 text-[0.72rem] uppercase tracking-[0.14em] text-ink-dim
                         transition-colors hover:text-ink"
            >
              Continue
            </button>
          )}
        </div>
      </div>
    );
  }

  const showCaption = Boolean(caption?.text?.trim());
  const hasCite = Boolean(citations && citations.length > 0);

  if (!showCaption && !citeOpen) return null;

  return (
    <div className="mb-4 flex w-full max-w-[36rem] flex-col items-center gap-2">
      {showCaption && (
        <div className="relative flex w-full items-end justify-center gap-2">
          <p
            className="glass max-w-full overflow-hidden text-ellipsis whitespace-nowrap
                       rounded-2xl px-5 py-3 text-center font-body text-[1.02rem]
                       leading-none text-ink/92"
            aria-live="off"
          >
            {caption!.text}
          </p>

          {hasCite && (
            <button
              type="button"
              onClick={onToggleCite}
              aria-label="View verse citation"
              aria-pressed={citeOpen}
              className={`mb-1 grid h-9 w-9 shrink-0 place-items-center rounded-full border
                transition-all
                ${
                  citeOpen
                    ? "border-gold/60 bg-gold/25 text-gold shadow-[0_0_18px_rgba(158,201,232,0.45)]"
                    : "border-gold/40 bg-gold/15 text-gold animate-pulse-listen"
                }`}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
                <path d="M6 4h9a3 3 0 0 1 3 3v13H9a3 3 0 0 0-3 3V4z" />
                <path d="M6 4v16" />
              </svg>
            </button>
          )}
        </div>
      )}

      {citeOpen && citations && citations.length > 0 && (
        <div className="glass-strong w-full space-y-2 rounded-2xl p-3">
          {citations.map((c) => (
            <VerseCard key={c.id} citation={c} />
          ))}
        </div>
      )}
    </div>
  );
}
