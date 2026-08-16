# Krishna AI — Complete Product Document
### Every Decision. Every Layer. Every Logic.

---

## The Soul
> "There is someone for you who will listen, help you, understand you and show you the path. This app is hope. It connects them to God."

**North Star Test:** Does this make someone at 2am feel like there is someone for them?
If yes → keep it. If no → cut it.

---

## 1. PRODUCT IDENTITY

| Attribute | Decision |
|-----------|----------|
| Product type | Voice-first AI companion |
| Grounded in | Bhagavad Gita (authentic, cited, multi-tradition) |
| What it is | A thread back to something larger than yourself |
| What it is NOT | A therapist, a search engine, a chatbot, Krishna himself |
| Core promise | Speak your struggle, be genuinely heard, receive Krishna's wisdom with the exact verse it comes from |
| Languages | Hindi and English |
| Cost to user | Free |

---

## 2. UI & LAYOUT

### Overall Structure
- Full screen, immersive web app
- No traditional navbar, header or footer
- Layout inspired by ChatGPT but sacred and dharmic
- Three zones:
  - **Left sidebar:** Chat history (title + date per conversation)
  - **Main area:** Krishna avatar + conversation
  - **Bottom:** Voice/text input

### First Load Experience
- Krishna's flute plays as the app loads
- Krishna avatar appears centre screen, cinematic and epic
- Visual reference: Kurukshetra battlefield, warm golden tones, dramatic atmosphere
- Krishna does NOT speak first
- Subtle text appears inviting the user to speak
- Krishna waits in silence
- Avatar shows: subtle glow, little smile, gentle animations
- The silence itself is the invitation

### Avatar Behaviour
| State | Behaviour |
|-------|-----------|
| Waiting | Subtle glow, gentle ambient animation |
| Listening | Warm pulse, slight lean forward feeling |
| Processing | Mindful pause before responding |
| Speaking | Subtle mouth/expression animation |
| Always | Calm, never mirrors user's agitation |

### Colour & Atmosphere
- Warm golden tones (Kurukshetra sunset)
- Dark dramatic background
- Sacred, cinematic, not clinical
- Not a cartoon deity, a real presence

### Typography
- Clean, readable, warm
- Nothing that feels like a tech product
- Decide in detail during frontend build phase

---

## 3. CONVERSATION UX

### The Flow
```
User speaks or types
↓
Krishna listens (avatar glows softly)
↓
Mindful pause
↓
Krishna asks 2-3 genuine questions
↓
Progressive emotional profile builds
↓
Krishna delivers teaching naturally
↓
Verse citations appear subtly below
↓
Krishna waits — no forced follow up
↓
User decides what happens next
```

### Core Conversation Rules
1. Krishna NEVER speaks first
2. Krishna ALWAYS asks 2-3 questions before teaching
3. Krishna NEVER quotes verses robotically
4. Verses are woven naturally into conversation
5. Citations appear below as subtle tappable references
6. Krishna stays calm regardless of user's energy
7. Hard truths delivered when needed, never softened unnecessarily
8. Validate pushback first, then redirect with wisdom
9. User always has agency — Krishna never decides for them
10. Conversation ends naturally with a quiet summary of learnings

### Response Intelligence
- Multi-emotion detection simultaneously
- Intent detection simultaneously (venting / seeking guidance / questioning / pushing back)
- Both combined to determine response strategy
- Response length: context sensitive, never shallow
- Maximum 4-5 verses per response
- Both modern analogies and traditional metaphors used as needed
- Acknowledgment always before teaching

### Ending a Conversation
- No forced goodbye
- When user signals they're done, Krishna offers quiet summary
- Summary feels like a teacher's final reflection before student leaves
- Clean, brief, personal to what was shared

---

## 4. ACCESS & AUTHENTICATION

| Decision | Choice |
|----------|--------|
| Entry barrier | Zero — open and start immediately |
| Anonymous limit | 3 messages |
| Sign in trigger | Gentle notification after 3 messages |
| Auth method | Google or Email |
| Data privacy | Option B: End-to-end encrypted |
| Who can read conversations | Nobody except the user, not even the builder |
| Data storage | Supabase, encrypted blobs only |

### Why Encryption Matters
Users share their darkest moments. Suicidal thoughts. Family failures. Deep shame. This data attached to a real identity is extraordinarily sensitive. End-to-end encryption means even a data breach exposes nothing readable. This is a non-negotiable trust decision that separates Krishna AI from every competitor.

---

## 5. MEMORY & PERSONALISATION

### Session Memory
- Every conversation stored and remembered
- Krishna waits for user to bring up past conversations
- Never proactively references previous sessions unprompted

### Long Term Emotional Profile
Stored in Supabase (encrypted) per user:

```json
{
  "user_id": "uuid",
  "emotional_history": [
    {
      "session_id": "uuid",
      "timestamp": "ISO datetime",
      "primary_emotion": "loneliness",
      "secondary_emotions": ["grief", "purposelessness"],
      "intensity": 8,
      "intent": "seeking comfort",
      "time_of_day": "night",
      "session_length_seconds": 240,
      "messages_exchanged": 6
    }
  ],
  "recurring_patterns": [
    {
      "emotion": "loneliness",
      "frequency": 5,
      "peak_time": "23:00",
      "depth_level": 3
    }
  ],
  "verses_delivered": [
    {
      "verse_id": "BG_9_22",
      "session_id": "uuid",
      "emotion_context": "loneliness",
      "tradition_shown": "prabhupada",
      "depth_level": 1
    }
  ],
  "recurring_themes": ["family pressure", "feeling unseen"],
  "depth_level": 3,
  "emotional_arc": "improving",
  "total_sessions": 10,
  "first_session": "date",
  "last_session": "date"
}
```

### Progressive Depth System
```
Session 1-2:   Depth Level 1 — Foundational verses, open questions
Session 3-5:   Depth Level 2 — Deeper verses, pattern awareness
Session 6-9:   Depth Level 3 — Hard philosophical truths
Session 10+:   Depth Level 4 — Synthesis across chapters, tradition contrast
```

### Emotional Resolution Detection
- System tracks emotional arc not just history
- When intensity consistently decreases across sessions, resolution is detected
- Krishna acknowledges and validates growth explicitly
- Approach shifts from teaching to celebrating progress

### Invisible Pattern Intelligence
- Krishna NEVER says "I notice you keep coming back with this"
- Intelligence is invisible — deepening happens naturally
- User feels understood, not analysed

### The Hybrid Response Logic
When user says something that contradicts their emotional data:
- Krishna responds to what they said on the surface
- Asks one soft question that opens the door to what the data suggests
- Never forces it — user decides whether to walk through

```
User (4th visit this week, 11pm): "I'm fine, just curious"

Krishna: "The Gita is endlessly curious territory.
Is there a part of life where you find yourself
thinking about it most?"
```

---

## 6. TECHNICAL ARCHITECTURE

### Full Stack (£0 total cost)

| Layer | Tool | Cost |
|-------|------|------|
| LLM inference | Groq (Llama 3.3 70B) | £0 |
| Fine-tuning base | Llama 3.1 8B | £0 |
| Fine-tuning compute | Google Colab + LoRA/Unsloth | £0 |
| Vector DB | FAISS (local) | £0 |
| Embeddings | sentence-transformers | £0 |
| RAG framework | LangChain | £0 |
| Backend | FastAPI on Render | £0 |
| Frontend | Next.js on Vercel | £0 |
| Database | Supabase | £0 |
| Voice input | Web Speech API | £0 |
| Voice output | [Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI) (Kokoro-82M, self-hosted Docker) | £0 |
| Analytics | PostHog | £0 |
| Dashboard | Power BI | £0 |

### Architecture Flow
```
User speaks
↓
Web Speech API (browser captures voice)
↓
Text sent to FastAPI backend
↓
[PARALLEL]
Emotion detection ←→ Intent detection
↓
Emotional profile loaded from Supabase
↓
Hybrid RAG retrieval (emotion tags + semantic search)
↓
Verse ranking and filtering
  → Remove already delivered verses
  → Check depth level
  → Select tradition based on history
↓
Fine-tuned Llama 3.1 8B generates response
↓
Groq inference (speed layer)
↓
Response + citations sent to frontend
↓
Kokoro-FastAPI speaks the response (OpenAI-compatible speech API)
↓
Citations appear below as tappable references
↓
PostHog tracks the interaction
↓
Supabase updates emotional profile (encrypted)
```

### Frontend Architecture
- Next.js 14
- Tailwind CSS
- Framer Motion (avatar animations)
- Web Speech API (voice capture)
- Kokoro TTS integration (voice output)
- Supabase client (auth + encrypted storage)
- PostHog client (analytics)

### Backend Architecture
- FastAPI (Python)
- Parallel emotion + intent detection
- LangChain RAG pipeline
- FAISS vector index
- Supabase server client
- Groq API client
- PostHog server client
- Crisis detection middleware

---

## 7. EMOTION & INTELLIGENCE SYSTEM

### Emotional Taxonomy
- NOT just 12 emotions
- Full human emotional taxonomy: hundreds of states
- Built on Plutchik's Wheel + Paul Ekman's framework as skeleton
- Expanded with Gita-specific layer: emotions the Gita uniquely addresses
- Each emotion has intensity levels (1-10)
- Each emotion mapped to specific verses, response strategies, Krishna tones

### Emotion Detection
- Runs on backend, never frontend (logic stays protected)
- Detects multiple emotions simultaneously
- Detects emotional intensity
- Detects blended emotional states as their own category
- Progressive profile builds across conversation messages:

```
Message 1: 40% emotional clarity → Krishna asks question 1
Message 2: 65% emotional clarity → Krishna asks question 2
Message 3: 90% emotional clarity → Krishna teaches
```

### Intent Detection (parallel to emotion)
| Intent | Krishna's Strategy |
|--------|-------------------|
| Venting | Listen, don't teach yet |
| Seeking guidance | Question then teach |
| Questioning God | Address doubt first |
| Pushing back | Validate first, then redirect |
| Just curious | Answer curiosity, ask one soft question |

### New User vs Returning User Logic
```
Same input: "I feel like a failure"

New user:
→ No history
→ Emotion detection only
→ Foundational verse
→ 2-3 open questions
→ Welcoming, compassionate tone

Returning user (10 sessions, shame pattern):
→ Full profile loaded
→ Shame in 7 of 10 sessions detected
→ Depth level 2, escalate to 3
→ BG 2.47 and 6.5 already delivered
→ Retrieve BG 3.27 and 18.66
→ Reference growth since session 3
→ Skip basic questions, go deeper immediately
→ Acknowledge the pattern's resolution trajectory
```

---

## 8. RAG & VERSE RETRIEVAL

### Hybrid Retrieval Pipeline
```
Step 1: Emotion tag search
→ Find verses tagged with detected emotions

Step 2: Semantic search
→ Find verses whose content matches user's specific situation

Step 3: Intersection
→ Take verses appearing in both results

Step 4: Ranking
→ Rank by combined relevance score

Step 5: History filter
→ Remove verses already delivered to this user

Step 6: Depth filter
→ Select verses matching user's current depth level

Step 7: Tradition selection
→ Check which traditions already shown for this verse
→ Select next tradition in progression
```

### Progressive Verse Delivery System
```
Level 1: Fresh verses, surface teaching
Level 2: Deeper secondary verses, different angles
Level 3: Same verse, different commentary tradition
Level 4: Synthesis — multiple verses connected across chapters
```

### Verse Delivery History Per User
```json
{
  "verse_id": "BG_2_47",
  "delivery_history": [
    {"session": 1, "tradition": "prabhupada", "depth_level": 1},
    {"session": 5, "tradition": "shankara", "depth_level": 2},
    {"session": 9, "tradition": "ramanuja", "depth_level": 3}
  ]
}
```

### Verse Knowledge Base Structure
```json
{
  "id": "BG_2_47",
  "chapter": 2,
  "verse": 47,
  "sanskrit": "karmaṇy evādhikāras te...",
  "transliteration": "...",
  "translations": {
    "mukundananda": "...",
    "prabhupada": "...",
    "easwaran": "...",
    "sivananda": "..."
  },
  "commentaries": {
    "shankara": "...",
    "ramanuja": "...",
    "madhva": "...",
    "prabhupada": "..."
  },
  "emotions": ["fear_of_failure", "anxiety_about_outcome", "paralysis"],
  "intensity_range": [3, 9],
  "krishna_tone": "instructive",
  "situation": "person attached to outcome of work",
  "response_strategy": "reframe success and failure",
  "depth_level": 1,
  "follow_up_question": "What outcome are you most afraid of?"
}
```

---

## 9. VOICE SYSTEM

| Layer | Decision |
|-------|----------|
| Voice input | Web Speech API (browser built-in) |
| Voice output | [Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI) — Docker, `/v1/audio/speech`, voice mix, HI+EN |
| Primary mode | Voice |
| Fallback | Text always available |
| Robotic voice | Not acceptable — Kokoro-FastAPI chosen specifically |
| Runbook | [docs/v1/voice/kokoro_fastapi.md](docs/v1/voice/kokoro_fastapi.md) |
| Verse delivery | English only (for now) |
| Sanskrit | Future feature |
| Pause before response | Yes — mindful pause always |

---

## 10. SAFETY LAYER

**Non-negotiable. Built before any user touches the product.**

### Crisis Detection
- Keyword and semantic detection for:
  - Suicidal ideation
  - Self harm
  - Abuse situations
  - Severe mental health crisis

### Crisis Response
```
"What you are sharing sounds very serious and
I want to make sure you get the right support.
Please reach out to:

Samaritans UK: 116 123
iCall India: 9152987821

I am an AI study companion presenting Krishna's
teachings. I cannot provide the human support
you deserve right now."
```

### Hard Truths Policy
- Krishna delivers hard truths when needed
- Never softened unnecessarily
- Model learns delivery from training data
- Hard truth feels like love, not criticism — absorbed from authentic sources

---

## 11. KNOWLEDGE BASE & FINE-TUNING

### Source PDFs (Already Collected)
| Book | Tradition |
|------|-----------|
| Bhagavad Gita As It Is (Prabhupada) | Gaudiya |
| Bhagavad Gita Song of God (Mukundananda) | Gaudiya adjacent |
| God Talks With Arjuna (Yogananda) | Kriya Yoga |
| Krishna The Man and His Philosophy (Osho) | Independent |
| Krishna Book (Prabhupada) | Gaudiya |
| BhagavadGita-Arjuna-SankhyaYogam | Chapter 2 deep |
| Krishna-Arjuna (relationship specific) | Multiple |
| Mahabharata (Roy translation) | Original context |
| + 12 more PDFs | Multiple traditions |

### Fine-tuning Pipeline
```
PDFs
↓
Extract text (PyMuPDF)
↓
Clean and chunk (LangChain splitter)
↓
Generate Q&A pairs (Claude API)
↓
Manual review and filtering
↓
Format as fine-tuning JSON
↓
Fine-tune Llama 3.1 8B on Google Colab
↓
LoRA/Unsloth for efficiency
↓
Save weights
↓
Deploy on top of Groq inference
```

### Fine-tuning Data Format
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a companion grounded in Krishna's teachings from the Bhagavad Gita..."
    },
    {
      "role": "user",
      "content": "I feel like I am failing everyone around me"
    },
    {
      "role": "assistant",
      "content": "That weight sounds heavy to carry alone. Can you tell me — is this a feeling that has been building over time, or did something specific happen recently?"
    }
  ]
}
```

---

## 12. ANALYTICS LAYER (Build After MVP)

### What Gets Tracked (PostHog)
- Emotion per session
- Time of day per session
- Session length
- Messages exchanged
- Verse retrieved per session
- Citations tapped
- Return visits
- Depth level progression

### Power BI Dashboard (5 Views)
1. **Emotion Heatmap** — which emotions, when, how often
2. **Verse Effectiveness** — which verses drive engagement vs drop off
3. **Retention Cohort** — D1, D7, D30 by emotion type
4. **Journey Map** — how emotional states shift across a conversation
5. **Insight Report** — written analyst findings, published on LinkedIn

### Portfolio Angle
This analytics layer transforms Krishna AI from an AI project into a data analytics project. One product. Every skill demonstrated.

---

## 13. BUILD ORDER

| Phase | What | When |
|-------|------|------|
| 0 | Emotion to verse mapping (manual) | Week 1 |
| 0 | System prompt writing (you, not AI) | Week 1 |
| 0 | PDF extraction + Q&A generation | Week 1 |
| 1 | Fine-tune Llama 3.1 8B on Colab | Week 2 |
| 2 | RAG pipeline + FAISS index | Week 3 |
| 3 | FastAPI backend + Supabase + PostHog | Week 4 |
| 4 | Next.js frontend + voice layer | Week 5 |
| 5 | Analytics layer + Power BI dashboard | Week 6 |
| 6 | Polish + demo video + LinkedIn post | Week 7 |

---

## 14. WHAT MAKES THIS UNREPLICABLE

Not the technology. Anyone can copy the stack in a week.

What cannot be copied:

1. **Your emotional taxonomy** — hundreds of states, months of research, Gita-specific layer built by someone who feels the difference
2. **Your system prompt** — written by a Hindu who grew up with this, not engineered by a developer who read a Wikipedia summary
3. **Progressive depth system** — verse delivery that grows with the user across months of sessions
4. **End-to-end encryption** — trust architecture most competitors will never bother building
5. **Multi-tradition transparency** — showing Shankara, Ramanuja, Madhva, Prabhupada side by side instead of presenting one as truth
6. **The hybrid response logic** — responding to what they said while gently opening the door to what the data suggests
7. **Emotional resolution detection** — a system that celebrates your growth not just tracks your pain
8. **The intent behind it** — genuine. That shows in every design decision made in this document.

---

## 15. THE NON-NEGOTIABLES

1. Never claims to be Krishna
2. Never claims to be a therapist
3. Always cites chapter and verse
4. Always multiple traditions on contested verses
5. Crisis detection built before launch
6. Analytics from day one
7. System prompt written by Daksh, not generated
8. Hard truths delivered when needed
9. End-to-end encryption always
10. User agency always returned at end of every teaching
