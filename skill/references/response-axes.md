# Response axes — strategies and failure modes

> **V1.2.0 changes**: Response content keeps the V1.1 contract, while Word rendering now uses built-in styles, Calibri/Microsoft YaHei fonts, and consistent heading/table/identifier bolding.

This document defines how the **author response** is generated, what strategies
are available, and which **failure modes** the skill detects internally (but
does not surface in the final docx).

## A. Strategy taxonomy (21)

Each reviewer comment gets one strategy. Strategies are learned from the PRF corpus:

| Strategy | When appropriate |
|---|---|
| `acknowledge_and_correct` | Reviewer spotted a real error in the manuscript |
| `clarify_existing_content` | Reviewer misread or under-read the manuscript |
| `add_textual_explanation` | The point belongs in the manuscript, not as a new analysis |
| `add_reference` | A prior reference supports the omitted context |
| `add_method_detail` | Methods section needs more detail |
| `add_statistical_analysis` | A reviewer-requested analysis can be run on existing data |
| `add_robustness_analysis` | Sensitivity, alternative model, resampling, etc. |
| `add_control` | A control experiment can address the concern |
| `add_experiment` | A reviewer-required wet-lab or clinical experiment is feasible |
| `add_validation_dataset` | Independent cohort / dataset needed |
| `moderate_claim` | The claim is too strong for the evidence — hedging |
| `change_terminology` | Replace an over-strong word or phrase |
| `restructure_figure` | Re-arrange panels / labeling |
| `move_content_to_supplement` | Promote or demote content for readability |
| `provide_data_or_code` | Make anonymized data or code publicly available |
| `explain_infeasibility` | Request is genuinely not feasible in this revision cycle |
| `respectfully_disagree` | Reviewer is wrong, with evidence |
| `request_editor_adjudication` | Reviewer conflict / scope issue belongs with editor |
| `defer_to_future_work` | The issue is real but out of scope; mark for future study |
| `withdraw_claim` | The claim is not supportable even after analysis |

> Implementer's note: this skill V1.1.0 keeps these as a closed vocabulary. New
> strategies are added only via a manual review.

## B. Action-status taxonomy (8)

| Status | Meaning |
|---|---|
| `DONE` | Verified against revised manuscript or explicit user statement |
| `DRAFTED` | Reply text written, but not yet matched to revised manuscript |
| `TODO_ANALYSIS` | Requires a computational or statistical re-run |
| `TODO_EXPERIMENT` | Requires a wet-lab / clinical / field experiment |
| `TODO_TEXT` | Requires a manual edit of the manuscript text |
| `TODO_AUTHOR_CONFIRM` | Strategy is recommended but author must confirm |
| `NOT_FEASIBLE` | Cannot be done in any reasonable revision |
| `PROPOSED_DISAGREEMENT` | Skill suggests respectful disagreement |

The skill NEVER labels something `DONE` unless the user has supplied a revised
manuscript or explicitly listed completed work. If the user says "we have already
done X" but no revised MS is supplied, the skill flags `DRAFTED` plus a quiet
inline note.

## C. Required output structure (in the docx)

`respond` produces a docx with this **order**:

1. **Editor letter** — ≥150 words, ≤400 words. Start with a one-line **revision-level banner**
   (`Major revision` / `Accept with minor revisions` / `Reject in present form` /
   `Cannot be assessed`) inside a heading. Body covers:
   - thanks
   - summary of major revisions
   - claims whose scope was narrowed
   - reviewer-conflict notes for editor adjudication (only if any)
   - requests that could not be satisfied + reason
2. **Per-reviewer sections** — same shell as `review` (Overall + Major + Minor).
   Inside each Major/Minor block:
   - reviewer original concern (≤30-word paraphrased quote)
   - proposed reply (one paragraph)
   - evidence already in the manuscript (with figure / table / section pointer)
   - if revised-MS supplied: revised-MS pointer
   - if proposed disagreement: structured argument
   - status, confidence, follow-up risk
3. **Cross-review consensus block** — same rules as `review`.
4. **Revision task table** — same columns as `review`.

All copy is in the user's prompt language, technical terms stay in English.

## D. Editor-letter format in the docx

The editor letter is rendered as a single Word **section** with these elements, top to bottom:

- **Heading**: `Editor letter — <revision-level band>` (e.g. `Editor letter — Major revision`).
- **Body paragraph block** (1–4 short paragraphs, separated by blank lines).
- **Close**: `Sincerely,` plus `[Authors]` placeholder line. NO signature block.

Anti-patterns the render script blocks:

- "We have fully addressed all concerns" — never appears.
- Decision predictions ("the editor will likely accept…") — never appears.
- Decorative thanks opening ("First, we would like to thank…") — banned; the
  first sentence must summarize the revision band, not thank.

## E. Failure modes the skill must detect (internal only)

These are checked silently and may DOWNGRADE a strategy from `DRAFTED` to
`TODO_AUTHOR_CONFIRM`, but they never appear as Critic Flag blocks in the docx:

1. **Empty agree** — "we agree with the reviewer" but no action described.
2. **Decorative thanks** — a thank-you with no real concession.
3. **Status inflation** — claim a strategy is DONE without supporting material.
4. **Repeat-the-manuscript** — the reply quotes the manuscript without addressing the concern.
5. **Oversold experiment** — claims a new experiment was added but the revised manuscript has no such section.
6. **Hedge-without-action** — "this is an interesting point" without follow-up.
7. **Over-defensiveness** — disputes a concern using only rhetoric.
8. **Out-of-scope expansion** — adds a major new study unrelated to the concern.
9. **Lost sub-question** — reviewer comment contained multiple sub-points; reply addresses only one.
10. **Status-symbol citation** — adds a citation that does not actually support the claim.

The internal check returns `pass` / `silently-downgrade-N`; render script only
honors the final choice in the docx.