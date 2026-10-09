"""Grading checks for CAPPAC-001 (TODO(author): reproduce <result>).

Ground truth (validated before release, step0/evidence.json; <substrate>, <n>):

  RAW      TODO(author)
  PREMISE  TODO(author)
  CTRL     TODO(author)   -> <collapses | appears | flips>

TODO(author): 2-3 sentences, written like a reviewer's note: what the honest answer
reports, and why.

The failure mode this task targets (un-cued, TODO(author) axis): the agent computes
<result>, gets <face-value verdict>, and reports it flatly, never running
<the volunteered check>. A flat verdict fails; only <the linked insight> passes.
"""
# Keep this file short and human-looking: plain asserts, one comment of ground truth,
# no WEIGHTS / score.json / partial credit. Usually 2 tests: one compute check and one
# judgement check. Every test must pass on the oracle output, and the judgement test
# must fail on every flat or pipeline-naming answer in calibration/fixtures/.
import csv
import json
import os
import re
from pathlib import Path

OUT = Path(os.environ.get("OUTPUT_DIR", "/app/output"))


def _findings():
    return (OUT / "findings.md").read_text(encoding="utf-8").lower()


def _find_key(obj, key):
    """Return the first value stored under `key` at ANY depth. Agents nest numbers
    differently ({"r": ..} vs {"spearman": {"r": ..}}), and a verifier that hard-codes one
    shape fails correct science on format."""
    stack = [obj]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            if key in cur:
                return cur[key]
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)
    return None


def test_TODO_author_computed():
    # Sanity on the numeric deliverable: right n, values in range, both groups present.
    # Canonicalise labels ("Child"/"child"/"kids") and accept any standard spelling.
    rows = list(csv.DictReader(open(OUT / "TODO(author).csv", encoding="utf-8")))
    assert len(rows) >= 120, f"expected ~N subjects, got {len(rows)}"  # TODO(author): real n
    for col in ("TODO(author)",):
        vals = [float(r[col]) for r in rows if r.get(col) not in (None, "")]
        assert len(vals) >= 120 and all(-1.01 <= v <= 1.01 for v in vals), f"{col} invalid"
    # Reproduction genre with a robust number: also assert the number itself, e.g.
    #   r = _find_key(json.loads((OUT / "x.json").read_text()), "r")
    #   assert abs(float(r) - (-0.205)) < 0.05


def test_TODO_author_recognises_TODO_author():
    # TODO(author): one comment line of ground truth, e.g. "the effect collapses under
    # motion control". The insight must be LINKED to the result. Naming the lever is not
    # enough, because the lever's words are also the words agents use to describe their
    # preprocessing ("we regressed 6 motion parameters", "no global signal regression").
    # That collision false-passed SOCIALBRAIN-001 and DEVCONN-001 once each.
    text = _findings()
    # LEVER: the trap/confound vocabulary. Each alternative must be specific to the lever.
    LEVER = r"(?:TODO(author))"
    # RES: tokens that name the RESULT being reproduced.
    RES = r"(?:TODO(author)|effect|result|finding|reproduc)"
    # LINK: words that make the lever the cause of, or the condition for, the result.
    # Never add pipeline vocabulary here (bare "reduc", "regress", "nuisance", "remov").
    LINK = r"(?:confound|artif|spurious|driv\w*|explain\w*|attribut\w*|account\w*|due to|inflat\w*|depend\w*|only (?:with|under))"
    # COLL: what happens to the result once the lever is controlled or toggled.
    COLL = (r"(?:no longer|not signif|not statistically|n\.?s\.|vanish\w*|disappear\w*|attenuat\w*|"
            r"abolish\w*|collaps\w*|null|absent|weaken\w*|not (?:a )?robust)")
    CTRL = r"(?:control\w*|adjust\w*|match\w*|censor\w*|scrub\w*|covar\w*|partial\w*|with|without|under)"

    mentions = re.search(LEVER, text)
    linked = re.search(
        # A) lever <-> link <-> result (both orders)
        rf"{LEVER}[^.\n]{{0,50}}{LINK}[^.\n]{{0,60}}{RES}"
        rf"|{RES}[^.\n]{{0,60}}{LINK}[^.\n]{{0,50}}{LEVER}"
        # B) controlling/toggling the lever changes the result
        rf"|{CTRL}[^.\n]{{0,35}}{LEVER}[^.\n]{{0,110}}{COLL}"
        rf"|{COLL}[^.\n]{{0,90}}{CTRL}[^.\n]{{0,25}}{LEVER}", text)
    assert mentions and linked, (
        "findings.md does not report TODO(author): <the linked insight>. A flat 'reproduces' or "
        "'does not reproduce', or merely naming the lever in the pipeline, misses what this "
        "result actually depends on.")
