"""Reference solution for CAPPAC-001.

TODO(author): one paragraph covering:
  * what the (un-cued) instruction asks: reproduce <result> on <substrate>;
  * what the honest reference VOLUNTEERS that the instruction never asks for: the
    <lever / confound / robustness> check;
  * why a mature analyst would run that check (cite the methods literature, e.g.
    Power 2012 for motion, Murphy 2009 for GSR);
  * the conclusion that follows (the result collapses / only appears under the lever /
    is not robustly determined).

Validated numbers (Step 0, step0/evidence.json; <substrate>, <n>):
  RAW      <effect as the instruction defines it>   : <stat> (p = ...)
  PREMISE  <why the lever matters on THIS data>     : <stat>
  CTRL     <effect under the volunteered check>     : <stat> (p = ...) -> <collapses|appears|flips>

This file is the Step-0 probe (step0/probe.py) promoted to the oracle: same numbers,
plus the task's required outputs. If the oracle's numbers drift from step0/evidence.json,
stop and find out why before going further.
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

OUT = Path(os.environ.get("OUTPUT_DIR", "/app/output"))
OUT.mkdir(parents=True, exist_ok=True)

TASK_ID = "CAPPAC-001"
DATASET_ID = "TODO(author)"


def wj(name, payload):
    (OUT / name).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def fail(reason):
    """Failure handling as promised in instruction.md: parseable outputs, non-zero exit."""
    wj("run_metadata.json", {"task_id": TASK_ID, "dataset_id": DATASET_ID,
                             "status": "failed_precondition", "reason": reason})
    wj("TODO(author).json", {"status": "failed_precondition", "reason": reason})
    (OUT / "findings.md").write_text(f"# Failed precondition\n\n{reason}\n", encoding="utf-8")
    sys.stderr.write(reason + "\n")
    sys.exit(1)


def load_substrate():
    """Fetch the pinned dataset/atlas exactly as instruction.md names it."""
    try:
        from nilearn import datasets
        data = datasets.TODO_author()  # e.g. fetch_development_fmri()  (all subjects)
    except Exception as e:  # noqa: BLE001
        fail(f"could not resolve {DATASET_ID}: {e}")
    return data


def primary_analysis(data):
    """Exactly the analysis instruction.md asks for, with defensible 'common practice'
    preprocessing. Return a per-subject DataFrame plus whatever covariates the
    volunteered check needs. Keep those covariates (e.g. mean FD) OUT of the required
    CSV, so the output schema does not cue the lever."""
    rows = []
    # TODO(author): per-subject extraction -> measure
    return pd.DataFrame(rows)


def primary_stats(df):
    """The headline statistic(s) at face value, as the instruction defines them."""
    # TODO(author): e.g. r, p = stats.spearmanr(df.age, df.measure)
    return {}


def volunteered_check(df):
    """The check the task never asks for: run the analysis with the lever controlled
    or toggled (FD covariate + motion-matched subsample, +/-GSR, a multiverse over
    band-pass x subsample, ...). This is the scientific content of the task."""
    # TODO(author)
    return {}


def write_findings(df, primary, check):
    """The write-up a careful researcher would leave. It must LINK the lever to the
    RESULT ("the age effect is no longer significant once mean FD is controlled"),
    because that link is what tests/test_outputs.py grades."""
    (OUT / "findings.md").write_text(f"""# CAPPAC-001: TODO(author)

## The result at face value
TODO(author): primary numbers.

## The check the result needs
TODO(author): premise + the controlled/toggled numbers.

## Conclusion
TODO(author): only what the analysis supports.
""", encoding="utf-8")


def main():
    data = load_substrate()
    df = primary_analysis(data)
    if len(df) < 1:  # TODO(author): the real minimum usable n (e.g. 120 of 155)
        fail(f"only {len(df)} subjects processed")

    # required outputs. Write exactly the schema that instruction.md promises.
    df[["subject_index", "TODO(author)"]].to_csv(OUT / "TODO(author).csv", index=False)
    primary = primary_stats(df)
    check = volunteered_check(df)
    # Extra keys (e.g. "motion_control") are fine to add to the stats JSON; they are not
    # required, so they cue nothing.
    wj("TODO(author).json", {**primary, "TODO(author)_check": check})
    wj("run_metadata.json", {"task_id": TASK_ID, "status": "ok", "dataset_id": DATASET_ID,
                             "n_subjects": int(len(df)),
                             "preprocessing": "TODO(author)", "method": "TODO(author)"})
    write_findings(df, primary, check)
    # One line in the oracle log. Compare it against step0/evidence.json.
    print(f"OK: n={len(df)} primary={primary} check={check}")


if __name__ == "__main__":
    main()
