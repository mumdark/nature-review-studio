# Workflow — orchestration across `review`, `respond`, `update`

> **V1.4.0 changes**: `review` and `respond` have a strict two-file contract: one formal `.docx` plus one same-stem `.md`; no additional user-facing report files are created.

This document is the orchestration backbone. Codex dispatches the user's request
into one of three operational chains, then routes the result through a single
**docx render pipeline** that emits exactly one Word file.

## 0. Entry detection

| Detected signal | Entry | Comments |
|---|---|---|
| User supplies only a manuscript (no reviewer report) and asks for "审稿" / "评审" / "review" / "Nature-style review" | `review` | |
| User supplies a manuscript AND reviewer report, and asks for "回复" / "response" / "rebuttal" / "逐条" / "point-by-point" / "回信" / "编辑信" | `respond` | If reviewer report is missing, fall back to `review` first and synthesize a hypothetical reviewer set |
| User asks to "入库" / "蒸馏" / "更新知识库" / "ingest" / "rebuild knowledge base" | `update` | Triggers the offline Python pipeline under `build/pipeline/` |

Multiple entries in one prompt are allowed; the skill executes them in the
order `update → review → respond` so the new knowledge is consulted first.

## 1. Language detection (added in V1.1.0)

Before any generation:

1. Scan the most recent user message for any CJK character (U+4E00 – U+9FFF or
   Japanese kana, Korean Hangul). If any are present, set `language = zh`.
2. Else, if `language=` parameter is in the prompt, honor it.
3. Else, default `language = en`.

All copy the skill emits (editor letter, reviewer Overall / concerns, task
table headings) follows the detected language. Technical terms (e.g. `p-value`,
`n=`, `Figure`, `Methods`) stay in English unless the manuscript itself
overrides them. The render script resolves the right Chinese-vs-English
heading dictionary from `review-axes.md §D`.

## 2. Shared preprocessing

For all entries that touch a manuscript:

1. **Identifier sniff** — find any of: `@`, ORCID pattern, `10.xxxx/`, `NCT\d+`,
   URLs, common grant prefixes. If found, the in-loop self-check flags it and
   the render script strips it from the docx, but the user is informed via a
   single console line outside the docx.
2. **Structural extraction** — split the manuscript into `abstract`,
   `introduction`, `methods`, `results`, `discussion`, `figures & tables`,
   `references`. If a section is missing, mark `MISSING: <name>` in the silent
   self-check (not in the docx).
3. **Claim–evidence bind** — each numbered concern binds one claim and one
   evidence pointer inline. No separate dump.
4. **Method family assignment** — `wet-lab | observational | clinical | imaging | ML | simulation | theory | data-resource`.
5. **Article type classification** — `Article | Letter | Brief Communication | Perspective & Review | Resource | Case Report`.

If any step fails, the skill writes its guess and `confidence` drops.

## 3. `review` orchestration

```
Input: manuscript
   ↓
Preprocess (Step 1)
   ↓
Language detection → set zh/en
   ↓
Method family + article type → reviewer selector (see review-axes.md §B)
   ↓
Concern retrieval → PRF case graph (top-k)
   ↓
For each reviewer role in the chosen set:
    Build per-reviewer JSON:
      - role_label
      - overall_paragraph
      - major_concerns: [{heading, body, evidence, confidence}]
      - minor_concerns: [...] 
      - overall_confidence
   ↓
Cross-review consensus (concerns raised by ≥2 reviewers only — see review-axes.md §E)
   ↓
Revision task table (compile from all reviewers)
   ↓
Silent adversarial self-check (see adversarial-checklist.md)
   ↓
render_review_docx.py →  <one .docx file + one same-stem .md file>
   ↓
Console output: file path + one-line summary
```

The editor letter is generated from the cross-review consensus + revision
task table. Its first paragraph carries the **revision-level banner**
(see review-axes.md §F).

## 4. `respond` orchestration

```
Input: manuscript, reviewer_reports, optional revised_manuscript
   ↓
If revised_manuscript is provided:
    Mark matching concerns as DONE; otherwise mark DRAFTED.
   ↓
For each reviewer in rr:
    Split into atomic sub-comments.
    For each comment: strategy (one of 21) + status (one of 8) + confidence + follow-up risk.
   ↓
Build editor-letter JSON: revision-level band + 1–4 paragraphs.
   ↓
Compile per-reviewer sections.
   ↓
Cross-review consensus block.
   ↓
Revision task table.
   ↓
Silent self-check.
   ↓
render_review_docx.py →  <one .docx file + one same-stem .md file>
```

The editor letter's revision-level band follows the same rule as `review`
(see review-axes.md §F) but is computed from the comment-level status counts:
- ≥1 unresolved Major → `Major revision`
- otherwise, ≥3 minor unresolved → `Accept with minor revisions`
- otherwise, core conclusion unsupported → `Reject in present form`
- otherwise, missing materials → `Cannot be assessed`

## 5. `update` orchestration

```
Input: folder of PRF PDFs
   ↓
python build/pipeline/run_pipeline.py \
    --input <folder> --out <new_out_dir> --anonymize
   ↓
Diff new cases.jsonl against previous stable snapshot.
   ↓
Stage new snapshot under build/snapshots/ — never overwrite.
   ↓
Console update_report summary (NOT written into a docx).
```

## 6. Docx render stage (added in V1.1.0)

After generation and silent self-check, the skill hands a JSON payload to:

```
python build/pipeline/render_review_docx.py \
    --payload <tmp.json> \
    --out <output.docx> \
    --language zh | en
```

Layout rules:

- Page size A4; margins 2.5 cm top/bottom, 2.5 cm left/right.
- Title in 16 pt bold.
- Section headings (`Editor letter — …`, `Reviewer X — <Role>`) in 13 pt bold.
- `Overall` / `整体点评` heading at 11 pt bold.
- `Major concerns` / `主要问题` and `Minor concerns` / `次要问题` at 11 pt bold.
- Numbered items use arabic numerals, with the concern heading inline-bold and
  one body paragraph following.
- Tables use the docx `Table Grid` style with header row bold.
- A single footer line: `Generated by nature-review-studio · <date> · <case id>`.

See `references/render-docx.md` for the full payload schema.

## 7. Data flow

```
        user
         │
   ┌─────┴──────┐
   │            │
 review      respond
   │            │
   ▼            ▼
   structured JSON payload (concerns + strategies + statuses + consensus + tasks)
                 ↓
        silent adversarial self-check
                 ↓
        render_review_docx.py →  <one .docx + one same-stem .md>
   ▲
   │
   └──── update → cases.jsonl
```

## 8. Failure handling

- **Empty manuscript / unreadable** — print an in-loop error; do not render.
- **Manuscript + reviewer report conflict** — log to self-check; do not surface.
- **Update overwrites a non-trivial prior snapshot** — diff and require user confirmation.
- **Concerning researcher misconduct / duplicate publication** — defer to editor; do not generate strategy.

The full failure-handling matrix lives in `adversarial-checklist.md`.
