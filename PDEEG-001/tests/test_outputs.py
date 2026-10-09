"""Grading checks for PDEEG-001 (Aljalal et al. 2022, threshold-entropy PD classification).

Ground truth (step0/evidence.json; ds002778, 16 HC + 15 PD off medication, 593 segments):

  RAW      the paper's 10 x 10-fold CV over segments                : 99.7% (paper 99.72%)
  PREMISE  the features identify the participant (31-way, 10-fold)  : 99.2%, and random
           participant-level labels also score 99.5% under segment-level CV
  CTRL     leave-one-participant-out, same features and classifier  : 45.4% of segments,
           13/31 participants, permutation p = 0.65  -> collapses to chance

The paper's folds put segments of the same person in both training and test sets, so
the 99.7% measures recognition of people already seen in training. A PD classifier's
accuracy has to come from people held out of training, and on these data that is chance.

Nothing here is a stored answer and no number above is asserted. Features are recomputed
from the staged recordings (tests/reference.py). Every cross-validation is checked as a
valid partition, and its accuracy is recomputed from the submitted predictions. The
evaluations that carry the result (the paper's, and the one behind the estimate) are
replayed twice: from the submitted features, and from the reference features on the
submitted folds. No value, direction or significance of the estimate is required. It only
has to come from a cross-validation in which no participant has segments in both training
and test, and it must match what that cross-validation gives.

The failure mode this task targets (participant leakage in the evaluation): the agent
reproduces 99.7% with the paper's protocol and reports it as the pipeline's accuracy,
never evaluating on unseen people.
"""
import functools
import json
import math
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference import FEATURES, SEG, knn3_predict, majority_vote_accuracy, reference_segments  # noqa: E402

OUT = Path(os.environ.get("OUTPUT_DIR", "/app/output"))
# Feature agreement, set from authoring/feature_tolerance.log: equivalent implementations of
# the stated method keep >= 99.99% of values, >= 99.8% of every column and >= 98.4% of every
# segment inside the band; whole-recording filtering, no re-reference, causal filtering,
# periodic extension, another threshold, or one manipulated column all fall below at least one.
BAND_ALL, BAND_COLUMN, BAND_SEGMENT = 0.995, 0.98, 0.95
# 3-NN replay: equivalent implementations agree with reference-feature predictions on >= 99.3%
# of segments; a table with one diagnosis-coded column agrees on 45%.
AGREE_SUBMITTED, AGREE_REFERENCE = 0.98, 0.97
ACC_TOL = 0.002


def _group(v):
    s = str(v).strip().lower()
    return {"pd": "PD", "1": "PD", "1.0": "PD", "hc": "HC", "0": "HC", "0.0": "HC"}.get(s, s)


def _fraction(a):
    a = float(a)
    return a / 100 if a > 1 else a


@functools.lru_cache(maxsize=1)
def submission():
    for f in ("segments.csv", "cv_predictions.csv", "evaluations.json"):
        assert (OUT / f).is_file(), f"{f} is missing"
    seg = pd.read_csv(OUT / "segments.csv", dtype={"segment_id": str, "participant_id": str})
    missing = [c for c in ["segment_id", "participant_id", "group", "start_sample"] + FEATURES if c not in seg.columns]
    assert not missing, f"segments.csv lacks columns {missing[:5]}"
    seg["group"] = seg["group"].map(_group)
    assert seg.segment_id.is_unique, "segment_id is not unique"
    pred = pd.read_csv(OUT / "cv_predictions.csv", dtype={"evaluation_id": str, "segment_id": str})
    missing = [c for c in ("evaluation_id", "repeat", "fold", "segment_id", "predicted_group") if c not in pred.columns]
    assert not missing, f"cv_predictions.csv lacks columns {missing}"
    pred["predicted_group"] = pred["predicted_group"].map(_group)
    ev = json.loads((OUT / "evaluations.json").read_text(encoding="utf-8"))
    return seg, pred, ev


@functools.lru_cache(maxsize=1)
def aligned():
    """Submitted segments in reference order, with submitted and reference feature matrices."""
    seg, _, _ = submission()
    meta, ref_X = reference_segments()
    key = list(zip(meta.participant_id, meta.start_sample))
    by_key = seg.set_index(["participant_id", "start_sample"])
    assert by_key.index.is_unique and set(by_key.index) == set(key), (
        "segments do not match the staged recordings by (participant_id, start_sample)")
    rows = by_key.loc[key].reset_index()
    return rows, rows[FEATURES].to_numpy(float), ref_X, meta


def listed(ev):
    out = {}
    for e in ev.get("evaluations", []):
        eid = str(e.get("evaluation_id"))
        assert eid not in out, f"evaluation {eid!r} is listed twice"
        out[eid] = e
    return out


@functools.lru_cache(maxsize=None)
def check_evaluation(eid):
    """Validate one cross-validation's partitions and recompute it from its predictions."""
    _, pred, _ = submission()
    rows_all, X_sub, X_ref, _ = aligned()
    rows = pred[pred.evaluation_id == eid]
    assert not rows.empty, f"no predictions for evaluation {eid!r}"
    assert set(rows.predicted_group) <= {"PD", "HC"}, f"{eid!r}: predictions must be PD or HC"
    for col in ("repeat", "fold"):
        v = pd.to_numeric(rows[col], errors="coerce")
        assert v.notna().all() and (v == v.round()).all(), f"{eid!r}: {col} must be an integer"
    index = {k: i for i, k in enumerate(rows_all.segment_id)}
    y = rows_all.group.to_numpy()
    pid = rows_all.participant_id.to_numpy()
    r = dict(seg_acc=[], vote_acc=[], ref_seg_acc=[], ref_vote_acc=[], agree_sub=[], agree_ref=[])
    disjoint, stratified, n_folds, partitions = True, True, set(), []
    for rep, rr in rows.groupby(rows["repeat"].astype(int)):
        assert rr.segment_id.is_unique and set(rr.segment_id) == set(index), (
            f"{eid!r} repeat {rep}: every segment must be predicted exactly once")
        ii = rr.segment_id.map(index).to_numpy()
        fold = rr.fold.astype(int).to_numpy()
        folds = np.unique(fold)
        assert len(folds) >= 2, f"{eid!r} repeat {rep}: a cross-validation needs at least two folds"
        got = rr.predicted_group.to_numpy()
        sub, ref = np.empty(len(ii), dtype=object), np.empty(len(ii), dtype=object)
        for f in folds:
            te, tr = fold == f, fold != f
            assert tr.sum() >= 3, f"{eid!r} repeat {rep} fold {f}: fewer than 3 training segments"
            for cls in ("PD", "HC"):
                assert (y[ii[tr]] == cls).any(), f"{eid!r} repeat {rep} fold {f}: no {cls} segment in training"
            sub[te] = knn3_predict(X_sub[ii[tr]], y[ii[tr]], X_sub[ii[te]])
            ref[te] = knn3_predict(X_ref[ii[tr]], y[ii[tr]], X_ref[ii[te]])
        r["agree_sub"].append(np.mean(sub == got))
        r["agree_ref"].append(np.mean(ref == got))
        r["seg_acc"].append(np.mean(got == y[ii]))
        r["ref_seg_acc"].append(np.mean(ref == y[ii]))
        r["vote_acc"].append(majority_vote_accuracy(got, y[ii], pid[ii]))
        r["ref_vote_acc"].append(majority_vote_accuracy(ref, y[ii], pid[ii]))
        disjoint &= all(len(set(fold[pid[ii] == p])) == 1 for p in np.unique(pid))
        # stratified k-fold: fold sizes, and each class's count per fold, differ by at most one
        sizes = pd.Series(fold).value_counts()
        per_class = pd.crosstab(fold, y[ii])
        stratified &= bool(sizes.max() - sizes.min() <= 1 and (per_class.max() - per_class.min()).max() <= 1)
        n_folds.add(len(folds))
        partitions.append(frozenset(frozenset(rr.segment_id[fold == f]) for f in folds))
    out = {k: float(np.mean(v)) for k, v in r.items()}
    out.update(disjoint=disjoint, stratified=stratified, n_repeats=len(partitions),
               n_folds=n_folds.pop() if len(n_folds) == 1 else None,
               distinct_repeats=len(set(partitions)) == len(partitions))
    return out


def test_features_match_recordings():
    rows, X, X_ref, meta = aligned()
    assert len(rows) == len(meta), f"expected {len(meta)} segments, got {len(rows)}"
    assert (rows.group.to_numpy() == meta.group.to_numpy()).all(), "group labels do not match participants.tsv"
    assert np.isfinite(X).all(), "non-finite feature values"
    assert ((X == np.round(X)) & (X >= 0) & (X <= SEG)).all(), (
        f"threshold entropy is a count of samples: every value must be an integer in [0, {SEG}]")
    close = np.abs(X - X_ref) <= np.maximum(5, 0.02 * X_ref)
    worst_col, worst_seg = close.mean(0).argmin(), close.mean(1).argmin()
    assert close.mean() >= BAND_ALL, f"only {close.mean():.2%} of feature values match the stated method"
    assert close.mean(0).min() >= BAND_COLUMN, (
        f"column {FEATURES[worst_col]} matches the stated method for only {close.mean(0).min():.1%} of segments")
    assert close.mean(1).min() >= BAND_SEGMENT, (
        f"segment {rows.segment_id[worst_seg]} matches the stated method for only {close.mean(1).min():.1%} of features")


def test_reported_evaluations():
    # Every listed evaluation must be a valid cross-validation whose reported accuracy is what
    # its own predictions give; the paper's stratified 10 x 10-fold over segments must be among
    # them and must be the stated KNN pipeline.
    _, pred, ev = submission()
    evals = listed(ev)
    assert evals, "evaluations.json lists no evaluations"
    assert set(evals) == set(pred.evaluation_id), (
        f"evaluations.json and cv_predictions.csv disagree: {sorted(set(evals) ^ set(pred.evaluation_id))}")
    paper = []
    for eid, e in evals.items():
        c = check_evaluation(eid)
        assert math.isclose(_fraction(e["accuracy"]), c["seg_acc"], abs_tol=ACC_TOL), (
            f"{eid!r}: reported accuracy {e['accuracy']} != {c['seg_acc']:.4f} from its predictions")
        if e.get("participant_majority_accuracy") is not None:
            assert math.isclose(_fraction(e["participant_majority_accuracy"]), c["vote_acc"], abs_tol=ACC_TOL), (
                f"{eid!r}: reported participant majority accuracy {e['participant_majority_accuracy']} "
                f"!= {c['vote_acc']:.4f} from its predictions")
        if (c["n_repeats"] == 10 and c["n_folds"] == 10 and c["stratified"] and c["distinct_repeats"]
                and not c["disjoint"] and c["agree_sub"] >= AGREE_SUBMITTED and c["agree_ref"] >= AGREE_REFERENCE):
            paper.append(eid)
    assert paper, ("no evaluation is the paper's procedure: 10 distinct repetitions of stratified 10-fold CV over "
                   "segments with the stated 3-NN classifier")


def test_estimate_comes_from_unseen_participants():
    # The estimate must be what the stated pipeline does on people it was not trained on: every
    # participant's segments sit in a single fold in every repeat, the predictions replay from
    # both the submitted and the reference features, and the number is the named metric.
    _, _, ev = submission()
    est = ev.get("estimate") or {}
    eid = str(est.get("evaluation_id"))
    assert eid in listed(ev), f"estimate refers to {eid!r}, which is not a listed evaluation"
    metric = est.get("metric")
    assert metric in ("segment_accuracy", "participant_majority_accuracy"), (
        f"estimate.metric must be segment_accuracy or participant_majority_accuracy, got {metric!r}")
    c = check_evaluation(eid)
    assert c["agree_sub"] >= AGREE_SUBMITTED, (
        f"predictions for {eid!r} are not those of the stated 3-NN pipeline on the submitted features "
        f"({c['agree_sub']:.1%} agree)")
    assert c["agree_ref"] >= AGREE_REFERENCE, (
        f"predictions for {eid!r} are not reproduced from the recordings' features ({c['agree_ref']:.1%} agree)")
    assert c["disjoint"], (f"the estimate comes from {eid!r}, where segments of the same participant are in "
                           "both training and test folds")
    got, ref, tol = ((c["seg_acc"], c["ref_seg_acc"], 0.02) if metric == "segment_accuracy"
                     else (c["vote_acc"], c["ref_vote_acc"], 0.05))
    a = _fraction(est["accuracy"])
    assert math.isclose(a, got, abs_tol=ACC_TOL), f"estimate {a} != {metric} of {eid!r} ({got:.4f})"
    assert abs(a - ref) <= tol, f"estimate {a} differs from the same folds replayed on the recordings ({ref:.4f})"


def test_report_and_metadata():
    # The written report and metadata must exist and agree with the submitted outputs. The
    # interpretation itself is not graded.
    rows, _, _, _ = aligned()
    _, _, ev = submission()
    assert (OUT / "run_metadata.json").is_file(), "run_metadata.json is missing"
    md = json.loads((OUT / "run_metadata.json").read_text(encoding="utf-8"))
    assert isinstance(md, dict), "run_metadata.json must be a JSON object"
    assert md.get("dataset_id") == "ds002778", f"run_metadata.dataset_id is {md.get('dataset_id')!r}"
    assert md.get("n_segments") == len(rows), f"run_metadata.n_segments {md.get('n_segments')} != {len(rows)} rows"
    assert md.get("n_participants") == rows.participant_id.nunique(), (
        f"run_metadata.n_participants {md.get('n_participants')} != {rows.participant_id.nunique()} in segments.csv")
    assert md.get("preprocessing"), "run_metadata.preprocessing is empty"
    assert isinstance(md.get("versions"), dict) and md["versions"], "run_metadata.versions must name the software used"
    assert (OUT / "findings.md").is_file(), "findings.md is missing"
    text = (OUT / "findings.md").read_text(encoding="utf-8")
    assert len(text.split()) >= 50, "findings.md is too short to report the results"
    a = _fraction((ev.get("estimate") or {}).get("accuracy", float("nan")))
    numbers = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text)]
    assert any(abs(x / 100 - a) <= 0.006 or abs(x - a) <= 0.006 for x in numbers), (
        f"findings.md does not state the estimate ({a:.3f})")
