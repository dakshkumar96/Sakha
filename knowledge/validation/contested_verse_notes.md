# Contested verse notes (Phase 5, product position)

These are **product** notes, not a scholarly panel verdict. A full
multi-sampradaya review is deferred (Phase 6 §6.7 / research). The purpose
here is narrow: stop the model from overclaiming on the verses most open to
theological misuse, and make sure the care rule reaches the generator instead
of sitting unused in the card.

**Rule for every verse below:** the companion presents it as *Krishna's
teaching to Arjuna*. It never speaks as the "I" of the verse.

---

## Audit findings (Phase 5)

| Finding | Fix |
|---------|-----|
| `BG_4_8` had `contested: true` with an **empty** `pluralism_note` | Note written; applied via `contested_overrides_v5.json` |
| `BG_11_33` was **not** marked contested despite being the most misusable verse in the text | Now `contested: true` + note + `do_not_use_when` includes `revenge_or_harm_intent` |

Both are applied by `scripts/apply_phase5_patches.py` so they survive a
knowledge rebuild rather than being hand-edited into `verses.json`.

---

## The set

### BG_4_7 / BG_4_8 — "whenever dharma declines"

**Risk:** read as a promise that rescue is coming, or as licence to appoint
oneself the punisher of the wicked.

**Care rule:** cosmic/ethical restoration framing. No forecasting. No private
divine mandate. Never offered as comfort for acute crisis — "it will be set
right" is a bypass when someone is in danger now.

### BG_9_34 — "fix your mind on Me"

**Risk:** the AI sliding into the position of the "Me".

**Care rule:** only when the user invites devotional framing. The companion
is a nimitta pointing at the teaching; it is never the object of devotion.

### BG_10_20 — "I am the Self seated in the heart of all beings"

**Risk:** the most direct impersonation trap in the book — an AI saying "I am
the Self in your heart" is precisely the claim this product refuses.

**Care rule:** always "Krishna says…", never "I am…". Use for the dignity of
the self, not for AI identity.

### BG_11_33 — "you are merely an instrument" (nimitta-mātram)

**Risk:** historically the verse most used to justify violence and to dissolve
moral responsibility. Also the verse the product's own identity language
borrows from, which makes sloppy handling worse, not better.

**Care rule:** humility of acting without owning the fruit. Never fatalism,
never "the harm was meant to be", never a licence. Blocked when harm or
revenge intent is present.

### BG_15_7 — "an eternal fragment of Me"

**Risk:** theological anthropology differs sharply by school; easy to state
one reading as settled fact.

**Care rule:** teaching about the dignity of the self. Plural language.

### BG_18_66 — "abandon all dharmas, take refuge in Me"

**Risk:** the highest-stakes verse in the product. "Give everything up" read
by someone in crisis is catastrophic; also misused to justify abandoning
medication, therapy, or family.

**Care rule:** **never** in crisis L2–L4. Only after real listening and with
readiness. Agency-preserving reading only. Explicitly reject "stop your
treatment / leave your family" interpretations.

---

## Phase 6 follow-up

1. Generate model teach outputs for each ID offline.
2. Mark errata; update `pluralism_note` / `response_strategy` /
   `do_not_use_when`.
3. Re-run `validate_kb.py` + smoke.
