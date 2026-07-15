"""Pin SKILL.md version to 1.4.0 (V1.4 release)."""
from __future__ import annotations
import os
import re
import sys
from pathlib import Path

EXPECTED = "1.4.1"


def main() -> None:
    env = os.environ.get("NRS_ROOT") or os.environ.get("NRL_ROOT")
    if env:
        nrl_root = Path(env).resolve()
    else:
        # tests/ -> scripts/ -> <release_root> (legacy: tests/ -> pipeline/ -> build/ -> nature_open_peer_review/ -> <ws>)
        nrl_root = Path(__file__).resolve().parents[3]
    skill = nrl_root / "skill" / "SKILL.md"
    if not skill.exists():
        print(f"skip: {skill} does not exist")
        return
    text = skill.read_text(encoding="utf-8")
    m = re.search(r"^version:\s*(\S+)", text, re.MULTILINE)
    if not m:
        print(f"FAIL: no version: line in {skill}")
        sys.exit(1)
    if m.group(1).strip() != EXPECTED:
        print(f"FAIL: version is {m.group(1)!r}, expected {EXPECTED}")
        sys.exit(1)
    print(f"PASS: version == {EXPECTED}")


if __name__ == "__main__":
    main()
