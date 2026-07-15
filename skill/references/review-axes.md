# Review axes & per-reviewer output structure

> **V1.2.0 changes**: Reviewer selection and the 12-axis taxonomy are unchanged; Word rendering now uses built-in styles, Calibri/Microsoft YaHei fonts, and consistent heading/table/identifier bolding.

This document defines **how to choose the reviewer set**, **what axes each reviewer focuses on**, and the **per-reviewer output structure** that the docx must follow.

## A. Concern taxonomy (12 axes)

| Axis | Default severity | What to look for |
|---|---|---|
| `novelty-significance` | major | Mechanism novelty, advance over prior art, cross-discipline interest |
| `mechanism-evidence` | major | Causal claims, rescue experiments, orthogonal evidence |
| `experimental-design` | major | Controls, replicates, conditions, dose-response, batch effects |
| `statistical-rigor` | major | Power, multiple testing, estimator assumptions, pre-registration |
| `reproducibility` | major | Code/data availability, environment pins, random seeds, ablation |
| `clinical-validity` | major | Cohort selection, external validation, sensitivity/specificity, generalizability |
| `ethical-governance` | major | IRB, consent, animal welfare, dual-use, data sharing |
| `data-resource-quality` | minor-major | Completeness, documentation, future usability |
| `figures-and-tables` | minor | Axis labels, statistical overlays, color-blind safety, scale bars |
| `writing-clarity` | minor | Redundancy, jargon, abstract-vs-body consistency |
| `claim-moderation` | minor-major | Overclaim beyond evidence, hedging needed |
| `mechanistic-vs-correlative` | major | Whether correlative claims are reified into causal ones |

## B. Reviewer-set selector

| Manuscript fingerprint → reviewer set |
|---|
| Pure wet-lab mechanism: 3 → `mechanism`, `experimental-design`, `figures` |
| Cohort + ML clinical: 5 → `clinical-validity`, `ml-methods`, `statistics`, `ethics`, `figures` |
| Observational + theory: 3 → `mechanism`, `statistical-rigor`, `writing` |
| Resource (large data + tooling): 4 → `data-resource-quality`, `reproducibility`, `experimental-design`, `figures` |
| Review / Perspective: 2 → `novelty-significance`, `writing-clarity` |

## C. Concern evidence chain

Each concern emitted by the skill **MUST** carry:

- `claim_pointer`: one-line paraphrase of the claim being challenged.
- `evidence_pointer`: section / figure / table / page (page only when verifiable).

If the user provided a PDF and the page can be pinpointed via layout, the
page number is included; otherwise it is omitted. There is **no separate
claim–evidence map dump** in the docx — evidence pointers live inside each
numbered concern.

## D. Per-reviewer output structure (mandatory)

Each reviewer section in the docx MUST follow this shape:

```
### Reviewer X — <Role label>

**Overall.**  <one short paragraph: significance + headline concerns, 60–120 words>

**Major concerns**
1. <one heading line> — <one paragraph body, evidence pointer inline>
2. ...

**Minor concerns**
1. <one heading line> — <one paragraph body>
2. ...

**Confidence:** high | medium | low  (overall confidence across this reviewer's report)
```

Rules:

- **Role label** is role-only (`Mechanism Reviewer`, `Statistical Reviewer`,
  `Clinical Validity Reviewer`, `Reproducibility Reviewer`, `Figures & Tables
  Reviewer`, `Writing & Clarity Reviewer`). Never a name or bio.
- **Overall paragraph** MUST appear before any numbered concern. If absent,
  the docx render script inserts `[Overall missing — please regenerate]`.
- **Major concerns** are ordered by impact (highest first). **Minor concerns**
  follow majors, ordered by impact within their own bucket.
- **Headings of numbered concerns** are short noun phrases
  (e.g. "External validity of biomarker cutoffs",
  "Statistical power for cognitive-stratified subgroup",
  "Figure 3 axis range"). One body paragraph follows each heading.
- Body paragraphs use the user's prompt language; technical terms
  (e.g. `p-value`, `n=`, `ELISA`) stay in English regardless.

### Bilingual mapping

| English heading | 中文对应 |
|---|---|
| `Overall` | `整体点评` |
| `Major concerns` | `主要问题` |
| `Minor concerns` | `次要问题` |
| `Confidence` | `置信度` |
| `Reviewer X — <Role>` | `审稿人 X — <角色>` |

## E. Cross-review consensus (kept) vs divergence / decision (dropped)

The docx keeps only ONE cross-review block:

- **`Cross-review consensus`** — concerns raised by **≥2 reviewers**. Format:
  `Cc.N — <short description> | raised by: Reviewer X, Y | axis: <axis> | severity: major` followed by a 1–3 sentence rationale.

It deliberately does NOT emit:

- Divergence block (concerns raised by only one reviewer).
- Severity escalation/demotion rules.
- Decision-prediction hints (no `likely-major-revision` band, no Nature-fit verdict).
- Claim-evidence map dump.

These are all internal-only: the silent self-check uses them but they never
reach the file. The reason is operational: a reviewer-facing document should
not predict the editor's call, and should not relitigate concerns that are
already on the page.

## F. Revision-level banner (single line, top of editor letter)

The editor letter's first paragraph MUST start with **one** of these four bands:

- `Major revision` — at least one Major concern is open that cannot be answered by a textual fix alone.
- `Accept with minor revisions` — all Major concerns are closable by text or minor analyses.
- `Reject in present form` — the core conclusion is unsupported by the evidence; resubmission would need a different study.
- `Cannot be assessed` — manuscript or required files are missing or unreadable.

The bands are deliberately coarser than a Nature decision letter so that the
skill never claims a verdict that has not been earned.

## G. Revision task table (mandatory, last block in the docx)

A single table with these columns (Chinese equivalents in parentheses):

| ID | Reviewer (审稿人) | Concern (问题) | Strategy (策略) | Status (状态) | Input needed (所需输入) | Output (预期输出) | Blocks response? (是否阻塞) |

- `Status` is one of: `DONE` (only with revised MS), `DRAFTED`, `TODO_ANALYSIS`,
  `TODO_EXPERIMENT`, `TODO_TEXT`, `TODO_AUTHOR_CONFIRM`, `NOT_FEASIBLE`,
  `PROPOSED_DISAGREEMENT`.
- `Blocks response?` is `Yes` for tasks the author must complete before a credible resubmission, otherwise `No`.