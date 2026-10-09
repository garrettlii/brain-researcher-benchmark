# CAPPAC-001: source claim and planned Step-0 scope

Author-private record. Complete this before writing or running the probe (TASK_WORKFLOW
Stage 0.5). Keep the dated pre-probe version; record later changes as new revisions.
Source inspection is not a measured result, and passing this gate does not establish
benchmark difficulty. For an existing task, label a backfilled review as retrospective.

## Source inspection

- Review date and timing (pre-probe or retrospective): TODO(author)
- Primary paper identifier and stable full-text link/artifact: TODO(author)
- Relevant methods/results, figures/captions, tables, and supplement locations inspected:
  TODO(author): list exact locations, including where the claimed range is bounded.
- Missing source material: TODO(author): list it or state none; unavailable required
  material means insufficient_evidence, not permission to infer the claim from an abstract.

## Source-to-task comparison

Use faithful paraphrases with precise source locators. Identify what was computed/plotted
separately from what was claimed. Explain every difference without relying on local results.

| Dimension | Paper's claim/method and exact source locator | Planned task | Match or departure, and rationale |
|---|---|---|---|
| Population and inclusion/exclusion | TODO(author) | TODO(author) | TODO(author) |
| Condition and acquisition | TODO(author) | TODO(author) | TODO(author) |
| Preprocessing, estimator, normalization | TODO(author) | TODO(author) | TODO(author) |
| Time/scale/frequency range and units | TODO(author): computed range AND claimed range; index-to-unit mapping | TODO(author) | TODO(author) |
| Region, outcome, and aggregation | TODO(author) | TODO(author) | TODO(author) |
| Contrast, direction, statistic, uncertainty | TODO(author) | TODO(author) | TODO(author) |
| Interpretation and qualifications | TODO(author) | TODO(author) | TODO(author) |

## Controls and limitations already in the paper

TODO(author): identify the authors' normalized measures, alternative estimators, sensitivity
analyses, relevant supplementary findings, and acknowledged limitations, with locators and
reported outcomes. If none are located, document where you checked. State whether the
proposed diagnostic was already performed and how this changes the task's premise and
headroom hypothesis. Do not portray an existing control as an omission.

## Planned measurement before local outcomes

- Target claim and attribution: TODO(author): source-aligned claim or author-defined extension.
- Disclosed adaptations/extensions and independent scientific rationale: TODO(author).
- Primary RAW comparison (population, condition, estimator, range, contrast): TODO(author).
- PREMISE and CTRL comparisons in that same scope: TODO(author).
- Evidence that would change the interpretation, and evidence that would leave it
  unresolved: TODO(author): include effect size/uncertainty, not only a p-value crossing.
- Exploratory alternatives, kept separate from the primary comparison: TODO(author).
- Stop/reframe condition: TODO(author): e.g. the lever fails in the claimed range; a
  different window cannot be substituted after inspecting its result.

## Decision

TODO(author): proceed_paper_aligned | proceed_author_extension | reframe | archive |
insufficient_evidence. Justify the decision. Only the two proceed decisions permit the
probe; all others stop work here. A reframed question must pass this gate again.

Record the decision, verified source-review status, date, and this file's ArtifactRef in
`step0/evidence.json` under `claim_scope_review`. Scope or primary-comparison changes
require a new dated review; preserve the original and state why it changed.
