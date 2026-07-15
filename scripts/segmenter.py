"""Split a Peer Review File (PRF) into structured segments.

Empirically observed layout (Nature PRF):
  - Pages 1..k:  'Version 0' / 'Version 1' headers separate review rounds.
                 'Referee #N' headers separate individual reports inside a round.
  - Page m (license): full-page CC-BY boilerplate bounded by
                       'Open Access This Peer Review File' (start) and
                       'To view a copy of this license' (end).
  - Pages m+1..end: author rebuttal begins with 'We are grateful ...' or
                   'We thank ...' and continues interleaved with reviewer quotes.
"""
from __future__ import annotations
import re
from typing import List, Dict, Any

VERSION_HDR = re.compile(r"^\s*Version\s+(\d+)\s*:?\s*$", re.MULTILINE | re.IGNORECASE)
REFEREE_HDR = re.compile(r"^\s*Referee\s*#\s*(\d+)\s*$", re.MULTILINE | re.IGNORECASE)
CORRESPONDING = re.compile(r"^\s*Corresponding Author:\s*(.+)$", re.MULTILINE | re.IGNORECASE)
OPEN_ACCESS_FIRST = re.compile(r"^Open Access\s+This Peer Review File", re.MULTILINE | re.IGNORECASE)
LICENSE_END = re.compile(r"To view a copy of this license", re.IGNORECASE)
REPLY_INTRO = re.compile(
    r"^\s*We (?:are grateful|thank|appreciate)\b", re.MULTILINE | re.IGNORECASE
)
RE_REVIEWER_HEAD = re.compile(
    r"^\s*(?:Reviewer|Referee|Reviewer [0-9])\s*#?\s*\d*\s*[:\.\)]?\s*$",
    re.MULTILINE | re.IGNORECASE,
)
RE_REPLY_HEADER = re.compile(
    r"^\s*Reply to reviewer\s*\d+\s*$", re.MULTILINE | re.IGNORECASE
)

def _flatten_pages(pages: List[dict]) -> str:
    parts = []
    for p in pages:
        parts.append(f"\n\n===PAGE {p['index']}/{p['total']}===\n")
        parts.append(p["text"] or "")
    return "".join(parts)

def segment(pages: List[dict]) -> Dict[str, Any]:
    flat = _flatten_pages(pages)
    corresponding = ""
    m = CORRESPONDING.search(flat)
    if m:
        corresponding = m.group(1).strip()
    oa_match = OPEN_ACCESS_FIRST.search(flat)
    lic_end_match = LICENSE_END.search(flat)

    version_blocks: List[Dict[str, Any]] = []
    v_matches = list(VERSION_HDR.finditer(flat))
    review_cutoff = len(flat)
    if oa_match:
        review_cutoff = oa_match.start()
    if lic_end_match:
        review_cutoff = min(review_cutoff, lic_end_match.start())
    if v_matches:
        for i, v in enumerate(v_matches):
            start = v.end()
            end = v_matches[i + 1].start() if i + 1 < len(v_matches) else review_cutoff
            block_text = flat[start:end].strip()
            version_blocks.append({
                "version": i,
                "is_rebuttal_block": False,
                "reviewer_comments": _extract_reviewer_blocks(block_text),
                "raw_segment": block_text,
            })
    else:
        block_text = flat[:review_cutoff].strip()
        version_blocks.append({
            "version": 0,
            "is_rebuttal_block": False,
            "reviewer_comments": _extract_reviewer_blocks(block_text),
            "raw_segment": block_text,
        })

    rebuttal_blocks: List[Dict[str, Any]] = []
    if lic_end_match:
        reply_zone = flat[lic_end_match.end():].strip()
    elif oa_match:
        reply_zone = flat[oa_match.end():].strip()
    else:
        reply_zone = ""

    if reply_zone:
        # chop trailing license URL line "/4.0/" plus blank lines
        reply_zone = re.sub(
            r"^,\s*visit https?://creativecommons\.org/licenses[^\n]*\n+",
            "",
            reply_zone,
        ).strip()
        # If a second OA page appears later, chop it
        second_oa = OPEN_ACCESS_FIRST.search(reply_zone)
        if second_oa:
            reply_zone = reply_zone[:second_oa.start()].strip()
        if reply_zone:
            rebuttal_blocks.append({
                "is_rebuttal_block": True,
                "raw_segment": reply_zone,
                "rebuttal_segments": _extract_rebuttal_paragraphs(reply_zone),
            })

    return {
        "corresponding": corresponding,
        "version_blocks": version_blocks,
        "rebuttal_blocks": rebuttal_blocks,
        "open_access_present": bool(oa_match),
        "total_chars": len(flat),
    }

def _extract_reviewer_blocks(text: str) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []
    matches = list(REFEREE_HDR.finditer(text))
    if not matches:
        return [{"referee": "ANON", "text": text.strip()}] if text.strip() else []
    for i, m in enumerate(matches):
        n = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            blocks.append({"referee": f"#{n}", "text": body})
    return blocks

def _extract_rebuttal_paragraphs(text: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    # Prefer "Reply to reviewer N" markers
    reply_marks = list(RE_REPLY_HEADER.finditer(text))
    if reply_marks:
        for i, m in enumerate(reply_marks):
            label = m.group(0).strip()
            start = m.end()
            end = reply_marks[i + 1].start() if i + 1 < len(reply_marks) else len(text)
            body = text[start:end].strip()
            if body:
                out.append({"referee": label, "text": body})
        return out
    # Otherwise fall back to reviewer head markers
    rev_matches = list(RE_REVIEWER_HEAD.finditer(text))
    if rev_matches:
        for i, m in enumerate(rev_matches):
            label = m.group(0).strip(" :.\n")
            start = m.end()
            end = rev_matches[i + 1].start() if i + 1 < len(rev_matches) else len(text)
            body = text[start:end].strip()
            if body:
                out.append({"referee": label, "text": body})
        return out
    items = re.split(r"\n\s*\n+", text)
    for p in items:
        p = p.strip()
        if len(p) > 50:
            out.append({"referee": None, "text": p})
    return out
