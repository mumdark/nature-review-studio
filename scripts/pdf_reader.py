"""PDF reader that prefers text layer and falls back to OCR marker."""
from __future__ import annotations
import sys, importlib
from typing import List
try:
    pdfplumber = importlib.import_module("pdfplumber")
except Exception as e:  # pragma: no cover
    print("[fatal] pdfplumber missing. `pip install pdfplumber`", file=sys.stderr)
    raise

def extract_pages(path: str) -> List[dict]:
    out = []
    with pdfplumber.open(path) as pdf:
        total = len(pdf.pages)
        for i, page in enumerate(pdf.pages, start=1):
            t = page.extract_text() or ""
            t = t.strip()
            out.append({"index": i, "total": total, "text": t, "char_count": len(t)})
    return out

def is_scan_like(pages: List[dict], threshold_chars: int = 50) -> bool:
    """Return True if all pages have very little text -> likely scanned PDF."""
    if not pages:
        return True
    sample = pages[:5]
    return all(p["char_count"] < threshold_chars for p in sample)