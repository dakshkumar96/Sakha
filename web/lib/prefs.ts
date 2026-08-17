// Browser-only preference flags (no backend).

const MIC_TIP_KEY = "sakha.micTipSeen.v1";
const SPEECH_LANG_KEY = "sakha.speechLang.v1";
/** Bump when intro must show again for returning browsers. */
const ONBOARDING_KEY = "sakha.onboarding.v5";

/** Spoken reply preference. On-screen language follows the mode. */
export type SpeechLang = "en" | "hi" | "hinglish";

export const SPEECH_LANG_OPTIONS: {
  id: SpeechLang;
  label: string;
  subtitle: string;
}[] = [
  { id: "en", label: "English", subtitle: "Speak and reply in English" },
  { id: "hi", label: "Hindi", subtitle: "Devanagari: voice and subtitles" },
  {
    id: "hinglish",
    label: "Hinglish",
    subtitle: "Same Hindi voice · Hindi–English mix on screen",
  },
];


export function getMicTipSeen(): boolean {
  if (typeof window === "undefined") return true;
  try {
    return window.localStorage.getItem(MIC_TIP_KEY) === "1";
  } catch {
    return true;
  }
}

export function setMicTipSeen(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(MIC_TIP_KEY, "1");
  } catch {
    // storage blocked
  }
}

/** First-open identity → door screens. */
export function getOnboardingSeen(): boolean {
  if (typeof window === "undefined") return true;
  try {
    return window.localStorage.getItem(ONBOARDING_KEY) === "1";
  } catch {
    return true;
  }
}

export function setOnboardingSeen(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(ONBOARDING_KEY, "1");
  } catch {
    // storage blocked
  }
}

/** Prefer Hindi STT when the browser locale looks Indian. */
export function defaultSttLang(): SpeechLang {
  if (typeof navigator === "undefined") return "en";
  const tag = (navigator.language || "").toLowerCase();
  if (tag.startsWith("hi")) return "hi";
  if (tag.includes("-in") || tag.endsWith("_in")) return "hinglish";
  return "en";
}

/** Spoken reply + TTS language preference (on-screen follows mode). */
export function getSpeechLang(): SpeechLang {
  if (typeof window === "undefined") return defaultSttLang();
  try {
    const v = window.localStorage.getItem(SPEECH_LANG_KEY);
    if (v === "en" || v === "hi" || v === "hinglish") return v;
  } catch {
    // ignore
  }
  return defaultSttLang();
}

export function setSpeechLang(lang: SpeechLang): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(SPEECH_LANG_KEY, lang);
  } catch {
    // ignore
  }
}

/** English → en TTS/STT; Hindi + Hinglish → Hindi voice. */
export function voiceEngineLang(lang: SpeechLang): "en" | "hi" {
  return lang === "en" ? "en" : "hi";
}
