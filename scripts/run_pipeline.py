"""End-to-end pipeline: PDF -> segmented Case -> jsonl.

Usage:
    python run_pipeline.py --input <PDF_DIR> --out <OUT_DIR> [--limit N]
                            [--anonymize] [--doi-catalog <CATALOG_TSV>]
"""
from __future__ import annotations
import os
import argparse, glob, hashlib, json, os, sys, time
from pathlib import Path

# Local imports
def _nrs_root() -> Path:
    env = os.environ.get("NRS_ROOT") or os.environ.get("NRL_ROOT")
    if env: return Path(env).resolve()
    here = Path(__file__).resolve().parent
    for anc in [here, *here.parents]:
        if (anc / "knowledge" / "cases.jsonl").exists(): return anc
    return here.parents[3]
_NRS_ROOT = _nrs_root()
sys.path.insert(0, str(_NRS_ROOT / "scripts"))
sys.path.insert(0, str(_NRS_ROOT))
import pdf_reader      # noqa: E402
import segmenter       # noqa: E402
import distill_units   # noqa: E402
import anonymize       # noqa: E402
import io_utils        # noqa: E402


def make_case_id(pdf_path: str) -> str:
    h = hashlib.sha1(pdf_path.encode("utf-8")).hexdigest()[:10]
    base = Path(pdf_path).stem
    base = base.replace(" ", "_").replace("/", "_")
    return f"{base}__{h}"


def process_one(pdf_path: str, *, apply_anonymize: bool, doi_map: dict) -> dict:
    pages = pdf_reader.extract_pages(pdf_path)
    seg = segmenter.segment(pages)
    case = distill_units.distill_case(
        case_id=make_case_id(pdf_path),
        pdf_path=pdf_path,
        segmented=seg,
    )
    # Try to attach a DOI from the catalog
    case["doi"] = doi_map.get(Path(pdf_path).name.lower(), "")
    case["journal"] = "Nature" if "/Nature\\" in pdf_path or "/Nature/" in pdf_path else ""
    if apply_anonymize:
        distill_units.anonymize_case(case, anonymize.anonymize)
    return case


def build_doi_map(catalog_path: str | None) -> dict:
    if not catalog_path or not Path(catalog_path).exists():
        return {}
    import csv
    out = {}
    with open(catalog_path, "r", encoding="utf-8", errors="ignore") as f:
        rdr = csv.DictReader(f, delimiter="\t")
        for r in rdr:
            doi = r.get("doi", "").strip()
            if not doi:
                continue
            # Build a likely filename key by stripping the DOI parts
            key1 = doi.replace("/", "_").replace(".", "_").lower()
            key2 = doi.replace("10.1038/", "").replace("/", "_").lower()
            out[key1] = doi
            out[key2] = doi
    return out



def load_existing_case_ids(path: Path) -> set:
    if not path.exists():
        return set()
    out = set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            cid = rec.get("case_id")
            if cid:
                out.add(cid)
    return out
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--anonymize", action="store_true")
    ap.add_argument("--doi-catalog", default=None)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--append", action="store_true",
                    help="Append to existing cases.jsonl/manifest.tsv instead of overwriting.")
    ap.add_argument("--skip-existing", action="store_true",
                    help="When --append is set, skip PDFs whose case_id is already in cases.jsonl.")
    args = ap.parse_args()

    pdf_paths = sorted(
        p for p in glob.glob(os.path.join(args.input, "**", "*.pdf"), recursive=True)
    )
    if args.limit > 0:
        pdf_paths = pdf_paths[: args.limit]

    doi_map = build_doi_map(args.doi_catalog)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    cases_path = out_dir / "cases.jsonl"
    manifest_path = out_dir / "manifest.tsv"

    existing_ids = set()
    open_mode = "w"
    if args.append and cases_path.exists():
        existing_ids = load_existing_case_ids(cases_path)
        open_mode = "a"
    if args.append and args.skip_existing:
        keep = []
        for p in pdf_paths:
            if make_case_id(p) in existing_ids:
                continue
            keep.append(p)
        pdf_paths = keep

    n = 0
    started = time.time()
    with open(cases_path, open_mode, encoding="utf-8") as cf, \
         open(manifest_path, open_mode, encoding="utf-8") as mf:
        if open_mode == "w":
            mf.write("case_id\tpdf\tpages\topen_access\tversion_rounds\tcorresponding\tdoi\n")
        for pdf in pdf_paths:
            try:
                case = process_one(
                    pdf, apply_anonymize=args.anonymize, doi_map=doi_map,
                )
            except Exception as exc:
                if not args.quiet:
                    print(f"[error] {pdf}: {exc}", file=sys.stderr)
                continue
            cf.write(json.dumps(case, ensure_ascii=False) + "\n")
            mf.write(
                f"{case['case_id']}\t{pdf}\t"
                f"{sum(len(vb.get('reviewer_comments', [])) for vb in case.get('review_rounds', []))}\t"
                f"{case['open_access']}\t"
                f"{len(case['review_rounds'])}\t"
                f"{case['corresponding']}\t{case.get('doi','')}\n"
            )
            n += 1
            if not args.quiet and n % 25 == 0:
                print(f"[{n}/{len(pdf_paths)}] elapsed={time.time()-started:.1f}s")
    print(f"\nDone. wrote {n} cases to {cases_path}")

if __name__ == "__main__":
    main()
