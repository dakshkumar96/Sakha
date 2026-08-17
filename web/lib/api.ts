// Shapes must match backend/conversation/schemas.py (Phase 2 contract).

export type Role = "user" | "assistant";

export type HistoryMessage = { role: Role; content: string };

export type VerseCitation = {
  id: string;
  chapter: number;
  verse: number;
  short: string;
  translation_en: string | null;
  translation_hi?: string | null;
};

export type ChatResponse = {
  text: string;
  is_crisis: boolean;
  crisis_level: number;
  verses: string[];
  verse_citations: VerseCitation[];
  response_style: string;
  detected_emotion: string | null;
  teach_action: string;
  /** English movie subtitles (spoken `text` may be Hindi). */
  text_en?: string | null;
  /** English sidebar title for the thread. */
  title_en?: string | null;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export async function chat(params: {
  message: string;
  sessionId: string;
  turnNumber: number;
  history: HistoryMessage[];
  /** Spoken reply language preference. Captions: en/hi match voice; hinglish → text_en mix. */
  replyLang?: "en" | "hi" | "hinglish";
  signal?: AbortSignal;
}): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    signal: params.signal,
    body: JSON.stringify({
      message: params.message,
      session_id: params.sessionId,
      turn_number: params.turnNumber,
      conversation_history: params.history,
      reply_lang: params.replyLang ?? null,
    }),
  });

  if (!res.ok) {
    throw new Error(`chat failed: ${res.status}`);
  }
  return res.json();
}

/** Returns an mp3 Blob, or null when the voice service is resting (503). */
export async function ttsBlob(text: string, lang: "en" | "hi"): Promise<Blob | null> {
  try {
    const res = await fetch(`${API_URL}/tts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, lang }),
    });
    if (!res.ok) return null;
    return await res.blob();
  } catch {
    return null;
  }
}

export type Health = {
  status: string;
  knowledge_loaded: boolean;
  verse_count: number;
  faiss_loaded: boolean;
  llm_provider?: string;
  llm_configured?: boolean;
  /** @deprecated use llm_configured — kept for older backends */
  groq_configured: boolean;
  kokoro_reachable: boolean;
};

export async function health(): Promise<Health | null> {
  try {
    const res = await fetch(`${API_URL}/health`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}
