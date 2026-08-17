"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { SpeechListener, isSpeechSupported } from "@/lib/speechRecognition";
import {
  setMicTipSeen,
  setSpeechLang,
  voiceEngineLang,
  SPEECH_LANG_OPTIONS,
  type SpeechLang,
} from "@/lib/prefs";

/**
 * Mic + text input + EN / HI / Hinglish.
 * Hinglish: Hindi voice; on-screen text is Hindi–English mix.
 */
export default function Composer({
  onSend,
  busy,
  onListeningChange,
  showMicTip = false,
  onMicTipConsumed,
  speechLang,
  onSpeechLangChange,
}: {
  onSend: (text: string) => void;
  busy: boolean;
  onListeningChange: (listening: boolean) => void;
  showMicTip?: boolean;
  onMicTipConsumed?: () => void;
  speechLang: SpeechLang;
  onSpeechLangChange: (lang: SpeechLang) => void;
}) {
  const [listening, setListening] = useState(false);
  const [textOpen, setTextOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const [sttSupported, setSttSupported] = useState(false);
  const [langOpen, setLangOpen] = useState(false);

  const listenerRef = useRef<SpeechListener | null>(null);
  const pendingRef = useRef("");
  const busyRef = useRef(busy);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const langMenuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    busyRef.current = busy;
  }, [busy]);

  useEffect(() => {
    setSttSupported(isSpeechSupported());
    listenerRef.current = new SpeechListener();
    return () => listenerRef.current?.stop();
  }, []);

  useEffect(() => {
    onListeningChange(listening);
  }, [listening, onListeningChange]);

  useEffect(() => {
    if (textOpen) inputRef.current?.focus();
  }, [textOpen]);

  useEffect(() => {
    if (!langOpen) return;
    function onPointerDown(e: MouseEvent | TouchEvent) {
      const root = langMenuRef.current;
      if (!root) return;
      if (e.target instanceof Node && !root.contains(e.target)) {
        setLangOpen(false);
      }
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setLangOpen(false);
    }
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("touchstart", onPointerDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("touchstart", onPointerDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [langOpen]);

  function consumeTip() {
    setMicTipSeen();
    onMicTipConsumed?.();
  }

  function sendIfReady(raw: string) {
    const text = raw.trim();
    if (!text || busyRef.current) return;
    pendingRef.current = "";
    setDraft("");
    setTextOpen(false);
    onSend(text);
  }

  function stopListening() {
    listenerRef.current?.stop();
    setListening(false);
  }

  function toggleMic() {
    if (busy) return;
    consumeTip();

    if (listening) {
      stopListening();
      return;
    }

    setTextOpen(false);
    setLangOpen(false);
    pendingRef.current = "";
    const ok = listenerRef.current?.start(voiceEngineLang(speechLang), {
      onInterim: (text) => {
        pendingRef.current = text;
      },
      onFinal: (text) => {
        pendingRef.current = text;
      },
      onError: () => {
        setListening(false);
        pendingRef.current = "";
      },
      onEnd: () => {
        setListening(false);
        const text = pendingRef.current;
        pendingRef.current = "";
        if (text.trim()) sendIfReady(text);
      },
    });
    if (ok) setListening(true);
  }

  function submitText(e?: FormEvent) {
    e?.preventDefault();
    if (busy) return;
    sendIfReady(draft);
  }

  function pickSpeechLang(next: SpeechLang) {
    if (busy || listening) return;
    setSpeechLang(next);
    onSpeechLangChange(next);
    setLangOpen(false);
  }

  const currentLang =
    SPEECH_LANG_OPTIONS.find((o) => o.id === speechLang) ?? SPEECH_LANG_OPTIONS[0];

  const placeholder =
    speechLang === "hi"
      ? "जो कहना है, लिख दो"
      : speechLang === "hinglish"
        ? "Jo kehna hai, likh do"
        : "Say what you need to say";

  const micTip =
    speechLang === "hi"
      ? "माइक दबाकर बोलें"
      : speechLang === "hinglish"
        ? "Mic dabao, bolo"
        : "Tap the mic to speak";

  return (
    <div className="flex w-full flex-col items-center gap-2">
      {textOpen && (
        <form
          onSubmit={submitText}
          className="glass flex w-full max-w-[420px] items-center gap-2 rounded-2xl px-3 py-2"
        >
          <input
            ref={inputRef}
            type="text"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            disabled={busy}
            placeholder={placeholder}
            className="min-w-0 flex-1 bg-transparent px-1 py-1.5 font-body text-[0.95rem]
                       text-ink outline-none placeholder:text-ink-dim/55 disabled:opacity-40"
            autoComplete="off"
          />
          <button
            type="submit"
            disabled={busy || !draft.trim()}
            aria-label="Send"
            className="grid h-9 w-9 shrink-0 place-items-center rounded-full border border-white/20
                       text-gold transition-colors hover:bg-white/10 disabled:opacity-35"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M5 12h14M13 6l6 6-6 6" />
            </svg>
          </button>
        </form>
      )}

      <div className="relative flex flex-col items-center">
        {showMicTip && sttSupported && (
          <div
            className="glass absolute bottom-[calc(100%+0.55rem)] left-1/2 z-20 -translate-x-1/2
                       whitespace-nowrap rounded-full px-3 py-1.5 text-[0.72rem] tracking-wide text-ink/90"
            role="status"
          >
            {micTip}
          </div>
        )}

        <div className="glass flex items-center gap-2.5 rounded-full px-3 py-2.5">
          {sttSupported ? (
            <button
              type="button"
              onClick={toggleMic}
              disabled={busy}
              aria-label={listening ? "Turn mic off" : "Turn mic on"}
              aria-pressed={listening}
              className={`grid h-14 w-14 place-items-center rounded-full border transition-all
                ${
                  listening
                    ? "border-gold/80 bg-gold/25 text-gold shadow-[0_0_28px_rgba(158,201,232,0.4)] animate-pulse-listen"
                    : busy
                      ? "border-white/10 text-ink-dim/40"
                      : "border-white/25 bg-white/[0.08] text-gold hover:border-gold/60 hover:bg-white/[0.14]"
                }
                disabled:cursor-not-allowed`}
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
                <rect x="9" y="2" width="6" height="12" rx="3" />
                <path d="M5 11a7 7 0 0 0 14 0" />
                <path d="M12 18v3" />
              </svg>
            </button>
          ) : null}

          <button
            type="button"
            onClick={() => {
              if (busy) return;
              if (listening) stopListening();
              setLangOpen(false);
              setTextOpen((v) => !v);
            }}
            disabled={busy}
            aria-label={textOpen ? "Hide text input" : "Type instead"}
            aria-pressed={textOpen}
            className={`grid h-11 w-11 place-items-center rounded-full border transition-colors
              ${
                textOpen
                  ? "border-gold/50 bg-white/12 text-gold"
                  : "border-white/18 bg-white/[0.06] text-ink-dim hover:border-gold/40 hover:text-gold"
              }
              disabled:opacity-40`}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/images/chat-icon.png"
              alt=""
              aria-hidden
              className={`h-[18px] w-[18px] object-contain transition-opacity
                ${textOpen ? "opacity-100" : "opacity-80"}`}
            />
          </button>

          <div ref={langMenuRef} className="relative">
            <button
              type="button"
              onClick={() => {
                if (busy || listening) return;
                setLangOpen((v) => !v);
              }}
              disabled={busy || listening}
              aria-label={`Spoken language: ${currentLang.label}`}
              aria-haspopup="listbox"
              aria-expanded={langOpen}
              title="Language for voice and on-screen text"
              className="flex items-center gap-1.5 rounded-full border border-white/18 bg-white/[0.06]
                         px-3 py-2 text-[0.8rem] text-ink-dim transition-colors hover:border-gold/45
                         hover:text-gold disabled:opacity-40"
            >
              <span className="font-medium tracking-wide text-ink/90">{currentLang.label}</span>
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className={`opacity-70 transition-transform ${langOpen ? "rotate-180" : ""}`}
                aria-hidden
              >
                <path d="M6 9l6 6 6-6" />
              </svg>
            </button>

            {langOpen && (
              <div
                role="listbox"
                aria-label="Spoken language"
                className="glass-strong absolute bottom-[calc(100%+0.55rem)] right-0 z-50 w-[240px]
                           overflow-hidden rounded-2xl py-1.5 shadow-[0_12px_40px_rgba(0,0,0,0.45)]"
              >
                {SPEECH_LANG_OPTIONS.map((opt) => {
                  const active = speechLang === opt.id;
                  return (
                    <button
                      key={opt.id}
                      type="button"
                      role="option"
                      aria-selected={active}
                      onClick={() => pickSpeechLang(opt.id)}
                      className={`flex w-full items-start gap-2.5 px-3 py-2.5 text-left transition-colors
                        ${active ? "bg-white/12" : "hover:bg-white/[0.07]"}`}
                    >
                      <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center text-gold">
                        {active ? (
                          <svg
                            width="14"
                            height="14"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2.4"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            aria-hidden
                          >
                            <path d="M5 12.5l4.2 4.2L19 7.5" />
                          </svg>
                        ) : null}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block text-[0.92rem] font-semibold leading-snug text-ink">
                          {opt.label}
                        </span>
                        <span className="mt-0.5 block text-[0.78rem] leading-snug text-ink-dim">
                          {opt.subtitle}
                        </span>
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
