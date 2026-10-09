"""Grader-side recomputation for PDEEG-001, written independently of solution/compute.py.

Reference features come from the staged BDF files, so nothing in the grader is a stored
answer. Cross-validated predictions are replayed from the submitted features and fold
assignments with a plain nearest-neighbour vote.
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pywt
from scipy import signal

DATA = Path(os.environ.get("DS002778_DIR", "/app/data/ds002778"))
FS, SEG = 512, 5120
CHANNELS = ["Fp1", "AF3", "F7", "F3", "FC1", "FC5", "T7", "C3", "CP1", "CP5", "P7", "P3", "Pz", "PO3", "O1", "Oz",
            "O2", "PO4", "P4", "P8", "CP6", "CP2", "C4", "T8", "FC6", "FC2", "F4", "F8", "AF4", "Fp2", "Fz", "Cz"]
SIGNALS = ["D1", "D2", "D3", "D4", "A4", "X"]
FEATURES = [f"{c}_{s}" for c in CHANNELS for s in SIGNALS]


def recordings():
    part = pd.read_csv(DATA / "participants.tsv", sep="\t")
    out = []
    for pid in part.participant_id:
        ses, grp = ("ses-hc", "HC") if pid.startswith("sub-hc") else ("ses-off", "PD")
        out.append((pid, grp, DATA / pid / ses / "eeg" / f"{pid}_{ses}_task-rest_eeg.bdf"))
    return out


def wrcoef(x):
    """Single-branch reconstructions at full length: rows D1, D2, D3, D4, A4."""
    n = len(x)
    cA4, cD4, cD3, cD2, cD1 = pywt.wavedec(x, "db4", mode="symmetric", level=4)
    rows = []
    for lev, d in ((1, cD1), (2, cD2), (3, cD3), (4, cD4)):
        rows.append(pywt.upcoef("d", d, "db4", level=lev, take=n))
    rows.append(pywt.upcoef("a", cA4, "db4", level=4, take=n))
    return np.array(rows)


def reference_segments():
    import mne
    mne.set_log_level("ERROR")
    sos = signal.butter(5, (0.5, 32.0), "bandpass", fs=FS, output="sos")
    meta, feats = [], []
    for pid, grp, path in recordings():
        raw = mne.io.read_raw_bdf(path, preload=True, verbose="ERROR")
        v = raw.get_data(picks=CHANNELS) * 1e6
        v -= v.mean(axis=1, keepdims=True)
        v -= v.mean(axis=0, keepdims=True)
        for start in range(0, v.shape[1] - SEG + 1, SEG):
            filt = signal.sosfiltfilt(sos, v[:, start:start + SEG], axis=1)
            f = np.empty((len(CHANNELS), 6))
            for c in range(len(CHANNELS)):
                sig = np.vstack([wrcoef(filt[c]), filt[c][None]])
                f[c] = (np.abs(sig) > 0.2).sum(axis=1)
            meta.append((pid, grp, start))
            feats.append(f.ravel())
    m = pd.DataFrame(meta, columns=["participant_id", "group", "start_sample"])
    return m, np.array(feats)


def knn3_predict(Xtr, ytr, Xte):
    """3-nearest-neighbour majority vote (Euclidean, unscaled). Rejects inputs on which a
    3-NN vote is undefined instead of returning a default label."""
    Xtr, Xte, ytr = np.asarray(Xtr, float), np.asarray(Xte, float), np.asarray(ytr, dtype=object)
    if Xtr.ndim != 2 or Xte.ndim != 2 or Xtr.shape[1] != Xte.shape[1]:
        raise ValueError(f"feature arrays must be 2-D with matching columns, got {Xtr.shape} and {Xte.shape}")
    if len(Xtr) < 3:
        raise ValueError(f"3-NN needs at least 3 training samples, got {len(Xtr)}")
    if len(Xte) == 0:
        raise ValueError("empty test set")
    if len(ytr) != len(Xtr) or not set(ytr) <= {"PD", "HC"}:
        raise ValueError("training labels must be PD/HC, one per training sample")
    if not (np.isfinite(Xtr).all() and np.isfinite(Xte).all()):
        raise ValueError("non-finite feature values")
    d = (Xte ** 2).sum(1)[:, None] + (Xtr ** 2).sum(1)[None] - 2 * Xte @ Xtr.T
    nn = np.argsort(d, axis=1, kind="stable")[:, :3]
    votes = (ytr[nn] == "PD").sum(1)
    return np.where(votes >= 2, "PD", "HC")


def majority_vote_accuracy(pred, truth, pid):
    """Per-participant majority vote: PD if more than half of the participant's segments are
    predicted PD, HC if fewer than half; an exact tie counts as an error."""
    share = pd.Series(np.asarray(pred) == "PD").groupby(np.asarray(pid)).mean()
    label = pd.Series(np.asarray(truth)).groupby(np.asarray(pid)).first().loc[share.index]
    vote = np.where(share > 0.5, "PD", np.where(share < 0.5, "HC", "tie"))
    return float(np.mean(vote == label.to_numpy()))
