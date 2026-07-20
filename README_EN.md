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

In Codex, say
```powershell
Please install the Skill located at https://github.com/mumdark/nature-review-studio
```

The installation script will:
- Copy `skill/` to `$HOME/.codex/skills/nature-review-studio/`
- Write the current directory to NRS_ROOT (environment variable + persist it to `skill/.nrs_root`)
- Verify that the frontmatter and all 6 references are in place

Total size: **~11 MB**.

### Three interfaces

| Interface | Trigger | Output |
|---|---|---|
| `review` | review / peer review | `review_<case>_<YYYYMMDD>.docx + .md` |
| `respond` | response / reply | `respond_<case>_<YYYYMMDD>.docx + .md` |
| `update` | ingestion / distillation | No docx output; runs the offline pipeline |

`review` and `respond` always produce exactly two files, with no other accompanying artifacts.

## Distillation output mapping

| Distillation output | Where it goes in references | Purpose |
|---|---|---|
| 12 concern axes + default severity | `skill/references/review-axes.md` | Determines "what to ask" |
| 6 manuscript → reviewer set mappings | `skill/references/review-axes.md` | Determines "how many reviewers to assign and what each one covers" |
| 21 response strategies | `skill/references/response-axes.md` | Determines "how to respond" |
| 8 action statuses | `skill/references/response-axes.md` | Determines "the status field in the task table" |

### 1. Twelve concern axes (review issue categories)

**What they are**: A "table of contents" covering all questions reviewers may ask. The Skill manually categorized comments from 1,287 Nature PRFs, merged similar items, removed incidental ones, and arrived at 12 categories.

**Why there are 12**: Too few categories (for example, only "experiments/writing") would be overly broad, making it impossible for review comments to identify "which exact point was questioned"; too many categories (dozens) would instead reduce reusability because each category would have too few samples.

**Observed frequencies** (all comment labels across 1,287 cases were scanned):

| 12 axes | Hits across 1,287 PRFs |
|---|---|
| experimental-design | 6776 |
| figures-and-tables | 6379 |
| claim-moderation | 3824 |
| novelty-significance | 3185 |
| reproducibility | 2751 |
| writing-clarity | 2513 |
| data-resource-quality | 1153 |
| clinical-validity | 1149 |
| mechanism-evidence | 875 |
| mechanistic-vs-correlative | 516 |
| statistical-rigor | 465 |
| ethical-governance | 83 |

**Severity distribution** (`knowledge/index_severity.json`, three levels):

Each axis has three counts: `{major, minor, minor-major}`. For example, `experimental-design`: 572 major / 5991 minor / 213 minor-major. This indicates that the vast majority of experimental-design issues are minor points reviewers mention in passing, but about 9% are still major issues that "must be addressed."

**Example**: Suppose a reviewer reads your manuscript stating, "We found that tumors completely regressed after X gene knockout." The reviewer might raise questions belonging to different axes:

| Actual reviewer question | Which axis it belongs to | Default severity |
|---|---|---|
| A similar conclusion about the X gene was already reported by Nature/Science in 2022 | novelty-significance | major |
| How do you prove that tumor regression was not caused by the downstream Y gene? Add a rescue experiment | mechanism-evidence | major |
| Only one cell line was used; at least three are needed | experimental-design | major |
| n=6 does not constitute adequate power; add a power analysis | statistical-rigor | major |
| Please upload the analysis code | reproducibility | major |
| Has this mechanism been validated in patient samples? | clinical-validity | major |
| The animal ethics/IRB approval number is missing | ethical-governance | major |
| The database annotation files are incomplete | data-resource-quality | minor-major |
| The y-axis of Fig. 3 should run from 0–100% | figures-and-tables | minor |
| The Introduction is too verbose | writing-clarity | minor |
| The conclusion is overstated; "complete regression" is not supported by 100% of the data | claim-moderation | minor-major |
| Correlation ≠ causation; hedging is recommended | mechanistic-vs-correlative | major |

**Where the default severity comes from**: During distillation, the frequency of every reviewer comment in the 1,287 PRFs was counted—issues appearing in ≥ 5% of cases were marked as major candidates; 1–5% as minor-major; and < 1% as minor.

**Why severity is not fixed as major/minor**: The same type of issue may have different severity in different papers. For example, "incomplete database annotations" is major for a data-resource paper but minor for a mechanism paper. Therefore, the system uses three levels—major / minor / minor-major—allowing the Skill to adjust severity up or down based on manuscript type.

### 2. Six manuscript → reviewer set mappings

**What they are**: Based on the paper's "fingerprint" (method type + article type), the Skill decides how many reviewers to assign and what role each reviewer should play.

**Why they are needed**: A Nature paper usually has 2–5 reviewers, and they cannot be assigned arbitrarily. If the assignment is wrong: a clinical paper gets an "ML reviewer" → a pile of irrelevant questions; a pure wet-lab paper gets a "clinical reviewer" → the reviewer has nothing useful to ask; a Review paper gets five mechanism reviewers → resources are wasted.

**Basis for the mapping design**: The Skill analyzed how many reviewers Nature actually assigned to each paper type in 1,287 PRFs and what perspectives those reviewers represented, then summarized them into six typical fingerprints:

| Manuscript fingerprint | How many reviewers | What each reviewer covers |
|---|---|---|
| Pure wet-lab mechanism | 3 | mechanism / experimental-design / figures |
| Cohort + ML clinical | 5 | clinical-validity / ml / statistics / ethics / figures |
| Observation + theory | 3 | mechanism / statistical-rigor / writing |
| Large-scale data + tool | 4 | data-resource-quality / reproducibility / experimental-design / figures |
| Review / Perspective | 2 | novelty-significance / writing-clarity |
| Mixed multi-method | 4–5 | Combined as needed |

**Observed method families** (`knowledge/index_methods.json`, full text of all 1,287 cases was scanned):

| Method family | Number of matching cases among 1,287 PRFs |
|---|---|
| review-theory | 1177 |
| data-resource | 778 |
| ML | 588 |
| wet-lab | 492 |
| omics | 457 |
| imaging | 424 |
| clinical | 413 |
| simulation | 146 |
| unspecified | 20 |

**Example**: If you provide a paper combining "CRISPR screening + single-cell analysis + mouse models + a clinical cohort," the Skill detects four method components (wet-lab + omics + wet-lab + clinical) and automatically assigns 4–5 reviewers, each covering one perspective, rather than mechanically assigning "3 reviewers."

**Why Review / Perspective articles get only 2 reviewers**: These articles contain no new data, so the review focuses on whether "the argument is defensible" and "the writing is clear." Assigning more reviewers would only produce repetitive comments.

### 3. Twenty-one response strategies

**What they are**: An "action dictionary" describing how authors can respond to each reviewer comment. These strategies were extracted from 1,287 real author responses—the same types of concerns repeatedly elicited similar response patterns.

**Why 21 are needed**: Real reviewer responses involve far more than just "add an experiment" and "revise the text." The PRFs revealed 21 distinguishable types of action.

**A. Acceptance/addition strategies** (acknowledge the issue identified by the reviewer and add something)
- acknowledge_and_correct: The reviewer identified a real error → directly acknowledge it and correct it
- clarify_existing_content: The reviewer misread the original text → point out that it is already described in Methods §2.3
- add_textual_explanation: The explanation should be added to the manuscript, not left only in the response letter
- add_reference: Add a missing key reference
- add_method_detail: The Methods section is too brief; add more detail
- add_statistical_analysis: Run an additional statistical analysis on existing data
- add_robustness_analysis: Sensitivity analysis, bootstrap, alternative model
- add_control: Add a control experiment
- add_experiment: Conduct a completely new wet-lab/clinical experiment
- add_validation_dataset: Independent cohort / external validation set
- provide_data_or_code: Upload anonymized data/code

**B. Limitation/adjustment strategies** (reduce the strength instead of adding something)
- moderate_claim: The conclusion is overstated; add hedging (change "suggest" to "indicate")
- change_terminology: Replace one or two overly strong terms
- restructure_figure: Reorganize figures/tables
- move_content_to_supplement: Move content to the SI to save main-text space
- withdraw_claim: Completely remove an unsupported claim

**C. Rejection/delegation strategies** (disagree or defer to the editor)
- explain_infeasibility: The request truly cannot be completed; explain why (resources/time/ethics)
- respectfully_disagree: The reviewer is genuinely mistaken; rebut politely with evidence
- request_editor_adjudication: Reviewers conflict with each other → ask the editor to adjudicate
- defer_to_future_work: The point is valid but beyond the current scope; place it in future work

**Why the design uses this 21-strategy granularity**: Too coarse (only 4–5 types) → tasks cannot be assigned precisely, and the task table becomes full of "other," leaving authors unsure what to do; too fine-grained (dozens of types) → different reviewers/editors use inconsistent terminology, and the same action receives different names. These 21 strategies are the greatest common denominator abstracted from 1,287 PRFs: they cover all real actions while allowing the Skill to select a label directly when writing a JSON payload.

### 4. Eight action statuses (task statuses)

**What they are**: A state machine for tracking "Has this review comment been addressed? To what extent?"

**Why 8 statuses are needed**: A Nature revision letter must track whether each reviewer comment was genuinely addressed, whether the response merely says "we fixed it" without an actual change, or whether nothing was changed. These eight statuses cover every state observed in real PRF author responses and subsequent editorial follow-up.

| Status | Meaning | Trigger condition |
|---|---|---|
| DONE | Completed, and the change is visible in the revised manuscript | The user provides the revised MS and the text matches |
| DRAFTED | Completed, but not yet visible in the revised manuscript | The user says "it has been revised" but does not provide the MS |
| TODO_TEXT | Text needs revision | The strategy is add_textual_explanation, etc. |
| TODO_ANALYSIS | Analysis needs to be run | The strategy is add_statistical_analysis, etc. |
| TODO_EXPERIMENT | An experiment needs to be performed | The strategy is add_experiment, etc. |
| TODO_AUTHOR_CONFIRM | A change is recommended, but author confirmation is required | The Skill is uncertain |
| NOT_FEASIBLE | It truly cannot be done | The strategy is explain_infeasibility |
| PROPOSED_DISAGREEMENT | A respectful disagreement is recommended | The strategy is respectfully_disagree |

## Dual-output rendering contract

- `review` / `respond` must produce exactly two files: `.docx` + a same-stem `.md`
- The `.md` file is a plain-text mirror of the review content/response, with no additional annotation blocks
- Word fonts: use system defaults (Calibri / Microsoft YaHei selected automatically by Office); do not hard-code fonts in the docx
- Bold strategy: use bold only for titles, table headers, confidence lines, task-table ID columns, and evidence-anchor references; all other body text must remain non-bold
- Do not output internal blocks such as "Preface and Compliance Notes," "Claim → Evidence Mapping," "Coverage Notes," "Adversarial Self-Check," or "Disagreement/Severity Escalation/Editorial Decision" (these run only inside the Skill and must not appear in the files)

## Knowledge base scale

- **Overview of the distillation from 1,287 cases**:
  - Observed frequencies of the 12 axes (`knowledge/index_axes.json`) — exactly matches the 12 axis names in references
  - Observed frequencies of the 9 method families (`knowledge/index_methods.json`) — scanned from the full text of all 1,287 cases
  - 12 axes × 3-level severity distribution (`knowledge/index_severity.json`) — classified from reviewer comment text
