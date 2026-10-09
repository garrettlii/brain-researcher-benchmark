"""Reference solution for PDEEG-001.

The instruction asks for a reproduction of Aljalal et al. 2022's threshold-entropy result
(off-medication PD vs controls, UC San Diego resting EEG, ds002778): the pinned DWT/entropy
features, KNN k=3, and the paper's evaluation, 10 x 10-fold cross-validation over 10 s
segments. It also asks what accuracy the pipeline supports as a PD classifier.

What the honest reference volunteers: the paper's folds are drawn over segments, so every
test segment has ~16 sibling segments from the same person in the training set. A classifier
meant to detect PD has to be evaluated on people it has not seen (Saeb et al. 2017,
GigaScience 6:gix019; Varoquaux et al. 2017, NeuroImage 145:166). The reference therefore
also runs leave-one-participant-out and participant-grouped 10 x 10-fold cross-validation
of the same pipeline, plus a participant-level label permutation, and two checks of what the
segment-level number measures: the same segment-level CV on random participant-level labels,
and 31-way participant identification.

Validated numbers (Step 0, step0/evidence.json; 16 HC + 15 PD-off, 593 segments):
  RAW      segment-level 10 x 10-fold accuracy            : 99.7%  (paper 99.72%)
  PREMISE  same features identify the participant (31-way): 99.3%; random participant
           labels still give 99.5% under segment-level CV
  CTRL     leave-one-participant-out                      : 45.4% of segments, 13/31
           participants by majority vote, permutation p = 0.64  -> collapses to chance

This file is step0/probe.py restricted to the threshold-entropy feature and promoted to the
oracle: the same evaluation numbers, plus the task's required outputs. The permutation p (0.641 vs
Step-0 0.647) and 31-way identification (99.3% vs 99.2%) differ slightly because the oracle pins
algorithm="brute" (tie order) and uses one 10-fold split instead of the mean of three.
"""
import hashlib
import json
import os
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import signal, stats

OUT = Path(os.environ.get("OUTPUT_DIR", "/app/output"))
DATA = Path(os.environ.get("DS002778_DIR", "/app/data/ds002778"))
MANIFEST = Path(os.environ.get("SOURCE_MANIFEST", "/app/source_manifest.json"))
OUT.mkdir(parents=True, exist_ok=True)
warnings.filterwarnings("ignore")

TASK_ID = "PDEEG-001"
DATASET_ID = "ds002778"
FS, SEG_S = 512, 10
SEG = FS * SEG_S
CHANNELS = ["Fp1", "AF3", "F7", "F3", "FC1", "FC5", "T7", "C3", "CP1", "CP5", "P7", "P3", "Pz", "PO3", "O1", "Oz",
            "O2", "PO4", "P4", "P8", "CP6", "CP2", "C4", "T8", "FC6", "FC2", "F4", "F8", "AF4", "Fp2", "Fz", "Cz"]
SIGNALS = ["D1", "D2", "D3", "D4", "A4", "X"]
FEATURES = [f"{c}_{s}" for c in CHANNELS for s in SIGNALS]
N_PERM, N_RANDLAB = 1000, 100


def wj(name, payload):
    (OUT / name).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def fail(reason):
    wj("failure_report.json", {"task_id": TASK_ID, "dataset_id": DATASET_ID,
                               "status": "failed_precondition", "reason": reason})
    sys.stderr.write(reason + "\n")
    sys.exit(1)


def check_sources():
    try:
        man = json.loads(MANIFEST.read_text())
    except Exception as e:  # noqa: BLE001
        fail(f"cannot read source manifest {MANIFEST}: {e}")
    for f in man["files"]:
        p = DATA / f["path"]
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != f["sha256"]:
            fail(f"staged file missing or altered: {f['path']}")
    return man


def subbands(s):
    """D1, D2, D3, D4, A4 reconstructed separately at full length (MATLAB wrcoef), then the signal."""
    import pywt
    c = pywt.wavedec(s, "db4", level=4, mode="symmetric")          # [A4, D4, D3, D2, D1]
    rec = []
    for i in range(5):
        z = [x if j == i else np.zeros_like(x) for j, x in enumerate(c)]
        rec.append(pywt.waverec(z, "db4", mode="symmetric")[: s.shape[-1]])
    return np.stack(rec[::-1] + [s])                                # D1 D2 D3 D4 A4 X


def extract():
    import mne
    mne.set_log_level("ERROR")
    sos = signal.butter(5, [0.5, 32], btype="bandpass", fs=FS, output="sos")
    part = pd.read_csv(DATA / "participants.tsv", sep="\t")
    recs = [(s, "HC", f"{s}/ses-hc/eeg/{s}_ses-hc_task-rest_eeg.bdf") for s in part.participant_id if s.startswith("sub-hc")]
    recs += [(s, "PD", f"{s}/ses-off/eeg/{s}_ses-off_task-rest_eeg.bdf") for s in part.participant_id if s.startswith("sub-pd")]
    rows, X, n_samples = [], [], {}
    for pid, grp, f in recs:
        raw = mne.io.read_raw_bdf(DATA / f, preload=True)
        if raw.info["sfreq"] != FS:
            fail(f"{f}: sampling rate {raw.info['sfreq']} != {FS}")
        x = raw.get_data(picks=CHANNELS) * 1e6                       # V -> uV
        x = x - x.mean(1, keepdims=True)                             # channel mean over the recording
        x = x - x.mean(0, keepdims=True)                             # average reference, 32 channels
        n_samples[pid] = int(x.shape[1])
        for k in range(x.shape[1] // SEG):
            seg = signal.sosfiltfilt(sos, x[:, k * SEG:(k + 1) * SEG], axis=1)
            B = np.stack([subbands(ch) for ch in seg])               # 32 x 6 x 5120
            X.append((np.abs(B) > 0.2).sum(-1).astype(float).ravel())  # threshold entropy, 0.2 uV
            rows.append({"segment_id": f"{pid}_seg{k:03d}", "participant_id": pid, "group": grp,
                         "start_sample": k * SEG})
    return pd.DataFrame(rows), np.array(X), n_samples


def knn():
    from sklearn.neighbors import KNeighborsClassifier
    return KNeighborsClassifier(n_neighbors=3, metric="euclidean", algorithm="brute")


def cv_run(X, y, splits):
    """splits: list of (train_idx, test_idx). Returns fold id and prediction per segment."""
    fold, pred = np.full(len(y), -1), np.empty(len(y), dtype=object)
    for f, (tr, te) in enumerate(splits):
        fold[te] = f
        pred[te] = knn().fit(X[tr], y[tr]).predict(X[te])
    assert (fold >= 0).all()
    return fold, pred


def cp(k, n):
    lo = stats.beta.ppf(0.025, k, n - k + 1) if k > 0 else 0.0
    hi = stats.beta.ppf(0.975, k + 1, n - k) if k < n else 1.0
    return [round(float(lo), 4), round(float(hi), 4)]


def main():
    from sklearn.model_selection import (LeaveOneGroupOut, RepeatedStratifiedKFold, StratifiedGroupKFold,
                                         StratifiedKFold, cross_val_predict)
    t0 = time.time()
    if not DATA.is_dir():
        fail(f"dataset directory {DATA} not found")
    check_sources()
    seg, X, n_samples = extract()
    y = seg.group.to_numpy()
    g = seg.participant_id.to_numpy()
    subs = np.unique(g)
    ysub = np.array([y[g == s][0] for s in subs])

    runs = {}
    rskf = list(RepeatedStratifiedKFold(n_splits=10, n_repeats=10, random_state=0).split(X, y))
    runs["paper_segment_10x10"] = [rskf[r * 10:(r + 1) * 10] for r in range(10)]
    runs["leave_one_participant_out"] = [list(LeaveOneGroupOut().split(X, y, g))]
    runs["participant_grouped_10x10"] = [list(StratifiedGroupKFold(10, shuffle=True, random_state=r).split(X, y, g))
                                         for r in range(10)]
    desc = {"paper_segment_10x10": "The paper's evaluation: 10 repetitions of stratified 10-fold CV over segments "
                                   "(scikit-learn RepeatedStratifiedKFold, random_state=0).",
            "leave_one_participant_out": "Each participant's segments form one test fold; the model never sees "
                                         "the test participant during training.",
            "participant_grouped_10x10": "10 repetitions of stratified 10-fold CV with all segments of a participant "
                                         "in the same fold (StratifiedGroupKFold, random_state=0..9)."}
    pred_rows, evals = [], []
    for eid, reps in runs.items():
        accs, votes = [], []
        for r, splits in enumerate(reps):
            fold, pred = cv_run(X, y, splits)
            accs.append(float((pred == y).mean()))
            v = np.array(["PD" if (pred[g == s] == "PD").mean() >= 0.5 else "HC" for s in subs])
            votes.append(float((v == ysub).mean()))
            pred_rows.append(pd.DataFrame({"evaluation_id": eid, "repeat": r, "fold": fold,
                                           "segment_id": seg.segment_id, "predicted_group": pred}))
        e = {"evaluation_id": eid, "description": desc[eid], "n_repeats": len(reps), "n_folds": len(reps[0]),
             "classifier": "KNN k=3, Euclidean, unscaled features",
             "accuracy": round(float(np.mean(accs)), 6),
             "accuracy_sd_over_repeats": round(float(np.std(accs)), 6),
             "participant_majority_vote_accuracy": round(float(np.mean(votes)), 6)}
        if eid == "leave_one_participant_out":
            k = int(round(votes[0] * len(subs)))
            e["participant_majority_vote_correct"] = f"{k}/{len(subs)}"
            e["participant_majority_vote_ci95_exact"] = cp(k, len(subs))
        evals.append(e)
        print(f"{time.time() - t0:5.0f}s {eid}: acc {e['accuracy']:.4f} vote {e['participant_majority_vote_accuracy']:.4f}",
              flush=True)

    # participant-level label permutation for leave-one-participant-out
    rng = np.random.default_rng(0)
    logo = runs["leave_one_participant_out"][0]
    obs = evals[1]["accuracy"]
    null = []
    for _ in range(N_PERM):
        lab = dict(zip(subs, rng.permutation(ysub)))
        yp = np.array([lab[s] for s in g])
        null.append(float((cv_run(X, yp, logo)[1] == yp).mean()))
    perm = {"n_permutations": N_PERM, "observed": obs, "null_mean": round(float(np.mean(null)), 4),
            "null_95th_percentile": round(float(np.quantile(null, 0.95)), 4),
            "p": round(float((1 + np.sum(np.array(null) >= obs)) / (1 + N_PERM)), 4)}
    # what the segment-level number measures
    rand = []
    for _ in range(N_RANDLAB):
        lab = dict(zip(subs, rng.permutation(ysub)))
        yr = np.array([lab[s] for s in g])
        p = cross_val_predict(knn(), X, yr, cv=StratifiedKFold(10, shuffle=True, random_state=0))
        rand.append(float((p == yr).mean()))
    p_id = cross_val_predict(knn(), X, g, cv=StratifiedKFold(10, shuffle=True, random_state=0))
    ident = {"segment_10fold_accuracy_random_participant_labels": {
                 "n_assignments": N_RANDLAB, "mean": round(float(np.mean(rand)), 4),
                 "min": round(float(np.min(rand)), 4), "max": round(float(np.max(rand)), 4)},
             "participant_identification_31way_segment_10fold_accuracy": round(float((p_id == g).mean()), 4),
             "chance_31way": round(1 / len(subs), 4)}

    loso = evals[1]
    est = {"evaluation_id": "leave_one_participant_out", "accuracy": loso["accuracy"],
           "basis": "segment accuracy on participants held out of training"}
    seg.join(pd.DataFrame(X, columns=FEATURES)).to_csv(OUT / "segments.csv", index=False)
    pd.concat(pred_rows).to_csv(OUT / "cv_predictions.csv", index=False)
    wj("evaluations.json", {"evaluations": evals, "estimate": est,
                            "additional_analyses": {"leave_one_participant_out_permutation": perm,
                                                    "segment_level_cv_identification_checks": ident}})
    import mne
    import pywt
    import sklearn
    wj("run_metadata.json", {
        "task_id": TASK_ID, "dataset_id": DATASET_ID, "dataset_doi": "10.18112/openneuro.ds002778.v1.0.4",
        "n_participants": int(len(subs)), "n_pd_off": int((ysub == "PD").sum()), "n_hc": int((ysub == "HC").sum()),
        "n_segments": int(len(y)), "n_pd_segments": int((y == "PD").sum()), "n_hc_segments": int((y == "HC").sum()),
        "recording_samples": n_samples, "sampling_rate_hz": FS, "segment_seconds": SEG_S,
        "channels": CHANNELS, "units": "microvolt",
        "preprocessing": ["channel mean over the recording removed", "average reference over the 32 channels",
                          "per segment: 5th-order Butterworth 0.5-32 Hz, second-order sections, scipy sosfiltfilt",
                          "db4 4-level DWT (symmetric extension); D1-D4 and A4 reconstructed separately, plus "
                          "the filtered segment (X)",
                          "threshold entropy: count of samples with |x| > 0.2 uV"],
        "classifier": "scikit-learn KNeighborsClassifier(n_neighbors=3, metric='euclidean', algorithm='brute')",
        "versions": {"python": sys.version.split()[0], "numpy": np.__version__, "mne": mne.__version__,
                     "pywavelets": pywt.__version__, "scikit-learn": sklearn.__version__},
        "runtime_seconds": round(time.time() - t0, 1)})
    paper = evals[0]
    grp = evals[2]
    lo, hi = loso["participant_majority_vote_ci95_exact"]
    (OUT / "findings.md").write_text(f"""# Threshold-entropy PD classification on ds002778 (off medication vs controls)

**The paper's number reproduces, but it does not measure PD detection.** With the pinned
pipeline and the paper's 10 x 10-fold cross-validation over segments, KNN accuracy is
{paper['accuracy']:.1%} (paper: 99.72%). When the participant being classified is held out of
training, the same pipeline is at chance: leave-one-participant-out {loso['accuracy']:.1%} of
segments, {loso['participant_majority_vote_correct']} participants correct by majority vote
(exact 95% CI {lo:.2f}-{hi:.2f}), participant-grouped 10 x 10-fold {grp['accuracy']:.1%}.
A participant-level label permutation gives p = {perm['p']} (null mean {perm['null_mean']:.1%}).
The accuracy I would report for this pipeline as a PD-vs-control classifier is the held-out-
participant figure, about {loso['accuracy']:.0%}: no better than chance on these 31 people.

## Why the segment-level number is high

The paper's folds are drawn over the {len(y)} segments, so each test segment has about 16
segments from the same recording in the training set, and the 3 nearest neighbours are
almost always that person's own segments. The features fingerprint individuals:

- 31-way participant identification from a single segment:
  {ident['participant_identification_31way_segment_10fold_accuracy']:.1%} (chance {ident['chance_31way']:.1%}).
- The same segment-level CV with *random* participant-level labels (no disease information,
  {N_RANDLAB} assignments): mean {ident['segment_10fold_accuracy_random_participant_labels']['mean']:.1%},
  range {ident['segment_10fold_accuracy_random_participant_labels']['min']:.1%}-{ident['segment_10fold_accuracy_random_participant_labels']['max']:.1%}.

Any participant-level label is "classified" at ~99% under this design, so the 99.7% says the
features recognise a person seen in training, not that they carry a PD signature.

## Uncertainty and limits

- n = 31 (15 PD, 16 HC). The held-out estimate is imprecise: the majority-vote CI spans
  {lo:.0%}-{hi:.0%}, so a modest real effect (e.g. 60% accuracy) cannot be excluded. What is
  excluded is anything near the reported 99.7%.
- This tests one feature (threshold entropy) and one classifier as pinned. In Step-0 runs
  every entropy variant in the paper behaved the same way (99%+ segment-level, chance
  held-out); other classifiers or feature selection were not explored here.
- Segment counts differ slightly from the paper (593 vs 606) because some recordings are
  shorter than 10 x 20 s; this does not affect the comparison.
- Off-medication only; the on-medication sessions were not analysed.
""", encoding="utf-8")
    print(f"done {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
