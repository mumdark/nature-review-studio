# Source basis — what the skill has actually learned

> **V1.2.0 changes**: The production knowledge snapshot expands from the 50-case baseline to all 1287 local Nature PRF PDFs, with anonymization audit, SHA256 provenance, and distilled axis/method/severity indexes.

This document is the **provenance record** for the skill. It enumerates exactly
what data is used to build the knowledge base, what is in scope, and what is
out of scope.

## 1. Distilled knowledge snapshot (V1.1.0)

The skill ships with a snapshot from the project workspace:

```
build/samples/sample_50/cases.jsonl      50 PRF cases, anonymized
build/samples/sample_50/manifest.tsv     provenance + sanity stats
```

Each `cases.jsonl` row is a structured Case with:

```json
{
  "case_id": "<sha1(folder+name)[:10]>",
  "source_pdf": "<absolute path>",
  "corresponding": "[REDACTED]",
  "open_access": true,
  "review_rounds": [
    {"round_id": "R0", "version": 0, "reviewer_reports": [
        {"referee": "#1",
         "sub_comments": [{"sub_label": "1", "text": "...", "concern_labels": ["clinical", "writing"]}]}
    ]}
  ],
  "author_responses": [
    {"referee": "Reply to reviewer 1", "para_index": 0,
     "text": "...", "response_labels": ["added_analysis", "thank_reviewer", "undertook_revision"]}
  ],
  "doi": "",
  "journal": "Nature"
}
```

The skill uses **only** aggregations over the snapshot, never verbatim sentences
copied into the docx.

## 2. What's in scope

| Concept | In scope? | Notes |
|---|---|---|
| Concern categories (12) | yes | hard-coded in `review-axes.md §A` |
| Strategy categories (21) | yes | hard-coded in `response-axes.md §A` |
| Failure-mode categories (10) | yes | hard-coded in `response-axes.md §E` (internal use) |
| Field ontology (`wet-lab`, `clinical`, `imaging`, `ML`, …) | yes | |
| Reply patterns (10) | yes | |
| Severity calibration | yes | majority vote over the snapshot |
| Verbatim sentences from PRF | NO | never copied into docx output |
| Names / emails / DOIs / grant numbers | NO | stripped before storage |
| Predicted Nature decision | NO | only the bounded band is allowed |
| Specific Nature editor / journal style | NO | only abstract patterns used |

## 3. Building or extending the snapshot

Run from the project root:

```bash
python nature_open_peer_review/build/pipeline/run_pipeline.py ^
  --input nature_open_peer_review/PDFs/Nature/2025 ^
  --out nature_open_peer_review/build/snapshots/snap_YYYYMMDD ^
  --anonymize ^
  --doi-catalog nature_open_peer_review/Nature_catalog.tsv
```

For incremental updates:

```bash
python nature_open_peer_review/build/pipeline/run_pipeline.py ^
  --input nature_open_peer_review/PDFs/Nature/2026 ^
  --out nature_open_peer_review/build/snapshots/snap_YYYYMMDD_v2 ^
  --anonymize ^
  --doi-catalog nature_open_peer_review/Nature_Communications_catalog.tsv
```

then run the snapshot diff (added in V1.2) to merge into the active snapshot.

For the full 1287-PDF batch:

```bash
powershell -ExecutionPolicy Bypass -File nature_open_peer_review/build/pipeline/run_full_batch.ps1
```

## 4. Adversarial snapshot validation

Every snapshot must pass:

- `tests/test_no_identifiers.py` — no names/emails/DOIs in the case file
- `tests/test_round_consistency.py` — round_ids are monotonic and non-decreasing
- `tests/test_rebuttal_pairs.py` — each rebuttal paragraph is anchored to a reviewer comment

Tests live under `build/pipeline/tests/` and can be added by maintainers who
follow the same harness.

## 5. Out of scope (current V1.1.0)

- The full 1287-PDF batch distillation (compute-bound; expected ~30–60 min on
  a single CPU). To run now, drop `--limit 50`.
- Predicted-Nature-decision modelling.
- Multi-modal reviewer identity resolution across rounds.
- Live rerank against reviewer histories.

## 6. Maintenance checklist

- [ ] On every snapshot: re-run identifier-leak tests.
- [ ] On every snapshot: re-run round-consistency tests.
- [ ] On every snapshot: re-run rebuttal-pair tests.
- [ ] On user request: full snapshot diff with previous stable.
- [ ] On user request: export aggregate patterns only (no original sentences).