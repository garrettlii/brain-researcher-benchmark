## CAPPAC-001

**Proposal Title:** TODO(author): Reproduce <result>: an un-cued <lever> (the *<axis>* failure axis)

**Scientific Domain:** Life Sciences · **Field:** Neuroscience · **Subfield:** TODO(author)

**Source finding:** TODO(author): Author et al. (YEAR), *Journal*, https://doi.org/... ; methods critique of the lever: TODO(author). Dataset: TODO(author) via `TODO(author)`.

**Status:** TODO(author): one of: Step-0 only · v0 + oracle · agent-gated (k=…) · graduated.

### Why this exists

TODO(author): which suite gap this fills (failure axis × dataset × modality; see TASK_BOARD.md),
and why the declared target agents might miss a consequential judgement after the scientific
objective is clear. Keep this a hypothesis; implementation effort and omitted hints do not
by themselves establish difficulty.

### Source claim checked before the probe

Source: `step0/claim_scope.md`, referenced by `step0/evidence.json` → `claim_scope_review`.
TODO(author): record the review date/timing and gate decision, exact claimed range and
contrast, controls already performed by the authors, and independently justified
adaptations/extensions. Confirm RAW/PREMISE/CTRL used that recorded scope. Describe any
later scope changes and new gate decisions. A post-hoc review must be labelled retrospective.

### Benchmark fit after clarifying the objective

TODO(author): recheck the Stage-0.5 source mapping, then apply TASK_WORKFLOW.md Stage 2.
State the public scientific objective and unit of generalisation; the consequential
judgement that remains; the competing interpretations and sufficient evidence to distinguish
them; and why formula inspection,
a standard evaluation recipe, required-output inspection, or routine contrasts do not
already settle the graded issue. Explain why the judgement is necessary for the stated
objective and identify valid alternative reasoning. Record the verdict and remaining
uncertainty; keep this a design hypothesis until calibrated.

**Direction and fairness audit:** TODO(author): identify the diagnostic choices left to
the analyst, the necessary source/method information retained, and the method-neutral
evidence requirements stated publicly. Show that a correct alternative diagnostic or a
supported non-identifiability conclusion can pass. Neither the oracle's preferred method
nor a predetermined rejection of the paper may be an undisclosed requirement.

### The trap (Step-0 validated, real)

Source: `step0/evidence.json` (probe `step0/probe.py`, log `step0/run.log`).

| | raw (as instructed) | lever controlled/toggled | verdict |
|---|---|---|---|
| **premise** TODO(author) | | — | |
| TODO(author) effect | | | **collapses / appears / flips** |

**Honesty notes (no-fake-traps discipline, from Step 0):**
1. TODO(author): variants that did not flip, metrics that were discarded and why.

### Verifier (N plain checks)

`tests/test_outputs.py`: (1) TODO(author): compute check; (2) TODO(author): judgement check, which requires the insight to be *linked to the result*, not merely the lever named.

**Offline discrimination** (`python tools/check_verifier.py CAPPAC-001`):

| fixture | expected | observed |
|---|---|---|
| reference | PASS | |
| flat "reproduces" (+ names the lever in the pipeline) | FAIL | |
| flat "does not reproduce" | FAIL | |
| vague hedge ("<lever> can matter in general") | FAIL | |

**Minimum passing answer:** TODO(author): report probes using reference numerical outputs
with a concise caveat, untested mechanism, or routine contrasts where applicable. State
what the verifier accepts, what evidence is missing, and whether that evidence is needed
for the public objective. Preserve scientifically sufficient concise answers as positives.
These probes are not agent solves. Revisit Stage 2 if a shallow valid answer suffices.

### Difficulty (state whether predicted, pilot, or measured)

Oracle reward: TODO(author) (duration, downloads=0 via cache mount?).

Frozen task revision and protocol: TODO(author): instruction/data/environment/verifier
revision; models and reasoning settings; attempt count, retry policy, and predeclared
difficulty criterion; resource budget and tool/network access; clean-context isolation.
Name the model actually targeted (include Sol 6.1 MAX for a claim about its difficulty)
and another frontier family, confirming settings from raw traces. Separate pilot evidence,
retrospective rescoring, and explicitly cued diagnostic conditions from fresh un-cued runs.

| model, reasoning setting, and condition | attempts / genuine passes | reward | what it did (hand re-scored) |
|---|---|---|---|
| TODO(author): target model/settings, un-cued | TODO(author): every attempt / pass count | | |
| TODO(author): second frontier family/settings, un-cued | TODO(author): every attempt / pass count | | |

Hand re-score: TODO(author): inspect raw trajectories, implementations, and findings.
Record when each agent identified the issue, what evidence it produced, and the scientific
reason for its pass or failure. Separate implementation, verifier/format, and infrastructure
failures from the intended judgement gap. Preserve genuine passes and report observed k/n;
one solve does not estimate the general pass probability.

**Verifier-integrity note:** TODO(author): any false pass found by reading the runs, the fix, and the real sentence that is now a FAIL fixture under `calibration/fixtures/`.

**Disposition:** TODO(author): hard candidate, useful control, reframe, archive, or
insufficient evidence, with the actual support for that verdict. Preserve genuine solves;
a new claim/lever requires renewed source checking, measurement, and frozen calibration.

### Cost

Difficulty label and evidence state: TODO(author): target / pilot / measured; justify
the label above. Resources: cpus TODO, mem TODO GB, network access TODO(author): staged
offline or runtime downloads; timeouts TODO s. Oracle runtime TODO min; agent runtimes
TODO min. Deps: TODO(author).
