"""
Extract text from every PDF in Books/ into knowledge/raw_text/.
Writes knowledge/sources/manifest.json with page counts, char counts, and scan flags.
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parents[1]
BOOKS_DIR = ROOT / "Books"
OUT_DIR = ROOT / "knowledge" / "raw_text"
MANIFEST_PATH = ROOT / "knowledge" / "sources" / "manifest.json"

# Below this average chars/page, treat as likely scanned / image-heavy.
SCAN_CHARS_PER_PAGE = 40


def slugify(name: str) -> str:
    stem = Path(name).stem
    stem = re.sub(r"[^\w\-]+", "_", stem, flags=re.UNICODE)
    stem = re.sub(r"_+", "_", stem).strip("_")
    return stem[:120] or "unnamed"


def unique_out_path(pdf_path: Path, used_lower: set[str]) -> Path:
    """Avoid Windows case-insensitive collisions (His vs his)."""
    base = slugify(pdf_path.name)
    candidate = f"{base}.txt"
    if candidate.lower() not in used_lower:
        used_lower.add(candidate.lower())
        return OUT_DIR / candidate
    # Disambiguate with a short content hash of the source filename
    suffix = abs(hash(pdf_path.name)) % 10_000
    candidate = f"{base}_{suffix}.txt"
    used_lower.add(candidate.lower())
    return OUT_DIR / candidate


def extract_pdf(pdf_path: Path, out_path: Path) -> dict:
    started = time.time()
    doc = fitz.open(pdf_path)
    page_count = doc.page_count
    parts: list[str] = []
    empty_pages = 0

    for i, page in enumerate(doc):
        text = page.get_text("text") or ""
        text = text.replace("\x00", "")
        if not text.strip():
            empty_pages += 1
        parts.append(f"\n\n===== PAGE {i + 1} / {page_count} =====\n\n{text}")

    full_text = "".join(parts).strip() + "\n"
    char_count = len(full_text)
    # Exclude page markers from density estimate
    body_chars = sum(len((page.get_text("text") or "").strip()) for page in doc)
    avg_chars = body_chars / page_count if page_count else 0
    likely_scan = avg_chars < SCAN_CHARS_PER_PAGE

    out_path.write_text(full_text, encoding="utf-8", errors="replace")

    meta = {
        "source_file": pdf_path.name,
        "output_file": str(out_path.relative_to(ROOT)).replace("\\", "/"),
        "size_bytes": pdf_path.stat().st_size,
        "page_count": page_count,
        "char_count": char_count,
        "body_char_count": body_chars,
        "avg_chars_per_page": round(avg_chars, 1),
        "empty_pages": empty_pages,
        "likely_scanned": likely_scan,
        "extraction_method": "pymupdf_text",
        "needs_ocr": likely_scan,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(time.time() - started, 2),
        "status": "needs_ocr" if likely_scan else "ok",
    }
    doc.close()
    return meta


def main() -> int:
    if not BOOKS_DIR.exists():
        print(f"Books directory not found: {BOOKS_DIR}", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(BOOKS_DIR.glob("*.pdf"))
    if not pdfs:
        print("No PDFs found in Books/", file=sys.stderr)
        return 1

    print(f"Found {len(pdfs)} PDFs. Extracting...\n")
    entries: list[dict] = []
    used_lower: set[str] = set()

    for idx, pdf in enumerate(pdfs, start=1):
        print(f"[{idx}/{len(pdfs)}] {pdf.name}")
        try:
            out_path = unique_out_path(pdf, used_lower)
            meta = extract_pdf(pdf, out_path)
            flag = "NEEDS OCR" if meta["needs_ocr"] else "OK"
            print(
                f"  -> {meta['page_count']} pages | "
                f"{meta['body_char_count']:,} chars | "
                f"avg {meta['avg_chars_per_page']}/page | {flag}"
            )
            entries.append(meta)
        except Exception as exc:  # noqa: BLE001
            print(f"  -> FAILED: {exc}")
            entries.append(
                {
                    "source_file": pdf.name,
                    "status": "error",
                    "error": str(exc),
                    "extracted_at": datetime.now(timezone.utc).isoformat(),
                }
            )

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "books_dir": "Books",
        "output_dir": "knowledge/raw_text",
        "total_pdfs": len(pdfs),
        "ok_count": sum(1 for e in entries if e.get("status") == "ok"),
        "needs_ocr_count": sum(1 for e in entries if e.get("status") == "needs_ocr"),
        "error_count": sum(1 for e in entries if e.get("status") == "error"),
        "sources": entries,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nManifest written: {MANIFEST_PATH}")
    print(
        f"Summary: {manifest['ok_count']} ok | "
        f"{manifest['needs_ocr_count']} need OCR | "
        f"{manifest['error_count']} errors"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
