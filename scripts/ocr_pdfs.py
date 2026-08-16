"""
OCR scanned PDFs listed as needs_ocr in knowledge/sources/manifest.json.
Renders pages with PyMuPDF and OCRs with Tesseract via pytesseract.
"""

from __future__ import annotations

import io
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import fitz
import pytesseract
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BOOKS_DIR = ROOT / "Books"
MANIFEST_PATH = ROOT / "knowledge" / "sources" / "manifest.json"

TESSERACT_EXE = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
if TESSERACT_EXE.exists():
    pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_EXE)


def ocr_pdf(pdf_path: Path, out_path: Path, dpi: int = 150) -> dict:
    started = time.time()
    doc = fitz.open(pdf_path)
    page_count = doc.page_count
    parts: list[str] = []
    body_chars = 0

    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img) or ""
        text = text.replace("\x00", "")
        body_chars += len(text.strip())
        parts.append(f"\n\n===== PAGE {i + 1} / {page_count} =====\n\n{text}")

        if (i + 1) % 5 == 0 or (i + 1) == page_count:
            elapsed = time.time() - started
            rate = (i + 1) / elapsed if elapsed else 0
            eta = (page_count - i - 1) / rate if rate else 0
            print(
                f"  page {i + 1}/{page_count} | "
                f"{body_chars:,} chars | "
                f"{rate:.2f} p/s | ETA {eta / 60:.1f} min",
                flush=True,
            )

    full_text = "".join(parts).strip() + "\n"
    out_path.write_text(full_text, encoding="utf-8", errors="replace")
    avg = body_chars / page_count if page_count else 0
    doc.close()

    return {
        "source_file": pdf_path.name,
        "output_file": str(out_path.relative_to(ROOT)).replace("\\", "/"),
        "page_count": page_count,
        "char_count": len(full_text),
        "body_char_count": body_chars,
        "avg_chars_per_page": round(avg, 1),
        "extraction_method": "pymupdf_pytesseract_ocr",
        "needs_ocr": False,
        "likely_scanned": True,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(time.time() - started, 2),
        "status": "ok" if body_chars > 0 else "ocr_empty",
    }


def main() -> int:
    if not MANIFEST_PATH.exists():
        print("Run extract_pdfs.py first.", file=sys.stderr)
        return 1

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    targets = [
        s for s in manifest["sources"] if s.get("needs_ocr") or s.get("status") == "needs_ocr"
    ]
    # Smallest first so we land early wins and catch failures fast
    targets.sort(key=lambda s: s.get("page_count") or 10**9)
    if not targets:
        print("No sources marked needs_ocr.")
        return 0

    print(f"OCR targets: {len(targets)}\n", flush=True)
    updated_by_name = {s["source_file"]: s for s in manifest["sources"]}

    for idx, entry in enumerate(targets, start=1):
        name = entry["source_file"]
        pdf_path = BOOKS_DIR / name
        out_rel = entry.get("output_file")
        out_path = ROOT / out_rel if out_rel else ROOT / "knowledge" / "raw_text" / f"{Path(name).stem}.txt"
        print(f"[{idx}/{len(targets)}] OCR {name}", flush=True)
        if not pdf_path.exists():
            print("  -> missing PDF", flush=True)
            continue
        try:
            meta = ocr_pdf(pdf_path, out_path)
            updated_by_name[name] = {**entry, **meta}
            print(
                f"  -> done: {meta['body_char_count']:,} chars | "
                f"avg {meta['avg_chars_per_page']}/page | {meta['status']} "
                f"({meta['duration_seconds']}s)",
                flush=True,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  -> FAILED: {exc}", flush=True)
            updated_by_name[name] = {
                **entry,
                "status": "ocr_error",
                "error": str(exc),
                "extracted_at": datetime.now(timezone.utc).isoformat(),
            }

    sources = [updated_by_name[s["source_file"]] for s in manifest["sources"]]
    manifest["sources"] = sources
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
    manifest["ok_count"] = sum(1 for e in sources if e.get("status") == "ok")
    manifest["needs_ocr_count"] = sum(1 for e in sources if e.get("status") == "needs_ocr")
    manifest["error_count"] = sum(
        1 for e in sources if e.get("status") in {"error", "ocr_error", "ocr_empty"}
    )
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nManifest updated: {MANIFEST_PATH}", flush=True)
    print(
        f"Summary: {manifest['ok_count']} ok | "
        f"{manifest['needs_ocr_count']} need OCR | "
        f"{manifest['error_count']} errors",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
