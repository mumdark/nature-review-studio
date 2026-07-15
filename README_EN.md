# nature-review-studio v1.4.1

[简体中文](README.md) · **English**

> A Nature-style, multi-perspective manuscript review and response skill distilled from 1,287 Nature Peer Review File cases published in 2025–2026.

## What it does

`nature-review-studio` provides three interfaces:

| Interface | Purpose | User-facing output |
|---|---|---|
| `review` | Simulate 2–5 complementary reviewers and synthesize their concerns | exactly one `.docx` and one same-stem `.md` |
| `respond` | Draft an editor letter, point-by-point responses, and a revision task table | exactly one `.docx` and one same-stem `.md` |
| `update` | Ingest, anonymize, distill, index, benchmark, and version new peer-review material | internal knowledge artifacts and an update report |

The output language follows the user's prompt unless explicitly overridden.

## Installation

Ask Codex:

```text
Install the skill located at <path>/nature-review-studio-v1.4.1.
```

The installer:

- copies `skill/` to `$HOME/.codex/skills/nature-review-studio/`;
- records the release directory as `NRS_ROOT` in `skill/.nrs_root`;
- verifies the skill frontmatter and all six required reference files.

## Package layout

```text
nature-review-studio-v1.4.1/
├── README.md                  # Chinese documentation (default)
├── README_EN.md               # English documentation
├── RELEASE_NOTES.md           # Chinese release notes
├── RELEASE_NOTES_EN.md        # English release notes
├── install.ps1
├── skill/                     # Codex skill instructions and references
├── scripts/                   # Rendering and distillation pipeline
├── tests/                     # Regression checks
├── knowledge/                 # Compact distilled indexes
├── output/                    # Example synchronized outputs
└── pdfs/.gitkeep              # Placeholder for update inputs
```

The release is approximately 11 MB. The 138 MB offline `cases.jsonl` corpus is not bundled because review and response generation do not read it at runtime.

## Distilled review knowledge

The bundled knowledge layer contains:

- 12 canonical concern axes, including experimental design, novelty, statistical rigor, reproducibility, clinical validity, figures, and claim moderation;
- 6 manuscript-fingerprint-to-reviewer-set mappings;
- 21 response strategies, from adding controls or validation data to moderating claims or respectfully disagreeing;
- 8 revision task states for tracking whether each concern is complete, drafted, pending analysis, pending experiment, infeasible, or disputed;
- compact frequency, method-family, severity, and snapshot metadata derived from 1,287 cases.

Historical reviewer text and case identities must never be copied into generated reports.

## Locked two-file output contract

Both `review` and `respond` create exactly two synchronized files:

```text
<entry>_<case>_<YYYYMMDD>.docx
<entry>_<case>_<YYYYMMDD>.md
```

The files use the same language, section order, reviewer numbering, concerns, consensus content, and revision task table. Internal coverage checks, claim–evidence maps, adversarial checks, and editor-decision hints remain silent.

## Release notes

See [RELEASE_NOTES_EN.md](RELEASE_NOTES_EN.md). Chinese release notes are available in [RELEASE_NOTES.md](RELEASE_NOTES.md).
