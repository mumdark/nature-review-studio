# nature-review-studio (V1.4.1)

> **中文名：Nature_ReviewStudio 多视角高水平审稿与回复蒸馏系统**

V1.4.0 establishes a strict **two-file deliverable**:

- One editable Word file (.docx) and one clean Markdown file (.md).
- Both outputs share the same base name and substantive content.
- Edit letter with a **revision-level banner** is the first content section.
- Per-reviewer sections follow a strict **Overall + Major + Minor** structure.
- A single **Cross-review consensus** block; **no divergence / severity escalation / decision-hint** in the file.
- A **revision task table** at the end.
- **No preamble, no compliance note, no coverage note, no claim-evidence map dump, no critic-flag block** — those are internal-only.
- Output language follows the user's prompt language (Chinese / English auto-detect).
- Meta `.docx` rendering is done by the offline Python script `build/pipeline/render_review_docx.py` in the project workspace.

## File layout

```
nature-review-studio/
├── SKILL.md                  # entry point + contract
├── README.md                 # this file
└── references/
    ├── workflow.md           # entry detection + orchestration
    ├── review-axes.md        # 12 concern axes + per-reviewer output structure
    ├── response-axes.md      # 21 response strategies + 8 status taxonomy
    ├── adversarial-checklist.md  # internal QA only (NOT emitted to file)
    ├── source-basis.md       # snapshot provenance + extension commands
    └── render-docx.md        # docx payload schema + CLI
```

## Three entries

| Entry | Trigger | Output file shape |
|---|---|---|
| `review` | "审稿", "review", "Nature-style review", "multi-perspective review" | `review_<case>_<YYYYMMDD>.docx` + `.md` |
| `respond` | "回复", "response", "rebuttal", "逐条回复", "point-by-point" | `respond_<case>_<YYYYMMDD>.docx` + `.md` |
| `update` | "入库", "蒸馏", "更新知识库", "ingest PRF" | (no docx; offline pipeline) |

## How Codex uses this skill

1. User prompt triggers one of the three entries.
2. Skill runs the silent adversarial check.
3. Skill hands a JSON payload to the offline Python render script.
4. Render script emits one `.docx` and one same-stem `.md`.
5. Codex reports both paths; it does not create additional report files.

## Re-install the skill

From the project root:

```powershell
powershell -ExecutionPolicy Bypass -File nature_open_peer_review/build/pipeline/install_skill.ps1
```

The script:

1. Backs up any previous install (timestamped).
2. Copies `.codex/skills/nature-review-studio/` to the Codex global skills folder.
3. Verifies SKILL.md frontmatter and all 6 references are present.
4. Prints `[ok] Installed nature-review-studio v1.4.1 ...`.

## Quick commands

| Action | Command |
|---|---|
| Render an English review docx from a real sample | `python nature_open_peer_review/build/pipeline/render_review_docx.py --payload build/samples/sample_50/payload_review_en.json --out build/output/review_en.docx` |
| Render a Chinese review docx | same, with `payload_review_zh.json` |
| Generate a one-shot ad-hoc docx without writing payload JSON | `python nature_open_peer_review/build/pipeline/render_review_docx_quick.py --case-id foo --language zh --band "重大修改" --editor-paragraph "..." --reviewer "Mechanism Reviewer||Overall paragraph||Major heading 1\|Major heading 2\| Minor heading 1" --out build/output/foo.docx` |
| Re-distill 50 cases | `python nature_open_peer_review/build/pipeline/run_pipeline.py --input nature_open_peer_review/PDFs/Nature/2025 --out nature_open_peer_review/build/samples/sample_50 --limit 50 --anonymize --quiet` |
| Run full batch | `powershell -ExecutionPolicy Bypass -File nature_open_peer_review/build/pipeline/run_full_batch.ps1` |

## Sample outputs

Saved under `build/output/` for inspection:

- `review_en_sample.docx` — English render of Aarsland_2025 distilled payload.
- `review_zh_sample.docx` — Chinese render of the same case.
