// Web Speech API (STT) wrapper. Browser-only by product decision —
// Chrome/Edge primary. Silence ends a turn: finalize, send, mic OFF.
// No infinite auto-restart while "hot".

import { langGuess } from "@/lib/langGuess";

type SpeechRecognitionLike = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: ((e: any) => void) | null;
  onerror: ((e: any) => void) | null;
  onend: (() => void) | null;
};

function getConstructor(): (new () => SpeechRecognitionLike) | null {
  if (typeof window === "undefined") return null;
  const w = window as any;
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

export function isSpeechSupported(): boolean {
  return getConstructor() !== null;
}

export type SttHandlers = {
  onInterim: (text: string) => void;
  onFinal: (text: string) => void;
  onError: (kind: "not-allowed" | "other") => void;
  onEnd: () => void;
};

export class SpeechListener {
  private recognition: SpeechRecognitionLike | null = null;
  private finalText = "";
  private intentionalStop = false;
  private handlers: SttHandlers | null = null;
  private lang: "en" | "hi" = "en";
  private switchedToHi = false;
  private silenceTimer: ReturnType<typeof setTimeout> | null = null;
  /** After first final chunk, wait this long of quiet before ending the turn. */
  private static readonly SILENCE_MS = 1100;

  start(lang: "en" | "hi", handlers: SttHandlers): boolean {
    const Ctor = getConstructor();
    if (!Ctor) return false;

    this.abortInternal(false);
    this.finalText = "";
    this.intentionalStop = false;
    this.handlers = handlers;
    this.lang = lang;
    this.switchedToHi = lang === "hi";

    return this._begin(Ctor);
  }

  private clearSilenceTimer(): void {
    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
      this.silenceTimer = null;
    }
  }

  private scheduleSilenceEnd(): void {
    this.clearSilenceTimer();
    this.silenceTimer = setTimeout(() => {
      this.silenceTimer = null;
      // Browser silence detected after a final phrase — end the turn.
      this.finishTurn();
    }, SpeechListener.SILENCE_MS);
  }

  private finishTurn(): void {
    this.intentionalStop = true;
    this.clearSilenceTimer();
    const handlers = this.handlers;
    const text = this.finalText.trim();
    if (this.recognition) {
      try {
        this.recognition.onend = null;
        this.recognition.onresult = null;
        this.recognition.onerror = null;
        this.recognition.stop();
      } catch {
        // ignore
      }
      this.recognition = null;
    }
    if (handlers) {
      if (text) handlers.onFinal(text);
      handlers.onEnd();
    }
    this.handlers = null;
  }

  private _begin(Ctor: new () => SpeechRecognitionLike): boolean {
    const handlers = this.handlers;
    if (!handlers) return false;

    const rec = new Ctor();
    rec.lang = this.lang === "hi" ? "hi-IN" : "en-US";
    // continuous true until we intentionally stop after silence / manual stop.
    rec.continuous = true;
    rec.interimResults = true;

    rec.onresult = (event: any) => {
      let interim = "";
      let gotFinal = false;
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i];
        const transcript = result[0]?.transcript ?? "";
        if (result.isFinal) {
          this.finalText = `${this.finalText} ${transcript}`.replace(/\s+/g, " ").trim();
          gotFinal = true;
        } else {
          interim += transcript;
        }
      }
      const live = `${this.finalText} ${interim}`.replace(/\s+/g, " ").trim();
      handlers.onInterim(live);

      // Auto-switch to Hindi once if Devanagari appears mid-session.
      if (!this.switchedToHi && live && langGuess(live) === "hi") {
        this.switchedToHi = true;
        this.lang = "hi";
        this.restartWithLang("hi");
        return;
      }

      if (gotFinal) {
        this.scheduleSilenceEnd();
      } else if (interim) {
        // Keep listening — cancel silence timer while they speak.
        this.clearSilenceTimer();
      }
    };

    rec.onerror = (event: any) => {
      const err = event?.error as string | undefined;
      if (err === "not-allowed" || err === "service-not-allowed") {
        this.intentionalStop = true;
        this.clearSilenceTimer();
        handlers.onError("not-allowed");
        return;
      }
      if (err === "aborted" || err === "no-speech") {
        return;
      }
      handlers.onError("other");
    };

    rec.onend = () => {
      // No auto-restart: silence / browser end → finish the turn.
      if (this.intentionalStop) {
        this.recognition = null;
        return;
      }
      this.clearSilenceTimer();
      const text = this.finalText.trim();
      this.recognition = null;
      if (text) handlers.onFinal(text);
      handlers.onEnd();
      this.handlers = null;
    };

    this.recognition = rec;
    try {
      rec.start();
      return true;
    } catch {
      return false;
    }
  }

  private restartWithLang(lang: "en" | "hi"): void {
    const Ctor = getConstructor();
    const handlers = this.handlers;
    if (!Ctor || !handlers) return;
    const keep = this.finalText;
    // Soft restart without treating as intentional send.
    if (this.recognition) {
      try {
        this.recognition.onend = null;
        this.recognition.stop();
      } catch {
        // ignore
      }
      this.recognition = null;
    }
    this.lang = lang;
    this.finalText = keep;
    this.intentionalStop = false;
    this._begin(Ctor);
  }

  /** Manual off — still finalize/send any captured text via onEnd path. */
  stop(): void {
    if (this.intentionalStop && !this.recognition) return;
    if (!this.recognition && !this.handlers) return;
    this.finishTurn();
  }

  private abortInternal(_send: boolean): void {
    this.intentionalStop = true;
    this.clearSilenceTimer();
    if (this.recognition) {
      try {
        this.recognition.onend = null;
        this.recognition.onresult = null;
        this.recognition.onerror = null;
        this.recognition.abort();
      } catch {
        // ignore
      }
      this.recognition = null;
    }
  }
}
