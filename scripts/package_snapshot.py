"""Package a merged cases.jsonl into a release artifact with SHA256 provenance.

Usage:
    python package_snapshot.py --input <cases.jsonl> --out <snap_full_v1.2.json>
"""
from __future__ import annotations
import argparse, hashlib, json, time
from pathlib import Path


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--version", default="1.2.0")
    ap.add_argument("--label", default="nature_open_peer_review_full")
    args = ap.parse_args()

    src = Path(args.input)
    out = Path(args.out)
    n = 0
    with src.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                n += 1
    payload = {
        "label": args.label,
        "version": args.version,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": str(src),
        "case_count": n,
        "source_sha256": sha256_of(src),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"[package] {n} cases -> {out}  sha256={payload['source_sha256']}")


if __name__ == "__main__":
    main()