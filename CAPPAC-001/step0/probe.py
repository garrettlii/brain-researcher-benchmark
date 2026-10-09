"""Step-0 probe for CAPPAC-001: a throwaway script, NOT the oracle.

Prerequisite: complete step0/claim_scope.md against the primary full text and relevant
supplements BEFORE writing/running this probe. In evidence.json, claim_scope_review must
record status=verified and decision=proceed_paper_aligned or proceed_author_extension,
with a dated, hash-bound record. A missing source or ungrounded scope change stops work.
The author must check the science; a status field alone does not validate the premise.

Purpose: before the benchmark is authored, measure on the obtainable data
  1. RAW:     does the declared source-aligned claim (or explicitly justified author
              extension) reproduce in the scope recorded before local outcomes?
  2. PREMISE: is the lever/confound actually present in THIS data (e.g. children move
              more; global signal is large)?
  3. CTRL:    does controlling or toggling the lever change the interpretation in that
              SAME scope? Assess effect sizes/uncertainty, not just a p-value crossing.
If the lever fails in the declared range, a result in another window cannot rescue the
paper-derived trap. Record an easy-control, reframe, or archive decision in evidence.json.
For a reframe, return to the source-claim gate before a new probe. Preserve all outcomes.

Run it so the log and the environment are captured next to the numbers:

    python step0/probe.py 2>&1 | tee step0/run.log
    python -m pip freeze > step0/outputs/pip_freeze.txt

Then copy the numbers into step0/evidence.json and bind each one to its files with
`python tools/artifact_ref.py <file>`. Keep the outputs small (metrics JSON/CSV), never
NIfTIs or caches.
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

metrics = {}

# 0. SOURCE CHECK: TODO(author): finish claim_scope.md and its evidence.json record first.
# Use its primary comparisons unchanged; identify exploratory alternatives separately.

# 1. RAW: TODO(author)
# metrics["raw"] = {"stat": r, "p": p, "n": n}

# 2. PREMISE: TODO(author)
# metrics["premise"] = {...}

# 3. CTRL: TODO(author). Try several defensible variants and report all of them, not
#    just the one that flips. A lever that flips under only one of five variants is
#    fragile, so write that down in evidence.json.
# metrics["controlled"] = {...}

(OUT / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True))
print(json.dumps(metrics, indent=2, sort_keys=True))
