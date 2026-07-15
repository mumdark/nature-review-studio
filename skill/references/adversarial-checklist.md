# Adversarial checklist — internal QA, silent

> **V1.2.0 changes**: QA remains internal-only; generated Word files now use built-in styles, Calibri/Microsoft YaHei fonts, and the fixed heading/table/identifier bolding policy.

All 12 checks below run **in the loop** and influence the skill's payload. They
**do NOT** produce output text inside the docx. They are listed here so
maintainers can verify behavior, and so future agents can re-implement them
faithfully.

## A. Review-mode checks

1. **No fabricated fact** — page / figure / p-value / n / acc id must be in the
   manuscript or marked `[unverified]` inside the concern body (not as a separate block).
2. **No invented reviewer identities** — only role labels.
3. **Major concerns have evidence pointers** inline.
4. **Reviewer roles are role-bound**, not bio-bound.
5. **No demand for unrelated experiments**.
6. **Severity is calibrated** — only `Major` and `Minor` survive in the docx;
   `fatal` is internalized to "revision-level band" instead of appearing as a label.
7. **Cross-review overlap < 35 %** — enforced silently during generation.
8. **Decision-prediction text banned** — no `likely-major-revision` / `scope-fit`
   strings emitted to the file.

## B. Response-mode checks

1. **No sub-question lost** — every numbered / lettered sub-question in the
   reviewer comment has a reply entry.
2. **No fabricated evidence** — p-values / sample sizes / figure numbers must
   be in the revised MS or marked `DRAFTED` in the task table.
3. **DONE-label calibration** — `DONE` only when the revised MS actually
   contains the work, or the user has explicitly listed completed items.
4. **No decorative agreement** — every "we agree" must be followed by an action.
5. **Proposals for disagreement** must include evidence, not rhetoric.
6. **Editor letter first sentence** must NOT be a thank-you; it must state the
   revision-level band.
7. **Editor letter body** says nothing about the editor's probable decision.

## C. Update-mode checks

1. **No leakage of names/emails/DOIs/grant numbers** — the pipeline emits an
   `IDENTIFIER CHECK` report alongside each new snapshot. Done by
   `anonymize.py`; verified by counting matches on the audit regex set.
2. **Version diff is monotonic** — never overwrite a stable snapshot without a
   written diff and a `+1` semver bump.
3. **Fail-closed regression** — if a review-mode or respond-mode adversarial
   test fails on a regenerated snapshot, the update must NOT promote the new
   snapshot; it stays in `build/snapshots/staging/`.
4. **No fabricated coverage stats** — corpus profile numbers must come from
   running the pipeline; never quoted from memory.
5. **No raw PDF in the snapshot** — only anonymized JSONL.

## D. Cross-cutting checks

- **Privacy leak alert** — any name, email, DOI, ORCID, NCT, accession, or
  unusual abbreviation is replaced with `[REDACTED]` inside the docx.
- **Output stability** — running the skill twice on the same inputs must
  produce semantically equivalent docx payloads.
- **Honest boundary** — internal use only; **not** emitted to the file.

## E. Test matrix (runnable scenarios)

These scenarios verify the silent checks. Each is runnable against a real PRF:

| # | Scenario | Internal expectation |
|---|---|---|
| 1 | Manuscript already contains what reviewer asked for | Strategy `clarify_existing_content` selected; status `DRAFTED` or `DONE`. |
| 2 | Reviewer misread the manuscript | Strategy `clarify_existing_content`. |
| 3 | Reviewer requests infeasible experiment | Strategy `explain_infeasibility` + status `NOT_FEASIBLE`. |
| 4 | Two reviewers disagree | The disagreement is **NOT** emitted; consensus block only. |
| 5 | Reply claims new experiment but no revised MS | Status downgraded to `DRAFTED`. |
| 6 | New analysis unrelated to concern | Concern stays in the consensus block only if another reviewer independently raised it; otherwise dropped from the docx. |
| 7 | Manuscript text changed but abstract unchanged | Reminder in the editor letter body. |
| 8 | Figure renumbering after revision | Pointer re-resolved or marked `[unverified]` inside the concern body. |
| 9 | Multi-sub-question comment | Concern split into ≥N entries. |
| 10 | PRF contains reviewer name | Replaced with `[REDACTED]` in the docx. |
| 11 | Duplicate PRFs in the update folder | Pipeline dedupes by sha1. |
| 12 | Out-of-order Rounds | Pipeline preserves round IDs, flags `out-of-order` in self-check only. |

## F. Cross-check on revision-level banner

Before the docx render, the silent check confirms:

- The band belongs to `{Major revision, Accept with minor revisions, Reject in present form, Cannot be assessed}`.
- The band is the **first sentence** of the editor letter.
- No decision-prediction phrasing (e.g. "the editor will likely…") appears anywhere.
- No fabricated experiments described as "we have now added" appear in the
  editor letter (only in the task table with proper status).

## G. No-output contract

The skill NEVER writes to the docx the following items, regardless of input:

- A preamble that says "This is a multi-perspective manuscript review…".
- A "Compliance note" / "Coverage note" / "Adversarial critique" block.
- A claim–evidence map dump.
- A divergence / severity-escalation / decision-hint block.
- A round-trip explanation of how the skill works internally.
- Any markdown-only formatting (`**bold**`, `# heading`) inside the docx body — formatting lives in the docx run styles instead.

If the user asks the skill to surface any of these, the skill replies in chat,
not in the file.