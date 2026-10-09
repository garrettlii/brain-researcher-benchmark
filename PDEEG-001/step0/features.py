"""Feature extraction shared by the PDEEG-001 Step-0 probes (same definitions as probe.py).

db4 level-4 DWT, each sub-band reconstructed separately (MATLAB wrcoef), plus the segment;
entropies follow MATLAB's legacy wentropy definitions on signal values in uV.
"""
import numpy as np
import pywt
from scipy import signal

EPS = np.finfo(float).eps
SANDIEGO_32 = ["Fp1", "AF3", "F7", "F3", "FC1", "FC5", "T7", "C3", "CP1", "CP5", "P7", "P3", "Pz", "PO3", "O1", "Oz",
               "O2", "PO4", "P4", "P8", "CP6", "CP2", "C4", "T8", "FC6", "FC2", "F4", "F8", "AF4", "Fp2", "Fz", "Cz"]


def bandpass_sos(fs):
    return signal.butter(5, [0.5, 32], btype="bandpass", fs=fs, output="sos")


def subbands(s):
    """cD1, cD2, cD3, cD4, cA4 reconstructed separately, then the segment itself (6 x N)."""
    c = pywt.wavedec(s, "db4", level=4, mode="symmetric")
    rec = []
    for i in range(5):
        z = [x if j == i else np.zeros_like(x) for j, x in enumerate(c)]
        rec.append(pywt.waverec(z, "db4", mode="symmetric")[: s.shape[-1]])
    return np.stack(rec[::-1] + [s])


def tshen(S):
    """Paper Eqs. 8-9, best effort (values rounded to integers; k = number of unique values)."""
    T = np.round(np.where(S > 1, 255.0, np.where(S < 0, 0.0, 255.0 * S)))
    out = np.empty(S.shape[:-1])
    for idx in np.ndindex(S.shape[:-1]):
        v = T[idx]
        out[idx] = -(v ** 2 * np.log(v ** 2 + EPS)).sum() / len(np.unique(v))
    return out


METRICS = {
    "LogEn": lambda S: np.log(S ** 2 + EPS).sum(-1),
    "ThEn": lambda S: (np.abs(S) > 0.2).sum(-1).astype(float),
    "SuEn": lambda S: S.shape[-1] - (np.abs(S) <= 3).sum(-1) + np.minimum(S ** 2, 9).sum(-1),
    "TShEn": tshen,
}


def segment_features(seg, sos):
    """seg: channels x samples (uV). Returns {metric: channels x 6}."""
    seg = seg - seg.mean(1, keepdims=True)
    sf = signal.sosfiltfilt(sos, seg, axis=1)
    B = np.stack([subbands(ch) for ch in sf])
    return {m: fn(B) for m, fn in METRICS.items()}
