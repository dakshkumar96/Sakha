"use client";

import type { ReactNode } from "react";

export type PresenceState = "waiting" | "listening" | "processing" | "speaking";

// Bump query when the encode changes so browsers don't keep a soft cache.
const SRC = "/videos/krishna-presence.mp4?v=hq1440";
const POSTER = "/images/krishna-presence-poster.jpg?v=1";

/**
 * Full-bleed presence video — fills the stage edge-to-edge.
 * Native forward loop only (no reverse playback).
 */
export function CosmicStage({
  children,
}: {
  children: ReactNode;
  /** Kept for call sites; unused (no visual effects). */
  state?: PresenceState;
}) {
  return (
    <div className="relative flex h-full min-h-0 min-w-0 flex-1 flex-col rounded-none bg-[#050d1a] md:rounded-2xl">
      {/* Clip video only — keep UI overflow so language menu isn't cut off */}
      <div
        className="pointer-events-none absolute inset-0 overflow-hidden rounded-[inherit]"
        aria-hidden
      >
        <video
          key={SRC}
          src={SRC}
          poster={POSTER}
          autoPlay
          muted
          loop
          playsInline
          preload="auto"
          className="stage-video absolute inset-0 block h-full w-full max-w-none select-none"
        />
      </div>
      <div className="relative z-10 flex min-h-0 flex-1 flex-col overflow-visible stage-settle">
        {children}
      </div>
    </div>
  );
}
