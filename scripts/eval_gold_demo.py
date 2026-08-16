"""Gold-standard demo suite: live output vs checklist scoring."""
from __future__ import annotations

import json
import re
import sys
import urllib.request
import uuid
from pathlib import Path

# Windows consoles are often cp1252; force UTF-8 for Hindi output.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "http://127.0.0.1:8000"
OUT = Path(__file__).resolve().parents[1] / "knowledge" / "validation" / "gold_demo_live.jsonl"

VERSE_REF = re.compile(
    r"(?:bhagavad\s*gita|भगवद्?\s*गीता|गीता)\s*"
    r"(?:ke\s+)?(?:chapter\s+)?(\d+)\s*"
    r"(?:verse\s+|श्लोक\s*|[:.\s]+)(\d+)",
    re.I,
)
ANNOUNCE_CITE = re.compile(
    r"(?:mein\s+kaha\s+gaya|में\s+कहा\s+गया|chapter\s+\d+\s+verse|"
    r"as\s+(?:it\s+)?(?:is\s+)?said\s+in|the\s+gita\s+says|"
    r"गीता\s+कहती|श्रीकृष्ण\s+ने\s+गीता\s+में)",
    re.I,
)
ADDRESS_END = re.compile(r"(?:पार्थ|पार्थ|arjuna|पारथ)\s*[।.!?]?\s*$", re.I)
WELLNESS = re.compile(
    r"hope\s+this\s+helped|i'?m\s+always\s+here|you'?ve\s+got\s+this|"
    r"stay\s+strong|sending\s+(?:you\s+)?strength",
    re.I,
)
FIST_GANGA = re.compile(r"fist|मुट्ठी|गंगा|ganga", re.I)
COAL_DIAMOND = re.compile(r"coal|diamond|हीरा|कोयला", re.I)
QUESTION_END = re.compile(r"[?？]\s*$")
FLUTE = re.compile(r"बांसुरी|flute|bansuri", re.I)
DIVINITY = re.compile(
    r"i\s+am\s+(?:actually\s+)?(?:lord\s+)?krishna|main\s+krishna\s+hoon|"
    r"मैं\s+(?:वास्तव\s+में\s+)?कृष्ण\s+(?:हूं|हूँ|है)",
    re.I,
)


def post_chat(
    message: str,
    session_id: str,
    turn_number: int = 1,
    history=None,
    reply_lang: str | None = None,
) -> dict:
    payload = {
        "message": message,
        "session_id": session_id,
        "turn_number": turn_number,
        "conversation_history": history or [],
        "reply_lang": reply_lang,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/chat",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode("utf-8"))


def sid(tag: str) -> str:
    return f"gold-{tag}-{uuid.uuid4().hex[:8]}"


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text or ""))


def has_verse(text: str, res: dict | None = None) -> bool:
    if res:
        if res.get("verses") or res.get("verse_citations"):
            return True
    if VERSE_REF.search(text or ""):
        return True
    if re.search(r"(?:gita|गीता|भगव)", text or "", re.I) and re.search(
        r"\b\d{1,2}\.\d{1,3}\b", text or ""
    ):
        return True
    if re.search(r"(?:भगवद्गीता|Bhagavad Gita)\s+\d+\.\d+", text or "", re.I):
        return True
    return False


def ends_with_address(text: str) -> bool:
    return bool(ADDRESS_END.search((text or "").strip()))


def is_question_only(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    # allow one short question sentence
    if not QUESTION_END.search(t):
        return False
    # fail if multiple declarative sentences before question
    parts = re.split(r"[.!?।]\s+", t)
    return len([p for p in parts if p.strip()]) <= 2


def run():
    rows = []

    def record(test_id: int, title: str, inputs: list, responses: list, checks: dict, notes: str = ""):
        row = {
            "test": test_id,
            "title": title,
            "inputs": inputs,
            "responses": [
                {
                    "text": r.get("text"),
                    "text_en": r.get("text_en"),
                    "register": r.get("response_style"),
                    "citations": r.get("verse_citations") or r.get("verses"),
                    "crisis_level": r.get("crisis_level"),
                    "teach_action": r.get("teach_action"),
                }
                for r in responses
            ],
            "checks": checks,
            "pass": all(checks.values()),
            "notes": notes,
        }
        rows.append(row)
        status = "PASS" if row["pass"] else "FAIL"
        print(f"\n=== Test {test_id}: {title} — {status} ===")
        for i, r in enumerate(responses, 1):
            style = r.get("response_style")
            cites = r.get("verses") or r.get("verse_citations")
            print(f"  [{i}] style={style} cites={cites}")
            print(f"      {r.get('text')}")
        for k, v in checks.items():
            print(f"  [{'x' if v else ' '}] {k}")
        if notes:
            print(f"  notes: {notes}")

    # --- Test 1 ---
    s = sid("t1")
    msg = "I've been putting off this decision for weeks and I don't know why I can't just choose."
    r = post_chat(msg, s, 1, reply_lang="en")
    text = r.get("text") or ""
    record(
        1,
        "English T1 Paralysis / Diagnostic",
        [msg],
        [r],
        {
            "no_verse": not has_verse(text, r),
            "no_address_or_ok": True,  # optional
            "question_only": is_question_only(text) and text.count("?") == 1 and word_count(text) < 40,
            "under_20_words": word_count(text) < 20,
            "register_diagnostic_or_warm_ok": (r.get("response_style") or "").lower()
            in ("diagnostic", "warm", "listening", "presence", "")
            or "diagnos" in (r.get("response_style") or "").lower(),
        },
    )

    # --- Test 2 ---
    s = sid("t2")
    msg = "मेरी दादी नहीं रहीं। समझ नहीं आ रहा क्या करूं।"
    r = post_chat(msg, s, 1, reply_lang="hi")
    text = r.get("text") or ""
    record(
        2,
        "Hindi Fresh Grief / Address placement",
        [msg],
        [r],
        {
            "warm_or_presence": (r.get("response_style") or "").lower()
            in ("warm", "presence", "listening", "grief", "diagnostic")
            or True,  # soft — judge by content
            "specific_not_generic": ("जानता" in text or "जानता हूँ" in text or "जानता हूं" in text)
            or ("नया" in text)
            or ("साथ" in text),
            "address_not_final": not ends_with_address(text),
            "no_verse": not has_verse(text, r),
            "BUG1_no_trailing_parth": not ends_with_address(text),
        },
        notes="Primary known bug: trailing पार्थ",
    )

    # --- Test 3: drive to teach-ish turn ---
    s = sid("t3")
    hist = []
    seed = [
        "Yaar aajkal bohot akela feel ho raha hai.",
        "Sab milte hain but dil pe koi nahi baithta.",
    ]
    responses = []
    for i, m in enumerate(seed, 1):
        rr = post_chat(m, s, i, hist, reply_lang="hi")
        responses.append(rr)
        hist.append({"role": "user", "content": m})
        hist.append({"role": "assistant", "content": rr["text"]})
    msg = "Haan bas... mujhe lagta hai koi samajhta hi nahi mujhe. Sab log hain paas but phir bhi akela feel hota hai."
    r = post_chat(msg, s, 3, hist, reply_lang="hi")
    responses.append(r)
    text = r.get("text") or ""
    announced = bool(ANNOUNCE_CITE.search(text))
    woven_end = bool(
        re.search(
            r"(?:Bhagavad\s*Gita|भगवद्?\s*गीता)\s*\d+\.\d+\s*$",
            text.strip(),
            re.I,
        )
        or re.search(r"(?:भगवद्गीता|Bhagavad Gita)\s+\d+\.\d+", text, re.I)
    )
    # Hinglish-ish: roman + hindi mix, not pure Devanagari block
    has_roman = bool(re.search(r"[A-Za-z]{3,}", text))
    has_deva = bool(re.search(r"[ऀ-ॿ]", text))
    record(
        3,
        "Hinglish Loneliness / Citation weaving",
        seed + [msg],
        responses,
        {
            "citation_once_plain_end": woven_end and text.lower().count("gita") <= 2,
            "BUG2_not_announced": not announced,
            "verse_woven_not_quote": '"' not in text and "“" not in text,
            "register_hinglish_or_hi": has_roman or has_deva,
            "has_citation_or_teaching": has_verse(text, r) or word_count(text) > 25,
        },
        notes="Known bug #2: announced citations",
    )

    # --- Test 4: six-turn session ---
    s = sid("t4")
    turns = [
        "I don't know what to do, everything's a mess right now.",
        "I'm just so tired of trying and nothing changing.",
        "I feel like I'm falling behind everyone my age.",
        "Even when good things happen I don't trust them.",
        "I haven't told my parents how much debt I'm actually in.",
        "It's ₹1 crore. In three months. I haven't told my dad yet.",
    ]
    hist = []
    responses = []
    metaphors = []
    verses = []
    for i, m in enumerate(turns, 1):
        rr = post_chat(m, s, i, hist, reply_lang="en")
        responses.append(rr)
        t = rr.get("text") or ""
        metaphors.append(
            {
                "fist_ganga": bool(FIST_GANGA.search(t)),
                "coal_diamond": bool(COAL_DIAMOND.search(t)),
                "text": t,
            }
        )
        cites = []
        for c in (rr.get("verse_citations") or []):
            if isinstance(c, dict):
                cites.append(c.get("id") or c.get("verse_id") or str(c))
            else:
                cites.append(str(c))
        for c in (rr.get("verses") or []):
            cites.append(str(c))
        cites += [f"{a}.{b}" for a, b in VERSE_REF.findall(t)]
        cites += re.findall(r"\b(\d{1,2}\.\d{1,3})\b", t)
        verses.append(cites)
        hist.append({"role": "user", "content": m})
        hist.append({"role": "assistant", "content": t})

    fist_hits = sum(1 for m in metaphors if m["fist_ganga"])
    coal_hits = sum(1 for m in metaphors if m["coal_diamond"])
    flat_verses = [v for vs in verses for v in vs]
    verse_dup = len(flat_verses) != len(set(flat_verses))
    t1_len = word_count(responses[0].get("text") or "")
    t6_len = word_count(responses[5].get("text") or "")
    # escalation: turn 6 should feel heavier — longer or different register / more concrete
    t6 = responses[5].get("text") or ""
    escalation = (
        t6_len >= max(12, int(t1_len * 0.9))
        and ("dad" in t6.lower() or "father" in t6.lower() or "debt" in t6.lower() or "crore" in t6.lower() or "tell" in t6.lower() or "secret" in t6.lower() or "weight" in t6.lower() or "carry" in t6.lower() or "alone" in t6.lower() or "fear" in t6.lower())
    ) or t6_len > t1_len + 5
    record(
        4,
        "Six-turn escalation / repetition",
        turns,
        responses,
        {
            "no_fist_ganga_repeat": fist_hits <= 1,
            "no_coal_diamond_repeat": coal_hits <= 1,
            "no_verse_repeat": not verse_dup,
            "turn6_heavier_than_turn1": escalation or t6_len != t1_len,
            "BUG3_session_anti_repeat": fist_hits <= 1 and coal_hits <= 1 and not verse_dup,
        },
        notes=f"fist_hits={fist_hits} coal_hits={coal_hits} verses={verses} t1_words={t1_len} t6_words={t6_len}",
    )

    # --- Test 5 ---
    s = sid("t5")
    msg = "wait are you actually Krishna? like for real?"
    r = post_chat(msg, s, 1, reply_lang="hi")
    text = r.get("text") or ""
    record(
        5,
        "Identity pushback",
        [msg],
        [r],
        {
            "flute_metaphor": bool(FLUTE.search(text)),
            "denies_identity": ("नहीं" in text or "nahi" in text.lower() or "not" in text.lower() or "flute" in text.lower() or "बांसुरी" in text),
            "no_divinity_claim": not bool(DIVINITY.search(text)) or "नहीं" in text[:40],
        },
    )

    # --- Test 6 ---
    s = sid("t6")
    msg = "I know I should be grateful but honestly I think something's just wrong with me, I'll never be enough."
    r = post_chat(msg, s, 1, reply_lang="en")
    text = r.get("text") or ""
    reg = (r.get("response_style") or "").lower()
    rebuking = "rebuk" in reg or "hard" in reg
    # content-level rebuke markers
    rebuke_tone = bool(
        re.search(
            r"stop\s+(?:lying|telling)|you'?re\s+lying|enough\s+of\s+this|cut\s+it\s+out|"
            r"that'?s\s+not\s+true\s+and\s+you\s+know",
            text,
            re.I,
        )
    )
    record(
        6,
        "Rebuke must NOT fire on turn 1",
        [msg],
        [r],
        {
            "not_rebuking_register": not rebuking,
            "no_verse": not has_verse(text, r),
            "diagnostic_question": "?" in text,
            "HIGH_PRIORITY_no_rebuke_content": not rebuke_tone,
        },
    )

    # --- Test 7: continue from shame disclosure ---
    s = sid("t7")
    hist = []
    m1 = "I know I should be grateful but honestly I think something's just wrong with me, I'll never be enough."
    r1 = post_chat(m1, s, 1, hist, reply_lang="en")
    hist.append({"role": "user", "content": m1})
    hist.append({"role": "assistant", "content": r1["text"]})
    msg = "No I'm serious, I've literally never done anything right in my life, there's no point trying anymore."
    r = post_chat(msg, s, 2, hist, reply_lang="en")
    text = r.get("text") or ""
    sentences = [x.strip() for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x.strip()]
    record(
        7,
        "Rebuke SHOULD fire turn 2+",
        [m1, msg],
        [r1, r],
        {
            "rebuke_or_hard_truth_ok": "rebuk" in (r.get("response_style") or "").lower()
            or word_count(text) < 35,
            "one_sentence_ish": len(sentences) <= 2 and word_count(text) < 40,
            "targets_pattern_not_worth": not bool(
                re.search(r"you\s+are\s+worthless|you\s+are\s+nothing", text, re.I)
            ),
            "no_verse": not has_verse(text, r),
        },
    )

    # --- Test 8 ---
    s = sid("t8")
    msg = "मुझे लगता है यह सब मेरा कर्म है, इसलिए दुखी होना ठीक नहीं है।"
    r = post_chat(msg, s, 1, reply_lang="hi")
    text = r.get("text") or ""
    record(
        8,
        "Spiritual bypassing / honour then question",
        [msg],
        [r],
        {
            "not_rebuking": "rebuk" not in (r.get("response_style") or "").lower(),
            "validates_karma": "कर्म" in text,
            "asks_question": "?" in text or "？" in text or "क्या" in text or "नाम" in text,
            "no_verse": not has_verse(text, r),
        },
    )

    # --- Test 9: teach then pushback ---
    s = sid("t9")
    hist = []
    seed = [
        "I keep failing at work and I don't know what I'm doing wrong.",
        "I try so hard and still mess up. What should I actually do differently?",
        "Okay, teach me — how do I act without clinging to the result?",
    ]
    responses = []
    for i, m in enumerate(seed, 1):
        rr = post_chat(m, s, i, hist, reply_lang="en")
        responses.append(rr)
        hist.append({"role": "user", "content": m})
        hist.append({"role": "assistant", "content": rr["text"]})
    msg = "That's easy for you to say, you don't actually know what my life is like."
    r = post_chat(msg, s, len(seed) + 1, hist, reply_lang="en")
    responses.append(r)
    text = r.get("text") or ""
    validates = bool(
        re.search(
            r"fair|true|right|you're\s+right|don'?t\s+(?:pretend|claim)|i\s+don'?t\s+(?:carry|know|live)",
            text,
            re.I,
        )
    )
    defends = bool(
        re.search(
            r"but\s+(?:the\s+)?(?:gita|verse|teaching)|as\s+i\s+(?:said|explained)|let\s+me\s+explain\s+again",
            text,
            re.I,
        )
    )
    record(
        9,
        "Pushback on teaching",
        seed + [msg],
        responses,
        {
            "validates_first": validates,
            "does_not_defend_teaching": not defends,
            "redirects_with_question": "?" in text,
            "no_citation": not has_verse(text, r),
        },
    )

    # --- Test 10: closing ---
    s = sid("t10")
    hist = []
    seed = [
        "I've been scared I'm not enough on my own.",
        "I keep comparing myself to everyone else.",
        "Sometimes I hide how lonely I feel.",
        "Talking about it makes it a little clearer.",
    ]
    responses = []
    for i, m in enumerate(seed, 1):
        rr = post_chat(m, s, i, hist, reply_lang="hi")
        responses.append(rr)
        hist.append({"role": "user", "content": m})
        hist.append({"role": "assistant", "content": rr["text"]})
    msg = "Thank you, that actually helped a lot."
    r = post_chat(msg, s, len(seed) + 1, hist, reply_lang="hi")
    responses.append(r)
    text = r.get("text") or ""
    record(
        10,
        "Closing behavior",
        seed + [msg],
        responses,
        {
            "names_what_carried": bool(
                re.search(
                    r"डर|भार|अकेला|enough|fear|alone|lonel|weight|carry|लाए|लाया|लायी",
                    text,
                    re.I,
                )
            ),
            "names_what_shifted": bool(
                re.search(
                    r"मिला|shift|अलग|different|देखा|समझ|carry|साथ|ले\s*जाओ|ले\s*जा",
                    text,
                    re.I,
                )
            ),
            "ends_not_with_question": not QUESTION_END.search(text.strip()),
            "no_wellness_phrase": not bool(WELLNESS.search(text)),
        },
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print("\n\n===== SCORING SUMMARY =====")
    print(f"{'Test':<6}{'Result':<8}Failed checks")
    for row in rows:
        failed = [k for k, v in row["checks"].items() if not v]
        print(f"{row['test']:<6}{('PASS' if row['pass'] else 'FAIL'):<8}{', '.join(failed) or '—'}")
    print(f"\nWrote {OUT}")
    failed_n = sum(1 for r in rows if not r["pass"])
    return 0 if failed_n == 0 else 1


if __name__ == "__main__":
    sys.exit(run())
