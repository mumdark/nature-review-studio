"""No-identifier audit for any cases.jsonl produced by run_pipeline.py.

Iterates all reviewer / response text, fails if any of the 8 identifier
classes (email, ORCID, DOI, phone, NCT, R01 grant, URL, name pattern)
matches. Skips release of the snapshot otherwise.

Note: in the V1.4 flat release bundle, cases.jsonl is NOT shipped
(this is the offline knowledge base; the release ships only the
distilled indexes). Run this test from the workspace where cases.jsonl
exists, or pass a path to a cases.jsonl file:
    python tests/test_no_identifiers.py path/to/cases.jsonl
"""
from __future__ import annotations
import json
import os
import re
import sys
from pathlib import Path

PATTERNS = {
    "email":    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.(?:com|org|edu|net|gov|io|ac|uk|cn|de|fr|jp|au|ca|us|info|biz|co|me|tv|app|ai)\b", re.IGNORECASE),
    "orcid":    re.compile(r"\b\d{4}-\d{4}-\d{4}-\d{3}[\dX]\b"),
    "doi":      re.compile(r"\b10\.\d{4,}/\S+"),
    "phone":    re.compile(r"(?<![\d.])\+\d{1,3}[\s-]?\d{3,4}[\s-]?\d{3,4}(?![\d])"),
    "nct":      re.compile(r"\bNCT0\d{7}\b"),
    "R01":      re.compile(r"\bR01\b"),
    "url":      re.compile(r"https?://\S+"),
    "name_pat": re.compile(r"\b(?:Dr|Mr|Mrs|Ms|Prof|Professor)\.?\s+[A-Z][a-z]+\b"),
}


def collect_text(case) -> str:
    parts = [case.get("corresponding", "")]
    for r in case.get("review_rounds", []):
        for blob in r.get("reviewer_reports", []):
            for sc in blob.get("sub_comments", []):
                parts.append(sc.get("text", ""))
    for r in case.get("author_responses", []):
        parts.append(r.get("text", ""))
    return "\n".join(parts)


def audit(path: Path) -> dict:
    hits = {k: 0 for k in PATTERNS}
    n = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            c = json.loads(line)
            n += 1
            txt = collect_text(c)
            for k, pat in PATTERNS.items():
                if pat.search(txt):
                    hits[k] += 1
    return {"cases": n, "hits": hits}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        p = Path(sys.argv[1])
    else:
        env = os.environ.get("NRS_ROOT") or os.environ.get("NRL_ROOT")
        if env:
            p = Path(env).resolve() / "knowledge" / "cases.jsonl"
        else:
            p = Path(__file__).resolve().parents[2] / "snapshots" / "snap_full" / "cases.jsonl"
    if not p.exists():
        print(f"skip: {p} does not exist (cases.jsonl is optional in the V1.4 release bundle)")
        sys.exit(0)
    res = audit(p)
    print(f"audit {p.name}: {res['cases']} cases")
    bad = {k: v for k, v in res["hits"].items() if v}
    if bad:
        print("FAIL: identifier hits:", bad)
        sys.exit(1)
    print("PASS")
