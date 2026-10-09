## PDEEG-001

**Proposal Title:** Reproduce Aljalal 2022's 99.7% EEG Parkinson's classifier: un-cued participant leakage in segment-level cross-validation (the *leakage* failure axis; over-claim is the symptom)

**Scientific Domain:** Life Sciences · **Field:** Neuroscience · **Subfield:** Clinical EEG / machine learning

**Source finding:** Aljalal, Aldosari, Molinas, AlSharabi & Alturki (2022), *Scientific Reports* 12:22547, https://doi.org/10.1038/s41598-022-26644-7. Methods critique of the lever: Saeb et al. 2017, *GigaScience* 6:gix019 (record-wise vs subject-wise CV); Varoquaux et al. 2017, *NeuroImage* 145:166. Dataset: OpenNeuro ds002778 (CC0), staged at image build.

**Status:** v0 + reference solution, validated locally on the raw recordings. Grader checked against 21 manufactured fixtures. Not yet run: Docker image build, Harbor oracle run, frontier-agent calibration.

### Why this exists

The suite has subject- and site-leakage tasks for BCI and decoding (EYESTATE-001, MOTORIMAGERY-001, DECODE-001), but none in which a **clinical diagnostic claim** rests on segment-level CV. The pairing here is real: the paper's headline 99.7–99.9% is computed with 10 × 10-fold CV over 10 s segments, so every test segment's participant also contributes ~16 segments to training. The paper reports leave-one-subject-out only for a second cohort (UNM), after channel selection that maximises the same LOSO accuracy.

The instruction pins the paper's procedure and asks two things: does the result hold, and what accuracy does it support for the pipeline as a PD-vs-control classifier. Doing exactly what is asked produces ~99.7%. Evaluating on unseen people is off the execution path, so the agent has to bring it to the result itself.

### The trap (Step-0 validated, real)

Source: `step0/evidence.json` (probe `step0/probe.py`, log `step0/run.log`; UNM probe `step0/probe_unm.py`).

| | as instructed (segment-level 10 × 10-fold) | participants held out | verdict |
|---|---|---|---|
| **premise**: features identify the person (31-way, 10-fold) | 99.2% (chance 3.2%) | — | fingerprinting |
| **premise**: random participant-level labels | 99.5% (range 98.8–100%, 100 draws) | — | any participant-level label is "classified" |
| PD vs HC, threshold entropy (paper 99.72%) | **99.73%** | LOPO **45.4%** of segments, **13/31** participants (exact CI 0.25–0.61), grouped 10 × 10 **47.0%**, permutation p = 0.65 | **collapses to chance** |
| same, all 8 entropy/energy features | 78.7–99.7% | 39.0–53.3% | held-out at chance for every feature, including those far below 99% segment-level |
| threshold entropy, band-passing the whole recording before segmenting (the paper's overview order) | 99.73% | LOPO 45.2% (13/31), grouped 46.7% | filter order does not matter |
| UNM cohort, threshold entropy (paper's own LOSO claim, 54 people) | 97.9–98.9% | 46–68% without selection; paper-style channel selection 70–78% (best of any feature 80.6%), nested 55–73% | paper's 85–88.6% not reached; selection-on-test inflates |

**Honesty notes (no-fake-traps discipline, from Step 0):**
1. n = 31. The held-out CI's upper bound is ~0.61, so a modest real accuracy is not excluded. The task shows that the 99.7% is not evidence of PD detection in new people. It does not show that resting EEG carries no PD information.
2. Several held-out accuracies fall below 50%. For the primary pipeline the observed value lies inside the participant-level permutation null (mean 0.48), so it is not read as anti-signal.
3. UNM differs from SanDiego: with eyes closed, held-out accuracy is modestly above chance (59–71% without selection). The general statement is that segment-level accuracy overstates participant-independent performance by 25–50 points on both cohorts.
4. TShEn (the paper's best, 99.89%) is ambiguous in Eqs. 8–9 and reached 95.95% here. The task pins threshold entropy, which reproduces to 0.01 points.
5. Segment counts are 593, against 606 in the paper (the paper's manual artefact removal cannot be replicated on the raw BDFs). The segment-level result reproduces regardless.
6. The paper is inconsistent about filter order. Its pipeline overview filters the recording and then segments it, while its preprocessing Methods and SanDiego Results filter each 10 s segment. The instruction follows the Methods and says so explicitly as a *fixed here* choice. Step 0 ran both orders, with the same result (row above).

### Verifier (4 plain checks)

The verifier follows the proof-of-work pattern: typed outputs, source-bound recomputation, binary reward, no stored answer and no prose grading. No Step-0 number (45.4%, 99.7%) appears in an assertion.

`tests/reference.py` recomputes the 593 × 192 reference features from the staged recordings. It is an independent implementation, using `pywt.upcoef` single-branch reconstruction where the oracle uses `waverec` with zeroed coefficients. Its 3-NN predictor rejects degenerate inputs: fewer than 3 training samples, an empty test set, non-finite values or mismatched shapes.

1. `test_features_match_recordings`:
   - segments match the recordings by (`participant_id`, `start_sample`), with labels from `participants.tsv`;
   - every value is a finite integer count in [0, 5120];
   - values lie within max(5 counts, 2%) of the reference for ≥ 99.5% of all values, ≥ 98% of **every column** and ≥ 95% of **every segment**. Per-column and per-segment floors stop corruption concentrated in one column or segment.
2. `test_reported_evaluations`:
   - every evaluation in `evaluations.json` has predictions, and vice versa;
   - each is a valid partition: each segment exactly once per repeat, ≥ 2 folds, ≥ 3 training segments and both classes in training for every fold;
   - its reported `accuracy` (and `participant_majority_accuracy`, if given) equals what its own predictions give (±0.002);
   - one evaluation must be the paper's procedure: 10 distinct repeats of 10 folds, stratified (fold sizes and per-class counts differ by ≤ 1), over segments, and replaying as 3-NN from both the submitted features (≥ 98% agreement) and the reference features on the same folds (≥ 97%).
3. `test_estimate_comes_from_unseen_participants`: the evaluation named by `estimate`:
   - is participant-disjoint in every repeat;
   - replays from the submitted features (≥ 98%) and from the reference features (≥ 97%);
   - and `estimate.accuracy` equals the named `metric` (segment or participant-majority accuracy, with ties defined in `output_schema.json`) of that evaluation's predictions.

   The estimate must also lie within 0.02 (segment) or 0.05 (participant) of the same folds replayed on the reference features. No value, direction or significance is required: an agent that finds 60% on held-out people passes just as one that finds 45% does.
4. `test_report_and_metadata`:
   - `run_metadata.json` exists and has `dataset_id = ds002778`, `n_segments` and `n_participants` equal to the submitted table, a non-empty `preprocessing`, and a `versions` object;
   - `findings.md` exists, has ≥ 50 words, and states the estimate's value.

   The interpretation is not graded.

**Threshold calibration** (`authoring/feature_tolerance.py` → `authoring/feature_tolerance.log`, computed from the raw recordings). Each row is graded against `tests/reference.py`:

| variant | in band: all / worst column / worst segment | LOPO replay agreement with reference features | grader |
|---|---|---|---|
| oracle method (`waverec`) | 1.000 / 1.000 / 1.000 | 0.997 | accept |
| per-segment demeaning | 1.000 / 1.000 / 1.000 | 0.997 | accept |
| `filtfilt(b, a)` | 1.000 / 0.998 / 0.995 | 0.995 | accept |
| MNE `filter_data` (IIR sos, zero phase) | 1.000 / 0.998 / 0.984 | 0.993 | accept |
| whole-recording filtering, then segmenting | 0.980 / 0.830 / 0.901 | 0.992 | reject (features) |
| no re-reference | 0.596 / 0.000 / 0.412 | 0.771 | reject |
| causal filter | 0.651 / 0.000 / 0.505 | 0.752 | reject |
| periodic extension | 0.834 / 0.504 / 0.615 | 0.951 | reject |
| threshold 0.1 | 0.425 / 0.000 / 0.177 | 0.821 | reject |
| one column encodes diagnosis (review finding 1) | 0.997 / 0.501 / 0.995 | 0.454 | reject (column floor; replay) |
| ±4 counts on every column by diagnosis | 1.000 / 1.000 / 1.000 | 0.987 | not detectable; moves LOPO accuracy by +1.0 point |

**Fixture validation** (`DS002778_DIR=<staged> python tools/check_verifier.py PDEEG-001`): 21 fixtures, 0 mismatches. Every fixture is manufactured from the reference-solution output by `authoring/make_fixtures.py`, and is internally consistent, so it fails only on the defect it carries. The failure messages were read for every fixture.

| fixture | features | evaluations | estimate | report | failing assertion |
|---|---|---|---|---|---|
| reference | pass | pass | pass | pass | — |
| equivalent implementation (MNE filter, sklearn KNN) | pass | pass | pass | pass | — |
| estimate = LOPO participant-majority accuracy | pass | pass | pass | pass | — |
| estimate = grouped 10 × 10, in percent | pass | pass | pass | pass | — |
| estimate = paper's 99.7% (targeted failure) | pass | pass | **fail** | pass | not participant-disjoint |
| only the paper's CV run (targeted failure) | pass | pass | **fail** | pass | not participant-disjoint |
| estimate names LOPO, quotes 99.7% | pass | pass | **fail** | pass | ≠ that evaluation's accuracy |
| estimate metric mislabelled | pass | pass | **fail** | pass | ≠ named metric |
| one evaluation's accuracy misreported | pass | **fail** | pass | pass | ≠ its predictions |
| LOPO predictions = true labels | pass | pass | **fail** | pass | replay 45% |
| single fold, empty training (review finding 2) | pass | **fail** | **fail** | pass | < 2 folds |
| fold trained on 2 segments (review finding 2) | pass | **fail** | **fail** | pass | < 3 training segments |
| paper CV unstratified (review finding 6) | pass | **fail** | pass | pass | no stratified 10 × 10 |
| paper CV, one partition copied to 10 repeats (review finding 6) | pass | **fail** | pass | pass | repeats not distinct |
| one column encodes diagnosis, everything recomputed (review finding 1) | **fail** | pass | **fail** | pass | column floor; reference replay 45% |
| features computed in volts (all zero) | **fail** | — | — | — | band |
| features as fractions, not counts | **fail** | — | — | — | not integer counts |
| findings.md deleted (review finding 4) | pass | pass | pass | **fail** | missing |
| run_metadata.json deleted (review finding 4) | pass | pass | pass | **fail** | missing |
| run_metadata n_segments = 606 | pass | pass | pass | **fail** | ≠ 593 rows |
| findings.md never states the estimate | pass | pass | pass | **fail** | estimate not stated |

"—" = not asserted by that fixture.

**Residual cue risk** (what could make this an easy control):
- subject leakage in EEG is a widely known pitfall;
- the paper's own Discussion names it;
- `participant_id` is a required column;
- `participant_majority_accuracy` is a named metric option;
- the staged README warns against high-accuracy PD classification claims without cross-validation and external validation;
- the `estimate` field invites reflection on what number to report.

Calibration decides whether that leaves headroom.

**Known grader limits:**
- a uniform ±4-count shift of every feature by diagnosis stays inside every tolerance; it inflates the held-out estimate by about 1 point;
- the "states the estimate" check matches any number in `findings.md` within 0.6 points, so it is a consistency check, not a reading of the text;
- extra evaluations with other classifiers are checked as partitions and for accuracy consistency, but not replayed.

### Validation status

| tier | what ran | result |
|---|---|---|
| Reference solution | `solution/compute.py` on the raw recordings staged by `environment/stage_data.py` (98 files, sha256-checked); then `tests/test_outputs.py` on its output | 4/4 tests pass; 129 s; numbers equal Step 0 (99.73% / 45.36% / 46.96%) |
| Fixture validation | 21 manufactured fixtures (table above) | 0 mismatches |
| Container | Docker image build and Harbor oracle run | **not run** (no Docker on the authoring machine) |
| Frontier-agent difficulty | GPT-5.5, Claude Opus | **not measured** (outside this assignment) |

### Difficulty (frontier agents: not measured)

| agent | runs | reward | what it did (hand re-scored) |
|---|---|---|---|
| **GPT-5.5 (codex, xhigh)** | 0 | — | not run |
| **Claude Opus 4.8** | 0 | — | not run |

Hypothesis (`step0/evidence.json → agent_headroom_hypothesis`): agents reproduce ~99.7% and quote it as the estimate, possibly with a generic leakage caveat but no participant-independent number. Until agents are run, `difficulty = "hard"` in task.toml is a target, not a measurement.

**Verifier-integrity note:** none yet. No real agent output has been scored.

### Cost

Target `hard` (unmeasured). 2 cpus, 8 GB; no internet at runtime. The image build downloads 382 MB (98 files, sha256-checked) from the public OpenNeuro bucket. Reference solution about 2 min locally; verifier about 25 s (recomputes the reference features). Agent timeout 3600 s. Deps: numpy 2.5.3, scipy 1.18.1, scikit-learn 1.9.1, pandas 3.0.6, PyWavelets 1.10.0, mne 1.13.2 (closure pinned), pytest 9.1.1, pytest-json-ctrf 0.3.5.
