// Session + local thread persistence.
//
// Phase 3 keeps everything browser-local on purpose: Phase 4 moves
// threads to Supabase behind soft auth, so this is the clean boundary.
// The backend's own session memory is in-process and may vanish on
// restart — that's fine, we always send full conversation_history.

import type { HistoryMessage, VerseCitation } from "./api";

export type StoredMessage = {
  role: "user" | "assistant";
  /** Shown in chat UI. */
  content: string;
  /** Spoken reply when different from content (e.g. Hindi voice + English chat). */
  spoken?: string;
  citations?: VerseCitation[];
  isCrisis?: boolean;
};

export type Thread = {
  id: string;
  sessionId: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: StoredMessage[];
};

const THREADS_KEY = "sakha.threads.v1";
const ACTIVE_KEY = "sakha.activeThread.v1";
const LEGACY_THREADS_KEY = "krishna.threads.v1";
const LEGACY_ACTIVE_KEY = "krishna.activeThread.v1";

export function newId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `id-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export function loadThreads(): Thread[] {
  if (typeof window === "undefined") return [];
  try {
    let raw = window.localStorage.getItem(THREADS_KEY);
    if (!raw) {
      const legacy = window.localStorage.getItem(LEGACY_THREADS_KEY);
      if (legacy) {
        window.localStorage.setItem(THREADS_KEY, legacy);
        window.localStorage.removeItem(LEGACY_THREADS_KEY);
        raw = legacy;
      }
    }
    if (!raw) return [];
    const parsed = JSON.parse(raw) as Thread[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveThreads(threads: Thread[]): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(THREADS_KEY, JSON.stringify(threads));
  } catch {
    // Storage full or blocked — the conversation still works in memory.
  }
}

export function getActiveThreadId(): string | null {
  if (typeof window === "undefined") return null;
  const current = window.localStorage.getItem(ACTIVE_KEY);
  if (current) return current;
  const legacy = window.localStorage.getItem(LEGACY_ACTIVE_KEY);
  if (legacy) {
    window.localStorage.setItem(ACTIVE_KEY, legacy);
    window.localStorage.removeItem(LEGACY_ACTIVE_KEY);
    return legacy;
  }
  return null;
}

export function setActiveThreadId(id: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ACTIVE_KEY, id);
}

export function createThread(): Thread {
  const now = Date.now();
  return {
    id: newId(),
    sessionId: newId(),
    title: "New conversation",
    createdAt: now,
    updatedAt: now,
    messages: [],
  };
}

/** Title from the first user message, trimmed to something sidebar-sized.
 * Prefer Latin/English chrome — Devanagari titles wait for backend `title_en`.
 */
export function deriveTitle(firstUserMessage: string): string {
  const clean = firstUserMessage.trim().replace(/\s+/g, " ");
  if (/[\u0900-\u097F]/.test(clean)) {
    return "New conversation";
  }
  if (clean.length <= 42) return clean || "New conversation";
  return `${clean.slice(0, 42).trimEnd()}…`;
}

export function toHistory(messages: StoredMessage[]): HistoryMessage[] {
  return messages.map((m) => ({
    role: m.role,
    // Prefer what was actually spoken so the model keeps language continuity.
    content: m.spoken ?? m.content,
  }));
}

export function formatThreadDate(ts: number): string {
  const d = new Date(ts);
  const today = new Date();
  const isToday =
    d.getDate() === today.getDate() &&
    d.getMonth() === today.getMonth() &&
    d.getFullYear() === today.getFullYear();
  if (isToday) {
    return d.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
  }
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}
