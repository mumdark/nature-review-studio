"""Build the three calibration JSONs from a merged cases.jsonl.

  - index_axes.json:    per-concern-axis histogram (mapped to the 12-axis
                        taxonomy in references/review-axes.md)
  - index_methods.json: per-method-family histogram (best-effort heuristic
                        from full case text, not just corresponding field)
  - index_severity.json: per-axis severity mix (major / minor / minor-major
                        inferred from comment text)

Each index is a small JSON the Skill may load instead of recomputing
statistics on every generation.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

# Canonical 12-axis taxonomy (mirrors references/review-axes.md)
AXES = [
    "novelty-significance",
    "mechanism-evidence",
    "experimental-design",
    "statistical-rigor",
    "reproducibility",
    "clinical-validity",
    "ethical-governance",
    "data-resource-quality",
    "figures-and-tables",
    "writing-clarity",
    "claim-moderation",
    "mechanistic-vs-correlative",
]

# Mapping from raw 16-axis labels found in cases.jsonl to canonical 12-axis
AXIS_MAP = {
    "novelty":              "novelty-significance",
    "machinery":            "mechanism-evidence",
    "controls":             "experimental-design",
    "sample_size":          "experimental-design",
    "comparator":           "experimental-design",
    "statistical":          "statistical-rigor",
    "data_availability":    "reproducibility",
    "clinical":             "clinical-validity",
    "ethics":               "ethical-governance",
    "methods_detail":       "data-resource-quality",
    "external_validation":  "data-resource-quality",
    "figure_quality":       "figures-and-tables",
    "writing":              "writing-clarity",
    "interpretation":       "claim-moderation",
    "limitation":           "claim-moderation",
    "long_term_or_followup": "mechanistic-vs-correlative",
}

# Method-family keyword table (used to scan full case text)
METHOD_KW = {
    "wet-lab":      ["plasmid", "antibody", "western blot", "mice", "knockout",
                     "cell line", "transfection", "incubation", "pcr", "sirna",
                     "crispr", "flow cytometry", "immunofluorescence"],
    "clinical":     ["patient", "cohort", "irb", "consent", "recruitment",
                     "survival", "endpoint", "clinical trial", "hospital",
                     "diagnosis", "treatment outcome", "biopsy"],
    "imaging":      ["confocal", "fluorescence", "microscopy", "tomography",
                     "mri", "electron microscopy", "cryo-em", "staining",
                     "image j", "fluorescent imaging"],
    "ML":           ["classifier", "neural network", "deep learning", "gradient",
                     "cross-validation", "fold", "train/test", "convolutional",
                     "transformer", "embedding", "feature extraction", "auc"],
    "simulation":   ["molecular dynamics", "monte carlo", "ab initio", "lattice",
                     "temperature ramp", "force field", "langevin"],
    "data-resource": ["database", "deposited", "accession", "supplementary dataset",
                      "curated", "genbank", "geo", "pride", "metabolights"],
    "omics":        ["rna-seq", "single-cell", "scrna-seq", "chip-seq",
                     "atac-seq", "proteomics", "metabolomics", "lipidomics",
                     "wgbs", "methylation", "spectrum"],
    "review-theory": ["review", "perspective", "commentary", "hypothesis",
                      "theoretical framework", "minireview"],
}

# Severity heuristic: scan comment text
SEV_KEYWORDS_MAJOR = [
    r"\b(fatal flaw|critical|must (?:be )?addressed?|essential|fundamental|invalidates)\b",
    r"\b(unethical|not (?:be )?acceptable|reject(?:ing|ion)? in present form)\b",
    r"\b(major (?:concern|issue|revision))\b",
    r"\b(does not support|insufficient evidence|lacks? (?:proper |appropriate )?(?:control|validation))\b",
]
SEV_KEYWORDS_MINOR = [
    r"\b(minor (?:concern|issue|revision|point))\b",
    r"\b(suggest(?:ing|ion)?|recommend(?:ing|ation)?|consider|please (?:clarify|add|provide|revise))\b",
    r"\b(typo|grammar|capitalization|spelling|flow|readability)\b",
    r"\b(figure \d+ (?:axis|legend|caption))\b",
]
SEV_KEYWORDS_MM = [
    r"\b(caveat|moderate|hedge|soften|tone down|over(?:ly)? strong|overstated|overreach)\b",
    r"\b(may|might|could|possibly)\b.*\b(claim|conclusion|interpretation)\b",
    r"\b(claim[- ]moderation|interpret(?:ation|ive) caution)\b",
]


def _flatten_text(case: dict) -> str:
    """Concatenate all textual content of a case for keyword scanning."""
    parts = [case.get("corresponding", "") or ""]
    for rnd in case.get("review_rounds", []) or []:
        for blob in rnd.get("reviewer_reports", []) or []:
            parts.append(blob.get("text", "") or "")
            for sc in blob.get("sub_comments", []) or []:
                parts.append(sc.get("text", "") or "")
        for resp in rnd.get("author_responses", []) or []:
            parts.append(resp.get("text", "") or "")
    return "\n".join(parts).lower()


def _classify_severity(text: str) -> str:
    """Bucket a comment into major / minor / minor-major based on keyword density."""
    if not text:
        return "minor"
    text = text.lower()
    major = sum(len(re.findall(p, text)) for p in SEV_KEYWORDS_MAJOR)
    minor = sum(len(re.findall(p, text)) for p in SEV_KEYWORDS_MINOR)
    mm    = sum(len(re.findall(p, text)) for p in SEV_KEYWORDS_MM)
    if major >= max(minor, mm) + 1 and major > 0:
        return "major"
    if mm >= minor and mm > 0:
        return "minor-major"
    return "minor"


def load(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def axis_histogram(rows):
    """Count concerns by canonical 12-axis (mapped from raw 16-axis labels)."""
    c = Counter()
    for r in rows:
        for rnd in r.get("review_rounds", []) or []:
            for blob in rnd.get("reviewer_reports", []) or []:
                for sc in blob.get("sub_comments", []) or []:
                    for raw in sc.get("concern_labels", []) or []:
                        canon = AXIS_MAP.get(raw, raw)
                        if canon in AXES:
                            c[canon] += 1
    return c.most_common()


def method_family_histogram(rows):
    """Count cases by method family inferred from FULL case text."""
    fam = Counter()
    for r in rows:
        text = _flatten_text(r)
        hits = set()
        for fam_name, kws in METHOD_KW.items():
            for kw in kws:
                if kw in text:
                    hits.add(fam_name)
                    break
        if not hits:
            hits = {"unspecified"}
        for f in hits:
            fam[f] += 1
    return fam.most_common()


def severity_mix(rows):
    """Per-axis severity distribution.  Each concern is classified via
    text heuristic; axis comes from raw label (mapped to canonical)."""
    c = Counter()
    for r in rows:
        for rnd in r.get("review_rounds", []) or []:
            for blob in rnd.get("reviewer_reports", []) or []:
                for sc in blob.get("sub_comments", []) or []:
                    text = sc.get("text", "") or ""
                    sev = _classify_severity(text)
                    for raw in sc.get("concern_labels", []) or []:
                        canon = AXIS_MAP.get(raw, raw)
                        if canon in AXES:
                            c[(canon, sev)] += 1
    out = {}
    for (axis, sev), n in c.items():
        out.setdefault(axis, {"major": 0, "minor": 0, "minor-major": 0})
        out[axis][sev] = n
    # Sort inner dict deterministically
    return {ax: dict(sorted(d.items())) for ax, d in sorted(out.items())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="cases.jsonl")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    rows = load(Path(args.input))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ax = axis_histogram(rows)
    with (out_dir / "index_axes.json").open("w", encoding="utf-8") as f:
        json.dump(
            {
                "axes_ranked": ax,
                "axis_definitions": AXES,
                "raw_to_canonical": AXIS_MAP,
            },
            f, ensure_ascii=False, indent=2,
        )

    mf = method_family_histogram(rows)
    with (out_dir / "index_methods.json").open("w", encoding="utf-8") as f:
        json.dump(
            {
                "families_ranked": mf,
                "method_keywords": {k: len(v) for k, v in METHOD_KW.items()},
            },
            f, ensure_ascii=False, indent=2,
        )

    sm = severity_mix(rows)
    with (out_dir / "index_severity.json").open("w", encoding="utf-8") as f:
        json.dump(sm, f, ensure_ascii=False, indent=2)

    print(f"[done] {len(rows)} cases -> {out_dir}")
    print(f"  index_axes.json:    {len(ax)} canonical axes")
    print(f"  index_methods.json: {len(mf)} families")
    print(f"  index_severity.json: {len(sm)} axes x 3 severity buckets")


if __name__ == "__main__":
    main()
