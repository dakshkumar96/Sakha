"use client";

/**
 * The mindful pause. The UI never snaps a reply into place — this holds
 * the moment for a beat so the companion feels like it considered you.
 */
export default function MindfulPause() {
  return (
    <div className="flex items-center gap-1.5 py-1" aria-label="Considering">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="inline-block h-1.5 w-1.5 rounded-full bg-gold/70 animate-breathe"
          style={{ animationDelay: `${i * 0.28}s` }}
        />
      ))}
    </div>
  );
}
