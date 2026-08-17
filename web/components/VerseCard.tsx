"use client";

import { useState } from "react";
import type { VerseCitation } from "@/lib/api";

/**
 * Verse cards render ONLY from `verse_citations` returned by the backend
 * — never parsed out of the model's prose. That keeps the citation wall
 * intact all the way to the screen.
 *
 * Hindi shows on expand when the card has it (Phase 5 tier-A fill).
 */
export default function VerseCard({ citation }: { citation: VerseCitation }) {
  const [open, setOpen] = useState(false);
  const translation = citation.translation_en?.trim() ?? "";
  const hindi = citation.translation_hi?.trim() ?? "";
  const oneLine =
    translation.length > 96 ? `${translation.slice(0, 96).trimEnd()}…` : translation;

  return (
    <button
      type="button"
      onClick={() => setOpen((v) => !v)}
      aria-expanded={open}
      className="w-full text-left rounded-lg border border-gold/25 bg-gold-soft/40 px-3.5 py-2.5
                 transition-colors hover:border-gold/45 focus:outline-none focus-visible:ring-1
                 focus-visible:ring-gold/60"
    >
      <div className="flex items-baseline justify-between gap-3">
        <span className="font-display text-[0.95rem] tracking-wide text-gold">
          Bhagavad Gita {citation.chapter}.{citation.verse}
        </span>
        <span className="text-[0.68rem] uppercase tracking-[0.14em] text-ink-dim">
          {open ? "less" : "more"}
        </span>
      </div>

      {translation && (
        <p className="mt-1.5 text-[0.88rem] leading-relaxed text-ink-dim">
          {open ? translation : oneLine}
        </p>
      )}

      {open && hindi && (
        <p
          lang="hi"
          className="mt-2.5 border-t border-gold/15 pt-2.5 text-[0.88rem] leading-[1.85] text-ink-dim"
        >
          {hindi}
        </p>
      )}
    </button>
  );
}
