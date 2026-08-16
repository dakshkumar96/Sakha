"""
Extract and OCR only PDFs that are missing or thin in knowledge/raw_text/.
Merges into existing manifest.json (does not wipe prior good extracts).

Hindi/scan-heavy books use Tesseract with hin+eng when available.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
BOOKS_DIR = ROOT / "Books"
OUT_DIR = ROOT / "knowledge" / "raw_text"
MANIFEST_PATH = ROOT / "knowledge" / "sources" / "manifest.json"
TESSDATA = ROOT / "knowledge" / "tessdata"

# Prefer new Hindi / previously missing titles first
PRIORITY = [
    "bhagavad-gita-hindi.pdf",
    "Bhagavad-gita_As_It_Is_by_A._C._Bhaktivedanta_Swami_Prabhupada_in_Hindi_Bhagavad-gita_Yatharupa_1980.pdf",
    "unencrypted-geeta.pdf",
    "279.pdf",
    "Krishna_0.pdf",
]

MIN_BODY_CHARS = 5_000  # treat thinner extracts as needing refresh


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "books_dir": "Books",
        "output_dir": "knowledge/raw_text",
        "sources": [],
    }


def slugify(name: str) -> str:
    import re

    stem = Path(name).stem
    stem = re.sub(r"[^\w\-]+", "_", stem, flags=re.UNICODE)
    stem = re.sub(r"_+", "_", stem).strip("_")
    return stem[:120] or "unnamed"


def needs_work(pdf_name: str, by_name: dict) -> bool:
    entry = by_name.get(pdf_name)
    out = None
    if entry and entry.get("output_file"):
        out = ROOT / entry["output_file"]
    if out is None:
        cand = OUT_DIR / f"{slugify(pdf_name)}.txt"
        out = cand if cand.exists() else None
    if out is None or not out.exists():
        return True
    body = out.read_text(encoding="utf-8", errors="replace")
    # Private-use / broken font dumps aren't useful
    real = sum(1 for c in body if c.isalpha() or "\u0900" <= c <= "\u097F")
    if real < MIN_BODY_CHARS:
        return True
    if entry and (entry.get("needs_ocr") or entry.get("status") in {"needs_ocr", "ocr_error", "ocr_empty"}):
        return True
    return False


def extract_layer(pdf_path: Path, out_path: Path) -> dict:
    from scripts.extract_pdfs import extract_pdf  # type: ignore

    # Import fails if packages path odd — inline duplicate if needed
    raise NotImplementedError


def extract_inline(pdf_path: Path, out_path: Path) -> dict:
    started = time.time()
    doc = fitz.open(pdf_path)
    page_count = doc.page_count
    parts: list[str] = []
    empty_pages = 0
    body_chars = 0
    for i, page in enumerate(doc):
        text = (page.get_text("text") or "").replace("\x00", "")
        body_chars += len(text.strip())
        if not text.strip():
            empty_pages += 1
        parts.append(f"\n\n===== PAGE {i + 1} / {page_count} =====\n\n{text}")
    full = "".join(parts).strip() + "\n"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(full, encoding="utf-8", errors="replace")
    avg = body_chars / page_count if page_count else 0
    meta = {
        "source_file": pdf_path.name,
        "output_file": str(out_path.relative_to(ROOT)).replace("\\", "/"),
        "size_bytes": pdf_path.stat().st_size,
        "page_count": page_count,
        "char_count": len(full),
        "body_char_count": body_chars,
        "avg_chars_per_page": round(avg, 1),
        "empty_pages": empty_pages,
        "likely_scanned": avg < 40,
        "extraction_method": "pymupdf_text",
        "needs_ocr": avg < 40 or body_chars < MIN_BODY_CHARS,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(time.time() - started, 2),
        "status": "needs_ocr" if (avg < 40 or body_chars < MIN_BODY_CHARS) else "ok",
        "language_hint": "hi" if "hindi" in pdf_path.name.lower() or "yatharupa" in pdf_path.name.lower() else "mixed",
    }
    doc.close()
    return meta


def ocr_inline(pdf_path: Path, out_path: Path, lang: str = "hin+eng", dpi: int = 150) -> dict:
    import io

    import pytesseract
    from PIL import Image

    tesseract_exe = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if tesseract_exe.exists():
        pytesseract.pytesseract.tesseract_cmd = str(tesseract_exe)
    if TESSDATA.exists():
        # Point at the directory that contains *.traineddata
        os.environ["TESSDATA_PREFIX"] = str(TESSDATA)

    started = time.time()
    doc = fitz.open(pdf_path)
    page_count = doc.page_count
    parts: list[str] = []
    body_chars = 0
    for i, page in enumerate(doc):
        try:
            pix = page.get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(img, lang=lang) or ""
        except Exception as exc:  # noqa: BLE001
            # Fallback English-only if hin missing mid-run
            if lang != "eng":
                try:
                    pix = page.get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    text = pytesseract.image_to_string(img, lang="eng") or ""
                    text = f"[OCR lang fallback eng on page {i+1}: {exc}]\n" + text
                except Exception as exc2:  # noqa: BLE001
                    text = f"[OCR failed page {i+1}: {exc2}]\n"
            else:
                text = f"[OCR failed page {i+1}: {exc}]\n"
        text = text.replace("\x00", "")
        body_chars += len(text.strip())
        parts.append(f"\n\n===== PAGE {i + 1} / {page_count} =====\n\n{text}")
        if (i + 1) % 10 == 0 or (i + 1) == page_count:
            elapsed = time.time() - started
            rate = (i + 1) / elapsed if elapsed else 0
            eta = (page_count - i - 1) / rate if rate else 0
            print(
                f"  page {i + 1}/{page_count} | {body_chars:,} chars | "
                f"{rate:.2f} p/s | ETA {eta / 60:.1f} min",
                flush=True,
            )
    full = "".join(parts).strip() + "\n"
    out_path.write_text(full, encoding="utf-8", errors="replace")
    avg = body_chars / page_count if page_count else 0
    doc.close()
    return {
        "source_file": pdf_path.name,
        "output_file": str(out_path.relative_to(ROOT)).replace("\\", "/"),
        "page_count": page_count,
        "char_count": len(full),
        "body_char_count": body_chars,
        "avg_chars_per_page": round(avg, 1),
        "extraction_method": f"pymupdf_pytesseract_ocr:{lang}",
        "needs_ocr": False,
        "likely_scanned": True,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(time.time() - started, 2),
        "status": "ok" if body_chars > 0 else "ocr_empty",
        "language_hint": "hi" if "hin" in lang else "en",
    }


def main() -> int:
    priority_only = "--all" not in sys.argv
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    by_name = {s["source_file"]: s for s in manifest.get("sources", []) if "source_file" in s}

    # Order: priority list first, then any other missing PDF
    all_pdfs = {p.name: p for p in BOOKS_DIR.glob("*.pdf")}
    ordered: list[Path] = []
    for name in PRIORITY:
        if name in all_pdfs:
            ordered.append(all_pdfs[name])
    if not priority_only:
        for name, path in sorted(all_pdfs.items()):
            if path not in ordered:
                ordered.append(path)

    targets = [p for p in ordered if needs_work(p.name, by_name)]
    if not targets:
        print("No new/thin PDFs to process.")
        return 0

    mode = "priority" if priority_only else "all thin"
    print(f"Processing {len(targets)} PDFs ({mode})...\n", flush=True)

    for idx, pdf in enumerate(targets, start=1):
        out_path = OUT_DIR / f"{slugify(pdf.name)}.txt"
        print(f"[{idx}/{len(targets)}] {pdf.name}", flush=True)
        try:
            meta = extract_inline(pdf, out_path)
            print(
                f"  extract: {meta['page_count']}p | {meta['body_char_count']:,} chars | "
                f"avg {meta['avg_chars_per_page']} | {meta['status']}",
                flush=True,
            )
            # OCR if scanned / thin text layer
            if meta.get("needs_ocr") or meta.get("status") == "needs_ocr":
                is_hi = meta.get("language_hint") == "hi" or "hindi" in pdf.name.lower()
                # Deviagari garbled text often has medium char count but no real letters
                sample = out_path.read_text(encoding="utf-8", errors="replace")[:8000]
                dev_count = sum(1 for c in sample if "\u0900" <= c <= "\u097F")
                latin = sum(1 for c in sample if c.isascii() and c.isalpha())
                force_ocr = meta["body_char_count"] < MIN_BODY_CHARS or (is_hi and dev_count < 50)
                # unencrypted-geeta also broken encoding
                if "unencrypted" in pdf.name.lower() or "yatharupa" in pdf.name.lower() or force_ocr:
                    lang = "hin+eng" if (TESSDATA / "hin.traineddata").exists() else "eng"
                    if not (TESSDATA / "hin.traineddata").exists() and is_hi:
                        print("  WARN: hin.traineddata missing — OCR with eng only will be weak", flush=True)
                    print(f"  OCR start lang={lang} → {out_path.name}", flush=True)
                    meta = ocr_inline(pdf, out_path, lang=lang)
                    print(
                        f"  OCR done: {meta['body_char_count']:,} chars | "
                        f"{meta['duration_seconds']}s | {meta['status']}",
                        flush=True,
                    )
            by_name[pdf.name] = {**by_name.get(pdf.name, {}), **meta}
        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED: {exc}", flush=True)
            by_name[pdf.name] = {
                **by_name.get(pdf.name, {}),
                "source_file": pdf.name,
                "status": "error",
                "error": str(exc),
                "extracted_at": datetime.now(timezone.utc).isoformat(),
            }

    # Merge + keep unknown prior entries not in by_name from before if file missing pdf
    sources = list(by_name.values())
    # Prefer list order: all current pdfs first
    ordered_names = [p.name for p in ordered]
    sources_sorted = []
    for n in ordered_names:
        if n in by_name:
            sources_sorted.append(by_name[n])
    for n, e in by_name.items():
        if n not in ordered_names:
            sources_sorted.append(e)

    manifest["sources"] = sources_sorted
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
    manifest["total_pdfs"] = len(sources_sorted)
    manifest["ok_count"] = sum(1 for e in sources_sorted if e.get("status") == "ok")
    manifest["needs_ocr_count"] = sum(1 for e in sources_sorted if e.get("status") == "needs_ocr")
    manifest["error_count"] = sum(
        1 for e in sources_sorted if e.get("status") in {"error", "ocr_error", "ocr_empty"}
    )
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nManifest: {MANIFEST_PATH}", flush=True)
    print(
        f"Summary: {manifest['ok_count']} ok | "
        f"{manifest['needs_ocr_count']} need OCR | "
        f"{manifest['error_count']} errors",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
