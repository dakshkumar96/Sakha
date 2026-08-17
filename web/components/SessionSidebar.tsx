"use client";

import Link from "next/link";
import { formatThreadDate, type Thread } from "@/lib/session";

export default function SessionSidebar({
  threads,
  activeId,
  open,
  onSelect,
  onNew,
  onDelete,
  onClose,
}: {
  threads: Thread[];
  activeId: string | null;
  open: boolean;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  onClose: () => void;
}) {
  const sorted = [...threads].sort((a, b) => b.updatedAt - a.updatedAt);

  return (
    <>
      {/* Mobile scrim */}
      {open && (
        <button
          type="button"
          aria-label="Close history"
          onClick={onClose}
          className="fixed inset-0 z-30 bg-[#050d1a]/55 backdrop-blur-[2px] md:hidden"
        />
      )}

      <aside
        className={`fixed inset-y-3 left-3 z-40 flex w-[min(272px,calc(100vw-1.5rem))] flex-col
                    overflow-hidden rounded-2xl glass-strong transition-transform duration-300
                    md:static md:z-auto md:my-0 md:ml-0 md:mr-3 md:w-[264px] md:translate-x-0 md:self-stretch
                    ${open ? "translate-x-0" : "-translate-x-[calc(100%+1.25rem)]"}`}
      >
        <div className="flex items-center justify-between border-b border-white/12 px-4 pb-3 pt-5">
          <div className="flex flex-col items-start leading-none">
            <p className="onboard-accent font-sakha text-[1.3rem] font-bold leading-none tracking-[0.06em] md:text-[1.35rem]">
              Sakha
            </p>
            <p className="mt-0.5 font-body text-[0.68rem] uppercase leading-none tracking-[0.18em] text-ink-dim">
              Conversations
            </p>
          </div>
          <button
            type="button"
            onClick={onNew}
            aria-label="New conversation"
            className="grid h-7 w-7 place-items-center rounded-full border border-white/20 text-gold
                       transition-colors hover:bg-white/10"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M12 5v14M5 12h14" />
            </svg>
          </button>
        </div>

        <nav className="transcript-scroll flex-1 overflow-y-auto px-2.5 py-3">
          {sorted.length === 0 && (
            <p className="px-2 py-3 text-[0.8rem] leading-relaxed text-ink-dim/80">
              Nothing yet. Whatever you say stays in this browser.
            </p>
          )}

          {sorted.map((t) => {
            const isActive = t.id === activeId;
            return (
              <div
                key={t.id}
                className={`group mb-1 flex w-full items-start gap-1 rounded-xl transition-colors
                  ${
                    isActive
                      ? "bg-white/14 text-ink shadow-[inset_0_0_0_1px_rgba(255,255,255,0.12)]"
                      : "text-ink-dim hover:bg-white/[0.07] hover:text-ink/90"
                  }`}
              >
                <button
                  type="button"
                  onClick={() => onSelect(t.id)}
                  className="min-w-0 flex-1 px-2.5 py-2 text-left"
                >
                  <span className="block truncate text-[0.87rem] leading-snug">{t.title}</span>
                  <span className="mt-0.5 block text-[0.7rem] text-ink-dim/65">
                    {formatThreadDate(t.updatedAt)}
                  </span>
                </button>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(t.id);
                  }}
                  aria-label={`Delete conversation: ${t.title}`}
                  title="Delete conversation"
                  className="mr-1.5 mt-1.5 grid h-7 w-7 shrink-0 place-items-center rounded-full
                             text-ink-dim/50 opacity-100 transition-colors hover:bg-white/10
                             hover:text-ink md:opacity-0 md:group-hover:opacity-100
                             md:focus-visible:opacity-100"
                >
                  <svg
                    width="13"
                    height="13"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M3 6h18" />
                    <path d="M8 6V4h8v2" />
                    <path d="M19 6l-1 14H6L5 6" />
                    <path d="M10 11v6M14 11v6" />
                  </svg>
                </button>
              </div>
            );
          })}
        </nav>

        <div className="border-t border-white/10 px-4 py-3">
          <p className="font-body text-[0.72rem] tracking-wide text-ink-dim">
            <Link href="/about" className="transition-colors hover:text-gold">
              About
            </Link>
            <span className="mx-2 text-white/20">·</span>
            <Link href="/privacy" className="transition-colors hover:text-gold">
              Privacy
            </Link>
          </p>
        </div>
      </aside>
    </>
  );
}
