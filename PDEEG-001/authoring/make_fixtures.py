"""Build calibration/fixtures/ from an oracle run (solution/solve.sh output directory).

    DS002778_DIR=<staged ds002778> python authoring/make_fixtures.py <oracle_output_dir>

_base/ gets the oracle's outputs; each other fixture overrides some files (and may delete
some via `remove` in expect.toml). Every fixture is manufactured from the oracle output (no
agent run yet), and each expect.toml says so. A manipulated fixture is kept internally
consistent (accuracies, majority votes, metric and findings all match its own predictions),
so it fails only on the defect it carries.
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.neighbors import KNeighborsClassifier

sys.path.insert(0, str(Path(__file__).resolve().parent))
src = Path(sys.argv[1])
fx = Path(__file__).resolve().parents[1] / "calibration" / "fixtures"
for d in fx.iterdir():
    if d.is_dir():
        shutil.rmtree(d)
base = fx / "_base"
base.mkdir()
for f in ("segments.csv", "cv_predictions.csv", "evaluations.json", "run_metadata.json", "findings.md"):
    shutil.copy2(src / f, base / f)
SEG = pd.read_csv(src / "segments.csv")
PRED = pd.read_csv(src / "cv_predictions.csv")
EV = json.loads((src / "evaluations.json").read_text())
FINDINGS = (src / "findings.md").read_text()
FEAT = [c for c in SEG.columns if c not in ("segment_id", "participant_id", "group", "start_sample")]
ACC = {e["evaluation_id"]: e for e in EV["evaluations"]}
T_FEAT, T_EVAL = "test_features_match_recordings", "test_reported_evaluations"
T_EST, T_REP = "test_estimate_comes_from_unseen_participants", "test_report_and_metadata"


def fixture(name, note, expect, files=None, remove=()):
    d = fx / name
    d.mkdir()
    lines = [f'note = "{note}"'] + ([f"remove = {json.dumps(list(remove))}"] if remove else []) + ["[expect]"]
    lines += [f'"*" = "{v}"' if k == "*" else f'{k} = "{v}"' for k, v in expect.items()]
    (d / "expect.toml").write_text("\n".join(lines) + "\n")
    for fname, content in (files or {}).items():
        if isinstance(content, pd.DataFrame):
            content.to_csv(d / fname, index=False)
        elif isinstance(content, dict):
            (d / fname).write_text(json.dumps(content, indent=2))
        else:
            (d / fname).write_text(content)


def vote(pred, truth, pid):
    share = pd.Series(pred == "PD").groupby(pid).mean()
    label = pd.Series(truth).groupby(pid).first().loc[share.index]
    return float(np.mean(np.where(share > 0.5, "PD", np.where(share < 0.5, "HC", "tie")) == label.to_numpy()))


def summarize(seg, pred, ev, estimate):
    """Recompute every listed evaluation's accuracies from `pred` and set the estimate."""
    truth = dict(zip(seg.segment_id, seg.group))
    pid = dict(zip(seg.segment_id, seg.participant_id))
    ev = json.loads(json.dumps(ev))
    ev["evaluations"] = [e for e in ev["evaluations"] if e["evaluation_id"] in set(pred.evaluation_id)]
    known = {e["evaluation_id"] for e in ev["evaluations"]}
    ev["evaluations"] += [{"evaluation_id": i, "description": i} for i in dict.fromkeys(pred.evaluation_id) if i not in known]
    for e in ev["evaluations"]:
        rows = pred[pred.evaluation_id == e["evaluation_id"]]
        reps = [r for _, r in rows.groupby("repeat")]
        e["accuracy"] = float(np.mean([np.mean(r.predicted_group.to_numpy() == r.segment_id.map(truth).to_numpy()) for r in reps]))
        e["participant_majority_accuracy"] = float(np.mean([vote(r.predicted_group.to_numpy(), r.segment_id.map(truth).to_numpy(),
                                                                 r.segment_id.map(pid).to_numpy()) for r in reps]))
        for k in ("participant_majority_correct", "participant_majority_ci95_exact", "accuracy_sd_over_repeats"):
            e.pop(k, None)
    eid, metric = estimate
    e = next(x for x in ev["evaluations"] if x["evaluation_id"] == eid)
    ev["estimate"] = {"evaluation_id": eid, "metric": metric,
                      "accuracy": e["accuracy" if metric == "segment_accuracy" else "participant_majority_accuracy"]}
    return ev


def with_findings(ev):
    return FINDINGS + f"\n\nReported estimate: {100 * ev['estimate']['accuracy']:.1f}% ({ev['estimate']['metric']}).\n"


def knn_recompute(seg, pred):
    X, y = seg[FEAT].to_numpy(float), seg.group.to_numpy()
    idx = {k: i for i, k in enumerate(seg.segment_id)}
    pred = pred.reset_index(drop=True)
    out = pred.copy()
    for _, rows in pred.groupby(["evaluation_id", "repeat"]):
        ii, fold = rows.segment_id.map(idx).to_numpy(), rows.fold.to_numpy()
        new = np.empty(len(ii), dtype=object)
        for f in np.unique(fold):
            new[fold == f] = KNeighborsClassifier(3, algorithm="brute").fit(X[ii[fold != f]], y[ii[fold != f]]).predict(X[ii[fold == f]])
        out.loc[rows.index, "predicted_group"] = new
    return out


def estimate_only(eid, metric, accuracy):
    ev = json.loads(json.dumps(EV))
    ev["estimate"] = {"evaluation_id": eid, "metric": metric, "accuracy": accuracy}
    return ev


# --- should pass -------------------------------------------------------------------------
fixture("reference", "reference: oracle output unchanged (solution/compute.py, local run 2026-10-08)", {"*": "pass"})
ev = estimate_only("leave_one_participant_out", "participant_majority_accuracy",
                   ACC["leave_one_participant_out"]["participant_majority_accuracy"])
fixture("estimate-participant-vote", "manufactured: oracle output, estimate = leave-one-participant-out majority-vote accuracy",
        {"*": "pass"}, {"evaluations.json": ev, "findings.md": with_findings(ev)})
ev = estimate_only("participant_grouped_10x10", "segment_accuracy", round(100 * ACC["participant_grouped_10x10"]["accuracy"], 2))
fixture("estimate-grouped-percent", "manufactured: oracle output, estimate from the participant-grouped 10 x 10 CV, written in percent",
        {"*": "pass"}, {"evaluations.json": ev, "findings.md": FINDINGS + f"\n\nGrouped estimate: {ev['estimate']['accuracy']}%.\n"})
try:
    from feature_tolerance import features
    seg = SEG.copy()
    order = list(zip(seg.participant_id, seg.start_sample))
    import reference as R
    meta, _ = R.reference_segments()
    F = pd.DataFrame(features(filt="mne"), columns=FEAT)
    F[["participant_id", "start_sample"]] = meta[["participant_id", "start_sample"]].to_numpy()
    seg[FEAT] = F.set_index(["participant_id", "start_sample"]).loc[order][FEAT].to_numpy()
    pred = knn_recompute(seg, PRED)
    ev = summarize(seg, pred, EV, ("leave_one_participant_out", "segment_accuracy"))
    fixture("equivalent-implementation-mne-filter",
            "manufactured: features from MNE filter_data (IIR Butterworth sos, zero phase) instead of scipy sosfiltfilt; "
            "every evaluation recomputed with scikit-learn on those features",
            {"*": "pass"}, {"segments.csv": seg, "cv_predictions.csv": pred, "evaluations.json": ev, "findings.md": with_findings(ev)})
except ImportError as e:  # authoring tools need mne; skip the fixture rather than fake it
    print("skipped equivalent-implementation fixture:", e)

# --- targeted failure: the leaked number reported as the estimate -------------------------
ev = estimate_only("paper_segment_10x10", "segment_accuracy", ACC["paper_segment_10x10"]["accuracy"])
fixture("estimate-from-paper-cv", "manufactured, targeted failure: all evaluations reported, estimate = the paper's segment-level 99.7%",
        {T_FEAT: "pass", T_EVAL: "pass", T_EST: "fail", T_REP: "pass"}, {"evaluations.json": ev, "findings.md": with_findings(ev)})
pred = PRED[PRED.evaluation_id == "paper_segment_10x10"]
ev = summarize(SEG, pred, EV, ("paper_segment_10x10", "segment_accuracy"))
fixture("paper-cv-only", "manufactured, targeted failure: only the paper's 10 x 10-fold CV is run and its accuracy is the estimate",
        {T_FEAT: "pass", T_EVAL: "pass", T_EST: "fail", T_REP: "pass"},
        {"evaluations.json": ev, "cv_predictions.csv": pred, "findings.md": with_findings(ev)})

# --- invalid estimate or evaluation reporting ---------------------------------------------
ev = estimate_only("leave_one_participant_out", "segment_accuracy", ACC["paper_segment_10x10"]["accuracy"])
fixture("estimate-mismatched", "manufactured: estimate names leave-one-participant-out but quotes the segment-level 99.7%",
        {T_FEAT: "pass", T_EVAL: "pass", T_EST: "fail", T_REP: "pass"}, {"evaluations.json": ev, "findings.md": with_findings(ev)})
ev = estimate_only("leave_one_participant_out", "participant_majority_accuracy", ACC["leave_one_participant_out"]["accuracy"])
fixture("estimate-metric-mislabelled", "manufactured: estimate is the segment accuracy but labelled participant_majority_accuracy",
        {T_FEAT: "pass", T_EVAL: "pass", T_EST: "fail", T_REP: "pass"}, {"evaluations.json": ev, "findings.md": with_findings(ev)})
ev = json.loads(json.dumps(EV))
for e in ev["evaluations"]:
    if e["evaluation_id"] == "participant_grouped_10x10":
        e["accuracy"] = 0.62
fixture("evaluation-accuracy-misreported", "manufactured: the participant-grouped evaluation reports 62% although its predictions give 47%",
        {T_FEAT: "pass", T_EVAL: "fail", T_EST: "pass", T_REP: "pass"}, {"evaluations.json": ev})
fake = PRED.copy()
lopo = fake.evaluation_id == "leave_one_participant_out"
fake.loc[lopo, "predicted_group"] = fake.loc[lopo, "segment_id"].map(dict(zip(SEG.segment_id, SEG.group)))
ev = summarize(SEG, fake, EV, ("leave_one_participant_out", "segment_accuracy"))
fixture("fabricated-held-out-predictions",
        "manufactured: leave-one-participant-out predictions replaced by the true labels (not what the 3-NN pipeline predicts)",
        {T_FEAT: "pass", T_EVAL: "pass", T_EST: "fail", T_REP: "pass"},
        {"evaluations.json": ev, "cv_predictions.csv": fake, "findings.md": with_findings(ev)})

# --- reviewer finding 2: degenerate partitions ----------------------------------------------
one = pd.DataFrame({"evaluation_id": "single_fold", "repeat": 0, "fold": 0, "segment_id": SEG.segment_id, "predicted_group": "HC"})
pred = pd.concat([PRED, one])
ev = json.loads(json.dumps(EV))
ev["evaluations"].append({"evaluation_id": "single_fold", "description": "every segment in one test fold",
                          "accuracy": float((SEG.group == "HC").mean())})
ev["estimate"] = {"evaluation_id": "single_fold", "metric": "segment_accuracy", "accuracy": float((SEG.group == "HC").mean())}
fixture("single-fold-empty-training", "manufactured (review finding 2): one fold holds every segment, so the training set is empty; "
        "all predicted HC (50.6%) and used as the estimate",
        {T_FEAT: "pass", T_EVAL: "fail", T_EST: "fail", T_REP: "pass"},
        {"evaluations.json": ev, "cv_predictions.csv": pred, "findings.md": with_findings(ev)})
# two segments (one PD, one HC) form fold 1; fold 0, everything else, is trained on just those two
pair = [SEG.index[SEG.group == "PD"][0], SEG.index[SEG.group == "HC"][0]]
tiny = SEG[["segment_id"]].assign(fold=np.where(SEG.index.isin(pair), 1, 0), predicted_group="HC")
tiny = tiny.assign(evaluation_id="tiny_training", repeat=0)[["evaluation_id", "repeat", "fold", "segment_id", "predicted_group"]]
pred = pd.concat([PRED, tiny])
ev = summarize(SEG, pred, EV, ("tiny_training", "segment_accuracy"))
fixture("fold-with-fewer-than-3-training-segments",
        "manufactured (review finding 2): a 2-fold split in which one fold is trained on only 2 segments",
        {T_FEAT: "pass", T_EVAL: "fail", T_EST: "fail", T_REP: "pass"},
        {"evaluations.json": ev, "cv_predictions.csv": pred, "findings.md": with_findings(ev)})

# --- reviewer finding 6: the paper's split structure ----------------------------------------
y = SEG.group.to_numpy()
rows = []
for r in range(10):
    for f, (_, te) in enumerate(KFold(10, shuffle=True, random_state=r).split(SEG)):
        rows.append(pd.DataFrame({"evaluation_id": "paper_segment_10x10", "repeat": r, "fold": f,
                                  "segment_id": SEG.segment_id.iloc[te].to_numpy(), "predicted_group": "HC"}))
plain = pd.concat(rows)
pred = knn_recompute(SEG, pd.concat([plain, PRED[PRED.evaluation_id != "paper_segment_10x10"]]))
ev = summarize(SEG, pred, EV, ("leave_one_participant_out", "segment_accuracy"))
fixture("paper-cv-not-stratified", "manufactured (review finding 6): the paper's 10 x 10 CV done with unstratified KFold",
        {T_FEAT: "pass", T_EVAL: "fail", T_EST: "pass", T_REP: "pass"},
        {"evaluations.json": ev, "cv_predictions.csv": pred, "findings.md": with_findings(ev)})
first = PRED[(PRED.evaluation_id == "paper_segment_10x10") & (PRED.repeat == 0)]
same = pd.concat([first.assign(repeat=r) for r in range(10)])
pred = pd.concat([same, PRED[PRED.evaluation_id != "paper_segment_10x10"]])
ev = summarize(SEG, pred, EV, ("leave_one_participant_out", "segment_accuracy"))
fixture("paper-cv-identical-repeats", "manufactured (review finding 6): one stratified 10-fold partition copied as all 10 repeats",
        {T_FEAT: "pass", T_EVAL: "fail", T_EST: "pass", T_REP: "pass"},
        {"evaluations.json": ev, "cv_predictions.csv": pred, "findings.md": with_findings(ev)})

# --- reviewer finding 1: manipulated feature table ------------------------------------------
seg = SEG.copy()
seg["Fp1_D1"] = np.where(seg.group == "PD", 5000.0, 0.0)
pred = knn_recompute(seg, PRED)
ev = summarize(seg, pred, EV, ("leave_one_participant_out", "segment_accuracy"))
fixture("column-encodes-diagnosis",
        "manufactured (review finding 1): Fp1_D1 replaced by 5000 for PD and 0 for HC; every evaluation recomputed on the "
        "manipulated table (held-out accuracy 100%)",
        {T_FEAT: "fail", T_EVAL: "pass", T_EST: "fail", T_REP: "pass"},
        {"segments.csv": seg, "cv_predictions.csv": pred, "evaluations.json": ev, "findings.md": with_findings(ev)})
volts = SEG.copy()
volts[FEAT] = 0.0
fixture("features-threshold-in-volts", "manufactured: threshold 0.2 applied to signals in volts, so every count is zero",
        {T_FEAT: "fail"}, {"segments.csv": volts})
frac = SEG.copy()
frac[FEAT] = frac[FEAT] / 5120
fixture("features-not-counts", "manufactured: features written as fractions of the segment instead of sample counts",
        {T_FEAT: "fail"}, {"segments.csv": frac})

# --- reviewer finding 4: deliverables -------------------------------------------------------
fixture("missing-findings", "manufactured (review finding 4): findings.md deleted", {T_REP: "fail", "*": "pass"}, remove=["findings.md"])
fixture("missing-metadata", "manufactured (review finding 4): run_metadata.json deleted", {T_REP: "fail", "*": "pass"},
        remove=["run_metadata.json"])
md = json.loads((src / "run_metadata.json").read_text())
md["n_segments"] = 606
fixture("metadata-counts-wrong", "manufactured (review finding 4): run_metadata reports the paper's 606 segments, not the 593 written",
        {T_REP: "fail", "*": "pass"}, {"run_metadata.json": md})
fixture("findings-omit-estimate", "manufactured (review finding 4): findings.md is a generic paragraph that never states the estimate",
        {T_REP: "fail", "*": "pass"},
        {"findings.md": "# Findings\n\n" + "The pipeline was run as described in the instruction and the outputs are in this directory. " * 6})
print(sorted(d.name for d in fx.iterdir() if d.is_dir()))
