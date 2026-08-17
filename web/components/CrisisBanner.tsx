"use client";

/**
 * Crisis chrome: calm steel, never alarm-red. The backend's helpline text
 * is always shown as text first (it is the primary channel); voice is
 * secondary. No playful avatar energy while this is on screen.
 */
export default function CrisisBanner() {
  return (
    <div
      role="note"
      className="mb-2 flex items-center gap-2.5 rounded-md border border-crisis/35
                 bg-crisis/10 px-3.5 py-2"
    >
      <span
        className="inline-block h-1.5 w-1.5 shrink-0 rounded-full"
        style={{ background: "var(--crisis)" }}
      />
      <p className="text-[0.82rem] leading-relaxed text-crisis">
        Please reach a real person. The numbers below are staffed by people who can help right
        now.
      </p>
    </div>
  );
}
