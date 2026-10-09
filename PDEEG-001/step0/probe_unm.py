"""Step-0 probe 2 for PDEEG-001: the paper's subject-independent (LOSO) claim on the UNM cohort.

Aljalal et al. 2022 report, for the UNM resting EEG set (27 PD, 27 matched HC; PRED+CT d002):
  Tables 10-11  segment-level 10 x 10-fold CV ~99% (2 s segments, eyes open and closed separately)
  Table 12      leave-one-subject-out (LOSO) 77.8-88.6% after greedy forward channel selection
                (FA) that keeps the channel subset maximising the LOSO accuracy itself
                (caption: off-PD vs HC; text: on-PD vs HC; eyes state not stated).
Measured here, for {off, on}-PD vs HC x {eyes open, closed} x {ThEn, SuEn, LogEn, TShEn}:
  SEG        segment-level 10 x 10-fold KNN (paper Tables 10-11)
  LOSO_ALL   LOSO KNN on all 32 channels, no selection
  FA_PAPER   the paper's procedure: forward selection scored by LOSO on all 54 subjects
             (the reported number is the max over the 32 selection steps)
  FA_NESTED  the same selection run inside each outer LOSO fold on the 53 training subjects,
             scored on the held-out subject (subject-independent estimate of the procedure)
  FA_NULL    FA_PAPER on subject-level permuted labels: how high selection alone goes
  LDA        FA_PAPER with LDA + SuEn (the paper's best Table 12 cell, 88.58%)
Preprocessing (unstated for UNM in the paper): per-recording channel demeaning, the file's
average reference, 32 SanDiego channels, 2 s segments from the 1 s rest triggers, segment
demeaning, 0.5-32 Hz 5th-order Butterworth (zero phase), features as in probe.py.

    UNM_D002_DIR=/path/to/d002 CACHE=/tmp/x python step0/probe_unm.py > step0/run_unm.log 2>&1
"""
import json
import multiprocessing as mp
import os
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io as sio
from scipy import stats
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.neighbors import KNeighborsClassifier

sys.path.insert(0, str(Path(__file__).resolve().parent))
from features import SANDIEGO_32, bandpass_sos, segment_features  # noqa: E402

warnings.filterwarnings("ignore")
DATA = Path(os.environ.get("UNM_D002_DIR", "d002"))
CACHE = Path(os.environ.get("CACHE", Path(__file__).resolve().parent / "cache"))
OUT = Path(__file__).resolve().parent / "outputs"
CACHE.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
FS, SEGLEN = 500, 2.0
N_NULL = int(os.environ.get("N_NULL", 100))
NJOBS = int(os.environ.get("NJOBS", 8))
FEATS = ["ThEn", "SuEn", "LogEn", "TShEn"]
PRIMARY = "ThEn"
t0 = time.time()
log = lambda *a: print(f"{time.time() - t0:6.0f}s", *a, flush=True)  # noqa: E731

meta = pd.read_excel(DATA / "IMPORT_ME_REST.xlsx", sheet_name="Sheet1")
recs = []
for _, r in meta.iterrows():
    off = 1 if str(r["1st Visit Meds Status"]).strip().upper() == "OFF" else 2
    recs += [(f"PD{int(r.PD_ID)}", int(r.PD_ID), off, "off"), (f"PD{int(r.PD_ID)}", int(r.PD_ID), 3 - off, "on"),
             (f"HC{int(r['MATCH CTL_ID'])}", int(r["MATCH CTL_ID"]), 1, "hc")]

# ---------------------------------------------------------------- features (cached)
cache = CACHE / "unm_features.npz"
if cache.exists():
    z = np.load(cache, allow_pickle=True)
    F = {k: z[k] for k in FEATS}; seg_subj, seg_cond, seg_eyes = z["subj"], z["cond"], z["eyes"]
    nseg = json.loads(str(z["nseg"]))
else:
    sos = bandpass_sos(FS)
    F = {k: [] for k in FEATS}; seg_subj, seg_cond, seg_eyes, nseg = [], [], [], {}
    for name, sid, ses, cond in recs:
        E = sio.loadmat(DATA / f"{sid}_{ses}_PD_REST.mat", struct_as_record=False, squeeze_me=True)["EEG"]
        labs = [c.labels for c in E.chanlocs]
        x = E.data[[labs.index(c) for c in SANDIEGO_32]].astype(float)
        x = x - x.mean(1, keepdims=True)
        n = 0
        for eyes, trig in (("closed", "S  3"), ("open", "S  1")):
            for e in E.event:
                if e.type == trig:
                    a = int(round(e.latency)) - 1
                    if a + int(SEGLEN * FS) <= x.shape[1]:
                        f = segment_features(x[:, a:a + int(SEGLEN * FS)], sos)
                        for k in FEATS:
                            F[k].append(f[k])
                        seg_subj.append(name); seg_cond.append(cond); seg_eyes.append(eyes); n += 1
        nseg[f"{name}_{cond}"] = n
        log(f"{name} {cond} ses{ses}: {n} segments")
    F = {k: np.array(v, dtype=np.float32) for k, v in F.items()}
    seg_subj, seg_cond, seg_eyes = np.array(seg_subj), np.array(seg_cond), np.array(seg_eyes)
    np.savez_compressed(cache, subj=seg_subj, cond=seg_cond, eyes=seg_eyes, nseg=json.dumps(nseg), **F)

if os.environ.get("STAGE") == "features":
    sys.exit(0)


# ---------------------------------------------------------------- helpers
def cp(k, n):
    return [round(float(stats.beta.ppf(0.025, k, n - k + 1)) if k else 0.0, 3),
            round(float(stats.beta.ppf(0.975, k + 1, n - k)) if k < n else 1.0, 3)]


class Problem:
    """One classification problem: segments, labels, subjects, per-channel squared distances."""

    def __init__(self, cond, eyes, feat):
        m = ((seg_cond == cond) | (seg_cond == "hc")) & (seg_eyes == eyes)
        self.X = F[feat][m].astype(np.float64)                         # n x 32 x 6
        self.y = (seg_cond[m] != "hc").astype(int)
        self.g = seg_subj[m]
        self.subs, self.gi = np.unique(self.g, return_inverse=True)
        self.n = len(self.y)
        self.same = self.gi[:, None] == self.gi[None, :]
        Xc = self.X.transpose(1, 0, 2)                                 # 32 x n x 6
        sq = (Xc ** 2).sum(-1)
        self.Dc = (sq[:, :, None] + sq[:, None, :] - 2 * np.einsum("cif,cjf->cij", Xc, Xc)).clip(min=0).astype(np.float32)


def knn_rows(D, y, rows):
    idx = np.argpartition(D[rows], 3, axis=1)[:, :3]
    return (y[idx].sum(1) >= 2).astype(int)


def loso_acc(P, D, y, train_subj=None):
    """Mean over subjects of per-subject segment accuracy (the paper's LOSO average).
    train_subj: boolean over subject indices; if given, only those subjects are used (as both
    test rows and neighbours)."""
    M = np.where(P.same, np.inf, 0).astype(np.float32)
    rows = np.arange(P.n)
    if train_subj is not None:
        keep = train_subj[P.gi]
        M[:, ~keep] = np.inf
        rows = rows[keep]
    pred = knn_rows(D + M, y, rows)
    ok = pred == y[rows]
    gs = P.gi[rows]
    return float(np.mean([ok[gs == s].mean() for s in np.unique(gs)]))


def forward_select(P, y, train_subj=None):
    """Paper's FA: add the channel that maximises LOSO accuracy; return best (acc, subset)."""
    sel, rem = [], list(range(32))
    Dsel = np.zeros((P.n, P.n), np.float32)
    best = (-1, None)
    for _ in range(32):
        scores = [loso_acc(P, Dsel + P.Dc[c], y, train_subj) for c in rem]
        j = int(np.argmax(scores)); c = rem.pop(j); sel.append(c); Dsel = Dsel + P.Dc[c]
        if scores[j] > best[0]:
            best = (scores[j], list(sel))
    return best


_P = None


def _nested_one(s):
    P = _P
    train = np.ones(len(P.subs), bool); train[s] = False
    acc, subset = forward_select(P, P.y, train)
    D = P.Dc[subset].sum(0) + np.where(P.same, np.inf, 0).astype(np.float32)
    rows = np.flatnonzero(P.gi == s)
    pred = knn_rows(D, P.y, rows)
    return s, float((pred == P.y[rows]).mean()), int(len(subset)), acc


def _null_one(seed):
    P = _P
    r = np.random.default_rng(seed)
    ys = np.array([P.y[P.gi == s][0] for s in range(len(P.subs))])
    yp = r.permutation(ys)[P.gi]
    return forward_select(P, yp)[0]


def summarize_subjects(P, per_subj_acc):
    ys = np.array([P.y[P.gi == s][0] for s in range(len(P.subs))])
    votes = (np.array([a if ys[s] == 1 else 1 - a for s, a in enumerate(per_subj_acc)]) >= 0.5).astype(int)
    k = int((votes == ys).sum())
    return {"loso_mean_subject_acc": round(float(np.mean(per_subj_acc)), 4), "subject_vote_correct": k,
            "n_subjects": len(ys), "subject_vote_ci95_exact": cp(k, len(ys))}


# ---------------------------------------------------------------- analyses
# resumable: configs already in metrics_unm.json are skipped; the file is rewritten after each config
MPATH = OUT / "metrics_unm.json"
results = json.loads(MPATH.read_text()) if MPATH.exists() else {"configs": {}}
results["n_segments_by_recording"] = nseg


def save():
    MPATH.write_text(json.dumps(results, indent=2))
ctx = mp.get_context("fork")
for cond in ("off", "on"):
    for eyes in ("open", "closed"):
        for feat in FEATS:
            key = f"{cond}PD_vs_HC|{eyes}|{feat}"
            if key in results["configs"]:
                continue
            P = Problem(cond, eyes, feat)
            Xf = P.X.reshape(P.n, -1)
            seg = []
            for rep in range(10):
                p = cross_val_predict(KNeighborsClassifier(3), Xf, P.y, cv=StratifiedKFold(10, shuffle=True, random_state=rep))
                seg.append((p == P.y).mean())
            Dall = P.Dc.sum(0) + np.where(P.same, np.inf, 0).astype(np.float32)
            pred = knn_rows(Dall, P.y, np.arange(P.n))
            per = [float((pred[P.gi == s] == P.y[P.gi == s]).mean()) for s in range(len(P.subs))]
            fa_acc, fa_sub = forward_select(P, P.y)
            res = {"n_pd_segments": int(P.y.sum()), "n_hc_segments": int((P.y == 0).sum()),
                   "SEG_10x10fold_acc": round(float(np.mean(seg)), 4),
                   "LOSO_ALL": summarize_subjects(P, per),
                   "FA_PAPER": {"loso_acc_max_over_steps": round(fa_acc, 4), "n_channels": len(fa_sub),
                                "channels": [SANDIEGO_32[c] for c in fa_sub]}}
            if feat == PRIMARY:
                _P = P
                with ctx.Pool(NJOBS) as pool:
                    nested = sorted(pool.map(_nested_one, range(len(P.subs))))
                res["FA_NESTED"] = summarize_subjects(P, [a for _, a, _, _ in nested])
                res["FA_NESTED"]["inner_selected_n_channels_median"] = float(np.median([k for _, _, k, _ in nested]))
                res["FA_NESTED"]["inner_fa_acc_mean"] = round(float(np.mean([i for _, _, _, i in nested])), 4)
                if cond == "off" and eyes == "open":
                    with ctx.Pool(NJOBS) as pool:
                        null = np.array(pool.map(_null_one, range(N_NULL)))
                    res["FA_NULL"] = {"n_perm": N_NULL, "mean": round(float(null.mean()), 4),
                                      "pct95": round(float(np.quantile(null, 0.95)), 4), "max": round(float(null.max()), 4),
                                      "p_observed_fa": round(float((1 + (null >= fa_acc).sum()) / (1 + N_NULL)), 4)}
            results["configs"][key] = res
            save()
            log(key, json.dumps(res))
        # paper's best Table 12 cell: SuEn + LDA with FA scored by LOSO
        if f"{cond}PD_vs_HC|{eyes}|SuEn_LDA" in results["configs"]:
            continue
        P = Problem(cond, eyes, "SuEn")
        Xs = P.X  # n x 32 x 6
        sel, rem, best = [], list(range(32)), (-1, None)
        for _ in range(32):
            sc = []
            for c in rem:
                Xi = Xs[:, sel + [c]].reshape(P.n, -1)
                acc_s = []
                for s in range(len(P.subs)):
                    te = P.gi == s
                    lda = LinearDiscriminantAnalysis().fit(Xi[~te], P.y[~te])
                    acc_s.append((lda.predict(Xi[te]) == P.y[te]).mean())
                sc.append(float(np.mean(acc_s)))
            j = int(np.argmax(sc)); sel.append(rem.pop(j))
            if sc[j] > best[0]:
                best = (sc[j], list(sel))
        results["configs"][f"{cond}PD_vs_HC|{eyes}|SuEn_LDA"] = {"FA_PAPER": {"loso_acc_max_over_steps": round(best[0], 4),
                                                                             "n_channels": len(best[1])}}
        log(f"{cond}|{eyes}|SuEn_LDA FA_PAPER {best[0]:.4f} ({len(best[1])} ch)")
        save()

results["paper_reported"] = {"Table10_KNN_SEG_offPD_HC": {"open": {"LogEn": 98.64, "ThEn": 99.14, "SuEn": 97.53, "TShEn": 99.14},
                                                          "closed": {"LogEn": 99.06, "ThEn": 99.43, "SuEn": 96.17, "TShEn": 99.18}},
                             "Table10_KNN_SEG_onPD_HC": {"open": {"LogEn": 98.91, "ThEn": 99.52, "SuEn": 96.73, "TShEn": 99.21},
                                                         "closed": {"LogEn": 98.71, "ThEn": 99.20, "SuEn": 95.75, "TShEn": 98.89}},
                             "Table12_LOSO_FA_KNN": {"LogEn": [83.95, 9], "ThEn": [82.41, 16], "SuEn": [83.64, 15], "TShEn": [85.19, 14]},
                             "Table12_LOSO_FA_LDA": {"SuEn": [88.58, 21]},
                             "Table12_pairing": "caption off-PD vs HC; text on-PD vs HC; eyes state not stated"}
save()
log("done")
