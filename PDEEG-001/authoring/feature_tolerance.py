"""Authoring QA: how far do implementation variants move the 192 threshold-entropy features?

Compares each variant with tests/reference.py and prints the fraction of feature values inside
the grader's band, max(5, 2% of the reference). Variants of the stated method should land at
>= 99%; a different method should not. Not part of grading.

    DS002778_DIR=<staged ds002778> python authoring/feature_tolerance.py
"""
import sys
from pathlib import Path

import mne
import numpy as np
import pywt
from scipy import signal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
import reference as R  # noqa: E402

mne.set_log_level("ERROR")
SOS = signal.butter(5, (0.5, 32), "bandpass", fs=R.FS, output="sos")
BA = signal.butter(5, (0.5, 32), "bandpass", fs=R.FS)
VARIANTS = {
    "stated (waverec, zeroed coefficients)": {},
    "per-segment demean": {"seg_demean": True},
    "filtfilt(b, a)": {"filt": "ba"},
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
                 "causal": lambda a: signal.sosfilt(SOS, a, axis=1),
                 "whole": lambda a: whole[:, s:s + R.SEG]}[filt](seg)
            out.append(np.concatenate([(np.abs(subbands(ch, mode)) > thr).sum(1) for ch in f]))
    return np.array(out, float)


_, ref = R.reference_segments()
for name, kw in VARIANTS.items():
    d = np.abs(features(**kw) - ref)
    print(f"{name:40s} within band {np.mean(d <= np.maximum(5, 0.02 * ref)):.4f}  max |diff| {d.max():.0f}", flush=True)
