"use client";

/**
 * Glass confirmation modal for leaving an active conversation.
 */
export default function ConfirmDialog({
  open,
  title,
  body,
  confirmLabel = "Leave",
  cancelLabel = "Stay",
  onConfirm,
  onCancel,
}: {
  open: boolean;
  title: string;
  body: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#050d1a]/60 p-4 backdrop-blur-[3px]"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-title"
    >
      <div className="glass-strong w-full max-w-sm rounded-2xl px-5 py-5 shadow-2xl">
        <h2 id="confirm-title" className="font-body font-medium text-[1.15rem] text-ink">
          {title}
        </h2>
        <p className="mt-2 text-[0.9rem] leading-relaxed text-ink-dim">{body}</p>
        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-full border border-white/15 px-4 py-2 text-[0.8rem]
                       text-ink-dim transition-colors hover:text-ink"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="rounded-full border border-gold/40 bg-gold/20 px-4 py-2 text-[0.8rem]
                       text-gold transition-colors hover:bg-gold/30"
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
