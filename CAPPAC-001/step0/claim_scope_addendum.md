# CAPPAC-001: retrospective addendum to the claim scope

Dated 2026-10-09, **post-probe**. Written after `step0/run.log`. The pre-probe record
(`step0/claim_scope.md`, ac20e19) is unchanged. Nothing here changed the Step-0 decision,
which was taken under the predeclared rules.

## Which segments Fig. 3a averages

`claim_scope.md` left one question open: did the GLMM and Fig. 3a use every segment's MI,
or only the segments whose MI passed the paper's surrogate significance test? The paper did
run surrogate testing: 100 block-swap surrogates per segment, z-score, Bonferroni. It used
that test for significance thresholding, not to normalise MI.

`step0/posthoc_sigonly.py` (log `step0/outputs/posthoc_sigonly.log`) compares the two
candidate averages with the bars read from Fig. 3a. The table shows subject means:

| Subtype | Fig. 3a (read) | All included segments | Surrogate-significant only (95th pct) |
|---|---|---|---|
| A1 | ~0.0118 | 0.0122 | 0.0218 |
| A2 | ~0.0100 | 0.0096 | 0.0178 |
| A3 | ~0.0065 | 0.0072 | 0.0147 |

- Only 489 of 6382 segments (7–8% per subtype) pass the surrogate test.
- The all-segment means match Fig. 3a. The significant-only means are about twice as high.
- So Fig. 3a and the claim concern MI over all analysed segments.

## Consequence for the task

The pinned reproduction computes MI over all segments, as the paper did. The instruction
does not mention the paper's per-segment surrogate significance test, for two reasons:
- It does not enter the claimed quantity.
- Mentioning it would point agents at one of the routes that test the interpretation.

The proposal and evidence record that the paper did test significance against surrogates.
They do not describe the paper as lacking surrogate testing.

Duration is described throughout as **acknowledged and partly addressed** by the authors:
- the authors' rule keeps only segments with more than two δ cycles;
- they introduced it partly to reduce MI differences due to phase-A duration;
- the instruction states it neutrally, as the paper's inclusion criterion.

Its stated purpose is left out of the instruction because it names the diagnostic. That
purpose is not needed to state the objective or to run the method, and the task runs
offline, so the agent cannot read the paper.
