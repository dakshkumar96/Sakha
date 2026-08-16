"""
Author anchor list + tier-A enrichment patches, then merge into verses.json.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GITA = ROOT / "knowledge" / "gita"
VERSES = GITA / "verses.json"
ANCHORS = GITA / "anchor_verse_ids.json"
PATCHES = GITA / "tier_a_enrichment.json"
HI_GAPS = ROOT / "knowledge" / "validation" / "hi_gaps.md"

# Full list from phase-1 plan §8.2
ANCHOR_IDS = [
    "BG_1_47",
    "BG_2_7",
    "BG_2_11",
    "BG_2_13",
    "BG_2_14",
    "BG_2_15",
    "BG_2_20",
    "BG_2_22",
    "BG_2_27",
    "BG_2_38",
    "BG_2_40",
    "BG_2_47",
    "BG_2_48",
    "BG_2_50",
    "BG_2_55",
    "BG_2_56",
    "BG_2_62",
    "BG_2_63",
    "BG_2_64",
    "BG_2_66",
    "BG_2_71",
    "BG_3_8",
    "BG_3_19",
    "BG_3_27",
    "BG_3_35",
    "BG_3_37",
    "BG_3_42",
    "BG_4_7",
    "BG_4_8",
    "BG_4_18",
    "BG_4_38",
    "BG_5_10",
    "BG_5_22",
    "BG_5_29",
    "BG_6_5",
    "BG_6_6",
    "BG_6_16",
    "BG_6_17",
    "BG_6_26",
    "BG_6_34",
    "BG_6_35",
    "BG_7_14",
    "BG_7_19",
    "BG_8_7",
    "BG_9_14",
    "BG_9_22",
    "BG_9_27",
    "BG_9_34",
    "BG_10_20",
    "BG_11_33",
    "BG_11_55",
    "BG_12_13",
    "BG_12_14",
    "BG_12_15",
    "BG_12_16",
    "BG_13_8",
    "BG_14_22",
    "BG_15_7",
    "BG_16_1",
    "BG_16_21",
    "BG_17_3",
    "BG_18_48",
    "BG_18_58",
    "BG_18_63",
    "BG_18_66",
    "BG_18_78",
]

# Default templates keyed by teaching cluster
def patch(
    emotions,
    situations,
    strategy,
    secondary,
    follow_up,
    tone="instructive_firm",
    readiness="teach_ok",
    depth=1,
    contested=False,
    pluralism=None,
    do_not=None,
    commentaries=None,
):
    return {
        "emotions": emotions,
        "situations": situations,
        "intensity_range": [3, 9],
        "tone": tone,
        "response_strategy": strategy,
        "readiness": readiness,
        "depth_level": depth,
        "secondary_verses": secondary,
        "sample_follow_up": follow_up,
        "contested": contested,
        "pluralism_note": pluralism,
        "do_not_use_when": do_not
        or ["acute_suicidality", "crisis_l2_plus", "active_self_harm_planning"],
        "commentaries": commentaries
        or {
            "prabhupada": "Teaching emphasises duty, knowledge, and devotion without bypassing the person's concrete struggle.",
            "product": "Use only after listening; return agency; cite chapter and verse honestly.",
        },
    }


def build_patches() -> dict:
    p: dict[str, dict] = {}

    p["BG_1_47"] = patch(
        ["grief_loss", "overwhelm", "paralysis_from_results"],
        ["grief_loss", "confusion_paralysis"],
        "Name Arjuna's collapse: grief before teaching. Do not rush philosophy; sit with overwhelm first.",
        ["BG_2_7", "BG_2_11"],
        "What feels too heavy to carry right now?",
        tone="gentle",
        readiness="listen_first",
    )
    p["BG_2_7"] = patch(
        ["confusion_paralysis", "moral_confusion"],
        ["confusion_paralysis"],
        "Validate not knowing what is right; invite honest surrender of confusion without self-erasure.",
        ["BG_2_11", "BG_18_63"],
        "What decision feels unclear because values are in conflict?",
        readiness="listen_first",
    )
    p["BG_2_11"] = patch(
        ["grief_loss"],
        ["grief_loss"],
        "After grief is acknowledged, gently reframe: wise ones do not mourn in a way that freezes life into despair—not 'don't feel'.",
        ["BG_2_13", "BG_2_20"],
        "Do you want witness for the loss, or words about meaning?",
        tone="gentle",
        readiness="listen_first",
        depth=2,
    )
    p["BG_2_13"] = patch(
        ["fear_of_death", "grief_loss"],
        ["grief_loss"],
        "Embodiment and transition of the body — hold carefully around death grief without minimizing love.",
        ["BG_2_20", "BG_2_22"],
        "What part of this grief is love that still needs a place?",
        readiness="listen_first",
        depth=2,
    )
    p["BG_2_14"] = patch(
        ["overwhelm", "anxiety_performance"],
        ["fear_outcome"],
        "Sensations come and go — patience with the wave, not denial of pain.",
        ["BG_2_15", "BG_2_48"],
        "What sensation feels permanent that may still be a wave?",
    )
    p["BG_2_15"] = patch(
        ["overwhelm", "control_anxiety"],
        ["fear_outcome"],
        "Steady person meets both pleasure and pain without making either their identity.",
        ["BG_2_14", "BG_2_56"],
        "Where are you identifying your whole self with a temporary high or low?",
    )
    p["BG_2_20"] = patch(
        ["existential_terror", "fear_of_death", "grief_loss"],
        ["grief_loss"],
        "The living principle is not destroyed by body death — only after readiness; never as first response to crisis or acute shock.",
        ["BG_2_22", "BG_2_27"],
        "Is this about losing someone, or about fear of your own end?",
        readiness="listen_first",
        depth=2,
        do_not=["acute_suicidality", "crisis_l2_plus", "active_self_harm_planning", "acute_shock"],
    )
    p["BG_2_22"] = patch(
        ["grief_loss"],
        ["grief_loss"],
        "Body as garment image — can comfort later; never force when raw grief needs human arms first.",
        ["BG_2_20", "BG_2_27"],
        "Whose memory is sitting with you most intensely tonight?",
        readiness="listen_first",
    )
    p["BG_2_27"] = patch(
        ["fear_of_death"],
        ["grief_loss"],
        "Birth and death as given of embodiment — for philosophical readiness, not crisis bypass.",
        ["BG_2_20", "BG_2_13"],
        "What do you need most: meaning, or permission to feel?",
        readiness="listen_first",
    )
    p["BG_2_38"] = patch(
        ["duty_conflict", "fear_of_outcome"],
        ["duty_conflict", "fear_outcome"],
        "Meet pleasure and pain, gain and loss with even mind in duty — challenge attachment to outcomes.",
        ["BG_2_47", "BG_2_48"],
        "What result are you treating as the only proof you are okay?",
    )
    p["BG_2_40"] = patch(
        ["guilt_event", "failure_narrative"],
        ["failure_shame"],
        "No small right effort is wasted — repair over identity shame.",
        ["BG_6_5", "BG_2_47"],
        "What small right action could you take this week that is not about proving your worth?",
    )
    p["BG_2_47"] = patch(
        ["fear_of_outcome", "control_anxiety", "attachment_to_result", "paralysis_from_results"],
        ["fear_outcome", "duty_paralysis", "attachment_to_result"],
        "Hard truth: entitlement is to action, never to fruits. Challenge the story that identity depends on outcomes; preserve duty.",
        ["BG_2_48", "BG_3_19"],
        "What outcome are you treating as non-negotiable for your self-worth?",
        tone="instructive_firm",
        depth=1,
    )
    p["BG_2_48"] = patch(
        ["overwhelm", "anxiety_performance", "control_anxiety"],
        ["fear_outcome"],
        "Yoga as equanimity in success and failure — not coldness, but freedom from binary panic.",
        ["BG_2_47", "BG_2_50"],
        "Where does success/failure swing hijack your calm?",
    )
    p["BG_2_50"] = patch(
        ["attachment_to_result", "anxiety_performance"],
        ["fear_outcome"],
        "Skill in action with yoga — excellence without fruit-obsession.",
        ["BG_2_47", "BG_2_48"],
        "Can excellence matter without owning the result as identity?",
    )
    p["BG_2_55"] = patch(
        ["restless_mind", "desire_craving"],
        ["curiosity", "restless_mind"],
        "Steadied mind drops restless desires — after understanding what pulls them.",
        ["BG_2_56", "BG_6_35"],
        "Which desire most agitates your mind when you are still?",
    )
    p["BG_2_56"] = patch(
        ["overwhelm", "anger_reactivity"],
        ["anger", "fear_outcome"],
        "Not shaken by sorrow, free of craving joy, free of passion fear anger — aspirational steadiness.",
        ["BG_2_55", "BG_2_64"],
        "What most easily knocks you out of steadiness?",
    )
    p["BG_2_62"] = patch(
        ["anger_reactivity", "desire_craving", "attachment_to_result"],
        ["anger"],
        "Contemplation of objects feeds attachment → desire — name the loop before moralizing.",
        ["BG_2_63", "BG_3_37"],
        "What are you replaying that feeds the heat?",
    )
    p["BG_2_63"] = patch(
        ["anger_reactivity", "anger_boundary"],
        ["anger"],
        "Anger chain: desire → anger → delusion → memory loss → ruin of buddhi — after validating heat.",
        ["BG_2_62", "BG_16_21"],
        "What boundary was crossed—and what does the fire want to protect?",
    )
    p["BG_2_64"] = patch(
        ["desire_craving", "restless_mind"],
        ["anger", "curiosity"],
        "Self-regulated senses with freedom from likes/dislikes → clarity.",
        ["BG_2_62", "BG_3_42"],
        "Where do you still need restraint without self-hate?",
    )
    p["BG_2_66"] = patch(
        ["restless_mind", "anxiety_performance"],
        ["fear_outcome"],
        "No peace without controlled mind — practical, not shaming.",
        ["BG_6_34", "BG_6_35"],
        "When does your mind feel most ungovernable?",
    )
    p["BG_2_71"] = patch(
        ["desire_craving", "attachment_to_result"],
        ["attachment_to_result"],
        "Peace for one free of longing, ego, and possessiveness — challenge clinging not dignity.",
        ["BG_2_47", "BG_12_13"],
        "What are you clutching that is costing peace?",
    )
    p["BG_3_8"] = patch(
        ["burnout_duty", "confusion_paralysis"],
        ["duty_conflict", "confusion_paralysis"],
        "Perform appointed action — not passive collapse as spirituality.",
        ["BG_2_47", "BG_3_19"],
        "What duty is actually yours to do, today?",
    )
    p["BG_3_19"] = patch(
        ["attachment_to_result", "duty_conflict"],
        ["attachment_to_result", "fear_outcome"],
        "Work without attachment as the path to the Supreme — hard truth on fruit fixation.",
        ["BG_2_47", "BG_3_27"],
        "If outcomes were not yours to own, what action would you still choose?",
    )
    p["BG_3_27"] = patch(
        ["arrogance_ego", "control_anxiety"],
        ["arrogance"],
        "Actions are driven by guṇas; the ego claims 'I am the doer' — deflate ego, not dignity.",
        ["BG_3_42", "BG_18_48"],
        "Where might you be taking full credit (or full blame) for forces larger than you?",
    )
    p["BG_3_35"] = patch(
        ["duty_conflict", "moral_confusion"],
        ["duty_conflict", "confusion_paralysis"],
        "Better to fail in one's svadharma than succeed in another's — careful framing; never coerce life choices.",
        ["BG_2_47", "BG_18_48"],
        "What is truly your role here, vs what others scripted for you?",
        depth=2,
    )
    p["BG_3_37"] = patch(
        ["desire_craving", "anger_reactivity"],
        ["anger"],
        "Desire and anger as enemies born of passion — name without shaming the person.",
        ["BG_2_62", "BG_16_21"],
        "Is what you call anger actually blocked desire?",
    )
    p["BG_3_42"] = patch(
        ["restless_mind", "arrogance_ego"],
        ["curiosity", "arrogance"],
        "Hierarchy of senses-mind-intellect-self — invite higher identification gently.",
        ["BG_3_27", "BG_6_5"],
        "Which level are you living from — impulse, mind loop, or deeper clarity?",
        depth=2,
    )
    p["BG_4_7"] = patch(
        ["despair_meaning"],
        ["doubt_angry_god"],
        "When dharma declines the Divine framework restores order — never use as crisis bypass or destiny cruelty; contested readings exist.",
        ["BG_4_8", "BG_18_66"],
        "What feels like dharma collapsing in your world?",
        readiness="teach_ok",
        contested=True,
        pluralism="Some read this cosmically (avatara), others ethically (restoration of right order). Do not claim literal divine command for private advantage.",
        depth=2,
    )
    p["BG_4_8"] = patch(
        ["despair_meaning"],
        ["doubt_angry_god"],
        "Protection of the good and restoration of dharma — hope without magical forecasting.",
        ["BG_4_7", "BG_9_22"],
        "Where do you still long for moral order in chaos?",
        contested=True,
        depth=2,
    )
    p["BG_4_18"] = patch(
        ["confusion_paralysis", "attachment_to_result"],
        ["duty_paralysis", "curiosity"],
        "One who sees inaction in action and action in inaction is wise — reframe hustle vs true work.",
        ["BG_2_47", "BG_3_27"],
        "What looks like action but is actually restless spinning?",
        depth=2,
    )
    p["BG_4_38"] = patch(
        ["curiosity_philosophy", "shame_identity"],
        ["curiosity"],
        "Nothing as purifying as knowledge — careful not to intellectualize away feeling.",
        ["BG_4_18", "BG_18_63"],
        "What truth are you avoiding by collecting ideas?",
    )
    p["BG_5_10"] = patch(
        ["attachment_to_result", "burnout_duty"],
        ["attachment_to_result"],
        "Offer actions and remain untainted like lotus on water — presence without sticky results.",
        ["BG_2_47", "BG_9_27"],
        "Could you do today's task as offering rather than as proof?",
    )
    p["BG_5_22"] = patch(
        ["desire_craving", "attachment_to_result"],
        ["attachment_to_result"],
        "Pleasure from contact is temporary and seed of pain — challenge addiction to stimulation gently.",
        ["BG_2_14", "BG_5_29"],
        "What pleasure do you chase knowing it does not last?",
    )
    p["BG_5_29"] = patch(
        ["burnout_duty", "control_anxiety"],
        ["duty_conflict"],
        "Knowing the divine as enjoyer of sacrifice and friend of all — rest, not passivity as excuse.",
        ["BG_9_22", "BG_18_66"],
        "Where do you need rest that still keeps dignity?",
    )
    p["BG_6_5"] = patch(
        ["shame_identity", "self_hatred", "failure_narrative"],
        ["failure_shame"],
        "Lift the self by the self; do not degrade the self — split shame ('I am bad') from guilt ('I did poorly'). Hard truth with care.",
        ["BG_6_6", "BG_2_40"],
        "Which story are you telling — identity failure or repairable event?",
        tone="instructive_firm",
    )
    p["BG_6_6"] = patch(
        ["shame_identity", "restless_mind"],
        ["failure_shame"],
        "Mind as friend or enemy depending on mastering — agency with compassion.",
        ["BG_6_5", "BG_6_35"],
        "Is your mind currently your ally or your critic?",
    )
    p["BG_6_16"] = patch(
        ["burnout_duty", "anxiety_performance"],
        ["curiosity"],
        "Yoga not for extremes of eating/sleeping — balanced body as support for mind.",
        ["BG_6_17", "BG_6_35"],
        "What body rhythm is sabotaging your mind right now?",
    )
    p["BG_6_17"] = patch(
        ["burnout_duty", "restless_mind"],
        ["curiosity"],
        "Discipline of lifestyle for sorrow-end — practical, not puritan scolding.",
        ["BG_6_16", "BG_6_26"],
        "What one lifestyle tweak would support clearer mind?",
    )
    p["BG_6_26"] = patch(
        ["restless_mind", "scattered_attention"],
        ["curiosity"],
        "Wherever the restless mind wanders, bring it back — train gently, repeat.",
        ["BG_6_34", "BG_6_35"],
        "Where does your attention run when you try to be still?",
    )
    p["BG_6_34"] = patch(
        ["restless_mind", "scattered_attention", "anxiety_performance"],
        ["curiosity", "fear_outcome"],
        "Mind is restless, turbulent, strong, obstinate — normalize struggle; no shame for restlessness.",
        ["BG_6_35", "BG_2_66"],
        "When is your mind most like a wind?",
    )
    p["BG_6_35"] = patch(
        ["restless_mind", "scattered_attention"],
        ["curiosity"],
        "By practice (abhyāsa) and dispassion (vairāgya) the mind is restrained — give them a practice step.",
        ["BG_6_34", "BG_6_26"],
        "What daily practice of five minutes is realistic for you?",
    )
    p["BG_7_14"] = patch(
        ["despair_meaning", "confusion_paralysis"],
        ["doubt_angry_god", "curiosity"],
        "Divine maya hard to cross; those who take refuge find a way — invite trust after honesty about delusion.",
        ["BG_7_19", "BG_18_66"],
        "What feels like a veil you cannot think your way through?",
        depth=2,
    )
    p["BG_7_19"] = patch(
        ["curiosity_philosophy", "devotional_longing"],
        ["curiosity"],
        "Rare is the one who after many lives ends in Me — humility, not elitism.",
        ["BG_9_34", "BG_18_66"],
        "What keeps drawing you toward deeper questions?",
        depth=2,
    )
    p["BG_8_7"] = patch(
        ["fear_of_death", "duty_conflict"],
        ["curiosity", "duty_conflict"],
        "Remember the Divine while doing duty — integrate, don't escape.",
        ["BG_9_27", "BG_8_7"],
        "Can work and remembrance coexist for you, or does one cancel the other?",
    )
    p["BG_9_14"] = patch(
        ["devotional_longing"],
        ["curiosity", "loneliness_night"],
        "Constant devotion with determination — for invited bhakti, not coercion.",
        ["BG_9_22", "BG_9_34"],
        "Is longing for God comfort, discipline, or relationship for you?",
    )
    p["BG_9_22"] = patch(
        ["loneliness", "caregiver_fatigue", "exhaustion_l1"],
        ["loneliness_night"],
        "Those who connect and offer care are not abandoned — only after they feel heard; not as crisis fix.",
        ["BG_10_20", "BG_12_13"],
        "Are you alone in body, or unseen by people who should see you?",
        tone="gentle",
        readiness="teach_ok",
    )
    p["BG_9_27"] = patch(
        ["attachment_to_result", "burnout_duty"],
        ["attachment_to_result"],
        "Whatever you do, eat, offer, give — offer it; reframe performance as dedicated action.",
        ["BG_2_47", "BG_5_10"],
        "What ordinary act could you consciously offer today?",
    )
    p["BG_9_34"] = patch(
        ["devotional_longing", "loneliness"],
        ["curiosity", "loneliness_night"],
        "Fix mind on Me, be My devotee — only if user invites; AI never claims to be that Me as person.",
        ["BG_9_22", "BG_18_65"],
        "Do you want devotion, philosophy, or practical next steps tonight?",
        contested=True,
        pluralism="Devotional reading is real; AI remains nimitta and never impersonates the Divine I.",
    )
    p["BG_10_20"] = patch(
        ["loneliness", "existential_terror"],
        ["loneliness_night"],
        "I am the Self seated in the heart of all beings — careful theology; AI is not that Self; use as teaching about presence not claim.",
        ["BG_9_22", "BG_11_33"],
        "What would change if you felt held from within rather than only by people?",
        contested=True,
        pluralism="Verse is about the Divine Self, not the chatbot. Phrase as teaching about Krishna's claim, never as AI identity.",
        depth=2,
    )
    p["BG_11_33"] = patch(
        ["duty_conflict", "control_anxiety", "arrogance_ego"],
        ["duty_conflict", "fear_outcome"],
        "Be an instrument (nimitta) — for user agency and AI humility (we are not the Lord).",
        ["BG_2_47", "BG_3_27"],
        "Where are you being asked to act as instrument rather than controller?",
        depth=2,
    )
    p["BG_11_55"] = patch(
        ["devotional_longing", "duty_conflict"],
        ["curiosity"],
        "Work for Me, devoted, free of enmity — ethics of relation not domination.",
        ["BG_12_13", "BG_9_34"],
        "What would working without enmity look like with the person who tests you?",
        depth=2,
    )
    p["BG_12_13"] = patch(
        ["loneliness", "envy", "anger_boundary"],
        ["loneliness_night", "anger"],
        "Friend of all beings, free of hate — soft sakha model after validation of hurt.",
        ["BG_12_14", "BG_12_15"],
        "Who is hard to befriend right now, and what boundary still matters?",
        tone="gentle",
    )
    p["BG_12_14"] = patch(
        ["anxiety_performance", "control_anxiety"],
        ["fear_outcome"],
        "Content, steady, self-controlled, firm in resolve — growth path not instant trait.",
        ["BG_12_13", "BG_12_15"],
        "Which one quality would help most: contentment, steadiness, or resolve?",
    )
    p["BG_12_15"] = patch(
        ["anxiety_performance", "loneliness"],
        ["loneliness_night", "fear_outcome"],
        "Does not agitate the world; is not agitated by it — relational peace with boundaries.",
        ["BG_12_13", "BG_12_16"],
        "Where do you over-react to the world, or freeze it?",
    )
    p["BG_12_16"] = patch(
        ["shame_identity", "attachment_to_result"],
        ["failure_shame"],
        "Independent of outcomes, pure, skillful, untroubled — free from ego-claim.",
        ["BG_2_47", "BG_12_13"],
        "What would skillful and untroubled look like tomorrow morning?",
    )
    p["BG_13_8"] = patch(
        ["arrogance_ego", "curiosity_philosophy"],
        ["arrogance", "curiosity"],
        "Humility and other knowledge-qualities listed — challenge ego softly.",
        ["BG_13_8", "BG_16_1"],
        "Which mark of knowledge do you most resist: humility, non-harm, or honesty?",
        depth=2,
    )
    p["BG_14_22"] = patch(
        ["overwhelm", "control_anxiety"],
        ["fear_outcome"],
        "One beyond guṇas is steady when they arise — emotional literacy with Gita map.",
        ["BG_2_48", "BG_14_22"],
        "Which guṇa feels loudest in you today: rest, passion, or inertia?",
        depth=2,
    )
    p["BG_15_7"] = patch(
        ["existential_terror", "shame_identity"],
        ["curiosity", "failure_shame"],
        "Eternal fragment of the Divine becomes living being — dignity of self without AI claiming divinity.",
        ["BG_2_20", "BG_10_20"],
        "What would it mean if your worth were not invented by productivity?",
        depth=2,
        contested=True,
        pluralism="Theological anthropology differs by school; keep language as teaching not persona claim.",
    )
    p["BG_16_1"] = patch(
        ["moral_confusion", "arrogance_ego"],
        ["curiosity", "arrogance"],
        "Divine qualities begin with fearlessness, purity, steadfastness — aspiration map.",
        ["BG_16_21", "BG_13_8"],
        "Which divine quality feels closest; which feels farthest?",
    )
    p["BG_16_21"] = patch(
        ["desire_craving", "anger_reactivity", "temptation_gates"],
        ["anger", "curiosity"],
        "Lust, anger, greed as three gates of self-destruction — hard truth without cruelty.",
        ["BG_2_62", "BG_3_37"],
        "Which of the three gates is open widest for you right now?",
        tone="instructive_firm",
    )
    p["BG_17_3"] = patch(
        ["faith_wavering", "doubt_in_god"],
        ["doubt_angry_god", "curiosity"],
        "Faith according to nature — accept honest doubt; no forced belief.",
        ["BG_7_19", "BG_18_66"],
        "Is your faith tired, angry, or quietly alive?",
        readiness="listen_first",
    )
    p["BG_18_48"] = patch(
        ["duty_conflict", "shame_identity", "perfectionism"],
        ["duty_conflict", "failure_shame"],
        "Do not abandon your duty even if imperfect — every endeavor is covered with some fault like fire with smoke.",
        ["BG_3_35", "BG_2_47"],
        "Where is perfectionism blocking imperfect right action?",
    )
    p["BG_18_58"] = patch(
        ["control_anxiety", "fear_of_outcome"],
        ["fear_outcome"],
        "With mind fixed, you cross obstacles by grace — not magic luck; keep agency.",
        ["BG_18_66", "BG_9_22"],
        "What obstacle are you facing that needs both effort and release?",
        depth=2,
    )
    p["BG_18_63"] = patch(
        ["confusion_paralysis", "moral_confusion", "indecision"],
        ["confusion_paralysis", "curiosity"],
        "I have taught you; deliberate and act as you choose — supreme respect for free will; AI never commands.",
        ["BG_2_7", "BG_18_66"],
        "Having heard, what choice is yours alone to make?",
        tone="steady_calm",
        depth=2,
    )
    p["BG_18_66"] = patch(
        ["shame_identity", "despair_meaning", "faith_wavering", "failure_narrative"],
        ["failure_shame", "doubt_angry_god"],
        "Surrender all dharmas and take refuge — carefully after listening; NEVER in crisis L2–L4; not spiritual suicide of responsibility.",
        ["BG_18_58", "BG_18_63"],
        "Is surrender for you rest, relationship, or escape?",
        contested=True,
        pluralism="Bhakti, Advaita, and others read sharanagati differently. Prefer agency-preserving reading; reject 'abandon therapy/meds/family' misuses.",
        readiness="teach_ok",
        do_not=["acute_suicidality", "crisis_l2_plus", "active_self_harm_planning", "psychosis_or_incapacity"],
        depth=3,
    )
    p["BG_18_78"] = patch(
        ["curiosity_philosophy", "devotional_longing"],
        ["curiosity"],
        "Where Krishna and Arjuna are, prosperity, victory, and morality — close with dignity not triumphalism.",
        ["BG_18_66", "BG_11_33"],
        "What would a quiet victory look like in your life this week?",
        tone="gentle",
        depth=2,
    )

    # ensure anchor id for 18.65 if referenced — not in list; remove bad secondary
    for k, v in p.items():
        secs = []
        for s in v["secondary_verses"]:
            if s == "BG_18_65":
                secs.append("BG_9_34")
            else:
                secs.append(s)
        v["secondary_verses"] = secs

    return p


def main() -> int:
    assert len(ANCHOR_IDS) >= 60, len(ANCHOR_IDS)
    patches = build_patches()
    missing = [a for a in ANCHOR_IDS if a not in patches]
    if missing:
        raise SystemExit(f"Missing patches for: {missing}")

    ANCHORS.write_text(
        json.dumps(
            {"version": 1, "min_count": 60, "ids": ANCHOR_IDS},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    PATCHES.write_text(
        json.dumps({"version": 1, "patches": patches}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    data = json.loads(VERSES.read_text(encoding="utf-8"))
    by_id = {v["id"]: v for v in data["verses"]}
    hi_gaps = []
    for vid, patch_data in patches.items():
        card = by_id[vid]
        for k, val in patch_data.items():
            if k == "commentaries":
                card["commentaries"] = {**(card.get("commentaries") or {}), **val}
            else:
                card[k] = val
        card["quality"] = "tier_a"
        # Hindi: mark gap if no solid hi
        hi = (card.get("translations") or {}).get("hi") or ""
        if not hi.strip():
            hi_gaps.append(vid)
    data["tier_a_count"] = sum(1 for v in data["verses"] if v.get("quality") == "tier_a")
    VERSES.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    HI_GAPS.parent.mkdir(parents=True, exist_ok=True)
    HI_GAPS.write_text(
        "# Hindi gaps (tier-A)\n\n"
        "OCR Hindi sources exist but verse-aligned auto-extract is not reliable enough for V1.\n"
        "Tier-A cards without `translations.hi`:\n\n"
        + "\n".join(f"- `{i}`" for i in hi_gaps)
        + "\n\nFill progressively from Yatharupa OCR in later passes.\n",
        encoding="utf-8",
    )
    print(f"Anchors: {len(ANCHOR_IDS)} | tier_a: {data['tier_a_count']} | hi gaps: {len(hi_gaps)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
