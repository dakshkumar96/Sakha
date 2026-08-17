"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";
import {
  SPEECH_LANG_OPTIONS,
  type SpeechLang,
} from "@/lib/prefs";

type Step = 0 | 1 | 2 | 3;

const STEPS: {
  id: Step;
  title: string;
  titleLang?: "hi" | "en";
  body: string;
  nextLabel: string;
  voicePick?: boolean;
  imageSrc?: string;
  imageAlt?: string;
}[] = [
  {
    id: 0,
    title: "What this is for.",
    body:
      "A place to talk about what is weighing on you. It listens, asks questions until the problem is clear, then answers using the Bhagavad Gita, with chapter and verse when a teaching is given.",
    nextLabel: "Next",
    imageSrc: "/images/onboarding-gita.png",
    imageAlt: "Krishna teaching Arjuna on the chariot",
  },
  {
    id: 1,
    title: "This isn't Krishna.",
    body:
      "Sakha is a companion based on Krishna's words in the Gita. It is not divine, not a guru, and not a replacement for real people in your life.",
    nextLabel: "Next",
    imageSrc: "/images/onboarding-begin.png",
    imageAlt: "Krishna playing the flute in misted light",
  },
  {
    id: 2,
    title: "How should I speak?",
    body:
      "Pick the voice and on-screen language. You can change this anytime from the control next to the mic.",
    nextLabel: "Next",
    voicePick: true,
    imageSrc: "/images/onboarding-voice.png",
    imageAlt: "Krishna silhouette with flute against starlight",
  },
  {
    id: 3,
    title: "Say what needs to be said.",
    body:
      "No feature tour after this. Only the mic, the page, and whatever you bring.",
    nextLabel: "Begin",
    imageSrc: "/images/onboarding-not-krishna.png",
    imageAlt: "Krishna standing with Arjuna bowed on the battlefield",
  },
];

const FINAL_BY_LANG: Record<
  SpeechLang,
  { title: string; titleLang?: "hi" | "en"; body: string }
> = {
  en: {
    title: "Say what needs to be said.",
    body: "No feature tour after this. Only the mic, the page, and whatever you bring.",
  },
  hi: {
    title: "जो कहना है, कह दो।",
    titleLang: "hi",
    body: "इसके बाद कोई फीचर टूर नहीं। सिर्फ माइक, पेज, और जो तुम लाते हो।",
  },
  hinglish: {
    title: "Jo kehna hai, keh do.",
    body: "Iske baad koi feature tour nahi. Sirf mic, page, aur jo tum laate ho.",
  },
};

const panelEnter = {
  initial: { opacity: 0, y: 14 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: [0.25, 0.1, 0.25, 1] as const },
  },
  exit: {
    opacity: 0,
    y: 8,
    transition: { duration: 0.28, ease: [0.4, 0, 1, 1] as const },
  },
};

const stepContent = {
  initial: (direction: 1 | -1) => ({
    opacity: 0,
    x: direction * 16,
  }),
  animate: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.32, ease: [0.25, 0.1, 0.25, 1] as const },
  },
  exit: (direction: 1 | -1) => ({
    opacity: 0,
    x: direction * -12,
    transition: { duration: 0.2, ease: [0.4, 0, 1, 1] as const },
  }),
};

const shellExit = {
  initial: { opacity: 0 },
  animate: {
    opacity: 1,
    transition: { duration: 0.35, ease: [0.25, 0.1, 0.25, 1] as const },
  },
  exit: {
    opacity: 0,
    transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] as const },
  },
};

function CornerOrnament({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      width="44"
      height="44"
      viewBox="0 0 44 44"
      fill="none"
      aria-hidden
    >
      <path
        d="M6 38V22c0-10 8-16 16-16h16"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinecap="round"
      />
      <path
        d="M10 38V24c0-7 5.5-11.5 11.5-11.5H38"
        stroke="currentColor"
        strokeWidth="0.7"
        strokeOpacity="0.55"
        strokeLinecap="round"
      />
      <circle cx="6" cy="38" r="1.6" fill="currentColor" />
      <circle cx="38" cy="6" r="1.6" fill="currentColor" />
      <path
        d="M18 10c2.5 1.2 4 3.2 4.5 5.5M26 10c-1.2 2-1.5 4.2-1 6.2"
        stroke="currentColor"
        strokeWidth="0.8"
        strokeOpacity="0.7"
        strokeLinecap="round"
      />
    </svg>
  );
}

function FeatherMark({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      width="18"
      height="28"
      viewBox="0 0 18 28"
      fill="none"
      aria-hidden
    >
      <path
        d="M9 2c2.5 4 5 8.5 5 14.5S11.2 26 9 26 4 22.5 4 16.5 6.5 6 9 2z"
        stroke="currentColor"
        strokeWidth="1.1"
        strokeLinejoin="round"
      />
      <path
        d="M9 5.5v18M6.2 10.5c1.8.8 3.8.8 5.6 0M5.8 15c2 .9 4.4.9 6.4 0M6.4 19.2c1.6.7 3.6.7 5.2 0"
        stroke="currentColor"
        strokeWidth="0.85"
        strokeLinecap="round"
        strokeOpacity="0.75"
      />
    </svg>
  );
}

/**
 * First-open onboarding — richer Krishna frame over an opaque field.
 */
export default function Onboarding({
  onComplete,
  initialLang = "en",
}: {
  onComplete: (lang: SpeechLang) => void;
  initialLang?: SpeechLang;
}) {
  const [step, setStep] = useState<Step>(0);
  const [dir, setDir] = useState<1 | -1>(1);
  const [speechLang, setSpeechLangLocal] = useState<SpeechLang>(initialLang);
  const total = STEPS.length;
  const base = STEPS[step];
  const finalCopy = step === 3 ? FINAL_BY_LANG[speechLang] : null;
  const current = finalCopy
    ? {
        ...base,
        title: finalCopy.title,
        titleLang: finalCopy.titleLang,
        body: finalCopy.body,
      }
    : base;
  const progress = ((step + 1) / total) * 100;

  function goNext() {
    if (step >= total - 1) {
      onComplete(speechLang);
      return;
    }
    setDir(1);
    setStep((s) => (s + 1) as Step);
  }

  function goBack() {
    if (step <= 0) return;
    setDir(-1);
    setStep((s) => (s - 1) as Step);
  }

  return (
    <motion.div
      className="fixed inset-0 z-[60] flex items-center justify-center p-4 md:p-8"
      role="dialog"
      aria-modal="true"
      aria-labelledby="onboard-title"
      variants={shellExit}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      {/* Full-viewport background video — wash matched to nebula */}
      <div className="absolute inset-0 overflow-hidden bg-[#02040a]" aria-hidden>
        <video
          src="/videos/onboarding-bg-16x9.mp4?v=hq5"
          className="onboard-bg-video absolute inset-0 h-full w-full"
          autoPlay
          muted
          loop
          playsInline
          preload="auto"
        />
        <div className="absolute inset-0 bg-[#02040a]/62" />
        <div
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(42% 38% at 48% 48%, rgba(74,127,212,0.12) 0%, transparent 58%), radial-gradient(36% 34% at 72% 58%, rgba(224,138,60,0.08) 0%, transparent 55%), linear-gradient(180deg, rgba(2,4,10,0.48) 0%, rgba(2,4,10,0.82) 100%)",
          }}
        />
      </div>

      <motion.div
        className="onboard-panel relative z-10 grid w-full max-w-[900px] overflow-hidden
                   rounded-[1.75rem] md:grid-cols-[2fr_1fr] md:min-h-[552px]"
        variants={panelEnter}
        initial="initial"
        animate="animate"
        exit="exit"
      >
        {/* Inner frame — amber + nebula blue */}
        <div
          className="pointer-events-none absolute inset-[7px] z-20 rounded-[1.35rem]
                     border border-[rgba(224,138,60,0.28)]"
          aria-hidden
        />
        <div
          className="pointer-events-none absolute inset-[11px] z-20 rounded-[1.2rem]
                     border border-[rgba(74,127,212,0.14)]"
          aria-hidden
        />

        <CornerOrnament className="pointer-events-none absolute left-3 top-3 z-20 onboard-accent-muted" />
        <CornerOrnament className="pointer-events-none absolute right-3 top-3 z-20 rotate-90 onboard-accent-muted" />
        <CornerOrnament className="pointer-events-none absolute bottom-3 left-3 z-20 -rotate-90 onboard-accent-muted" />
        <CornerOrnament className="pointer-events-none absolute bottom-3 right-3 z-20 rotate-180 onboard-accent-muted" />

        <div className="relative z-10 flex min-h-[450px] flex-col px-6 py-7 md:min-h-[552px] md:px-8 md:py-8">
          <div className="onboard-panel-texture pointer-events-none absolute inset-0" aria-hidden />

          <div className="relative">
            <div className="flex items-center gap-2.5">
              <FeatherMark className="onboard-accent" />
              <div>
                <p className="font-display text-[0.72rem] tracking-[0.22em] onboard-accent">
                  भगवद्गीता
                </p>
                <p className="mt-0.5 font-body text-[0.7rem] tracking-[0.08em] text-ink-dim">
                  Companion · Step {step + 1} of {total}
                </p>
              </div>
            </div>

            {/* Step beads */}
            <div className="mt-4 flex items-center gap-2" aria-hidden>
              {STEPS.map((s) => {
                const active = s.id === step;
                const done = s.id < step;
                return (
                  <span
                    key={s.id}
                    className={`h-1.5 rounded-full transition-all duration-300
                      ${
                        active
                          ? "w-7 bg-[rgba(224,138,60,0.95)] shadow-[0_0_12px_rgba(224,138,60,0.45)]"
                          : done
                            ? "w-3 bg-[rgba(74,127,212,0.55)]"
                            : "w-3 bg-white/15"
                      }`}
                  />
                );
              })}
            </div>

            <div
              className="mt-3 h-[2px] w-full overflow-hidden rounded-full bg-white/10"
              role="progressbar"
              aria-valuenow={step + 1}
              aria-valuemin={1}
              aria-valuemax={total}
            >
              <motion.div
                className="h-full rounded-full"
                style={{
                  background:
                    "linear-gradient(90deg, rgba(74,127,212,0.75), rgba(224,138,60,0.95))",
                }}
                initial={false}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
              />
            </div>
          </div>

          <div className="relative mt-7 flex min-h-0 flex-1 flex-col overflow-hidden">
            <AnimatePresence mode="popLayout" custom={dir} initial={false}>
              <motion.div
                key={step === 3 ? `final-${speechLang}` : step}
                custom={dir}
                variants={stepContent}
                initial="initial"
                animate="animate"
                exit="exit"
                className="flex flex-1 flex-col"
              >
                <h1
                  id="onboard-title"
                  className={`font-display font-medium leading-[1.15] tracking-wide text-ink
                    ${
                      current.titleLang === "hi"
                        ? "text-[1.85rem] md:text-[2.15rem]"
                        : "text-[1.7rem] md:text-[2rem]"
                    }`}
                >
                  {current.title}
                </h1>
                <div
                  className="mt-3 h-px w-16"
                  style={{
                    background:
                      "linear-gradient(90deg, rgba(224,138,60,0.85), transparent)",
                  }}
                  aria-hidden
                />
                <p className="mt-4 max-w-md font-body text-[0.98rem] leading-[1.75] text-ink-dim md:text-[1.05rem]">
                  {current.body}
                </p>

                {current.imageSrc && (
                  <div
                    className="onboard-image-frame relative mt-6 overflow-hidden rounded-2xl md:hidden"
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={current.imageSrc}
                      alt={current.imageAlt ?? ""}
                      className="h-auto w-full object-cover object-center"
                    />
                  </div>
                )}

                {current.voicePick && (
                  <div
                    className="mt-6 flex max-w-md flex-col gap-2.5"
                    role="radiogroup"
                    aria-label="Spoken language"
                  >
                    {SPEECH_LANG_OPTIONS.map((opt) => {
                      const active = speechLang === opt.id;
                      return (
                        <button
                          key={opt.id}
                          type="button"
                          role="radio"
                          aria-checked={active}
                          onClick={() => setSpeechLangLocal(opt.id)}
                          className={`flex w-full items-start gap-3 rounded-2xl border px-4 py-3 text-left
                            transition-all
                            ${
                              active
                                ? "border-[rgba(224,138,60,0.5)] bg-[rgba(224,138,60,0.12)] shadow-[0_0_24px_rgba(74,127,212,0.12)]"
                                : "border-white/14 bg-white/[0.04] hover:border-[rgba(224,138,60,0.28)] hover:bg-white/[0.07]"
                            }`}
                        >
                          <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center text-[rgba(224,138,60,0.95)]">
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
                            ) : (
                              <span className="h-3.5 w-3.5 rounded-full border border-white/30" />
                            )}
                          </span>
                          <span className="min-w-0 flex-1">
                            <span className="block text-[0.95rem] font-semibold text-ink">
                              {opt.label}
                            </span>
                            <span className="mt-0.5 block text-[0.8rem] leading-snug text-ink-dim">
                              {opt.subtitle}
                            </span>
                          </span>
                        </button>
                      );
                    })}
                  </div>
                )}
              </motion.div>
            </AnimatePresence>
          </div>

          <div className="relative mt-8 flex items-end justify-between gap-2.5">
            <p className="onboard-accent font-sakha text-[0.95rem] font-bold tracking-[0.08em]">
              Sakha
            </p>
            <div className="flex items-center gap-2.5">
              <button
                type="button"
                onClick={goBack}
                disabled={step === 0}
                className="rounded-full border border-white/14 bg-white/[0.06] px-5 py-2.5
                           text-[0.8rem] text-ink-dim transition-colors hover:border-white/25
                           hover:text-ink disabled:cursor-not-allowed disabled:opacity-35"
              >
                Back
              </button>
              <button
                type="button"
                onClick={goNext}
                className="onboard-cta rounded-full px-6 py-2.5 text-[0.8rem] font-medium
                           tracking-wide transition-transform hover:scale-[1.02]"
              >
                {current.nextLabel}
              </button>
            </div>
          </div>
        </div>

        <div className="relative hidden min-h-[280px] md:block md:min-h-full">
          <div
            className="pointer-events-none absolute inset-y-6 left-0 z-20 w-px
                       bg-gradient-to-b from-transparent via-[rgba(74,127,212,0.4)] to-transparent"
            aria-hidden
          />
          <div className="absolute inset-0">
            {current.imageSrc ? (
              <>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  key={current.imageSrc}
                  src={`${current.imageSrc}?v=2`}
                  alt={current.imageAlt ?? ""}
                  className="absolute inset-0 h-full w-full object-cover object-center"
                />
                <div
                  className="absolute inset-0"
                  style={{
                    background:
                      "linear-gradient(90deg, rgba(5,13,26,0.55) 0%, transparent 32%), linear-gradient(180deg, rgba(5,13,26,0.2) 0%, transparent 30%, rgba(5,13,26,0.5) 100%)",
                  }}
                />
                <div
                  className="pointer-events-none absolute inset-3 rounded-xl
                             border border-[rgba(224,138,60,0.22)]"
                  aria-hidden
                />
              </>
            ) : null}
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
