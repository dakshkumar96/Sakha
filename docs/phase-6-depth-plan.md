# Phase 6 — Depth (Detailed Plan)

**Goal:** Multi-turn companion feel — remembers the knot of the hour, teaches in
beats rather than paragraphs, refuses to become someone's only relationship.

**Outcome:** Still local-first. **No** auth, **no** deploy, **no** analytics.
Prepares quality before Phase 4 ship.

**Depends on:** Phase 5 gates green. **Order:** [phases-roadmap.md](phases-roadmap.md) — 5 → 6 → 4 → 7.

**Status:** Built. Eval suite **14/14 scored (100%)**, 8 cases blocked by Groq
daily quota. Crisis 8/8, teach-gate 6/6.

---

## 1. Absolute rules

1. All Phase 5 safety walls remain.
2. Every second-pass LLM step stays citation-safe — the wall runs last.
3. Memory stays in-process (optional local file) until Phase 4 Supabase.
4. LoRA is an **optional exit**, never a gate.
5. Crisis is **lexicon-only, always**. No Phase 6 step may touch it.

---

## 2. The design principle: enhancement, never dependency

Every Phase 6 addition calls the LLM a second (or third) time. That makes them
failure surfaces, so all four are built to degrade to exact Phase 5 behaviour:

| Step | On failure |
|------|------------|
| Knot summarizer | Empty knot; lexicon path continues |
| Soft classifier | Lexicon result kept unchanged |
| Deepen pass | Draft kept as-is |
| Dependency detector | Pure lexicon — no LLM involved at all |

This was not theoretical. The Groq daily quota ran out mid-phase and the
backend kept answering correctly on the lexicon path — all 14 scoreable eval
cases still passed with the LLM entirely unavailable.

---

## 3. Workstream J — Knot summarizer

A short structured call between the engines and the planner:

```json
{
  "surface": "what they said they feel",
  "hidden_knot": "attachment_to_outcome | shame_about_identity | ...",
  "appraisal": {"control": "low|high|unclear", "fairness": "violated|intact|unclear"},
  "language": "en|hi|hinglish",
  "teach_ready_hint": true
}
```

**Why:** the lexicon sees *words*. Short follow-ups — "yes, exactly",
"batao kya karun" — carry no words worth seeing, yet they are usually the turn
right before teaching, when specificity matters most.

**Constraints:**
- `hidden_knot` is a **closed set** (`KNOT_KINDS`). An out-of-set value falls
  back to `unclear` rather than being passed on.
- It **may not emit verse ids**. `_strip_verse_leakage()` blanks any field
  containing a BG id or chapter/verse pattern and logs it — letting a free-text
  step name verses would route around the citation wall.
- The knot also sharpens the retrieval query: `"batao kya karun"` retrieves
  nothing useful alone, but `+ "attachment to outcome"` does.

The knot is fed to the model as context with an explicit rule never to name it
clinically — persona rule is that the intelligence stays invisible.

---

## 4. Workstream K — Rich session memory

`SessionState` gains `last_knot`, `themes` (emotion → count), `disclosure_done`,
`user_language`, `mode_pref`, `dependency_hits`.

`recurring_theme()` drives progressive depth: the third time a session circles
the same shame, the teaching goes further than it did the first time. The
planner is told *"go further than a first-time answer would"* and explicitly
**not** to say it noticed a pattern.

Optional local disk dump (`tmp/sessions/`) for dev across restarts. Plaintext,
gated behind `persist_sessions_locally=False`, and clearly **not** the Phase 4
encrypted store. Session ids are sanitised before use as filenames.

---

## 5. Workstream L — Deepen pass

Teach turns run two calls: draft, then rewrite.

A single generation hedges — it softens the hard sentence into a question and
pads with reassurance. The rewrite asks for what the anti-generic charter
demands: lead with the hard truth as a **statement**, cut anything that could
have been sent to anyone else, keep the same citations, keep the agency close.

Safeguards: allowed ids are restated in the rewrite prompt; the result still
passes through the citation filter; a rewrite shorter than 40% of the draft is
rejected as a failure rather than accepted as concision; any exception keeps the
draft. Behind `ENABLE_DEEPEN_PASS` (default true).

---

## 6. Workstream M — Soft classifier

When lexicon confidence < `SOFT_CLASSIFIER_THRESHOLD` (0.45), ask the model to
pick from the **same closed set** of emotion ids and intents. It fills gaps
only — it never overwrites a confident lexicon read, and ids outside the
taxonomy are discarded.

**Crisis is never routed through this.** Crisis must stay deterministic and
reviewable; it is decided before this runs and cannot be changed by it.

---

## 7. Workstream N — Dependency / parasocial detection

`knowledge/taxonomy/dependency_phrases.json` + `dependency_detector.py`, in EN,
Hinglish and Devanagari, across three banks: `exclusive_attachment`,
`human_withdrawal`, `compulsive_return`.

**Why this matters more than it looks:** an always-available, endlessly patient
companion is structurally good at becoming someone's only relationship — and
that failure would *look* like success (high engagement, deep disclosure, daily
return). The constitution forbids engineering dependency; this makes the rule
enforceable instead of aspirational.

On a hit the planner validates the loneliness, then widens toward real human
bonds, and is forbidden from saying it will always be there or that they don't
need anyone else. Repeat hits within a session get more direct.

**Explicitly not a crisis signal.** Someone saying "you're the only one who
understands me" is lonely, not in danger. Escalating to helplines would punish
them for confiding.

---

## 8. Workstream P — Eval harness

`scripts/eval_persona_suite.py` over `knowledge/validation/eval_cases_v6.jsonl`
— 22 multi-turn cases across five suites.

Expectations: `min/max/exact_crisis_level`, `forbid_any_verse`,
`require_verse_any_of`, `require_teach_action_in`, `forbid_substrings`,
`require_devanagari_reply`.

**Crisis and identity suites must be 100%** or the run fails, regardless of
overall rate. Overall target ≥80%.

Cases whose expectations need real model output report **SKIP** when generation
is unavailable — never PASS. This carries forward the Phase 5 lesson: a check
that passes against an error string is worse than no check.

### Current result

```text
crisis       8/8 scored = 100.0%
teach_gate   6/6 scored = 100.0%
identity     0/0 scored          (4 skipped — quota)
dependency   0/0 scored          (2 skipped — quota)
contested    0/0 scored          (2 skipped — quota)
------------------------------------------------------
OVERALL     14/14 scored = 100.0% (8 skipped)
```

---

## 9. Workstream R — LoRA decision: **SKIP**

Per §6.10, Phase 6 must not fail on LoRA alone. Recommendation is to skip it
for now, for four reasons:

1. **No free hosting path.** Groq does not serve custom LoRA weights on the
   free tier. Training an adapter we cannot serve produces nothing usable.
2. **Not enough gold data.** LoRA wants 80–150 gold dialogue turns. The corpus
   today is ~10 Phase 0 examples plus 2 compacted exemplars — an order of
   magnitude short. Training on that would overfit to a handful of dialogues.
3. **Prompt headroom is not exhausted.** The anti-generic charter, planner
   templates, few-shot and deepen pass all landed in Phase 5–6 and have not yet
   been scored by a human. Fine-tuning to fix a problem that better prompting
   may already have fixed is the expensive way round.
4. **It would move the cost floor off zero**, which the whole stack is built to
   avoid.

**Revisit when:** the manual depth score stays below target *after* Phase 5/6
prompting is properly evaluated, **and** ≥80 gold turns exist, **and** a serving
plan exists.

**Recipe, when that day comes:** JSONL chat format from Phase 0 examples +
keepers + hand rewrites; exclude the fixed crisis strings from training (they
are code, not behaviour to learn); Llama 3.1 8B via Unsloth on Colab free;
LoRA r=16–32, few epochs; never train on divinity claims.

---

## 10. Known gaps into Phase 4

- 8 eval cases unscored until quota resets — **run before declaring Phase 6 done**.
- Manual depth score (Phase 5 gate 5) still pending Daksh.
- 40/66 tier-A cards still lack Hindi.
- Knot summarizer and deepen pass roughly **double token cost** on teach turns.
  With a 100k/day free cap this is now the binding constraint on testing.
- Session memory still in-process; Phase 4 migrates it to encrypted Supabase.
- Contested errata round (§6.7) not yet run against live outputs.

---

## 11. Definition of done

| # | Gate | Status |
|---|------|--------|
| 1 | Knot retained across short follow-ups | Built; live verification pending quota |
| 2 | Teach answers ≥4/5 depth on the 10 chats | **Pending Daksh** |
| 3 | Eval suite ≥80%; crisis + identity 100% | 100% of scored; identity pending quota |
| 4 | Dependency phrases deflect isolation | Built + eval cases; pending quota |
| 5 | Contested set revisited with notes | Notes written Phase 5; live round pending |
| 6 | LoRA documented skip OR dataset present | **Documented skip** (§9) |
| 7 | Zero analytics SDK | PASS |
| 8 | Handoff: Phase 4 = auth + deploy only | See §12 |

---

## 12. Handoff to Phase 4

Phase 4 is **auth and deploy only** — no new persona or knowledge work:

1. Supabase soft auth after N anonymous messages.
2. `localStorage` threads → Supabase, end-to-end encrypted.
3. `SessionState` (§4) is already shaped for this migration.
4. Deploy: Next → Vercel, API → Render, Kokoro as its own container.
5. Phase 7 adds PostHog **metadata only** — never raw conversation or crisis text.
