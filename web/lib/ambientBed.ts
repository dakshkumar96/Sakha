// Continuous looping Krishna flute bed — single shared instance (no double play).

const AMBIENT_SRC = "/audio/krishna-flute-bg.m4a";
const VOL_TARGET = 0.12;
const FADE_IN_MS = 1200;
const FADE_STEPS = 20;

let shared: AmbientBed | null = null;

export class AmbientBed {
  private audio: HTMLAudioElement | null = null;
  private enabled = true;
  private unlocked = false;
  private fadeTimer: ReturnType<typeof setInterval> | null = null;
  private playToken = 0;
  private started = false;

  /** One bed for the whole app — Strict Mode remounts won't stack tracks. */
  static getShared(): AmbientBed {
    if (!shared) shared = new AmbientBed();
    return shared;
  }

  unlock(): void {
    if (typeof window === "undefined") return;
    this.unlocked = true;
    this.ensureElement();
  }

  private ensureElement(): HTMLAudioElement | null {
    if (typeof window === "undefined") return null;
    if (!this.audio) {
      const el = new Audio(AMBIENT_SRC);
      el.loop = true;
      el.preload = "auto";
      el.volume = 0;
      el.setAttribute("playsinline", "true");
      this.audio = el;
    }
    return this.audio;
  }

  private clearFade(): void {
    if (this.fadeTimer) {
      clearInterval(this.fadeTimer);
      this.fadeTimer = null;
    }
  }

  private fadeTo(target: number, durationMs: number): void {
    const el = this.audio;
    if (!el) return;

    this.clearFade();
    const from = el.volume;
    const steps = FADE_STEPS;
    const stepMs = Math.max(16, Math.floor(durationMs / steps));
    let i = 0;

    this.fadeTimer = setInterval(() => {
      i += 1;
      const t = Math.min(1, i / steps);
      const eased = t * t * (3 - 2 * t);
      el.volume = Math.max(0, Math.min(1, from + (target - from) * eased));
      if (t >= 1) {
        this.clearFade();
        el.volume = target;
      }
    }, stepMs);
  }

  /** Start continuous loop once. Safe to call many times. */
  async startContinuous(): Promise<void> {
    if (!this.enabled || typeof window === "undefined") return;
    this.unlock();
    const el = this.ensureElement();
    if (!el) return;

    el.loop = true;

    // Already audible — do nothing (prevents layered restarts).
    if (this.started && !el.paused) {
      if (el.volume < VOL_TARGET * 0.9) this.fadeTo(VOL_TARGET, 400);
      return;
    }

    const token = ++this.playToken;

    try {
      if (el.paused) {
        el.currentTime = el.currentTime || 0;
        await el.play();
      }
    } catch {
      // Autoplay blocked until a user gesture.
      return;
    }

    if (token !== this.playToken || !this.enabled) return;
    this.started = true;
    this.fadeTo(VOL_TARGET, FADE_IN_MS);
  }

  startWithVoice(): void {
    void this.startContinuous().then(() => this.duckForSpeech());
  }

  stopWithVoice(): void {
    this.restoreAfterSpeech();
  }

  /** Soften bed under companion speech so voice is audible. */
  duckForSpeech(): void {
    if (!this.audio || this.audio.paused) return;
    this.fadeTo(Math.min(VOL_TARGET, 0.045), 350);
  }

  restoreAfterSpeech(): void {
    if (!this.enabled || !this.started) return;
    if (!this.audio || this.audio.paused) {
      void this.startContinuous();
      return;
    }
    this.fadeTo(VOL_TARGET, 500);
  }

  async playIntro(_durationMs = 2800): Promise<void> {
    await this.startContinuous();
  }

  setEnabled(on: boolean): void {
    this.enabled = on;
    if (!on) this.pause();
  }

  private pauseImmediate(): void {
    if (!this.audio) return;
    try {
      this.audio.pause();
      this.audio.volume = 0;
    } catch {
      // ignore
    }
    this.started = false;
  }

  pause(): void {
    this.playToken += 1;
    this.clearFade();
    this.pauseImmediate();
  }

  /** Soft teardown for React unmount — keep shared element if Strict Mode remounts. */
  dispose(): void {
    // Do not destroy the shared audio on unmount; Strict Mode would stack/restart.
    // Full teardown only via pause() when disabling.
  }

  get isUnlocked(): boolean {
    return this.unlocked;
  }
}
