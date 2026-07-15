"""Strip identifying information from text."""
from __future__ import annotations
import re

EMAIL = re.compile(r"\b[\w\.\-+]+@[\w\.\-]+\.[A-Za-z]{2,}\b")
PHONE = re.compile(r"\b(\+?\d{1,3}[\s\-]?)?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}\b")
ORCID = re.compile(r"\b\d{4}-\d{4}-\d{4}-\d{3}[0-9X]\b")
DOI = re.compile(r"\b(?:https?://(?:dx\.)?doi\.org/|doi:\s*)?10\.\d{4,9}/[^\s)]+", re.IGNORECASE)
GRANT = re.compile(r"\b(?:NIH|NSFC|ERC|NIH/NCI|R01|U\d{2,3})[\-\s]?[A-Z0-9]+\b")
NCT = re.compile(r"\bNCT\d{6,8}\b")
ACCESSION = re.compile(r"\b(?:GenBank|Accession|ENA|GSE|SRA|PRJ[EON][A-Z]?\d{2,8})\s*[:#]?\s*[A-Z0-9]+", re.IGNORECASE)
URL = re.compile(r"https?://[^\s)]+")
PERSON_NAME_HINT = re.compile(r"\b(?:Dr|Mr|Mrs|Ms|Prof|Professor|Dr\.|Mr\.|Mrs\.|Ms\.|Prof\.)\s+[A-Z][a-z]+\b")

def anonymize(text: str) -> str:
    if not text:
        return text
    t = text
    t = EMAIL.sub("[EMAIL]", t)
    t = PHONE.sub("[PHONE]", t)
    t = ORCID.sub("[ORCID]", t)
    t = NCT.sub("[TRIAL_ID]", t)
    t = DOI.sub("[DOI]", t)
    t = GRANT.sub("[GRANT_ID]", t)
    t = ACCESSION.sub("[ACCESSION_ID]", t)
    t = URL.sub("[URL]", t)
    t = PERSON_NAME_HINT.sub("[NAME]", t)
    return t
def audit_file(path: Path) -> dict:
    import json
    hits = {
        "email": 0, "phone": 0, "orcid": 0, "doi": 0,
        "grant": 0, "nct": 0, "accession": 0, "url": 0,
        "person_name_hint": 0,
    }
    n = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            n += 1
            try:
                c = json.loads(line)
            except json.JSONDecodeError:
                continue
            text_parts = [c.get("corresponding", "")]
            for r in c.get("review_rounds", []):
                for blob in r.get("reviewer_reports", []):
                    for sc in blob.get("sub_comments", []):
                        text_parts.append(sc.get("text", ""))
            for r in c.get("author_responses", []):
                text_parts.append(r.get("text", ""))
            text = "\n".join(text_parts)
            if EMAIL.search(text): hits["email"] += 1
            if PHONE.search(text): hits["phone"] += 1
            if ORCID.search(text): hits["orcid"] += 1
            if DOI.search(text): hits["doi"] += 1
            if GRANT.search(text): hits["grant"] += 1
            if NCT.search(text): hits["nct"] += 1
            if ACCESSION.search(text): hits["accession"] += 1
            if URL.search(text): hits["url"] += 1
            if PERSON_NAME_HINT.search(text): hits["person_name_hint"] += 1
    return {"cases": n, "hits": hits}


if __name__ == "__main__":
    import argparse, sys
    from pathlib import Path
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", required=True, help="Path to cases.jsonl to audit")
    args = ap.parse_args()
    res = audit_file(Path(args.audit))
    print("audit", args.audit, ":", res["cases"], "cases")
    bad = {k: v for k, v in res["hits"].items() if v}
    if bad:
        print("FAIL identifier hits:", bad)
        sys.exit(1)
    print("PASS no identifiers")