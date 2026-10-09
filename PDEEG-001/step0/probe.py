"""Step-0 probe for PDEEG-001: a throwaway script, NOT the oracle.

Claim: Aljalal, Aldosari, Molinas, AlSharabi & Alturki 2022 (Sci Rep 12:22547,
doi:10.1038/s41598-022-26644-7) classify Parkinson's disease (off medication) vs healthy
controls from resting EEG (SanDiego set = OpenNeuro ds002778) at 99.7-99.9% accuracy:
10 s non-overlapping segments, 0.5-32 Hz 5th-order Butterworth, db4 level-4 DWT with each
sub-band reconstructed separately (cD1..cD4, cA4) plus the segment itself, one entropy per
signal per channel (6 x 32 = 192 features), KNN (k=3, Euclidean), 10 x 10-fold CV over the
606 segments. The paper presents the features as PD biomarkers for detection.

Question: the folds are over SEGMENTS, so every test segment has ~19 sibling segments from
the same person in training. Measured here:
  SEG      the paper's 10 x 10-fold segment-level CV (the paper-motivated analysis)
  SUBJ     subject-independent CV: leave-one-subject-out (LOSO) and 10 x subject-grouped
           10-fold; segment accuracy and per-subject majority vote with exact binomial CIs;
           subject-level label-permutation p
  IDENT    alternative explanation 1, subject fingerprinting: (a) segment-level CV on
           RANDOM subject-level labels (no disease information); (b) 31-way subject ID
  BAND     alternative explanation 2, non-neural recording cues: features from the
           0-32 Hz sub-bands (cA4, cD4) vs the 32-256 Hz sub-bands (cD1-cD3, above the
           paper's own low-pass); 60 Hz line-noise ratio by group
Filter order: the paper's Methods and Results sections filter each 10 s segment, its pipeline
overview filters before segmenting. The probe follows the Methods (per segment) and also
reports the other order as a variant (variants_primary.filter_whole_recording_then_segment).
Entropies follow MATLAB's legacy wentropy definitions applied to signal values in uV
(threshold 0.2, sure 3, norm p=1.1), which match the paper's Eqs. 3-7 and parameters.

    DS002778_DIR=/path/to/ds002778 python step0/probe.py > step0/run.log 2>&1
"""
import json
import os
import time
import warnings
from pathlib import Path

import mne
import numpy as np
import pandas as pd
import pywt
from scipy import signal, stats
from sklearn.model_selection import (LeaveOneGroupOut, RepeatedStratifiedKFold, StratifiedGroupKFold,
                                     StratifiedKFold, cross_val_predict)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
mne.set_log_level("ERROR")
DATA = Path(os.environ.get("DS002778_DIR", "ds002778"))
OUT = Path(__file__).resolve().parent / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
FS, SEG = 512, 10
N_PERM, N_RANDLAB = 1000, 100
rng = np.random.default_rng(0)
EEG = ["Fp1", "AF3", "F7", "F3", "FC1", "FC5", "T7", "C3", "CP1", "CP5", "P7", "P3", "Pz", "PO3", "O1", "Oz",
       "O2", "PO4", "P4", "P8", "CP6", "CP2", "C4", "T8", "FC6", "FC2", "F4", "F8", "AF4", "Fp2", "Fz", "Cz"]
SOS = signal.butter(5, [0.5, 32], btype="bandpass", fs=FS, output="sos")
EPS = np.finfo(float).eps


def subbands(s):
    """cD1, cD2, cD3, cD4, cA4 reconstructed separately (MATLAB wrcoef), then the segment itself."""
    c = pywt.wavedec(s, "db4", level=4, mode="symmetric")          # [cA4, cD4, cD3, cD2, cD1]
    rec = []
    for i in range(5):
        z = [x if j == i else np.zeros_like(x) for j, x in enumerate(c)]
        rec.append(pywt.waverec(z, "db4", mode="symmetric")[: s.shape[-1]])
    return np.stack(rec[::-1] + [s])                                # cD1 cD2 cD3 cD4 cA4 orig


METRICS = {
    "LogEn": lambda S: np.log(S ** 2 + EPS).sum(-1),
    "ThEn": lambda S: (np.abs(S) > 0.2).sum(-1).astype(float),
    "SuEn": lambda S: S.shape[-1] - (np.abs(S) <= 3).sum(-1) + np.minimum(S ** 2, 9).sum(-1),
    "NoEn": lambda S: (np.abs(S) ** 1.1).sum(-1),
    "ShEn": lambda S: -(S ** 2 * np.log(S ** 2 + EPS)).sum(-1),
    "Eng": lambda S: (S ** 2).sum(-1),
    "LBP": lambda S: np.log((S ** 2).mean(-1)),
}


def tshen(S):
    """Paper Eqs. 8-9 (best effort: 'k unique values' is ambiguous; values rounded to integers)."""
    T = np.round(np.where(S > 1, 255.0, np.where(S < 0, 0.0, 255.0 * S)))
    out = np.empty(S.shape[:-1])
    for idx in np.ndindex(S.shape[:-1]):
        v = T[idx]; k = len(np.unique(v))
        out[idx] = -(v ** 2 * np.log(v ** 2 + EPS)).sum() / k
    return out


part = pd.read_csv(DATA / "participants.tsv", sep="\t")
recs = [(s, 0, f"{s}/ses-hc/eeg/{s}_ses-hc_task-rest_eeg.bdf") for s in part.participant_id if s.startswith("sub-hc")]
recs += [(s, 1, f"{s}/ses-off/eeg/{s}_ses-off_task-rest_eeg.bdf") for s in part.participant_id if s.startswith("sub-pd")]
t0 = time.time()
feats = {k: [] for k in list(METRICS) + ["TShEn"]}
feats_causal = []
feats_whole = []                                                     # filter the recording, then segment
y, g, line = [], [], []
for s, lab, f in recs:
    raw = mne.io.read_raw_bdf(DATA / f, preload=True)
    x = raw.get_data(picks=EEG) * 1e6                                # uV
    x = x - x.mean(1, keepdims=True)
    x = x - x.mean(0, keepdims=True)                                 # common average reference
    fr, P = signal.welch(x, fs=FS, nperseg=4 * FS)
    line.append({"subject": s, "group": lab, "line60_ratio": float(np.median(P[:, (fr >= 59) & (fr <= 61)].mean(1)
                                                                             / P[:, ((fr >= 55) & (fr < 58)) | ((fr > 62) & (fr <= 65))].mean(1))),
                 "pow_64_128": float(np.log(P[:, (fr >= 64) & (fr <= 128)].mean())), "n_seg": int(x.shape[1] // (SEG * FS))})
    xf = signal.sosfiltfilt(SOS, x, axis=1)
    for k in range(x.shape[1] // (SEG * FS)):
        seg = x[:, k * SEG * FS:(k + 1) * SEG * FS]
        sf = signal.sosfiltfilt(SOS, seg, axis=1)
        B = np.stack([subbands(ch) for ch in sf])                    # 32 x 6 x N
        for m, fn in METRICS.items():
            feats[m].append(fn(B))                                    # 32 x 6
        feats["TShEn"].append(tshen(B))
        Bc = np.stack([subbands(ch) for ch in signal.sosfilt(SOS, seg, axis=1)])
        feats_causal.append(METRICS["ThEn"](Bc))
        Bw = np.stack([subbands(ch) for ch in xf[:, k * SEG * FS:(k + 1) * SEG * FS]])
        feats_whole.append(METRICS["ThEn"](Bw))
        y.append(lab); g.append(s)
    print(f"{time.time() - t0:5.0f}s {s} {line[-1]['n_seg']} segments", flush=True)

y, g = np.array(y), np.array(g)
F = {m: np.array(v) for m, v in feats.items()}                       # n x 32 x 6
F_causal = np.array(feats_causal)
F_whole = np.array(feats_whole)
subs = np.unique(g)
ysub = np.array([y[g == s][0] for s in subs])
print(f"segments: PD {int((y == 1).sum())}, HC {int((y == 0).sum())}; subjects {len(subs)}", flush=True)
knn = lambda: KNeighborsClassifier(n_neighbors=3, metric="euclidean")  # noqa: E731


def flat(A, bands=slice(None)):
    return A[:, :, bands].reshape(len(A), -1)


def seg_cv(X, labels, reps=10):
    accs = []
    for r in range(reps):
        p = cross_val_predict(knn(), X, labels, cv=StratifiedKFold(10, shuffle=True, random_state=r))
        accs.append((p == labels).mean())
    return float(np.mean(accs)), float(np.std(accs))


def seg_folds(X, labels):
    cv = RepeatedStratifiedKFold(n_splits=10, n_repeats=10, random_state=0)
    a = [(knn().fit(X[tr], labels[tr]).predict(X[te]) == labels[te]).mean() for tr, te in cv.split(X, labels)]
    return float(np.mean(a)), float(np.std(a))


def cp(k, n):
    lo = stats.beta.ppf(0.025, k, n - k + 1) if k > 0 else 0.0
    hi = stats.beta.ppf(0.975, k + 1, n - k) if k < n else 1.0
    return [round(float(lo), 3), round(float(hi), 3)]


def subject_votes(pred, labels):
    v = np.array([pred[g == s].mean() >= 0.5 for s in subs]).astype(int)
    return v


def loso(X, labels, model=knn):
    p = cross_val_predict(model(), X, labels, groups=g, cv=LeaveOneGroupOut())
    v = subject_votes(p, labels); ys = np.array([labels[g == s][0] for s in subs])
    k = int((v == ys).sum())
    return {"segment_acc": round(float((p == labels).mean()), 4),
            "segment_balanced_acc": round(float(((p == 1) & (labels == 1)).sum() / (labels == 1).sum() / 2
                                                + ((p == 0) & (labels == 0)).sum() / (labels == 0).sum() / 2), 4),
            "subject_vote_acc": round(k / len(subs), 4), "subject_vote_correct": k, "n_subjects": len(subs),
            "subject_vote_ci95_exact": cp(k, len(subs)),
            "sens_subjects": round(float(((v == 1) & (ys == 1)).sum() / (ys == 1).sum()), 3),
            "spec_subjects": round(float(((v == 0) & (ys == 0)).sum() / (ys == 0).sum()), 3)}


def group_cv(X, labels, reps=10):
    a = []
    for r in range(reps):
        p = cross_val_predict(knn(), X, labels, groups=g, cv=StratifiedGroupKFold(10, shuffle=True, random_state=r))
        a.append((p == labels).mean())
    return float(np.mean(a)), float(np.std(a))


metrics = {"n_segments": int(len(y)), "n_pd_segments": int((y == 1).sum()), "n_hc_segments": int((y == 0).sum()),
           "n_subjects": int(len(subs)), "n_pd": int(ysub.sum()), "n_hc": int((ysub == 0).sum()),
           "paper_reported_10x10fold_knn": {"TShEn": 99.89, "ThEn": 99.72, "SuEn": 99.66, "LogEn": 97.94, "Eng": 97.00,
                                            "LBP": 97.03, "ShEn": 80.33, "NoEn": 89.98},
           "by_feature": {}}
for m, A in F.items():
    X = flat(A)
    mf, sf_ = seg_folds(X, y)
    gm, gs = group_cv(X, y)
    metrics["by_feature"][m] = {"SEG_10x10fold_acc_mean_sd_over_folds": [round(mf, 4), round(sf_, 4)],
                                "SUBJ_loso": loso(X, y),
                                "SUBJ_grouped_10x10fold_acc_mean_sd_over_repeats": [round(gm, 4), round(gs, 4)]}
    print(m, json.dumps(metrics["by_feature"][m]), flush=True)

PRIMARY = "ThEn"
X = flat(F[PRIMARY])
metrics["primary_feature"] = PRIMARY
# subject-level label permutation for LOSO (segments of a subject keep a shared label)
null = []
for _ in range(N_PERM):
    perm = dict(zip(subs, rng.permutation(ysub)))
    yp = np.array([perm[s] for s in g])
    p = cross_val_predict(knn(), X, yp, groups=g, cv=LeaveOneGroupOut())
    null.append((p == yp).mean())
obs = metrics["by_feature"][PRIMARY]["SUBJ_loso"]["segment_acc"]
metrics["SUBJ_loso_permutation"] = {"n_perm": N_PERM, "observed_segment_acc": obs,
                                    "null_mean": round(float(np.mean(null)), 4), "null_95pct": round(float(np.quantile(null, 0.95)), 4),
                                    "p": round(float((1 + np.sum(np.array(null) >= obs)) / (1 + N_PERM)), 4)}
# alternative explanation 1: subject fingerprinting
rand = []
for _ in range(N_RANDLAB):
    lab = dict(zip(subs, rng.permutation(ysub)))
    yr = np.array([lab[s] for s in g])
    rand.append(seg_cv(X, yr, reps=1)[0])
sid = np.searchsorted(subs, g)
metrics["IDENT"] = {"SEG_10fold_acc_with_random_subject_labels": {"n_assignments": N_RANDLAB, "mean": round(float(np.mean(rand)), 4),
                                                                   "min": round(float(np.min(rand)), 4), "max": round(float(np.max(rand)), 4)},
                    "subject_id_31way_SEG_10fold_acc": round(seg_cv(X, sid, reps=3)[0], 4), "chance_31way": round(1 / len(subs), 4)}
# alternative explanation 2: which bands carry it (cD1 cD2 cD3 cD4 cA4 orig)
for name, bands in {"low_cA4_cD4_0_32Hz": [3, 4], "high_cD1_cD3_32_256Hz": [0, 1, 2], "orig_only": [5]}.items():
    Xb = flat(F[PRIMARY], bands)
    metrics.setdefault("BAND", {})[name] = {"SEG_10x10fold": [round(v, 4) for v in seg_folds(Xb, y)], "SUBJ_loso": loso(Xb, y)}
ld = pd.DataFrame(line)
ld.to_csv(OUT / "recording_qc.csv", index=False)
metrics["BAND"]["line60_ratio_median_by_group"] = {"HC": float(ld[ld.group == 0].line60_ratio.median()),
                                                   "PD": float(ld[ld.group == 1].line60_ratio.median()),
                                                   "mannwhitney_p": float(stats.mannwhitneyu(ld[ld.group == 0].line60_ratio,
                                                                                            ld[ld.group == 1].line60_ratio).pvalue)}
metrics["BAND"]["log_power_64_128Hz_by_group"] = {"HC": float(ld[ld.group == 0].pow_64_128.mean()), "PD": float(ld[ld.group == 1].pow_64_128.mean()),
                                                  "mannwhitney_p": float(stats.mannwhitneyu(ld[ld.group == 0].pow_64_128,
                                                                                           ld[ld.group == 1].pow_64_128).pvalue)}
# pipeline variants on the primary feature
metrics["variants_primary"] = {
    "causal_filter_sosfilt": {"SEG_10x10fold": [round(v, 4) for v in seg_folds(flat(F_causal), y)], "SUBJ_loso": loso(flat(F_causal), y)},
    "filter_whole_recording_then_segment": {"SEG_10x10fold": [round(v, 4) for v in seg_folds(flat(F_whole), y)],
                                            "SUBJ_loso": loso(flat(F_whole), y),
                                            "SUBJ_grouped_10x10fold": [round(v, 4) for v in group_cv(flat(F_whole), y)]},
    "zscored_features": {"SEG_10x10fold": None, "SUBJ_loso": loso(X, y, model=lambda: make_pipeline(StandardScaler(), knn()))},
}
a = [(make_pipeline(StandardScaler(), knn()).fit(X[tr], y[tr]).predict(X[te]) == y[te]).mean()
     for tr, te in RepeatedStratifiedKFold(n_splits=10, n_repeats=10, random_state=0).split(X, y)]
metrics["variants_primary"]["zscored_features"]["SEG_10x10fold"] = [round(float(np.mean(a)), 4), round(float(np.std(a)), 4)]
pd.DataFrame({"subject": g, "label_pd": y}).assign(**{f"{PRIMARY}_{i}": X[:, i] for i in range(X.shape[1])}).to_csv(
    OUT / "segment_features_ThEn.csv", index=False)
(OUT / "metrics.json").write_text(json.dumps(metrics, indent=2))
print(json.dumps({k: v for k, v in metrics.items() if k != "by_feature"}, indent=2))
print(f"total {time.time() - t0:.0f}s")
