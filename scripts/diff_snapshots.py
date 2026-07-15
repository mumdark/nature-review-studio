"""Merge two snap JSONLs (snap_2025 + snap_2026) into one full snapshot.

Behaviour:
  - Deduplicates by case_id (last write wins).
  - Writes merged JSONL to <out_dir>/cases.jsonl.
  - Writes combined manifest.tsv (case_id, source_pdf, version_rounds).
  - Prints `[done] <count> cases -> <out>`.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path


def load(path: Path):
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", action="append", required=True,
                    help="Path to a snap_XXXX/cases.jsonl. Repeat for multiple.")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    by_case = {}
    for src in args.input:
        rows = load(Path(src))
        for r in rows:
            by_case[r["case_id"]] = r
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    cases_path = out_dir / "cases.jsonl"
    manifest_path = out_dir / "manifest.tsv"
    with cases_path.open("w", encoding="utf-8") as f:
        for r in by_case.values():
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with manifest_path.open("w", encoding="utf-8") as f:
        f.write("case_id\tsource_pdf\tversion_rounds\topen_access\tcorresponding\n")
        for r in by_case.values():
            f.write(
                f"{r['case_id']}\t{r.get('source_pdf','')}\t"
                f"{len(r.get('review_rounds', []))}\t"
                f"{r.get('open_access', False)}\t"
                f"{r.get('corresponding','')}\n"
            )
    print(f"[done] {len(by_case)} cases -> {cases_path}")


if __name__ == "__main__":
    main()