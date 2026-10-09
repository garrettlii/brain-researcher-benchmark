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
    d = (Xte ** 2).sum(1)[:, None] + (Xtr ** 2).sum(1)[None] - 2 * Xte @ Xtr.T
    nn = np.argsort(d, axis=1, kind="stable")[:, :3]
    votes = (ytr[nn] == "PD").sum(1)
    return np.where(votes >= 2, "PD", "HC")
