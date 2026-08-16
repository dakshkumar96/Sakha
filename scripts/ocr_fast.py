"""
Fast parallel OCR for priority Hindi / scanned PDFs.
- Parallel workers
- DPI 110
- Progressive page append (resume-safe)
- hin+eng when available

Usage:
  python scripts/ocr_fast.py
  python scripts/ocr_fast.py --workers 6
"""

from __future__ import annotations

import io
import json
import os
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
BOOKS = ROOT / "Books"
OUT = ROOT / "knowledge" / "raw_text"
MANIFEST = ROOT / "knowledge" / "sources" / "manifest.json"
TESSDATA = ROOT / "knowledge" / "tessdata"
TESS = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")

# Fastest useful set for V1 Hindi (drop 279 / unencrypted for speed)
TARGETS = [
    (
        "Bhagavad-gita_As_It_Is_by_A._C._Bhaktivedanta_Swami_Prabhupada_in_Hindi_Bhagavad-gita_Yatharupa_1980.pdf",
        "Bhagavad-gita_As_It_Is_by_A_C_Bhaktivedanta_Swami_Prabhupada_in_Hindi_Bhagavad-gita_Yatharupa_1980.txt",
    ),
    (
        "bhagavad-gita-hindi.pdf",
        "bhagavad-gita-hindi.txt",
    ),
]

DPI = 100
LANG = "hin+eng"


def slug_ok() -> None:
    os.environ["TESSDATA_PREFIX"] = str(TESSDATA)


def ocr_page(args: tuple) -> tuple[int, str, int]:
    """Worker: (pdf_path, page_index, dpi, lang) -> (page_index, text, nchars)."""
    pdf_path, page_i, dpi, lang = args
    import pytesseract
    from PIL import Image

    if TESS.exists():
        pytesseract.pytesseract.tesseract_cmd = str(TESS)
    os.environ["TESSDATA_PREFIX"] = str(TESSDATA)

    doc = fitz.open(pdf_path)
    page = doc[page_i]
    pix = page.get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    # Fast LSTM path; psm 6 = block of text
    text = pytesseract.image_to_string(
        img,
        lang=lang,
        config="--oem 1 --psm 6",
    ) or ""
    doc.close()
    text = text.replace("\x00", "")
    return page_i, text, len(text.strip())


def ocr_pdf(pdf_name: str, out_name: str, workers: int) -> dict:
    pdf_path = BOOKS / pdf_name
    out_path = OUT / out_name
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    doc = fitz.open(pdf_path)
    n = doc.page_count
    doc.close()

    OUT.mkdir(parents=True, exist_ok=True)
    # Resume: count existing PAGE markers
    done: dict[int, str] = {}
    if out_path.exists() and out_path.stat().st_size > 50_000:
        raw = out_path.read_text(encoding="utf-8", errors="replace")
        # Only resume if it looks like prior OCR (real Devanagari present)
        dev = sum(1 for c in raw[:20000] if "\u0900" <= c <= "\u097F")
        if dev > 200:
            for m in re.finditer(
                r"===== PAGE (\d+) / \d+ =====\n\n(.*?)(?=\n\n===== PAGE |\Z)",
                raw,
                flags=re.S,
            ):
                done[int(m.group(1)) - 1] = m.group(2)
            print(f"  resume: {len(done)}/{n} pages already in output", flush=True)

    todo = [i for i in range(n) if i not in done]
    print(f"  {pdf_name}: {n} pages, todo={len(todo)}, workers={workers}, dpi={DPI}", flush=True)
    started = time.time()
    body_chars = sum(len(t.strip()) for t in done.values())

    # Process in large batches so we can rewrite file periodically
    batch_size = max(workers * 4, 16)
    for start in range(0, len(todo), batch_size):
        batch = todo[start : start + batch_size]
        jobs = [(str(pdf_path), i, DPI, LANG) for i in batch]
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(ocr_page, j): j[1] for j in jobs}
            for fut in as_completed(futs):
                i, text, nc = fut.result()
                done[i] = text
                body_chars += nc

        # Write full progressive output sorted by page
        parts = []
        for i in range(n):
            t = done.get(i, "")
            parts.append(f"\n\n===== PAGE {i + 1} / {n} =====\n\n{t}")
        out_path.write_text("".join(parts).strip() + "\n", encoding="utf-8", errors="replace")

        elapsed = time.time() - started
        finished = len(done)
        rate = finished / elapsed if elapsed else 0
        eta = (n - finished) / rate if rate else 0
        print(
            f"  page {finished}/{n} | {body_chars:,} chars | "
            f"{rate:.2f} p/s | ETA {eta / 60:.1f} min",
            flush=True,
        )

    meta = {
        "source_file": pdf_name,
        "output_file": str(out_path.relative_to(ROOT)).replace("\\", "/"),
        "page_count": n,
        "char_count": out_path.stat().st_size,
        "body_char_count": body_chars,
        "avg_chars_per_page": round(body_chars / n, 1) if n else 0,
        "extraction_method": f"parallel_ocr_{LANG}_dpi{DPI}",
        "needs_ocr": False,
        "likely_scanned": True,
        "status": "ok",
        "language_hint": "hi",
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(time.time() - started, 2),
    }
    return meta


def update_manifest(metas: list[dict]) -> None:
    if MANIFEST.exists():
        man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    else:
        man = {"books_dir": "Books", "output_dir": "knowledge/raw_text", "sources": []}
    by = {s["source_file"]: s for s in man.get("sources", []) if "source_file" in s}
    for m in metas:
        by[m["source_file"]] = {**by.get(m["source_file"], {}), **m}
    sources = list(by.values())
    man["sources"] = sources
    man["updated_at"] = datetime.now(timezone.utc).isoformat()
    man["ok_count"] = sum(1 for e in sources if e.get("status") == "ok")
    man["needs_ocr_count"] = sum(1 for e in sources if e.get("status") == "needs_ocr")
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(man, indent=2), encoding="utf-8")


def main() -> int:
    workers = 6
    if "--workers" in sys.argv:
        i = sys.argv.index("--workers")
        workers = int(sys.argv[i + 1])
    if not TESS.exists():
        print("Tesseract not found", file=sys.stderr)
        return 1
    if not (TESSDATA / "hin.traineddata").exists():
        print("hin.traineddata missing in knowledge/tessdata", file=sys.stderr)
        return 1

    slug_ok()
    # Windows process spawn needs guard
    metas = []
    for pdf_name, out_name in TARGETS:
        print(f"\n=== {pdf_name} ===", flush=True)
        # Drop garbled non-Devanagari extract so we don't "resume" junk
        out_path = OUT / out_name
        if out_path.exists():
            sample = out_path.read_text(encoding="utf-8", errors="replace")[:30000]
            dev = sum(1 for c in sample if "\u0900" <= c <= "\u097F")
            if dev < 200:
                print("  discarding garbled / incomplete extract", flush=True)
                out_path.unlink()
        meta = ocr_pdf(pdf_name, out_name, workers=workers)
        print(
            f"  DONE {meta['body_char_count']:,} chars in {meta['duration_seconds']}s",
            flush=True,
        )
        metas.append(meta)
    update_manifest(metas)
    print(f"\nManifest updated: {MANIFEST}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
