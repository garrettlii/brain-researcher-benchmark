## PDEEG-001

**Proposal Title:** Reproduce Aljalal 2022's 99.7% EEG Parkinson's classifier: un-cued participant leakage in segment-level cross-validation (the *over-claim / generalization* failure axis)

**Scientific Domain:** Life Sciences · **Field:** Neuroscience · **Subfield:** Clinical EEG / machine learning

**Source finding:** Aljalal, Aldosari, Molinas, AlSharabi & Alturki (2022), *Scientific Reports* 12:22547, https://doi.org/10.1038/s41598-022-26644-7. Methods critique of the lever: Saeb et al. 2017, *GigaScience* 6:gix019 (record-wise vs subject-wise CV); Varoquaux et al. 2017, *NeuroImage* 145:166. Dataset: OpenNeuro ds002778 (CC0), staged at image build.

**Status:** v0 + oracle (local). Grader calibrated offline against 8 fixtures. Harbor oracle run and frontier-agent calibration not run.

### Why this exists

The suite has subject- and site-leakage tasks for BCI and decoding (EYESTATE-001, MOTORIMAGERY-001, DECODE-001), but none in which a **clinical diagnostic claim** rests on segment-level CV. The pairing here is real: the paper's headline 99.7–99.9% is computed with 10 × 10-fold CV over 10 s segments, so every test segment's participant also contributes ~16 segments to training. The paper reports leave-one-subject-out only for a second cohort (UNM), after channel selection that maximises the same LOSO accuracy.

The instruction pins the paper's procedure and asks two things: does the result hold, and what accuracy does it support for the pipeline as a PD-vs-control classifier. Doing exactly what is asked produces ~99.7%. Evaluating on unseen people is off the execution path, so the agent has to bring it to the result itself.

### The trap (Step-0 validated, real)

Source: `step0/evidence.json` (probe `step0/probe.py`, log `step0/run.log`; UNM probe `step0/probe_unm.py`).

| | as instructed (segment-level 10 × 10-fold) | participants held out | verdict |
|---|---|---|---|
| **premise**: features identify the person (31-way, 10-fold) | 99.3% (chance 3.2%) | — | fingerprinting |
| **premise**: random participant-level labels | 99.5% (range 98.8–100%, 100 draws) | — | any participant-level label is "classified" |
| PD vs HC, threshold entropy (paper 99.72%) | **99.73%** | LOPO **45.4%** of segments, **13/31** participants (exact CI 0.25–0.61), grouped 10 × 10 **47.0%**, permutation p = 0.64 | **collapses to chance** |
| same, all 8 entropy/energy features | 78.7–99.7% | 39.0–53.3% | collapses for every feature |
| UNM cohort, threshold entropy (paper's own LOSO claim, 54 people) | 97.9–98.9% | 46–68% without selection; paper-style channel selection 70–78% (best of any feature 80.6%), nested 55–73% | paper's 85–88.6% not reached; selection-on-test inflates |

**Honesty notes (no-fake-traps discipline, from Step 0):**
1. n = 31. The held-out CI's upper bound is ~0.61, so a modest real accuracy is not excluded. The task shows that the 99.7% is not evidence of PD detection in new people. It does not show that resting EEG carries no PD information.
2. Several held-out accuracies fall below 50%. For the primary pipeline the observed value lies inside the participant-level permutation null (mean 0.48), so it is not read as anti-signal.
3. UNM differs from SanDiego: with eyes closed, held-out accuracy is modestly above chance (59–71% without selection). The general statement is that segment-level accuracy overstates participant-independent performance by 25–50 points on both cohorts.
4. TShEn (the paper's best, 99.89%) is ambiguous in Eqs. 8–9 and reached 95.95% here. The task pins threshold entropy, which reproduces to 0.01 points.
5. Segment counts are 593, against 606 in the paper (manual artefact rejection cannot be replicated on the raw BDFs). The segment-level result reproduces regardless.

### Verifier (2 plain checks)

The verifier follows the proof-of-work pattern: typed outputs, source-bound recomputation, binary reward, no stored answer and no prose grading. `tests/reference.py` recomputes the 593 × 192 reference features from the staged recordings. It is an independent implementation, using `pywt.upcoef` single-branch reconstruction where the oracle uses `waverec` with zeroed coefficients. It also replays any submitted cross-validation from the submitted features and fold assignments with a plain 3-NN vote.

1. `test_features_and_paper_evaluation` (compute) checks three things:
   - the segments match the recordings by (`participant_id`, `start_sample`);
   - ≥ 99% of feature values lie within max(5, 2%) of the reference;
   - a 10 × 10-fold evaluation that is not participant-pure replays at ≥ 98% agreement and matches its reported accuracy.

   The feature tolerance was set from implementation variants of the stated method. These all pass: `filtfilt(b, a)` (100% of values within tolerance), per-segment demeaning (100%) and `upcoef` versus `waverec` (max difference 3 counts). These fail: no re-reference (60%), a causal filter (65%), periodic extension (83%), threshold 0.1 (42%), and whole-recording filtering before segmentation (98.0%).
2. `test_estimate_comes_from_unseen_participants` (judgement, typed) checks the evaluation that `evaluations.json → estimate` names:
   - every participant's segments must sit in one fold in every repeat;
   - the predictions must replay;
   - the estimate must equal that evaluation's segment or majority-vote accuracy.

   No value, direction or significance is required. An agent that finds 60% on held-out people passes just as an agent that finds 45% does.

**Offline discrimination** (`python tools/check_verifier.py PDEEG-001`, 8 fixtures, 0 mismatches):

| fixture | expected | observed |
|---|---|---|
| reference (oracle output) | PASS | PASS |
| estimate = LOPO majority-vote accuracy | PASS | PASS |
| estimate = participant-grouped 10 × 10, written in percent | PASS | PASS |
| estimate = paper's segment-level 99.7% (all evaluations present) | FAIL (estimate) | FAIL |
| only the paper's CV run; its 99.7% is the estimate | FAIL (estimate) | FAIL |
| estimate names LOPO but quotes 99.7% | FAIL (estimate) | FAIL |
| LOPO predictions fabricated as the true labels | FAIL (estimate: replay) | FAIL |
| threshold applied to volts (all counts zero) | FAIL (features) | FAIL |

All failing fixtures are manufactured from oracle output. No real agent text exists yet; the first Harbor runs should be added here.

**Residual cue risk** (what could make this an easy control):
- subject leakage in EEG is a widely known pitfall;
- the paper's own Discussion names it;
- `participant_id` is a required column;
- the staged README warns against high-accuracy PD classification claims without proper validation;
- the `estimate` field invites reflection on what number to report.

Calibration decides whether that leaves headroom.

### Difficulty (MEASURED)

Oracle reward: 1.0 locally (`solution/compute.py` + `tests/test_outputs.py` on the build-time staging output, 130 s). Harbor oracle run in the built image: **not run** (no Docker on the authoring machine).

| agent | runs | reward | what it did (hand re-scored) |
|---|---|---|---|
| **GPT-5.5 (codex, xhigh)** | 0 | — | not run (calibration out of scope for this authoring pass) |
| **Claude Opus 4.8** | 0 | — | not run |

Hypothesis (`step0/evidence.json → agent_headroom_hypothesis`): agents reproduce ~99.7% and quote it as the estimate, possibly with a generic leakage caveat but no participant-independent number.

**Verifier-integrity note:** none yet. No real agent output has been scored.

### Cost

Target `hard` (unmeasured). 2 cpus, 8 GB; no internet at runtime. The image build downloads 382 MB (98 files, sha256-checked) from the public OpenNeuro bucket. Oracle runtime about 2 min locally; verifier about 15 s. Agent timeout 3600 s. Deps: numpy 2.5.3, scipy 1.18.1, scikit-learn 1.9.1, pandas 3.0.6, PyWavelets 1.10.0, mne 1.13.2 (closure pinned), pytest 9.1.1, pytest-json-ctrf 0.3.5.
