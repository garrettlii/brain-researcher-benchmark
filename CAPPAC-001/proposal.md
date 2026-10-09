## CAPPAC-001

**Proposal Title:** Reproduce Yeh & Shi 2018's CAP phase-A coupling ordering (A1 > A2 > A3): an un-cued segment-length bias of the modulation index (the *wrong-cause* failure axis)

**Scientific Domain:** Life Sciences · **Field:** Neuroscience · **Subfield:** Sleep EEG / cross-frequency coupling

**Source finding:** Yeh C-H & Shi W (2018), *Sci Rep* 8:3049, https://doi.org/10.1038/s41598-018-21013-9 (PMC5805690, CC BY 4.0).

- **The lever's methods literature:** the finite-sample dependence of Tort's MI on data length (Tort et al. 2010, *J Neurophysiol* 104:1195).
- **Dataset:** PhysioNet CAP Sleep Database 1.0.0, the paper's own data. Healthy recordings n1–n16, staged and sha256-checked at build.

**Status:** v0 + oracle (local). Docker/Harbor and agent calibration have not run.

### Why this exists

This is the suite's first sleep-EEG task, and its first cross-frequency-coupling task. It uses the
wrong-cause axis in a new modality (Lane E), with the paper's own open data.

The measurement reproduces almost exactly:
- subject-mean MI is .0122 / .0096 / .0072, against Fig. 3a's ~.0118 / .0100 / .0065;
- the A1 − A3 effect is very large (d_z 2.5, p = 4e-8).

But most of the difference comes from how much data each phase-A segment has. A1 segments are
half as long as A3, and the MI of a short segment has a higher no-coupling floor.

The hypothesis is that agents will implement the pinned estimator, see the paper's numbers, and
confirm "strongest coupling in A1". The decisive check is off the requested path: comparing
segment lengths against the estimator's floor. This is a design hypothesis until Stage 5.

### Source claim checked before the probe

Source: `step0/claim_scope.md`, referenced by `step0/evidence.json` → `claim_scope_review`.
- **Status:** verified, pre_probe, 2026-10-09, `proceed_paper_aligned`.
- **Commit order:** committed alone (ac20e19) before the probe (6a12fa7) and the run (96aa82d).
- **Claim:** Control group, δ (0.25–2.5 Hz) phase × α/low-β (10–17 Hz) amplitude, Tort MI with
  20 bins, all phase-A segments with more than two δ cycles, A1 > A2 > A3 (Fig. 3a).
- **Disclosed adaptations:**
  - filter–Hilbert in place of masking EMD, whose settings are under-specified;
  - one central–mastoid derivation;
  - subject-level inference in place of the segment-level GLMM, which is also reported.
- **The authors' existing duration control** is recorded and kept in the measurement. It is the
  >2-δ-cycle inclusion rule, introduced partly "to reduce the differences in MIs due to different
  phase-A durations".
- **Duration is therefore acknowledged and partly addressed by the paper.** The task tests whether
  that rule is enough. It does not treat duration as an omission.

RAW, PREMISE and CTRL all use the recorded scope: same bands, cohort, estimator and inclusion rule.

`step0/claim_scope_addendum.md` is a dated post-probe note. It records that Fig. 3a averages all
analysed segments. The surrogate-significant-only means would be about twice as high (.0218 /
.0178 / .0147), with only 489 of 6382 segments significant.

### Benchmark fit after clarifying the objective

**Public objective:** do these data show the paper's subtype ordering, and support its
conclusion that δ–α/low-β coupling is strongest in A1 and weakest in A3? The unit of
generalisation is the healthy sleeper (n = 16).

Reproducing the number and supporting the interpretation are different things. The
interpretation is a claim about coupling strength, so it requires MI to be comparable across
subtypes.

**The consequential judgement:** is the subtype difference in MI a difference in coupling, or in
segment length?
- **Competing interpretation 1:** A1 α/low-β activity is more tightly locked to δ phase.
- **Competing interpretation 2:** shorter A1 segments carry a higher finite-sample MI floor.
- **Evidence that separates them**, any one of which is sufficient:
  - MI at equal length;
  - MI against each segment's no-coupling floor or surrogates;
  - duration-matched comparisons;
  - MI vs 1/duration within a subtype;
  - duration as a covariate.

**Critical-path test: no.** The pinned method never needs any of the following, and the required
outputs (subject × subtype means and paired contrasts) contain no duration or significance column:
- a length comparison;
- a floor;
- equal windows.

The authors' inclusion rule handles cycles, not equal length, and an agent applies it mechanically.

**Remaining-judgement test.** The four routine routes don't settle it:
- **Formula inspection:** MI = (ln N − H) / ln N says nothing about sample size until one reasons
  about the finite-sample bias of H.
- **Standard recipe:** filter–Hilbert, per-segment MI, paired tests reproduce the ordering.
- **Inspection of the required outputs:** they show a large, consistent effect, A1 > A3 in 16/16
  subjects.
- **Routine contrasts:** A1 − A2, A2 − A3 and A1 S2 − S4 all repeat the length confound, so
  enumerating them does not settle it.

A standard PAC habit is to z-score MI against surrogates, and it would settle the issue: z-scored
A1 − A3 is not significant. That is accepted as a sufficient route; it is not a hidden
requirement.

The judgement is necessary for the stated objective, because the paper's interpretation is
exactly the claim at stake.

**Verdict:** `build_hard_candidate`. Remaining uncertainty:
- PAC-literate agents may z-score MI out of habit.
- An agent that recalls the paper's Methods may follow up the duration rationale. The task runs
  offline, and the instruction states the rule without its rationale.

**Direction and fairness audit.**
- **Left to the analyst:** whether and how to check MI comparability across subtypes.
- **Retained in the instruction:** the source and method information, namely the paper, claim,
  numbers, bands, estimator, inclusion rule, channel and statistics.
- **Neutral evidence requirement:** "If `findings.md` relies on further analyses, save their
  numbers". No diagnostic is named.
- **No fixed key or forced verdict:**
  - The grader passes any length-controlled or surrogate-referenced route linked to the ordering,
    including "mostly length, a small residual may remain" (`floor-mostly-residual`).
  - It does not require a null verdict, or the oracle's 4-s crop.
  - A "length explains everything" answer backed by an equal-length result also passes
    (`artefact-wording`). The data do not contradict it at equal length.
- **On the paper's surrogates:** the per-segment surrogate significance test is omitted from the
  pinned method because it does not enter Fig. 3a (addendum). The paper is never described as
  lacking surrogate testing.

### The trap (Step-0 validated, real)

Source: `step0/evidence.json` (probe `step0/probe.py`, log `step0/run.log`). All rows are n = 16 subjects, A1 − A3, subject-level paired.

| | raw (as instructed) | length controlled | verdict |
|---|---|---|---|
| **premise**: segment duration | A1 6.0 s vs A3 13.2 s (t15 = −14.8) | — | A1 shorter in every subject |
| **premise**: no-coupling floor | +0.00422 [+0.00328, +0.00517] | — | 84% of the raw difference |
| MI, A1 − A3 | +0.00503 [+0.00398, +0.00609], p = 4e-8 | first 4 s: +0.00088 [−0.00068, +0.00243], p = .25 (17%) | **collapses** |
| | | MI − floor: +0.00081 [+0.00022, +0.00139], p = .0099 (16%) | small residual |

The predeclared rule was met. For both controls, the point estimate is ≤ 25% of raw and the upper CI
is < 50% of raw. The verdict is **length bias accounts**.

**Honesty notes (no-fake-traps discipline, from Step 0):**
1. **The residual.** A small A1 > A3 residual survives floor subtraction (p = .0099). It is not
   seen in any of these:
   - crops of 3, 5 and 6 s, or the middle 4 s (all p > .3);
   - 1-s duration bins (p ≈ .09);
   - surrogate z (p = .09 and .17);
   - δ 1–2.5 Hz or F4-C4 (4–16% of raw, p > .13).

   The defensible key is therefore "most of the difference is length; at most a small subtype
   difference remains". "No coupling difference at all" overstates it.
2. **Duration covariate route** (segment-level mixed model, post hoc). A1 − A3 shrinks by:
   - 74% with a linear duration term;
   - 84% with 1/duration;
   - 97% with log duration.

   The linear and inverse fits stay significant only at the segment level, which is
   pseudo-replication. The subject-level residualised contrast is p = .16.
3. **Surrogate significance:** only 7–8% of segments in each subtype pass their own surrogate
   95th percentile, near the 5% chance rate.
4. **Segment counts** exceed Table S2's (3923/1314/1145 vs 2741/829/820). The paper does not say
   what else it excluded. The length gap (7.2 s) is present in every subject.
5. **The paper's secondary "light > deep" claim** behaves the same way within A1: S2 − S4 is
   p = .0001 raw and p = .59 cropped. This is not used in the task.

### Verifier (2 plain checks)

`tests/test_outputs.py`:
1. **Compute check.**
   - A1 − A3 = 0.0050 ± 0.0015 in `subtype_effects.json`, under any key spelling and at any
     depth.
   - A1 − A2 > 0 and A2 − A3 > 0.
   - `subject_mi.csv` covers 15–16 subjects × 3 subtypes, accepting `MCAP-A1`-style labels and
     `mi`/`mean_mi` columns, and agrees with the JSON.
2. **Judgement check.** Within a window of up to three sentences, `findings.md` needs all three:
   - a length or null-reference control: equal or first-N-s windows, matched durations, floor or
     surrogate subtraction or z-scores, MI vs 1/duration, a duration covariate, or the share of
     surrogate-significant segments;
   - a length or null term;
   - the subtype difference either collapsing (no longer significant, does not differ, shrinks to
     N%) or unhedged attributed to length or the floor.

   Before matching, the grader neutralises:
   - the pinned inclusion rule and its purpose clause;
   - surrogate significance-testing descriptions;
   - statements that a check was not performed;
   - negated collapses and attributions.

**Offline discrimination** (`python tools/check_verifier.py CAPPAC-001`): 34 fixtures, 0
mismatches. All are author-written probes with the reference numerical outputs held fixed in
`_base/`; none is an agent run. A further 24 ad-hoc probes were also graded correctly. The
fixtures that should FAIL are:

| fixture | what it is |
|---|---|
| `flat-verdict` | flat confirmation |
| `flat-refutation` | flat refutation |
| `pipeline-names-lever` | "excluded to control for duration; A1 > A3 holds" |
| `rule-purpose-pipeline` | the inclusion rule with its purpose clause |
| `surrogate-significance-pipeline` | surrogate significance testing described as pipeline |
| `zscore-pipeline` | z-scores used only for significance |
| `caveat-one-liner` | "MI depends on data length (Tort 2010)" |
| `description-only` | durations described, not linked |
| `untested-hedge` | "may reflect…; not performed" |
| `asserted-untested` | a mechanism asserted, with the check named as not done |
| `future-work-caveat` | a proposed but unrun check |
| `persists-claim` | claims the difference survives length control |
| `length-controlled-persists` | a length control reported as persistence |
| `z-still-significant` | the surrogate route reported as persistence |
| `cycles-equalise-rebuttal` | "the two-cycle rule suffices", no test |
| `generic-pac-caveats` | volume conduction, waveform shape, power |
| `routine-contrasts` | routine enumeration of contrasts |
| `unequal-boundary` | word-boundary probe on "unequal" / "without correction" |
| `no-longer-collision` | "no longer" / "longer" with a routine correction |
| `z-partial` | a null on A2 only, A1 asserted above both |

The fixtures that should PASS are:

| fixture | route |
|---|---|
| `reference` | the oracle's own findings |
| `concise-crop` | equal-length MI, minimal wording |
| `equal-4s-minimal` | one equal-length result linked to the contrast |
| `surrogate-z-route` | surrogate z-scores |
| `floor-mostly-residual` | "mostly length, a small residual may remain" |
| `slope-and-bins` | MI vs 1/duration and duration bins |
| `chance-share-route` | equal share of surrogate-significant segments |
| `artefact-wording` | stronger "artefact" wording backed by an equal-length result |
| `duration-matched` | duration-matched comparison |
| `tests-rule-adequacy` | tests whether the paper's rule is enough |
| `covariate-route` | duration as a covariate |
| `control-purpose-crop` | a valid crop whose purpose clause resembles the pipeline note |

The compute check has one PASS fixture, `nested-schema`, and one FAIL fixture, `wrong-magnitude`.

**Minimum passing answer** (`equal-4s-minimal`): one sentence giving an equal-length result
linked to the contrast. For example: "At equal 4-s length the A1 − A3 difference is not
significant (p = 0.25)."

That is sufficient for the public objective, because it is the direct test that the
interpretation requires. These answers fail:
- a recalled caveat with no test;
- an untested or hedged mechanism;
- a check named but not run;
- routine contrasts.

A bare ATTR answer ("driven by shorter segments") also needs a control in the window. So an
asserted but untested attribution fails (`asserted-untested`).

### Difficulty (predicted; not yet measured)

Oracle reward: not run in Harbor. Locally, `solution/compute.py` reproduces every Step-0 number
exactly in 46 s on 2 processes, and both tests pass on its outputs.

Frozen task revision and protocol: not yet frozen. The planned protocol is in
`benchmark_spec.json`.
- **Models:** the target model plus a second frontier family.
- **Runs:** un-cued, k ≥ 3 each.
- **Environment:** offline image, 2 CPUs, 8 GB.

| model, reasoning setting, and condition | attempts / genuine passes | reward | what it did (hand re-scored) |
|---|---|---|---|
| not run | — | — | — |

Hand re-score: not run.

**Verifier-integrity note:** no agent runs yet. Several false passes were found while building
the probes and fixed by class. Each now has a FAIL fixture:
- "following" matching an attribution word;
- the inclusion rule's purpose clause supplying a control word;
- "X was not performed" leaving the control word standing;
- hedges earlier in the sentence.

**Disposition:** hard candidate (draft). Uncalibrated.

### Cost

**Difficulty label and evidence state:** target "hard", predicted, with no calibration yet.

**Resources:**
- 2 CPUs and 8 GB memory. The oracle peaks at about 1.6 GB per process, with 2 processes.
- 16 GB storage.
- Network: the 32 files (3.8 GB) are staged offline at build time; there are no runtime
  downloads.
- Timeouts: agent 3600 s, verifier 600 s, build 3600 s.

**Runtimes:** the oracle takes about 1 min locally, and a few minutes is expected in the
container. Agent runtimes are not measured.

**Dependencies:** numpy 2.5.3, scipy 1.18.1 and pandas 3.0.6, plus pytest 9.1.1 for the offline
verifier.
