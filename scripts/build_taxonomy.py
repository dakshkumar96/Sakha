"""Author knowledge/taxonomy/* for V1 operational emotions and crisis rules."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAX = ROOT / "knowledge" / "taxonomy"


def main() -> int:
    TAX.mkdir(parents=True, exist_ok=True)

    emotions = [
        {
            "id": "fear_of_outcome",
            "label": "Fear of future result",
            "definition": "Anxiety that self-worth depends on controlled outcomes",
            "primary_verse": "BG_2_47",
            "secondary_verses": ["BG_2_48", "BG_2_50"],
            "crisis_override": None,
            "behaviour_matrix_row": "Fear (outcome, future)",
        },
        {
            "id": "control_anxiety",
            "label": "Control anxiety",
            "definition": "Distress from need to control results",
            "primary_verse": "BG_2_47",
            "secondary_verses": ["BG_3_27", "BG_11_33"],
            "crisis_override": None,
        },
        {
            "id": "overwhelm",
            "label": "Overwhelm",
            "definition": "Sensory/emotional overload",
            "primary_verse": "BG_2_48",
            "secondary_verses": ["BG_2_14", "BG_2_56"],
            "crisis_override": None,
        },
        {
            "id": "grief_loss",
            "label": "Grief / loss",
            "definition": "Bereavement or love with nowhere to go",
            "primary_verse": "BG_2_11",
            "secondary_verses": ["BG_2_13", "BG_2_20"],
            "crisis_override": None,
            "readiness_hint": "listen_first",
            "behaviour_matrix_row": "Grief / loss",
        },
        {
            "id": "existential_terror",
            "label": "Existential terror",
            "definition": "Fear of non-being or meaning collapse",
            "primary_verse": "BG_2_20",
            "secondary_verses": ["BG_2_27", "BG_15_7"],
            "readiness_hint": "listen_first",
        },
        {
            "id": "anger_boundary",
            "label": "Anger (boundary crossed)",
            "definition": "Heat protecting a violated boundary",
            "primary_verse": "BG_2_63",
            "secondary_verses": ["BG_2_62", "BG_12_13"],
            "behaviour_matrix_row": "Anger",
        },
        {
            "id": "anger_reactivity",
            "label": "Anger reactivity loop",
            "definition": "Runaway anger chain",
            "primary_verse": "BG_2_63",
            "secondary_verses": ["BG_2_62", "BG_16_21"],
        },
        {
            "id": "arrogance_ego",
            "label": "Arrogance / ego claim",
            "definition": "Defended superiority or know-it-all stance",
            "primary_verse": "BG_3_27",
            "secondary_verses": ["BG_13_8", "BG_16_1"],
            "behaviour_matrix_row": "Arrogance / know-it-all",
        },
        {
            "id": "confusion_paralysis",
            "label": "Confusion / paralysis",
            "definition": "Fog and inability to choose",
            "primary_verse": "BG_2_47",
            "secondary_verses": ["BG_2_7", "BG_18_63"],
            "behaviour_matrix_row": "Confusion / paralysis",
        },
        {
            "id": "duty_conflict",
            "label": "Duty conflict",
            "definition": "Competing roles and svadharma tension",
            "primary_verse": "BG_3_35",
            "secondary_verses": ["BG_2_47", "BG_18_48"],
        },
        {
            "id": "loneliness",
            "label": "Loneliness",
            "definition": "Isolation or being unseen",
            "primary_verse": "BG_9_22",
            "secondary_verses": ["BG_12_13", "BG_10_20"],
            "behaviour_matrix_row": "Loneliness (often night)",
        },
        {
            "id": "shame_identity",
            "label": "Shame (identity)",
            "definition": "Global I am bad condemnation",
            "primary_verse": "BG_6_5",
            "secondary_verses": ["BG_6_6", "BG_2_40"],
            "behaviour_matrix_row": "Failure / shame",
        },
        {
            "id": "guilt_event",
            "label": "Guilt (event)",
            "definition": "Specific I did badly",
            "primary_verse": "BG_2_40",
            "secondary_verses": ["BG_6_5", "BG_18_66"],
        },
        {
            "id": "failure_narrative",
            "label": "Failure narrative",
            "definition": "Story of chronic failure",
            "primary_verse": "BG_6_5",
            "secondary_verses": ["BG_2_40", "BG_18_48"],
        },
        {
            "id": "doubt_in_god",
            "label": "Doubt in God",
            "definition": "Intellectual or existential unbelief",
            "primary_verse": None,
            "secondary_verses": [],
            "teach_gate": "only_if_invited",
            "behaviour_matrix_row": "Doubt / angry at God",
        },
        {
            "id": "anger_at_god",
            "label": "Anger at God",
            "definition": "Moral injury toward the Divine",
            "primary_verse": None,
            "secondary_verses": [],
            "teach_gate": "only_if_invited",
        },
        {
            "id": "curiosity_philosophy",
            "label": "Curiosity / philosophy",
            "definition": "Seeking knowledge without acute distress",
            "primary_verse": "BG_4_38",
            "secondary_verses": ["BG_18_63", "BG_2_47"],
            "behaviour_matrix_row": "Curiosity / philosophy",
        },
        {
            "id": "exhaustion_l1",
            "label": "Exhaustion L1",
            "definition": "Tired of life without clear plan",
            "primary_verse": None,
            "secondary_verses": [],
            "crisis_override": "block_teaching",
            "behaviour_matrix_row": "Crisis L1",
        },
        {
            "id": "hopelessness_l1",
            "label": "Hopelessness L1",
            "definition": "Pointlessness without active plan",
            "primary_verse": None,
            "secondary_verses": [],
            "crisis_override": "block_teaching",
        },
        {
            "id": "attachment_to_result",
            "label": "Attachment to result",
            "definition": "Clinging to fruits of action",
            "primary_verse": "BG_2_47",
            "secondary_verses": ["BG_3_19", "BG_5_10"],
        },
        {
            "id": "desire_craving",
            "label": "Desire / craving",
            "definition": "Passionate wanting as fuel of suffering",
            "primary_verse": "BG_3_37",
            "secondary_verses": ["BG_2_62", "BG_5_22"],
        },
        {
            "id": "restless_mind",
            "label": "Restless mind",
            "definition": "Agitated, wind-like mind",
            "primary_verse": "BG_6_34",
            "secondary_verses": ["BG_6_35", "BG_6_26"],
        },
        {
            "id": "scattered_attention",
            "label": "Scattered attention",
            "definition": "Cannot hold focus",
            "primary_verse": "BG_6_35",
            "secondary_verses": ["BG_6_34", "BG_6_26"],
        },
        {
            "id": "self_hatred",
            "label": "Self-hatred",
            "definition": "Active hostility toward self",
            "primary_verse": "BG_6_5",
            "secondary_verses": ["BG_6_6"],
            "crisis_check": True,
        },
        {
            "id": "despair_meaning",
            "label": "Despair of meaning",
            "definition": "World or dharma feels empty",
            "primary_verse": "BG_4_7",
            "secondary_verses": ["BG_4_8", "BG_18_66"],
        },
        {
            "id": "caregiver_fatigue",
            "label": "Caregiver fatigue",
            "definition": "Exhausted from caring for others",
            "primary_verse": "BG_9_22",
            "secondary_verses": ["BG_12_13", "BG_5_29"],
        },
        {
            "id": "envy",
            "label": "Envy",
            "definition": "Pain at others' good",
            "primary_verse": "BG_12_13",
            "secondary_verses": ["BG_12_14"],
        },
        {
            "id": "moral_confusion",
            "label": "Moral confusion",
            "definition": "Not knowing right action",
            "primary_verse": "BG_2_7",
            "secondary_verses": ["BG_16_21", "BG_18_63"],
        },
        {
            "id": "spiritual_bypass_risk",
            "label": "Spiritual bypass risk",
            "definition": "Using philosophy to avoid feeling",
            "primary_verse": None,
            "secondary_verses": [],
            "teach_gate": "redirect_to_concrete",
        },
        {
            "id": "devotional_longing",
            "label": "Devotional longing",
            "definition": "Bhakti yearning",
            "primary_verse": "BG_9_34",
            "secondary_verses": ["BG_9_14", "BG_9_22"],
            "user_led": True,
        },
        {
            "id": "fear_of_death",
            "label": "Fear of death",
            "definition": "Fear of dying or annihilation",
            "primary_verse": "BG_2_20",
            "secondary_verses": ["BG_2_27", "BG_2_13"],
            "readiness_hint": "listen_first",
        },
        {
            "id": "anxiety_performance",
            "label": "Performance anxiety",
            "definition": "Fear of failing in evaluation",
            "primary_verse": "BG_2_48",
            "secondary_verses": ["BG_2_47", "BG_2_50"],
        },
        {
            "id": "indecision",
            "label": "Indecision",
            "definition": "Stuck between options",
            "primary_verse": "BG_18_63",
            "secondary_verses": ["BG_2_7", "BG_3_35"],
        },
        {
            "id": "dependence_on_approval",
            "label": "Dependence on approval",
            "definition": "Worth outsourced to others' regard",
            "primary_verse": "BG_6_5",
            "secondary_verses": ["BG_2_47", "BG_12_16"],
        },
        {
            "id": "revenge_drive",
            "label": "Revenge drive",
            "definition": "Desire to retaliate",
            "primary_verse": "BG_12_13",
            "secondary_verses": ["BG_2_63", "BG_16_21"],
            "notes": "Never fuel revenge with scripture",
        },
        {
            "id": "burnout_duty",
            "label": "Burnout in duty",
            "definition": "Exhausted from role load",
            "primary_verse": "BG_3_8",
            "secondary_verses": ["BG_2_47", "BG_5_29"],
        },
        {
            "id": "gratitude",
            "label": "Gratitude",
            "definition": "Thankfulness",
            "primary_verse": "BG_9_27",
            "secondary_verses": ["BG_12_13"],
        },
        {
            "id": "awe",
            "label": "Awe",
            "definition": "Wonder at the vast",
            "primary_verse": "BG_11_33",
            "secondary_verses": ["BG_10_20"],
            "notes": "No impersonation of cosmic form",
        },
        {
            "id": "faith_wavering",
            "label": "Faith wavering",
            "definition": "Belief under strain",
            "primary_verse": "BG_17_3",
            "secondary_verses": ["BG_18_66", "BG_7_19"],
            "readiness_hint": "listen_first",
        },
        {
            "id": "temptation_gates",
            "label": "Temptation (gates)",
            "definition": "Lust/anger/greed pull",
            "primary_verse": "BG_16_21",
            "secondary_verses": ["BG_3_37", "BG_2_62"],
        },
        {
            "id": "perfectionism",
            "label": "Perfectionism",
            "definition": "Blocking action for perfect image",
            "primary_verse": "BG_18_48",
            "secondary_verses": ["BG_2_47", "BG_3_35"],
        },
        {
            "id": "crisis_l2_plus",
            "label": "Crisis L2–L4",
            "definition": "Elevated risk requiring human help",
            "primary_verse": None,
            "secondary_verses": [],
            "crisis_override": "block_teaching",
            "behaviour_matrix_row": "Crisis L2–L4",
        },
    ]

    situations = {
        "version": 1,
        "situations": [
            {
                "id": "fear_outcome",
                "mode": "R→G",
                "teach_gate": "after_two_questions",
                "primary_emotions": ["fear_of_outcome", "control_anxiety"],
                "forbidden": ["Just trust destiny / karma fixed it"],
            },
            {
                "id": "arrogance",
                "mode": "G",
                "teach_gate": "after_1_2_questions",
                "primary_emotions": ["arrogance_ego"],
                "forbidden": ["Shame, mockery"],
            },
            {
                "id": "grief_loss",
                "mode": "S",
                "teach_gate": "delay_teaching",
                "primary_emotions": ["grief_loss"],
                "forbidden": ["Don't cry as first line", "challenge too early"],
            },
            {
                "id": "confusion_paralysis",
                "mode": "R",
                "teach_gate": "after_clarity",
                "primary_emotions": ["confusion_paralysis", "duty_conflict"],
                "forbidden": ["Decide for them"],
            },
            {
                "id": "duty_paralysis",
                "mode": "R",
                "teach_gate": "after_clarity",
                "primary_emotions": ["confusion_paralysis", "attachment_to_result"],
                "forbidden": ["Decide for them"],
            },
            {
                "id": "anger",
                "mode": "S→G",
                "teach_gate": "after_validation",
                "primary_emotions": ["anger_boundary", "anger_reactivity"],
                "forbidden": ["Moralize", "fuel revenge with scripture"],
            },
            {
                "id": "curiosity",
                "mode": "G",
                "teach_gate": "cite_freely_if_not_distress",
                "primary_emotions": ["curiosity_philosophy"],
                "forbidden": ["Walls of text without check-in"],
            },
            {
                "id": "loneliness_night",
                "mode": "S",
                "teach_gate": "after_presence",
                "primary_emotions": ["loneliness"],
                "forbidden": ["Spiritualize loneliness as renounce people"],
            },
            {
                "id": "failure_shame",
                "mode": "S→G",
                "teach_gate": "after_shame_guilt_split",
                "primary_emotions": ["shame_identity", "failure_narrative", "guilt_event"],
                "forbidden": ["You failed karma"],
            },
            {
                "id": "doubt_angry_god",
                "mode": "S",
                "teach_gate": "only_if_invited",
                "primary_emotions": ["doubt_in_god", "anger_at_god"],
                "forbidden": ["Defend God", "guilt-trip faith"],
            },
            {
                "id": "crisis_l1",
                "mode": "C/S",
                "teach_gate": "never",
                "primary_emotions": ["exhaustion_l1", "hopelessness_l1"],
                "forbidden": ["Bypass with detachment verse"],
            },
            {
                "id": "crisis_l2_l4",
                "mode": "C",
                "teach_gate": "never",
                "primary_emotions": ["crisis_l2_plus"],
                "forbidden": ["Any spiritual gloss for safety"],
            },
            {
                "id": "attachment_to_result",
                "mode": "G",
                "teach_gate": "after_two_questions",
                "primary_emotions": ["attachment_to_result"],
                "forbidden": [],
            },
        ],
    }

    e2v = {}
    for e in emotions:
        e2v[e["id"]] = {
            "primary": e.get("primary_verse"),
            "secondary": e.get("secondary_verses") or [],
            "teach_gate": e.get("teach_gate")
            or (
                "never"
                if e.get("crisis_override") == "block_teaching"
                else "after_two_questions"
            ),
            "crisis_override": e.get("crisis_override"),
        }

    crisis = {
        "levels": {
            "L1": {
                "allow_soft_grounding": True,
                "allow_gita_teaching": False,
                "allow_cite_for_comfort_dump": False,
            },
            "L2": {"allow_gita_teaching": False, "escalate": True},
            "L3": {"allow_gita_teaching": False, "helplines_only": True},
            "L4": {"allow_gita_teaching": False, "helplines_only": True},
        },
        "never_cite_when": [
            "active_plan",
            "means_and_intent",
            "goodbye_finality_language",
        ],
        "helpline_refs": [
            "India iCall 9152987821",
            "AASRA +91-22-27546669",
            "UK Samaritans 116 123",
            "US 988",
        ],
    }

    (TAX / "emotions_v1.json").write_text(
        json.dumps({"version": 1, "count": len(emotions), "emotions": emotions}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    (TAX / "situations_v1.json").write_text(
        json.dumps(situations, indent=2) + "\n", encoding="utf-8"
    )
    (TAX / "emotion_to_verses.json").write_text(
        json.dumps({"version": 1, "map": e2v}, indent=2) + "\n", encoding="utf-8"
    )
    (TAX / "crisis_forbidden.json").write_text(
        json.dumps(crisis, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(emotions)} emotions, {len(situations['situations'])} situations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
