"""Authoring QA: how far do implementation variants move the features and the KNN predictions?

For each variant this prints, against tests/reference.py:
  * the fraction of feature values inside the grader's band, max(5, 2% of the reference),
    overall, for the worst column and for the worst segment;
  * how often 3-NN predictions made from the variant's features agree with predictions made
    from the reference features on the same folds (paper 10 x 10-fold, leave-one-participant-out),
    and the resulting accuracy difference.
Variants of the stated method should pass every grader threshold; a different method or a
manipulated table should not. Not part of grading.

    DS002778_DIR=<staged ds002778> python authoring/feature_tolerance.py
"""
import sys
from pathlib import Path

import mne
import numpy as np
import pywt
from scipy import signal
from sklearn.model_selection import LeaveOneGroupOut, RepeatedStratifiedKFold

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
import reference as R  # noqa: E402

mne.set_log_level("ERROR")
SOS = signal.butter(5, (0.5, 32), "bandpass", fs=R.FS, output="sos")
BA = signal.butter(5, (0.5, 32), "bandpass", fs=R.FS)
VARIANTS = {
    "stated (waverec, zeroed coefficients)": {},
    "per-segment demean": {"seg_demean": True},
    "filtfilt(b, a)": {"filt": "ba"},
    "MNE filter_data (IIR sos, zero phase)": {"filt": "mne"},
    "filter whole recording, then segment": {"filt": "whole"},
    "no re-reference": {"car": False},
    "causal filter (sosfilt)": {"filt": "causal"},
    "periodic extension": {"mode": "periodization"},
    "threshold 0.1": {"thr": 0.1},
}


def subbands(x, mode):
    c = pywt.wavedec(x, "db4", level=4, mode=mode)
    rec = []
    for i in range(5):
        z = [y if j == i else np.zeros_like(y) for j, y in enumerate(c)]
        rec.append(pywt.waverec(z, "db4", mode=mode)[: len(x)])
    return np.array(rec[::-1] + [x])


def mne_filter(a):
    return mne.filter.filter_data(a, R.FS, 0.5, 32, method="iir", phase="zero",
                                  iir_params=dict(order=5, ftype="butter", output="sos"), verbose="ERROR")


def features(seg_demean=False, filt="sos", car=True, mode="symmetric", thr=0.2):
    out = []
    for _, _, path in R.recordings():
        v = mne.io.read_raw_bdf(path, preload=True).get_data(picks=R.CHANNELS) * 1e6
        v -= v.mean(1, keepdims=True)
        if car:
            v -= v.mean(0, keepdims=True)
        whole = signal.sosfiltfilt(SOS, v, axis=1) if filt == "whole" else None
        for s in range(0, v.shape[1] - R.SEG + 1, R.SEG):
            seg = v[:, s:s + R.SEG]
            if seg_demean:
                seg = seg - seg.mean(1, keepdims=True)
            f = {"sos": lambda a: signal.sosfiltfilt(SOS, a, axis=1),
                 "ba": lambda a: signal.filtfilt(*BA, a, axis=1),
                 "mne": mne_filter,
                 "causal": lambda a: signal.sosfilt(SOS, a, axis=1),
                 "whole": lambda a: whole[:, s:s + R.SEG]}[filt](seg)
            out.append(np.concatenate([(np.abs(subbands(ch, mode)) > thr).sum(1) for ch in f]))
    return np.array(out, float)


def predictions(X, y, splits):
    p = np.empty(len(y), dtype=object)
    for tr, te in splits:
        p[te] = R.knn3_predict(X[tr], y[tr], X[te])
    return p


def main():
    meta, ref = R.reference_segments()
    y, g = meta.group.to_numpy(), meta.participant_id.to_numpy()
    splits = {"paper": [list(RepeatedStratifiedKFold(n_splits=10, n_repeats=10, random_state=0).split(ref, y))[r * 10:(r + 1) * 10]
                        for r in range(10)],
              "lopo": [list(LeaveOneGroupOut().split(ref, y, g))]}
    ref_pred = {k: [predictions(ref, y, s) for s in reps] for k, reps in splits.items()}

    def report(name, F):
        d = np.abs(F - ref)
        ok = d <= np.maximum(5, 0.02 * ref)
        line = (f"{name:42s} band all {ok.mean():.4f} col-min {ok.mean(0).min():.4f} seg-min {ok.mean(1).min():.4f}"
                f" max|d| {d.max():5.0f}")
        for k, reps in splits.items():
            pv = [predictions(F, y, s) for s in reps]
            agree = np.mean([np.mean(a == b) for a, b in zip(pv, ref_pred[k])])
            dacc = np.mean([np.mean(a == y) for a in pv]) - np.mean([np.mean(b == y) for b in ref_pred[k]])
            line += f" | {k} agree {agree:.4f} dacc {dacc:+.4f}"
        print(line, flush=True)

    for name, kw in VARIANTS.items():
        report(name, features(**kw))
    col = ref.copy()
    col[:, R.FEATURES.index("Fp1_D1")] = np.where(y == "PD", 5000.0, 0.0)
    report("manipulated: Fp1_D1 encodes diagnosis", col)
    report("manipulated: all columns +/-4 by diagnosis", ref + np.where(y == "PD", 4.0, -4.0)[:, None])


if __name__ == "__main__":
    main()
