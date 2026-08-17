"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import Composer from "@/components/Composer";
import ConfirmDialog from "@/components/ConfirmDialog";
import FullChatView from "@/components/FullChatView";
import Onboarding from "@/components/Onboarding";
import {
  CosmicStage,
  type PresenceState,
} from "@/components/PresenceAvatar";
import SessionSidebar from "@/components/SessionSidebar";
import SubtitleOverlay, {
  type CaptionFrame,
} from "@/components/SubtitleOverlay";
import { AmbientBed } from "@/lib/ambientBed";
import { chat, health, ttsBlob, type VerseCitation } from "@/lib/api";
import {
  getMicTipSeen,
  getOnboardingSeen,
  getSpeechLang,
  setOnboardingSeen,
  setSpeechLang,
  voiceEngineLang,
  type SpeechLang,
} from "@/lib/prefs";
import {
  captionSyncedToSpeech,
  isBrowserTtsSupported,
  SpeechPlayer,
  tokenizeWords,
} from "@/lib/speechPlayback";
import {
  createThread,
  deriveTitle,
  getActiveThreadId,
  loadThreads,
  saveThreads,
  setActiveThreadId,
  toHistory,
  type StoredMessage,
  type Thread,
} from "@/lib/session";

const MIN_PAUSE_MS = 700;
const INTRO_MS = 1600;

function cleanCaption(text: string): string {
  return text
    .replace(/^\[generation-unavailable\]\s*/i, "")
    .replace(/\s+/g, " ")
    .trim();
}

export default function Home() {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [presence, setPresence] = useState<PresenceState>("waiting");
  const [busy, setBusy] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [view, setView] = useState<"presence" | "fullChat">("presence");
  const [boot, setBoot] = useState<"intro" | "ready">("intro");
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [showMicTip, setShowMicTip] = useState(false);
  const [confirmNew, setConfirmNew] = useState(false);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const [caption, setCaption] = useState<CaptionFrame | null>(null);
  const [crisisSticky, setCrisisSticky] = useState<string | null>(null);
  const [activeCitations, setActiveCitations] = useState<VerseCitation[]>([]);
  const [citeOpen, setCiteOpen] = useState(false);
  const [canViewFullChat, setCanViewFullChat] = useState(false);
  const [speechLang, setSpeechLangState] = useState<SpeechLang>("en");

  const playerRef = useRef<SpeechPlayer | null>(null);
  const ambientRef = useRef<AmbientBed | null>(null);

  useEffect(() => {
    playerRef.current = new SpeechPlayer();
    const bed = AmbientBed.getShared();
    ambientRef.current = bed;
    bed.setEnabled(true);

    const stored = loadThreads();
    const wantedId = getActiveThreadId();
    const existing = stored.find((t) => t.id === wantedId) ?? stored[0];

    if (existing) {
      setThreads(stored);
      setActiveId(existing.id);
      setCanViewFullChat(
        existing.messages.some((m) => m.role === "assistant"),
      );
    } else {
      const fresh = createThread();
      setThreads([fresh]);
      setActiveId(fresh.id);
      saveThreads([fresh]);
      setActiveThreadId(fresh.id);
    }

    setShowMicTip(!getMicTipSeen());
    setSpeechLangState(getSpeechLang());
    setShowOnboarding(!getOnboardingSeen());

    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.getVoices();
      window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
      };
    }

    health().catch(() => null);
    isBrowserTtsSupported();

    const t = window.setTimeout(() => setBoot("ready"), INTRO_MS);

    // One unlock path — start bed on first gesture only (no eager double-start).
    const unlockAndStartBed = () => {
      void ambientRef.current?.startContinuous();
    };
    window.addEventListener("pointerdown", unlockAndStartBed, { once: true });
    window.addEventListener("keydown", unlockAndStartBed, { once: true });

    return () => {
      window.clearTimeout(t);
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.onvoiceschanged = null;
      }
      window.removeEventListener("pointerdown", unlockAndStartBed);
      window.removeEventListener("keydown", unlockAndStartBed);
      playerRef.current?.stop();
      // Keep shared ambient alive across Strict Mode remount.
    };
  }, []);

  const activeThread = threads.find((t) => t.id === activeId) ?? null;
  const messages = activeThread?.messages ?? [];
  const isEmpty = messages.length === 0;
  const crisisActive = Boolean(crisisSticky);

  const persist = useCallback((next: Thread[]) => {
    setThreads(next);
    saveThreads(next);
  }, []);

  function clearTransientCaptions() {
    setCaption(null);
    setActiveCitations([]);
    setCiteOpen(false);
  }

  /** One subtitle row — advances with speech (Hinglish maps onto Hindi voice). */
  function showCaptionSynced(spokenText: string, captionText: string, activeIndex: number) {
    const line = captionSyncedToSpeech({
      spokenText,
      captionText,
      activeSpokenIndex: activeIndex,
    });
    if (!line) {
      setCaption(null);
      return;
    }
    setCaption({ text: line });
  }

  function resetShellToWaiting() {
    playerRef.current?.stop();
    ambientRef.current?.stopWithVoice();
    clearTransientCaptions();
    setCrisisSticky(null);
    setPresence("waiting");
    setView("presence");
    setCanViewFullChat(false);
  }

  function doCreateThread() {
    const fresh = createThread();
    const next = [fresh, ...threads];
    persist(next);
    setActiveId(fresh.id);
    setActiveThreadId(fresh.id);
    setSidebarOpen(false);
    setConfirmNew(false);
    resetShellToWaiting();
  }

  function handleNewThread() {
    const hasUser = Boolean(
      activeThread?.messages.some((m) => m.role === "user"),
    );
    if (hasUser) {
      setConfirmNew(true);
      return;
    }
    doCreateThread();
  }

  function handleSelectThread(id: string) {
    setActiveId(id);
    setActiveThreadId(id);
    setSidebarOpen(false);
    playerRef.current?.stop();
    ambientRef.current?.stopWithVoice();
    clearTransientCaptions();
    setCrisisSticky(null);
    setPresence("waiting");
    setView("presence");
    const t = threads.find((x) => x.id === id);
    setCanViewFullChat(
      Boolean(t?.messages.some((m) => m.role === "assistant")),
    );
  }

  function handleDeleteRequest(id: string) {
    setConfirmDeleteId(id);
  }

  function doDeleteThread() {
    const id = confirmDeleteId;
    if (!id) return;

    playerRef.current?.stop();
    ambientRef.current?.stopWithVoice();

    const remaining = threads.filter((t) => t.id !== id);
    let nextActive = remaining.find((t) => t.id === activeId) ?? null;

    if (id === activeId) {
      nextActive = remaining[0] ?? null;
      if (!nextActive) {
        nextActive = createThread();
        remaining.unshift(nextActive);
      }
      resetShellToWaiting();
      setCanViewFullChat(
        Boolean(nextActive.messages.some((m) => m.role === "assistant")),
      );
    }

    persist(remaining);
    if (nextActive) {
      setActiveId(nextActive.id);
      setActiveThreadId(nextActive.id);
    } else {
      setActiveId(null);
    }
    setConfirmDeleteId(null);
  }

  const handleListeningChange = useCallback(
    (listening: boolean) => {
      if (listening) {
        playerRef.current?.stop();
        ambientRef.current?.stopWithVoice();
        // Transient captions clear; crisis sticky stays until dismiss / next send.
        clearTransientCaptions();
        setPresence("listening");
      } else {
        setPresence((p) => (p === "listening" ? "waiting" : p));
      }
    },
    [],
  );

  async function handleSend(text: string) {
    if (!activeThread || busy) return;

    ambientRef.current?.unlock();
    playerRef.current?.stop();
    ambientRef.current?.stopWithVoice();
    clearTransientCaptions();
    setCrisisSticky(null);
    setBusy(true);
    // No processing spinner / glow — stay waiting until speech.
    setPresence("waiting");

    const userMsg: StoredMessage = { role: "user", content: text };
    const historyBefore = toHistory(activeThread.messages);
    const turnNumber =
      activeThread.messages.filter((m) => m.role === "user").length + 1;

    const withUser: Thread = {
      ...activeThread,
      title:
        activeThread.messages.length === 0
          ? deriveTitle(text)
          : activeThread.title,
      updatedAt: Date.now(),
      messages: [...activeThread.messages, userMsg],
    };
    persist(threads.map((t) => (t.id === withUser.id ? withUser : t)));

    const startedAt = Date.now();

    try {
      const res = await chat({
        message: text,
        sessionId: activeThread.sessionId,
        turnNumber,
        history: historyBefore,
        replyLang: speechLang,
      });

      const elapsed = Date.now() - startedAt;
      if (elapsed < MIN_PAUSE_MS) {
        await new Promise((r) => setTimeout(r, MIN_PAUSE_MS - elapsed));
      }

      const replyText = cleanCaption(res.text || "");
      const textEn = cleanCaption(res.text_en || "");
      const isCrisis = Boolean(res.is_crisis);
      const citations = res.verse_citations ?? [];

      // On-screen + chat language by mode:
      // EN → English · HI → Devanagari · Hinglish → Hindi–English code-switch

      const onScreenText =
        speechLang === "en"
          ? textEn || replyText
          : speechLang === "hinglish"
            ? textEn || replyText
            : replyText;

      const assistantMsg: StoredMessage = {
        role: "assistant",
        content: onScreenText,
        spoken: speechLang === "hinglish" ? replyText : undefined,
        citations,
        isCrisis,
      };

      const withReply: Thread = {
        ...withUser,
        title: res.title_en?.trim() || withUser.title,
        updatedAt: Date.now(),
        messages: [...withUser.messages, assistantMsg],
      };
      setThreads((prev) => {
        const next = prev.map((t) => (t.id === withReply.id ? withReply : t));
        saveThreads(next);
        return next;
      });

      if (!replyText) {
        ambientRef.current?.stopWithVoice();
        setPresence("waiting");
        return;
      }

      setCanViewFullChat(true);

      if (isCrisis) {
        setCrisisSticky(onScreenText);
        setActiveCitations([]);
        setCiteOpen(false);
        setCaption(null);
        setPresence("waiting");
        const lang = voiceEngineLang(speechLang);
        const words = tokenizeWords(replyText);
        const player = playerRef.current;
        void ambientRef.current?.startWithVoice();
        setPresence("speaking");
        const handlers = {
          onWord: () => {
            /* crisis: sticky full text, no karaoke */
          },
          onEnded: () => {
            ambientRef.current?.stopWithVoice();
            setPresence("waiting");
          },
        };
        let spoken = false;
        const blob = await ttsBlob(replyText, lang);
        if (blob && player) {
          spoken = await player.play(blob, handlers, words);
        }
        if (!spoken && player?.speakBrowser) {
          spoken = await player.speakBrowser(replyText, lang, handlers, words);
        }
        if (!spoken) {
          ambientRef.current?.stopWithVoice();
          setPresence("waiting");
        }
        return;
      }

      const lang = voiceEngineLang(speechLang);
      setActiveCitations(citations);
      setCiteOpen(false);

      // Hinglish: same Hindi voice as HI; only on-screen text is code-switch mix.
      const speakText = replyText;
      const captionText = onScreenText;
      const spokenWords = tokenizeWords(speakText);

      const handlers = {
        onWord: (activeIndex: number) => {
          if (!captionText.trim()) return;
          showCaptionSynced(speakText, captionText, activeIndex);
        },
        onEnded: () => {
          ambientRef.current?.stopWithVoice();
          setCaption(null);
          setActiveCitations([]);
          setCiteOpen(false);
          setPresence("waiting");
        },
      };

      showCaptionSynced(speakText, captionText, 0);
      setPresence("speaking");
      void ambientRef.current?.startWithVoice();

      const player = playerRef.current;
      let spoken = false;
      const blob = await ttsBlob(speakText, lang);
      if (blob && player) {
        spoken = await player.play(blob, handlers, spokenWords);
      }
      if (!spoken && player) {
        spoken = await player.speakBrowser(speakText, lang, handlers, spokenWords);
      }
      if (!spoken) {
        // Advance captions from spoken-word timing if TTS is unavailable.
        player?.runTimedWords(spokenWords, handlers);
      }
    } catch {
      clearTransientCaptions();
      setPresence("waiting");
    } finally {
      setBusy(false);
    }
  }

  function handleOnboardingComplete(lang: SpeechLang) {
    setSpeechLang(lang);
    setSpeechLangState(lang);
    setOnboardingSeen();
    setShowOnboarding(false);
    ambientRef.current?.unlock();
    void ambientRef.current?.startContinuous();
  }

  return (
    <main className="dusk-field relative flex h-[100dvh] w-full overflow-hidden md:gap-0 md:p-3">
      <AnimatePresence mode="sync">
        {showOnboarding && (
          <Onboarding
            key="onboarding"
            initialLang={speechLang}
            onComplete={handleOnboardingComplete}
          />
        )}
      </AnimatePresence>

      <motion.div
        className="flex h-full min-h-0 w-full min-w-0 flex-1 md:gap-0"
        initial={false}
        animate={
          showOnboarding
            ? { opacity: 0 }
            : { opacity: 1 }
        }
        transition={{
          duration: 0.45,
          ease: [0.25, 0.1, 0.25, 1],
          delay: showOnboarding ? 0 : 0.08,
        }}
      >
      <SessionSidebar
        threads={threads}
        activeId={activeId}
        open={sidebarOpen}
        onSelect={handleSelectThread}
        onNew={handleNewThread}
        onDelete={handleDeleteRequest}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="flex h-full min-h-0 min-w-0 flex-1 flex-col">
        {view === "fullChat" ? (
          <FullChatView
            messages={messages}
            onBack={() => setView("presence")}
          />
        ) : (
          <CosmicStage state={presence}>
            <div className="flex items-center justify-between px-4 pt-4 md:px-6">
              <button
                type="button"
                onClick={() => setSidebarOpen(true)}
                aria-label="Open history"
                className="glass-chip grid h-9 w-9 place-items-center rounded-full
                           text-ink-dim transition-colors hover:text-gold md:invisible"
              >
                <svg
                  width="15"
                  height="15"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.9"
                  strokeLinecap="round"
                >
                  <path d="M4 7h16M4 12h16M4 17h16" />
                </svg>
              </button>

              <div className="flex items-center gap-2">
                {canViewFullChat && (
                  <button
                    type="button"
                    onClick={() => setView("fullChat")}
                    className="glass-chip rounded-full px-3 py-1.5 text-[0.72rem] uppercase
                               tracking-[0.12em] text-ink-dim transition-colors hover:text-gold"
                  >
                    View full chat
                  </button>
                )}
              </div>
            </div>

            <div className="flex min-h-0 flex-1 flex-col items-center justify-end px-5 pb-2">
              {boot === "ready" && (
                <SubtitleOverlay
                  caption={caption}
                  crisisText={crisisSticky}
                  crisisActive={crisisActive}
                  onDismissCrisis={() => setCrisisSticky(null)}
                  citations={activeCitations}
                  citeOpen={citeOpen}
                  onToggleCite={() => setCiteOpen((v) => !v)}
                />
              )}
            </div>

            <div className="relative z-20 px-4 pb-[max(1.5rem,env(safe-area-inset-bottom))] pt-1 md:px-6">
              <div className="mx-auto flex w-full max-w-[420px] flex-col items-center overflow-visible">
                {boot === "ready" && (
                  <Composer
                    onSend={handleSend}
                    busy={busy}
                    onListeningChange={handleListeningChange}
                    showMicTip={showMicTip && isEmpty}
                    onMicTipConsumed={() => setShowMicTip(false)}
                    speechLang={speechLang}
                    onSpeechLangChange={setSpeechLangState}
                  />
                )}
              </div>
            </div>
          </CosmicStage>
        )}
      </div>
      </motion.div>

      <ConfirmDialog
        open={confirmNew}
        title="Leave this conversation?"
        body="Your current exchange will stay in the sidebar. A new conversation will begin empty."
        confirmLabel="New conversation"
        cancelLabel="Stay"
        onConfirm={doCreateThread}
        onCancel={() => setConfirmNew(false)}
      />

      <ConfirmDialog
        open={confirmDeleteId !== null}
        title="Delete this conversation?"
        body="This removes it from this browser. It cannot be undone."
        confirmLabel="Delete"
        cancelLabel="Keep"
        onConfirm={doDeleteThread}
        onCancel={() => setConfirmDeleteId(null)}
      />
    </main>
  );
}
