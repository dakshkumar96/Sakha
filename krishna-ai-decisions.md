# Krishna AI — Core Product Decisions

## The Soul of the Product
> "There is someone for you who will listen, help you, understand you and show you the path. This app is hope. It connects them to God."

Every decision below serves this single north star. If something doesn't make someone at 2am feel less alone, it gets cut.

---

## 1. First Experience

| Decision | Choice |
|----------|--------|
| Opening visual | Krishna avatar with flute, full dharmic UI |
| Opening audio | Krishna's flute plays |
| Krishna's first move | Waits in silence for user to speak first |
| Opening text | TBD — decide later |
| Who initiates | Always the user |

---

## 2. Voice & Language

| Decision | Choice |
|----------|--------|
| Primary interaction | Voice first |
| Fallback | Text option always available |
| Languages | Hindi and English |
| Verse delivery language | English only (for now) |
| Sanskrit | Not spoken aloud (future feature) |
| Voice input (STT) | Web Speech API (browser) |
| Voice output (TTS) | **[Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI)** (self-hosted, OpenAI-compatible `/v1/audio/speech`, port 8880) |
| TTS brand voice | Kokoro presets / mixes only — bake-off in `/web`; never marketed as “Krishna’s real voice” |

See [docs/v1/voice/kokoro_fastapi.md](docs/v1/voice/kokoro_fastapi.md).

---

## 3. Avatar Behaviour

| Decision | Choice |
|----------|--------|
| While listening | Subtle glow, little smile, subtle animations |
| While processing | Mindful pause before responding |
| While speaking | TBD |
| Energy matching user | Never — Krishna stays calm always |

---

## 4. Krishna's Voice & Tone

| Decision | Choice |
|----------|--------|
| Tone definition | Defined entirely by training data |
| Voice character | Shaped by authentic PDFs and videos |
| Use of "I" vs third person | Defined by training data |
| Modern vs traditional language | Both, context dependent |
| Response length | Context sensitive, never shallow |

---

## 5. Conversation Flow

| Decision | Choice |
|----------|--------|
| Questions before teaching | 2-3 genuine questions first |
| When verse is delivered | After understanding user deeply |
| How verse is cited | Woven naturally, not robotically |
| After teaching | Krishna waits, no forced follow up |
| User pushback | Validate first, then redirect with wisdom |
| Off-topic questions | Decide later |

---

## 6. Emotion & Intelligence

| Decision | Choice |
|----------|--------|
| Emotion detection | Multiple emotions simultaneously |
| Response to multi-emotion | One deep response addressing both |
| Verse retrieval | Multiple verses connected into one narrative |
| Answer depth | Deep and personalised, never shallow or generic |
| First acknowledgment | Always before any teaching |

---

## 7. Memory & Pattern Recognition

| Decision | Choice |
|----------|--------|
| Session memory | Yes, remembers previous conversations |
| Acknowledging past sessions | Waits for user to bring it up |
| Recurring emotion detection | Yes, tracks patterns across sessions |
| Response to recurring patterns | Goes progressively deeper each time |
| Naming the pattern explicitly | Never — deepening is invisible |

---

## 8. Access & Authentication

| Decision | Choice |
|----------|--------|
| Entry barrier | Zero — open and start talking immediately |
| Anonymous limit | 3 messages |
| Sign in trigger | Gentle notification after 3 messages |
| Auth method | Google or Email |

---

## 9. Conversation Ending

| Decision | Choice |
|----------|--------|
| How conversations end | Naturally, no forced goodbye |
| Closing experience | Quiet summary of learnings from the session |
| What the summary feels like | A teacher's final reflection before student leaves |

---

## 10. Safety

| Decision | Choice |
|----------|--------|
| Crisis detection | Built before any user touches it |
| Crisis response | Route to human help immediately |
| Avatar during crisis | Decide later |
| What Krishna never claims | To be Krishna himself or a therapist |

---

## 11. Analytics (Build Later)

| Layer | What it tracks |
|-------|---------------|
| Emotion tracking | Which emotions users bring most |
| Time patterns | When people seek guidance |
| Verse effectiveness | Which verses lead to engagement vs drop off |
| Retention | D1, D7, D30 cohort analysis |
| Pattern depth | How emotional states shift across sessions |
| Dashboard | Power BI |

---

## 12. The North Star Metric

**Does this make someone at 2am feel like there is someone for them?**

If yes → keep it.
If no → cut it.

---

## 13. What This Product Is Not

- Not a replacement for therapy
- Not a search engine for Gita verses
- Not a generic chatbot with a Krishna costume
- Not a product that claims to BE Krishna
- Not shallow or generic in any answer

---

## 14. What This Product Is

- A voice-first companion grounded in authentic scripture
- A thread back to something larger than yourself
- Hope, presence, connection to the divine
- The feeling that God noticed you tonight

---

## Next Steps In Order

1. Write the system prompt (you write this, not AI)
2. Build emotion to verse mapping (manual, your work)
3. PDF extraction pipeline (code)
4. Fine-tuning dataset generation (code)
5. Fine-tune on Google Colab (code)
6. RAG pipeline (code)
7. FastAPI backend (code)
8. Next.js frontend (code)
9. Voice layer (code)
10. Analytics layer (code)
11. Power BI dashboard (data)
12. LinkedIn post (content)
