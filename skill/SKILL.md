---
name: nature-review-studio
description: >-
  Multi-perspective manuscript review and point-by-point response generation,
  distilled from 1287 Nature Peer-Review-File PDFs (2025–2026). Review and
  respond each produce exactly two synchronized deliverables: one formal DOCX
  and one clean Markdown file with the same base name. Output language follows
  the user's prompt. Also trigger on 多视角审稿、高水平审稿、Nature 风格审稿、
  审稿回复、逐条回复、修订程度、修改任务表、蒸馏审稿语料、审稿知识库更新。
version: 1.4.1
inputs:
  - manuscript (PDF / DOCX / TXT)
  - reviewer_reports (optional PDF / DOCX / TXT)
  - revised_manuscript (optional PDF / DOCX / TXT)
  - target_journal (optional string)
  - update_payload (optional PDF folder or PRF archives)
  - language (auto-detected; optional override en | zh)
outputs:
  - exactly one formal .docx file for review or respond
  - exactly one same-stem .md companion for review or respond
  - update_report for update only
references:
  - references/workflow.md
  - references/review-axes.md
  - references/response-axes.md
  - references/adversarial-checklist.md
  - references/source-basis.md
  - references/render-docx.md
---

# Nature Review Studio

> V1.4.0: full 1287-case knowledge base, simplified Word styling, and a locked two-file output contract.

## Interfaces

| Interface | Purpose | User-facing outputs |
|---|---|---|
| `Nature_ReviewStudio.review` | Generate 2–5 independent reviewer reports from a manuscript | one `.docx` + one same-stem `.md` |
| `Nature_ReviewStudio.respond` | Generate editor letter, point-by-point responses, and revision tasks | one `.docx` + one same-stem `.md` |
| `Nature_ReviewStudio.update` | Ingest, anonymize, distill, index, benchmark, and version new PRF material | update report and internal knowledge artifacts |

## Locked output contract

For `review` and `respond`, create exactly two synchronized user-facing files:

- `build/output/<entry>_<case>_<YYYYMMDD>.docx`: formal Word deliverable.
- `build/output/<entry>_<case>_<YYYYMMDD>.md`: clean Markdown companion.
- The two files must use the same language, section order, reviewer numbering,
  concerns, consensus content, and revision task table.
- Do not create separate preamble, compliance, claim–evidence, coverage,
  adversarial-check, divergence, severity-change, or editor-decision files.
- Markdown output is mandatory. Do not expose or use a `--no-md` mode.

## Formal content order

1. Editor letter and revision-level banner.
2. Each reviewer in `Overall assessment` followed by numbered `Major concerns`
   and `Minor concerns`.
3. Cross-review consensus, without divergence or editor-decision hints.
4. Revision task table.

Internal compliance checks, source coverage, claim–evidence mapping, and
adversarial review remain silent and are never inserted into either deliverable.

## Language

Use the language of the user's request unless the user explicitly requests a
different output language. Chinese requests return Chinese DOCX and Markdown;
English requests return English DOCX and Markdown.

## Rendering

Use `nature_open_peer_review/build/pipeline/render_review_docx.py`. It writes the
DOCX and the mandatory same-stem Markdown companion in one invocation. Report
both absolute paths to the user after successful generation.

Word styling follows the current V1.4 renderer: system-default fonts, black text,
no forced hyperlink decoration, and bold limited to headings, table headers,
confidence lines, task IDs, and evidence anchors.

## Knowledge use

- `review`: retrieve concern axes, method checks, severity priors, reviewer-set
  patterns, and structurally similar historical cases.
- `respond`: retrieve response strategies, action statuses, resolution patterns,
  and second-round follow-up risks.
- Never copy historical reviewer sentences verbatim or expose case identities.

Read the references for workflow details and silent quality-control rules.
