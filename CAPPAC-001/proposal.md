## CAPPAC-001

**Proposal Title:** Reproduce Yeh & Shi 2018's CAP phase-A coupling ordering (A1 > A2 > A3): an un-cued segment-length bias of the modulation index (the *wrong-cause* failure axis)

**Scientific Domain:** Life Sciences · **Field:** Neuroscience · **Subfield:** Sleep EEG / cross-frequency coupling

**Source finding:** Yeh C-H & Shi W (2018), *Sci Rep* 8:3049, https://doi.org/10.1038/s41598-018-21013-9 (PMC5805690, CC BY 4.0).

- **The lever's methods literature:** the finite-sample dependence of Tort's MI on data length (Tort et al. 2010, *J Neurophysiol* 104:1195).
- **Dataset:** PhysioNet CAP Sleep Database 1.0.0, the paper's own data. Healthy recordings n1–n16, staged and sha256-checked at build.

**Status:** v1 + oracle (local), revised after the review of ba56a10 (F1–F5). Docker/Harbor and agent calibration have not run.

### Why this exists

This is the suite's first sleep-EEG task, and its first cross-frequency-coupling task. It uses the
wrong-cause axis in a new modality (Lane E), with the paper's own open data.

The measurement reproduces almost exactly:
- subject-mean MI is .0122 / .0096 / .0072, against Fig. 3a's ~.0118 / .0100 / .0065;
- the A1 − A3 effect is very large (d_z 2.5, p = 4e-8).

But most of the difference comes from how much data each phase-A segment has. A1 segments are
half as long as A3, and the MI of a short segment has a higher no-coupling floor. That floor is
93–99% of the mean MI in every subtype and 84% of the A1 − A3 difference. Above it a small A1 > A2
> A3 ordering remains, so raw MI overstates the subtype difference about sixfold.

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
reading that δ–α/low-β coupling is strongest in A1 and weakest in A3? The unit of
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
A1 − A3 is not significant (same direction). That is accepted as a sufficient route; it is not a hidden
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
    including "mostly length, a small residual may remain" (`floor-mostly-residual`) and "the
    ordering survives but is much smaller" (`survives-smaller`).
  - It does not require a null verdict, or the oracle's 4-s crop. "Not significant at equal
    length" passes as a report of that test (`equal-4s-minimal`).
  - "Largely an artefact" and a bare "an artefact of segment duration" pass (`largely-artefact`,
    `artefact-wording`). Unqualified totality fails: "entirely an artefact", "fully explained",
    "no coupling difference", "the same coupling" (`slope-entirely-artefact`,
    `no-coupling-difference`). The floor-subtracted residual (p = .0099) contradicts these, and a
    non-significant crop is not evidence of no effect.
- **On the paper's surrogates:** the per-segment surrogate significance test is omitted from the
  pinned method because it does not enter Fig. 3a (addendum). The paper is never described as
  lacking surrogate testing.

### The trap (Step-0 validated, real)

Source: `step0/evidence.json` (probe `step0/probe.py`, log `step0/run.log`). All rows are n = 16 subjects, A1 − A3, subject-level paired.

| | raw (as instructed) | length controlled | verdict |
|---|---|---|---|
| **premise**: segment duration | A1 6.0 s vs A3 13.2 s (t15 = −14.8) | — | A1 shorter in every subject |
| **premise**: no-coupling floor | +0.00422 [+0.00328, +0.00517] | — | 84% of the raw difference |
| **premise**: floor share of MI | A1 93%, A2 95%, A3 99% | — | raw MI is mostly floor |
| MI, A1 − A3 | +0.00503 [+0.00398, +0.00609], p = 4e-8 | first 4 s: +0.00088 [−0.00068, +0.00243], p = .25 (17%) | **falls to a sixth**, imprecise |
| | | MI − floor: +0.00081 [+0.00022, +0.00139], p = .0099 (16%) | small residual, same size |

The predeclared rule was met. For both controls, the point estimate is ≤ 25% of raw and the upper CI
is < 50% of raw. The verdict is **length bias accounts**.

**Rule margin (F4).** The margin is narrow. The 4-s crop's upper CI is 48.3% of raw against the
50% bound. Under the same rule:
- the 3-s crop (53.5%), duration-matched 1-s bins (54.1%) and the middle 4 s (49.9%) would have
  been unresolved;
- the 5-s and 6-s crops (32.7%, 24.3%) clear it easily.

L = 4 s was predeclared in `claim_scope.md`, so the verdict stands. The key is worded to match the
margin: most of the ordering is length, and a small residual remains (`evidence.json` →
`controlled_effect.rule_margin`).

**Honesty notes (no-fake-traps discipline, from Step 0):**
1. **The residual (F1).** Above the floor a small A1 > A2 > A3 ordering remains:
   - MI − floor is .00091 / .00050 / .00010;
   - A1 − A3 = +.00081, p = .0099; A1 − A2 p = .087; A2 − A3 p = .066.

   The equal-length estimate (+.00088) is the same size, only less precise. Its p = .25 is not
   evidence of no effect. Duration-matched bins (+.00125, p = .09) and surrogate z (p = .09, .17)
   point the same way. Crops of 3, 5 and 6 s, the middle 4 s, δ 1–2.5 Hz and F4-C4 give smaller,
   non-significant differences (4–16% of raw).

   So every control agrees on the direction and on a small residual; they differ in precision.
   The key is: raw MI is mostly segment length (floor ≈ 93–99% of MI, ≈ 84% of A1 − A3). Above
   the floor a small ordering remains, significant only for A1 − A3 after floor subtraction. Raw
   MI overstates the subtype difference about sixfold and cannot be read as coupling strength.
   "No coupling difference at all" overstates the evidence in the other direction.
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
     depth. The search is breadth-first. Subtrees named raw/primary are preferred, and subtrees
     named after a control (crop, floor, first, equal, z, surrogate, adjusted, …) are read last,
     so a nested control block cannot stand in for the face-value contrast (F3). Rows that name
     their contrast (`{"contrast": "A1 vs A3", ...}`) are read too.
   - A1 − A2 > 0 and A2 − A3 > 0.
   - `subject_mi.csv` covers 15–16 subjects × 3 subtypes, accepting `MCAP-A1`-style labels and
     `mi`/`mean_mi` columns, and agrees with the JSON.
2. **Judgement check**, in three parts.
   - **Contradiction guard (document level, F2a).** Any un-negated, unqualified rebuttal fails the
     answer. Rebuttals are counted against it, not stripped. They include:
     - "not driven / explained by length", "not a length artefact";
     - "independent of / robust to segment length";
     - "length accounts for only a small part", "length explains about a third", "the length bias
       is minor";
     - "the paper's conclusion holds / stands / is supported", "confirms the paper";
     - "remains highly significant / large", "most of the difference survives", "still exceeds"
       when the sentence attaches no small or residual qualifier;
     - "reflects stronger / genuine coupling", "coupling strength", "the difference is real";
     - totality overclaims: "entirely an artefact", "fully explained", "no coupling difference",
       "the same coupling".

     Exemptions: a negation just before the phrase; a residual or small qualifier ("a small
     residual … not explained by length"); "not entirely / not simply"; face-value framing ("at
     face value the paper's conclusion holds"); attribution to the paper ("the authors interpret
     this as reflecting stronger coupling"); and questions, which assert nothing.
   - **Linked explanation.** One sentence must show the subtype difference either collapsing or
     attributed to length or the floor, with a length or null-reference control in that sentence
     or the one before (F2d).
     - Collapse means: no longer significant, does not differ, much smaller, a sixth of the raw
       difference, overstates, "is mostly the floor". A reduction counts only if it is large:
       "by ≥ 50%", "to < 50%", "most" (F2b).
     - Attribution is directional (F2c): the attribution word must be followed within a few
       words by segment length, duration, the floor, bias, surrogates or the estimator ("reflects
       the higher MI floor of short segments"). "Mostly …" works the same way, as do "length
       explains most of the ordering" and "the null MI is 84% of the difference".
     - Controls (F2e): equal or first-N-s windows, matched durations, floor or surrogate
       subtraction, z-scores, comparisons relative to surrogates (numbers may sit in between),
       plain floor or surrogate values with a number ("surrogates reach 0.0113 and 0.0071, 93% and
       99% of the observed means"), MI vs 1/duration, a duration covariate, duration bins, or the
       share of surrogate-significant segments. "Within each subtype" counts only alongside a
       slope, regression or duration.
   - **Saved computation (backstop).** Some A1 − A3 contrast other than the face-value one must
     be saved in the output directory, as the instruction already asks ("save their numbers"). It
     must be at most half the raw difference or have p ≥ .05. JSON or CSV are accepted, under a
     contrast key, in a row naming the contrast, or as a pair of A1/A3 values. This is
     method-neutral, and it stops wording with no computation behind it.

   Before matching the positive patterns (but not the guard), the grader neutralises:
   - the pinned inclusion rule and its purpose clause;
   - surrogate significance-testing descriptions;
   - statements that a check was not performed;
   - negated collapses, controls and attributions.

**Offline discrimination** (`python tools/check_verifier.py CAPPAC-001`): 61 fixtures, 0
mismatches. All are author-written probes with the reference numerical outputs held fixed in
`_base/`; none is an agent run.
- 27 were added in v1 for the review's classes. Ten are reconstructed from quotes in the
  reviewer's held-out probes, noted as such.
- Separately, 106 ad-hoc probes were graded correctly:
  - 78 short texts, including the review's 13 classes and the 24 v0 probes;
  - 14 long agent-style write-ups with headings, tables and a face-value section;
  - 14 schema / backstop layouts.

**v0 FAIL fixtures:**

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

**v1 FAIL fixtures:**

| fixture | what it is |
|---|---|
| `nevertheless-holds` | equal-length null, then "the paper's conclusion holds" (review, F2a) |
| `reduced-only-10` | "reduced by only 10%… remained highly significant" (review, F2b) |
| `small-fraction-15` | "the floor accounts for only a small fraction (15%)" (review) |
| `remained-not-driven` | "remained (p = 0.09), showing it is not driven by length" (review) |
| `physiology-longer-lasting` | "reflects the longer-lasting slow waves"; unrelated "within each subtype" (review, F2c/d) |
| `follows-the-paper` | "follows the paper" next to a duration description (review, F2c) |
| `slope-entirely-artefact` | slopes plus "entirely an artefact… no coupling difference" (review, F1) |
| `no-coupling-difference` | a non-significant crop read as "no difference in coupling" (F1) |
| `length-check-then-endorse` | long form: crop run, then "consistent with the paper's conclusion" |
| `length-explains-a-third` | length credited with a minority share |
| `no-saved-check` | reference text, but no further analysis saved (backstop) |
| `saved-raw-only` | only face-value, duration and floor contrasts saved (backstop) |

**PASS fixtures:**

| fixture | route |
|---|---|
| `reference` | the oracle's own findings |
| `concise-crop` | equal-length MI, minimal wording |
| `equal-4s-minimal` | one equal-length result linked to the contrast |
| `surrogate-z-route` | surrogate z-scores |
| `floor-mostly-residual` | "mostly length, a small residual may remain" |
| `slope-and-bins` | MI vs 1/duration and duration bins |
| `chance-share-route` | equal share of surrogate-significant segments |
| `artefact-wording` | bare "an artefact of segment duration" backed by an equal-length result |
| `duration-matched` | duration-matched comparison |
| `tests-rule-adequacy` | tests whether the paper's rule is enough |
| `covariate-route` | duration as a covariate |
| `control-purpose-crop` | a valid crop whose purpose clause resembles the pipeline note |
| `survives-smaller` | "the ordering survives but is much smaller" (F1) |
| `largely-artefact` | "largely an artefact" (F1) |
| `residual-not-explained` | "a small residual remains that is not explained by length" |
| `not-entirely-length` | "not entirely a length effect… raw MI overstates it sixfold" |
| `one-sixth-overstates` | "one sixth… greatly overstates" (review false negative) |
| `pure-noise-same-length` | noise at matched lengths (review false negative) |
| `z-relative-to-surrogates` | "z relative to 200 time-shifted surrogates" (review false negative) |
| `surrogate-share-of-mi` | "surrogates reach … 93% and 99%" (review false negative) |
| `question-heading` | "## Does the paper's conclusion hold?" heading |
| `face-value-then-length` | long form: face-value agreement, then the length check |
| `table-of-controls` | long form: controls in a markdown table |
| `csv-saved-check` | the length check saved as CSV rather than JSON |

The compute check has four PASS fixtures and one FAIL fixture:
- PASS: `nested-schema`, `control-first-schema`, `contrasts-nested-schema`, `contrast-rows-schema` (F3);
- FAIL: `wrong-magnitude`.

**Minimum passing answer** (`equal-4s-minimal`): one sentence giving an equal-length result
linked to the contrast, with its numbers saved. For example: "At equal 4-s length the A1 − A3
difference is not significant (p = 0.25)."

That is sufficient for the public objective, because it is the direct test that the
interpretation requires. These answers fail:
- a recalled caveat with no test;
- an untested or hedged mechanism;
- a check named but not run;
- routine contrasts;
- a length check followed by an endorsement of the paper's reading.

A bare ATTR answer ("driven by shorter segments") also needs a control in that sentence or the
one before. So an asserted but untested attribution fails (`asserted-untested`).

**Known residual risks:**
- The guard is lexical. An answer can state a rebuttal in a form it does not list and still pass,
  if it also contains a linked control sentence.
- An honest answer that reports its control numbers only in prose, and saves nothing, fails the
  backstop. The instruction asks for the numbers to be saved.

### Difficulty (predicted; not yet measured)

Oracle reward: not run in Harbor. Locally, `solution/compute.py` reproduces every Step-0 number
exactly in 46–80 s on 2 processes, and both tests pass on its outputs.

Frozen task revision and protocol: not yet frozen. The planned protocol is in
`benchmark_spec.json`.
- **Models:** the target model plus a second frontier family.
- **Runs:** un-cued, k ≥ 3 each.
- **Environment:** offline image, 2 CPUs, 8 GB.

| model, reasoning setting, and condition | attempts / genuine passes | reward | what it did (hand re-scored) |
|---|---|---|---|
| not run | — | — | — |

Hand re-score: not run.

**Verifier-integrity note:** no agent runs yet. In v0, several false passes were found while
building the probes and fixed by class. Each now has a FAIL fixture:
- "following" matching an attribution word;
- the inclusion rule's purpose clause supplying a control word;
- "X was not performed" leaving the control word standing;
- hedges earlier in the sentence.

The review of ba56a10 then probed 13 held-out texts. 7 of 7 wrong answers passed and 4 of 6
correct ones failed. v1 fixes these by class (F2a–e, F3) rather than by phrase, and adds the
saved-computation backstop. Each class has fixtures in both directions. The reviewer will re-probe
with a fresh held-out set.

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
