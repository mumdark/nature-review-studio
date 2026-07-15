# Release Notes — v1.4.1

[简体中文](RELEASE_NOTES.md) · **English**

## v1.4.1 — 2026-07-14

### Highlights

- Renamed the skill and release package to `nature-review-studio`.
- Renamed the public interfaces to `Nature_ReviewStudio.review`, `Nature_ReviewStudio.respond`, and `Nature_ReviewStudio.update`.
- Added `NRS_ROOT` as the primary release-root variable while retaining legacy `NRL_ROOT` lookup for compatibility.
- Added synchronized Chinese and English documentation, with Chinese as the default GitHub README.
- Removed the 138 MB `cases.jsonl` corpus and the 125 KB `manifest.tsv` from the release. Runtime review and response rendering do not read either file.
- Reduced the release size from approximately 150 MB to approximately 11 MB.
- Reworked `extract_concerns.py` with explicit raw-to-canonical axis mapping, three-level severity inference, and full-text method-family detection.
- Reduced unspecified method-family assignments from 1,287 to 20 cases.
- Updated the README with measured frequencies across 1,287 peer-review cases.

### Distilled data included

- `knowledge/index_axes.json`: frequencies and mappings for 12 canonical concern axes.
- `knowledge/index_methods.json`: frequencies for nine method families.
- `knowledge/index_severity.json`: three-level severity distributions across the 12 axes.
- `knowledge/snap_full_v1.2.json`: frozen case count and source SHA-256 metadata.

### Validation behavior

- `test_version_pin.py` verifies version `1.4.1`.
- `test_no_identifiers.py` exits successfully with a skip message when the optional offline corpus is absent.
- `test_render_review_docx.py` checks synchronized English and Chinese DOCX rendering when the required document dependencies are available.

### Known limitations

- The release does not include `cases.jsonl`; full-corpus identifier audits and similarity retrieval require a separately authorized local copy.
- Severity labels reflect reviewer wording patterns and should be calibrated for manuscript type and evidentiary context rather than treated as fixed decisions.
