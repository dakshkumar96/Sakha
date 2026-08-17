// Companion voice playback.
//
// Preferred path: Kokoro mp3 from POST /tts (SpeechPlayer.play).
// Fallback: browser Speech Synthesis when Kokoro is down or Docker is missing.
// Captions advance word-by-word with speech (boundary events or timed progress).

export type SpeakHandlers = {
  onEnded?: () => void;
  /**
   * Fired as speech advances through the full word list.
   * `activeIndex` is which word is currently being spoken (0-based).
   */
  onWord?: (activeIndex: number, words: string[]) => void;
};

/** Split spoken text into display words (keeps punctuation on the token). */
export function tokenizeWords(text: string): string[] {
  return text
    .replace(/\s+/g, " ")
    .trim()
    .split(" ")
    .map((w) => w.trim())
    .filter(Boolean);
}

/** Map 0–1 audio progress → word index (weighted by word length). */
export function wordIndexForProgress(words: string[], progress: number): number {
  if (words.length <= 1) return 0;
  const p = Math.min(0.999, Math.max(0, progress));
  const weights = words.map((w) => Math.max(w.replace(/[^\p{L}\p{N}]/gu, "").length, 2));
  const total = weights.reduce((a, b) => a + b, 0) || 1;
  let acc = 0;
  for (let i = 0; i < words.length; i++) {
    acc += weights[i] / total;
    if (p < acc) return i;
  }
  return words.length - 1;
}

/** Map a character offset in `text` to a word index. */
export function wordIndexForChar(text: string, charIndex: number): number {
  const words = tokenizeWords(text);
  if (!words.length) return 0;
  if (charIndex <= 0) return 0;

  let cursor = 0;
  const clean = text.replace(/\s+/g, " ").trim();
  for (let i = 0; i < words.length; i++) {
    const start = cursor;
    const end = start + words[i].length;
    if (charIndex < end) return i;
    cursor = end;
    // skip one space between words
    if (cursor < clean.length && clean[cursor] === " ") cursor += 1;
  }
  return words.length - 1;
}

/** Which words belong on the current caption line around the active word. */
export function captionWindow(
  words: string[],
  activeIndex: number,
  maxWords = 8,
): { start: number; end: number; localActive: number } {
  if (!words.length) return { start: 0, end: 0, localActive: 0 };
  const idx = Math.min(Math.max(activeIndex, 0), words.length - 1);

  // Prefer sentence-ish windows that reflow when the active word reaches ~2/3 of the window.
  const windowSize = Math.min(maxWords, words.length);
  let start = Math.max(0, idx - Math.floor(windowSize * 0.55));
  let end = Math.min(words.length, start + windowSize);
  start = Math.max(0, end - windowSize);

  return { start, end, localActive: idx - start };
}

/** Split words into single-row caption chunks (by word count + char budget). */
export function buildCaptionLines(
  words: string[],
  maxWords = 8,
  maxChars = 54,
): string[][] {
  if (!words.length) return [];
  const lines: string[][] = [];
  let cur: string[] = [];
  let chars = 0;
  for (const w of words) {
    const nextChars = chars + (cur.length ? 1 : 0) + w.length;
    if (cur.length && (cur.length >= maxWords || nextChars > maxChars)) {
      lines.push(cur);
      cur = [w];
      chars = w.length;
    } else {
      cur.push(w);
      chars = nextChars;
    }
  }
  if (cur.length) lines.push(cur);
  return lines;
}

/** One subtitle row for the current spoken progress — whole line, then next. */
export function captionLineForProgress(
  words: string[],
  activeIndex: number,
  maxWords = 8,
  maxChars = 54,
): string {
  const lines = buildCaptionLines(words, maxWords, maxChars);
  if (!lines.length) return "";
  const idx = Math.min(Math.max(activeIndex, 0), words.length - 1);
  let cursor = 0;
  for (const line of lines) {
    if (idx < cursor + line.length) return line.join(" ");
    cursor += line.length;
  }
  return lines[lines.length - 1]!.join(" ");
}

function wordWeight(w: string): number {
  return Math.max(w.replace(/[^\p{L}\p{N}]/gu, "").length, 2);
}

/** 0–1 speech progress at the active spoken word (length-weighted). */
export function spokenProgressAt(words: string[], activeIndex: number): number {
  if (!words.length) return 0;
  const weights = words.map(wordWeight);
  const total = weights.reduce((a, b) => a + b, 0) || 1;
  const idx = Math.min(Math.max(activeIndex, 0), words.length - 1);
  let before = 0;
  for (let i = 0; i < idx; i++) before += weights[i]!;
  return Math.min(0.999, (before + weights[idx]! * 0.45) / total);
}

/** Split into sentences for voice↔caption alignment. */
export function splitSentences(text: string): string[] {
  const clean = text.replace(/\s+/g, " ").trim();
  if (!clean) return [];
  const parts = clean
    .split(/(?<=[.!?।…])\s+/)
    .map((s) => s.trim())
    .filter(Boolean);
  return parts.length ? parts : [clean];
}

/** Which spoken sentence contains word `activeIndex`. */
export function sentenceIndexForWord(
  sentences: string[],
  activeIndex: number,
): { sentenceIndex: number; localWordIndex: number } {
  if (!sentences.length) return { sentenceIndex: 0, localWordIndex: 0 };
  let offset = 0;
  for (let i = 0; i < sentences.length; i++) {
    const n = tokenizeWords(sentences[i]!).length;
    if (activeIndex < offset + n) {
      return { sentenceIndex: i, localWordIndex: Math.max(0, activeIndex - offset) };
    }
    offset += n;
  }
  const last = sentences.length - 1;
  const lastWords = tokenizeWords(sentences[last]!);
  return {
    sentenceIndex: last,
    localWordIndex: Math.max(0, lastWords.length - 1),
  };
}

/**
 * One caption row synced to speech.
 * Same text → word index. Different text (Hinglish) → sentence align + length-weighted progress.
 */
export function captionSyncedToSpeech(opts: {
  spokenText: string;
  captionText: string;
  activeSpokenIndex: number;
  maxWords?: number;
  maxChars?: number;
}): string {
  const {
    spokenText,
    captionText,
    activeSpokenIndex,
    maxWords = 8,
    maxChars = 54,
  } = opts;
  const captionWords = tokenizeWords(captionText);
  if (!captionWords.length) return "";

  const spokenWords = tokenizeWords(spokenText);
  if (!spokenWords.length) {
    return captionLineForProgress(captionWords, 0, maxWords, maxChars);
  }

  // Identical on-screen and spoken → perfect word sync.
  if (spokenText.replace(/\s+/g, " ").trim() === captionText.replace(/\s+/g, " ").trim()) {
    return captionLineForProgress(captionWords, activeSpokenIndex, maxWords, maxChars);
  }

  const spokenSentences = splitSentences(spokenText);
  const captionSentences = splitSentences(captionText);
  const { sentenceIndex, localWordIndex } = sentenceIndexForWord(
    spokenSentences,
    activeSpokenIndex,
  );

  // Prefer matching sentence when counts align (Hinglish rewrite keeps sentence order).
  if (
    captionSentences.length === spokenSentences.length &&
    captionSentences.length > 1
  ) {
    const capSent = captionSentences[sentenceIndex]!;
    const spokenSent = spokenSentences[sentenceIndex]!;
    const localSpoken = tokenizeWords(spokenSent);
    const localCaption = tokenizeWords(capSent);
    if (!localCaption.length) {
      return captionLineForProgress(captionWords, 0, maxWords, maxChars);
    }
    if (localSpoken.length <= 1) {
      return captionLineForProgress(localCaption, 0, maxWords, maxChars);
    }
    const localProgress = spokenProgressAt(localSpoken, localWordIndex);
    const localIdx = wordIndexForProgress(localCaption, localProgress);
    return captionLineForProgress(localCaption, localIdx, maxWords, maxChars);
  }

  // Fallback: global length-weighted progress across the full caption.
  const progress = spokenProgressAt(spokenWords, activeSpokenIndex);
  const capIdx = wordIndexForProgress(captionWords, progress);
  return captionLineForProgress(captionWords, capIdx, maxWords, maxChars);
}

export class SpeechPlayer {
  private audio: HTMLAudioElement | null = null;
  private objectUrl: string | null = null;
  private cancelled = false;
  private chunkTimer: ReturnType<typeof setTimeout> | null = null;
  private lineTimer: ReturnType<typeof setTimeout> | null = null;
  private rafId: number | null = null;
  private lastWordIndex = -1;

  private emitWord(
    index: number,
    words: string[],
    handlers: SpeakHandlers,
  ): void {
    if (this.cancelled || !words.length) return;
    const i = Math.min(Math.max(index, 0), words.length - 1);
    if (i === this.lastWordIndex) return;
    this.lastWordIndex = i;
    handlers.onWord?.(i, words);
  }

  /**
   * Play a Kokoro (or any) audio blob.
   * Words advance from audio time (length-weighted).
   */
  async play(
    blob: Blob,
    handlers: SpeakHandlers = {},
    words: string[] = [],
  ): Promise<boolean> {
    this.stop();
    this.cancelled = false;
    this.lastWordIndex = -1;

    const url = URL.createObjectURL(blob);
    this.objectUrl = url;

    const audio = new Audio(url);
    this.audio = audio;

    if (words.length) this.emitWord(0, words, handlers);

    const tick = () => {
      if (this.cancelled || !this.audio) return;
      const a = this.audio;
      if (a.duration && Number.isFinite(a.duration) && words.length) {
        const progress = a.currentTime / a.duration;
        this.emitWord(wordIndexForProgress(words, progress), words, handlers);
      }
      this.rafId = requestAnimationFrame(tick);
    };

    audio.onended = () => {
      this.stopRaf();
      this.cleanupAudio();
      if (!this.cancelled) {
        if (words.length) this.emitWord(words.length - 1, words, handlers);
        handlers.onEnded?.();
      }
    };
    audio.onerror = () => {
      this.stopRaf();
      this.cleanupAudio();
      if (!this.cancelled) handlers.onEnded?.();
    };

    try {
      await audio.play();
      this.rafId = requestAnimationFrame(tick);
      return true;
    } catch {
      this.cleanupAudio();
      return false;
    }
  }

  /**
   * Browser TTS — waits for voices, resumes if stuck, and delays after cancel
   * (Chrome often drops the first utterance if speak() follows cancel() instantly).
   */
  async speakBrowser(
    text: string,
    lang: "en" | "hi",
    handlers: SpeakHandlers = {},
    words?: string[],
  ): Promise<boolean> {
    if (typeof window === "undefined" || !window.speechSynthesis) {
      return false;
    }

    this.stop();
    this.cancelled = false;
    this.lastWordIndex = -1;

    const spoken = text.replace(/\s+/g, " ").trim();
    if (!spoken) return false;

    const wordList = words?.length ? words : tokenizeWords(spoken);
    const voiceLang = lang === "hi" ? "hi-IN" : "en-US";

    // Let cancel() settle, then ensure voices are loaded.
    await new Promise((r) => setTimeout(r, 80));
    if (this.cancelled) return false;

    let voices = window.speechSynthesis.getVoices();
    if (!voices.length) {
      voices = await waitForVoices(1500);
    }
    if (this.cancelled) return false;

    try {
      window.speechSynthesis.resume();
    } catch {
      // ignore
    }

    const chunks = chunkFullText(spoken, 280);
    const chunkCharStarts: number[] = [];
    {
      let searchFrom = 0;
      for (const chunk of chunks) {
        const at = spoken.indexOf(chunk, searchFrom);
        chunkCharStarts.push(at >= 0 ? at : searchFrom);
        searchFrom = (at >= 0 ? at : searchFrom) + chunk.length;
      }
    }

    const speakNext = (chunkIndex: number) => {
      if (this.cancelled) {
        handlers.onEnded?.();
        return;
      }
      if (chunkIndex >= chunks.length) {
        if (wordList.length) this.emitWord(wordList.length - 1, wordList, handlers);
        handlers.onEnded?.();
        return;
      }

      const chunk = chunks[chunkIndex];
      const charBase = chunkCharStarts[chunkIndex] ?? 0;
      const wordOffset = wordIndexForChar(spoken, charBase);
      if (chunkIndex === 0) this.emitWord(wordOffset, wordList, handlers);

      const utterance = new SpeechSynthesisUtterance(chunk);
      utterance.lang = voiceLang;
      utterance.rate = 0.92;
      utterance.pitch = 1.0;

      const pick = pickVoice(window.speechSynthesis.getVoices(), voiceLang, lang);
      if (pick) utterance.voice = pick;

      const chunkWords = tokenizeWords(chunk);
      const chunkWeight =
        chunkWords.reduce(
          (a, w) => a + Math.max(w.replace(/[^\p{L}\p{N}]/gu, "").length, 2),
          0,
        ) || 1;
      const estimatedMs = Math.max(800, (chunkWeight / 0.9) * 55);
      const startedAt = performance.now();
      let boundarySeen = false;

      const fallbackTick = () => {
        if (this.cancelled) return;
        if (boundarySeen) return;
        const t = (performance.now() - startedAt) / estimatedMs;
        const local = wordIndexForProgress(chunkWords, Math.min(0.99, t));
        this.emitWord(wordOffset + local, wordList, handlers);
        if (t < 1) this.rafId = requestAnimationFrame(fallbackTick);
      };
      this.rafId = requestAnimationFrame(fallbackTick);

      utterance.onboundary = (ev: SpeechSynthesisEvent) => {
        if (this.cancelled) return;
        if (ev.name && ev.name !== "word" && ev.name !== "sentence") return;
        boundarySeen = true;
        const localChar = Math.max(0, ev.charIndex ?? 0);
        this.emitWord(wordIndexForChar(spoken, charBase + localChar), wordList, handlers);
      };

      utterance.onend = () => {
        this.stopRaf();
        this.chunkTimer = setTimeout(() => speakNext(chunkIndex + 1), 60);
      };
      utterance.onerror = () => {
        this.stopRaf();
        this.chunkTimer = setTimeout(() => speakNext(chunkIndex + 1), 40);
      };

      try {
        window.speechSynthesis.resume();
      } catch {
        // ignore
      }
      window.speechSynthesis.speak(utterance);
    };

    speakNext(0);
    return true;
  }

  /** Timed word advance when no TTS path works. */
  runTimedWords(words: string[], handlers: SpeakHandlers, msPerChar = 48): void {
    this.stop();
    this.cancelled = false;
    this.lastWordIndex = -1;
    if (!words.length) {
      handlers.onEnded?.();
      return;
    }

    let i = 0;
    const step = () => {
      if (this.cancelled) {
        handlers.onEnded?.();
        return;
      }
      if (i >= words.length) {
        handlers.onEnded?.();
        return;
      }
      this.emitWord(i, words, handlers);
      const hold = Math.min(900, Math.max(180, words[i].length * msPerChar));
      i += 1;
      this.lineTimer = setTimeout(step, hold);
    };
    step();
  }

  stop(): void {
    this.cancelled = true;
    this.stopRaf();

    if (this.chunkTimer) {
      clearTimeout(this.chunkTimer);
      this.chunkTimer = null;
    }
    if (this.lineTimer) {
      clearTimeout(this.lineTimer);
      this.lineTimer = null;
    }

    if (this.audio) {
      try {
        this.audio.pause();
      } catch {
        // ignore
      }
    }
    this.cleanupAudio();

    if (typeof window !== "undefined" && window.speechSynthesis) {
      try {
        window.speechSynthesis.cancel();
      } catch {
        // ignore
      }
    }
  }

  private stopRaf(): void {
    if (this.rafId != null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
  }

  private cleanupAudio(): void {
    if (this.objectUrl) {
      URL.revokeObjectURL(this.objectUrl);
      this.objectUrl = null;
    }
    this.audio = null;
  }
}

/** Keep browser TTS chunks under engine limits without breaking word maps badly. */
function chunkFullText(text: string, maxLen = 280): string[] {
  if (text.length <= maxLen) return [text];

  const parts = text.split(/(?<=[.!?।…])\s+/).map((p) => p.trim()).filter(Boolean);
  const chunks: string[] = [];
  let buf = "";

  const flush = () => {
    if (buf) chunks.push(buf);
    buf = "";
  };

  for (const part of parts.length ? parts : [text]) {
    if (!buf) {
      buf = part;
      continue;
    }
    if ((buf + " " + part).length <= maxLen) {
      buf = `${buf} ${part}`;
    } else {
      flush();
      if (part.length <= maxLen) {
        buf = part;
      } else {
        // hard wrap long part
        let rest = part;
        while (rest.length > maxLen) {
          const cut = rest.lastIndexOf(" ", maxLen);
          const at = cut > maxLen * 0.4 ? cut : maxLen;
          chunks.push(rest.slice(0, at).trim());
          rest = rest.slice(at).trim();
        }
        buf = rest;
      }
    }
  }
  flush();
  return chunks.filter(Boolean);
}

export function isBrowserTtsSupported(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}

function waitForVoices(timeoutMs: number): Promise<SpeechSynthesisVoice[]> {
  return new Promise((resolve) => {
    if (typeof window === "undefined" || !window.speechSynthesis) {
      resolve([]);
      return;
    }
    const existing = window.speechSynthesis.getVoices();
    if (existing.length) {
      resolve(existing);
      return;
    }
    const timer = window.setTimeout(() => {
      window.speechSynthesis.onvoiceschanged = null;
      resolve(window.speechSynthesis.getVoices());
    }, timeoutMs);
    window.speechSynthesis.onvoiceschanged = () => {
      window.clearTimeout(timer);
      window.speechSynthesis.onvoiceschanged = null;
      resolve(window.speechSynthesis.getVoices());
    };
  });
}

/** Cached so Hindi and Hinglish always use the identical browser voice. */
let _cachedHiVoiceURI: string | null = null;
let _cachedEnVoiceURI: string | null = null;

function pickVoice(
  voices: SpeechSynthesisVoice[],
  bcp47: string,
  lang: "en" | "hi",
): SpeechSynthesisVoice | null {
  if (!voices.length) return null;

  const cacheURI = lang === "hi" ? _cachedHiVoiceURI : _cachedEnVoiceURI;
  if (cacheURI) {
    const cached = voices.find((v) => v.voiceURI === cacheURI);
    if (cached) return cached;
  }

  let pick: SpeechSynthesisVoice | null = null;

  if (lang === "hi") {
    // Prefer a stable named Hindi voice first (same for Hindi + Hinglish modes).
    pick =
      voices.find((v) =>
        /google हिन्दी|google hindi|microsoft heera|microsoft hemant|hemant|kalpana|swara|hindi/i.test(
          v.name,
        ),
      ) ?? null;
    if (!pick) {
      const lower = bcp47.toLowerCase();
      pick =
        voices.find((v) => v.lang.toLowerCase() === lower) ??
        voices.find((v) => v.lang.toLowerCase().startsWith("hi")) ??
        null;
    }
  } else {
    pick =
      voices.find((v) =>
        /david|mark|daniel|guy|aaron|james|google us english|microsoft david|microsoft mark/i.test(
          v.name,
        ),
      ) ?? null;
    if (!pick) {
      const lower = bcp47.toLowerCase();
      pick =
        voices.find((v) => v.lang.toLowerCase() === lower) ??
        voices.find((v) => v.lang.toLowerCase().startsWith("en")) ??
        null;
    }
  }

  pick = pick ?? voices[0] ?? null;
  if (pick) {
    if (lang === "hi") _cachedHiVoiceURI = pick.voiceURI;
    else _cachedEnVoiceURI = pick.voiceURI;
  }
  return pick;
}
