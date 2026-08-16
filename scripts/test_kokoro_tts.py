"""Smoke-test Kokoro-FastAPI (http://localhost:8880).

Requires the container running:
  docker compose -f docker/kokoro-compose.yml up -d

Usage:
  python scripts/test_kokoro_tts.py
  python scripts/test_kokoro_tts.py --voice am_michael --text "Hello, friend."
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Install requests: pip install requests", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = os.environ.get("KOKORO_BASE_URL", "http://localhost:8880/v1").rstrip("/")
DEFAULT_VOICE = os.environ.get("KOKORO_VOICE_EN", "am_michael")
DEFAULT_SPEED = float(os.environ.get("KOKORO_SPEED", "0.9"))
SAMPLE = (
    "I am a digital sevak, a nimitta pointing toward the Gita — not God, not a therapist. "
    "Tell me what is heavy tonight."
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Kokoro-FastAPI TTS smoke test")
    parser.add_argument("--base", default=DEFAULT_BASE, help="OpenAI-compatible base URL")
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    parser.add_argument("--text", default=SAMPLE)
    parser.add_argument("--speed", type=float, default=DEFAULT_SPEED)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "tmp" / "kokoro_sample.mp3",
    )
    args = parser.parse_args()

    health_root = args.base.replace("/v1", "") if args.base.endswith("/v1") else args.base
    try:
        voices_r = requests.get(f"{args.base}/audio/voices", timeout=10)
    except requests.RequestException as e:
        print(f"Cannot reach Kokoro at {args.base}: {e}", file=sys.stderr)
        print("Start: docker compose -f docker/kokoro-compose.yml up -d", file=sys.stderr)
        return 1

    if voices_r.status_code != 200:
        print(f"Voices endpoint failed: {voices_r.status_code} {voices_r.text[:200]}", file=sys.stderr)
        return 1

    print(f"OK voices @ {args.base}/audio/voices")
    print(f"UI tip: {health_root}/web")

    speech_r = requests.post(
        f"{args.base}/audio/speech",
        json={
            "model": "kokoro",
            "input": args.text,
            "voice": args.voice,
            "response_format": "mp3",
            "speed": args.speed,
        },
        timeout=120,
    )
    if speech_r.status_code != 200:
        print(f"Speech failed: {speech_r.status_code} {speech_r.text[:300]}", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(speech_r.content)
    print(f"Wrote {args.out} ({len(speech_r.content)} bytes) voice={args.voice} speed={args.speed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
