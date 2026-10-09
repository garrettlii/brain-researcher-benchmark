# TODO(author): Reproducing <the headline finding> (CAPPAC-001)

<!-- TODO(author): DELETE EVERY COMMENT IN THIS FILE BEFORE SHIPPING. The agent reads this
file verbatim, and tools/check_task.py rejects any leftover comment or TODO marker.

Voice: a condensed methods section written by a colleague, not a spec and not a test.
The un-cued rule is the whole task: name the RESULT to reproduce and pin the analysis
the instruction asks for. Never mention the lever, the confound, robustness,
sensitivity, a multiverse, or how the work is scored. List the lever's vocabulary in
step0/evidence.json -> cue_terms; check_task greps for it here.

Pin everything except the lever (ROIs, atlas, cohort, metric). Leave the lever to
"common practice", using the same sentence the three examples use. -->

## Scientific context

<!-- TODO(author): 1 paragraph. Cite the paper (authors, year, journal, DOI), state the
headline claim in the paper's own terms, and give the reported numbers
(e.g. "reported Spearman r_s ≈ −0.35"). Present it as an established finding. -->

TODO(author)

## Task

<!-- TODO(author): Say exactly what to compute, the way a methods section would:
dataset + fetcher + cohort ("all subjects" / "first 20 subjects"), the atlas/ROIs (with
coordinates if pinned), the measure, and the statistic. Then add the
leave-it-to-the-analyst sentence and the closing honesty line, both verbatim: -->

Using TODO(author) (`TODO(author): fetcher`, **all subjects**), **reproduce this result
and report whether it holds on these data.**

TODO(author): the pinned analysis (atlas/ROIs, measure, statistic).

The standard preprocessing choices the analysis leaves to the analyst (nuisance
regression, temporal filtering, signal normalisation) should follow common practice.

Report, in plain terms, **whether TODO(author): the result reproduces on these data**,
stating only what your analysis actually supports.

## Output Location

Write all outputs to `${OUTPUT_DIR}` (default `/app/output`).

## Required Outputs

<!-- TODO(author): Natural deliverables only: one numeric table, one stats JSON,
run_metadata.json, and findings.md. Do NOT require a column or field for the lever
(DEVCONN's connectivity.csv has no motion column), and do NOT require a rigor-artifact
trio (robustness.json / claim_support.json / ...). Every file listed here must be
written by solution/compute.py. -->

- `TODO(author).csv`: one row per subject:
  `subject_index, age, group, TODO(author)`.
- `TODO(author).json`: TODO(author) statistics as `{"<name>": {"r": ..., "p": ...}}`.
- `run_metadata.json`: dataset id, n subjects, method, and the preprocessing choices
  you made.
- `findings.md`: a short written summary stating whether the result reproduces on
  these data. State only what your analysis actually supports.

## Failure handling

If the dataset cannot be resolved, exit non-zero with `failed_precondition` and a
non-empty reason, and still write parseable `run_metadata.json`, `TODO(author).json`,
and `findings.md`.
