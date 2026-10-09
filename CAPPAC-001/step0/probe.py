"""Step 0 for CAPPAC-001: Yeh & Shi 2018 (Sci Rep 8:3049) delta-alpha/low-beta phase-amplitude coupling
across CAP phase-A subtypes, healthy recordings n1-n16 of the PhysioNet CAP Sleep Database 1.0.0.

Scope, estimator and decision rules are fixed in step0/claim_scope.md (committed before this file).

  RAW      Tort MI (20 bins) of delta (0.25-2.5 Hz) phase vs 10-17 Hz amplitude on every included phase-A
           segment; subject means; paired A1 - A3 across subjects (d_raw). Reproduces if > 0, 95% CI excl. 0.
  PREMISE  (i) included A1 segments shorter than A3 (paired); (ii) the length floor (mean MI of 50
           within-segment circular-shift surrogates) is larger in A1 than A3: CI excl. 0 and >= 0.25 d_raw.
  CTRL     C-crop (primary): MI on the first 4.0 s of every included segment >= 4 s (>2-delta-cycle rule
           applied inside the window).  C-debias (secondary): full-length MI minus the segment's floor.
           "length accounts": both point <= 0.25 d_raw and upper CI < 0.5 d_raw.
           "coupling persists": both lower CI > 0 and point >= 0.5 d_raw.  Otherwise unresolved -> archive.

    DATA_DIR=~/.cache/brb/capslpdb python step0/probe.py
"""
import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from scipy.fft import next_fast_len
from scipy.signal import butter, hilbert, sosfiltfilt

DATA = Path(os.environ.get("DATA_DIR", "~/.cache/brb/capslpdb")).expanduser()
OUT = Path(__file__).resolve().parent / "outputs"
SUBJECTS = [f"n{i}" for i in range(1, 17)]
PRIMARY = ["C4-A1", "C4A1", "C3-A2", "C3A2"]      # central-mastoid; n6-n9 have only C3-A2
PHASE_BAND, AMP_BAND = (0.25, 2.5), (10.0, 17.0)
NBINS, NSURR, MIN_SEG = 20, 50, 5
WINDOWS = [(3.0, "first"), (4.0, "first"), (5.0, "first"), (6.0, "first"), (4.0, "mid")]
SUBTYPES = ["A1", "A2", "A3"]


def read_events(sid):
    lines = (DATA / f"{sid}.txt").read_text(errors="replace").splitlines()
    h = next(i for i, l in enumerate(lines) if l.startswith("Sleep Stage"))
    cols = [c.strip() for c in lines[h].split("\t")]
    rows = [l.split("\t") for l in lines[h + 1:] if l.strip()]
    df = pd.DataFrame([r[:len(cols)] for r in rows if len(r) >= len(cols)], columns=cols)
    dcol = next(c for c in cols if c.startswith("Duration"))
    df = df.rename(columns={"Sleep Stage": "stage", "Time [hh:mm:ss]": "clock", "Event": "event", dcol: "dur"})
    df["dur"] = df["dur"].astype(float)
    hms = df["clock"].str.split(":", expand=True).astype(int)
    df["tod"] = hms[0] * 3600 + hms[1] * 60 + hms[2]
    return df[["stage", "clock", "tod", "event", "dur"]]


def read_edf_channel(path, prefer):
    """One channel of an EDF at its native sampling rate (no resampling across mixed-rate records)."""
    with open(path, "rb") as f:
        h = f.read(256)
        hb, nrec, rdur, ns = int(h[184:192]), int(h[236:244]), float(h[244:252]), int(h[252:256])
        h2 = f.read(ns * 256)
    field = lambda off, w: [h2[ns * off + w * k: ns * off + w * (k + 1)].decode().strip() for k in range(ns)]
    labels = field(0, 16)
    pmin, pmax = map(float, field(104, 8)), map(float, field(112, 8))
    pmin, pmax = list(pmin), list(pmax)
    dmin, dmax = list(map(float, field(120, 8))), list(map(float, field(128, 8)))
    spr = list(map(int, field(216, 8)))
    ci = next(labels.index(c) for c in prefer if c in labels)
    tot = sum(spr)
    if nrec < 0:
        nrec = (Path(path).stat().st_size - hb) // (2 * tot)
    d = np.memmap(path, dtype="<i2", mode="r", offset=hb, shape=(nrec, tot))
    o = sum(spr[:ci])
    x = np.asarray(d[:, o:o + spr[ci]], dtype=float).ravel()
    gain = (pmax[ci] - pmin[ci]) / (dmax[ci] - dmin[ci])
    x = (x - dmin[ci]) * gain + pmin[ci]
    hh, mm, ss = (int(v) for v in h[176:184].decode().split("."))
    return x, spr[ci] / rdur, labels[ci], hh * 3600 + mm * 60 + ss


def load_signal(sid, prefer):
    return read_edf_channel(DATA / f"{sid}.edf", prefer)


def analytic(x, fs, band):
    y = sosfiltfilt(butter(4, band, btype="band", fs=fs, output="sos"), x)
    n = len(y)
    return hilbert(y, next_fast_len(n))[:n]


def mi(phase, amp):
    b = np.minimum((((phase + np.pi) / (2 * np.pi)) * NBINS).astype(int), NBINS - 1)
    s = np.bincount(b, weights=amp, minlength=NBINS)
    c = np.bincount(b, minlength=NBINS)
    m = np.divide(s, c, out=np.zeros(NBINS), where=c > 0)
    p = m / m.sum()
    p = p[p > 0]
    return (np.log(NBINS) + np.sum(p * np.log(p))) / np.log(NBINS)


def ncycles(phase):
    u = np.unwrap(phase)
    return (u[-1] - u[0]) / (2 * np.pi)


def floor(phase, amp, rng):
    n = len(amp)
    lags = rng.integers(int(0.2 * n), max(int(0.8 * n), int(0.2 * n) + 1), NSURR)
    return float(np.mean([mi(phase, np.roll(amp, k)) for k in lags]))


def segments(sid, x, fs, start, phase_band=PHASE_BAND, full=True):
    ev = read_events(sid)
    ph = np.angle(analytic(x, fs, phase_band))
    am = np.abs(analytic(x, fs, AMP_BAND))
    n = len(x)
    ev["onset"] = (ev["tod"] - start) % 86400
    mt = ev[ev["stage"].str.strip() == "MT"]
    mt_iv = list(zip(mt["onset"], mt["onset"] + mt["dur"]))
    rng = np.random.default_rng(int(sid[1:]))
    rows = []
    for _, e in ev[ev["event"].str.startswith("MCAP-A")].iterrows():
        on, d = float(e["onset"]), float(e["dur"])
        a, z = int(round(on * fs)), int(round((on + d) * fs))
        r = dict(subject=sid, subtype=e["event"][-2:], stage=e["stage"].strip(), onset=on, dur=d, excluded="")
        if r["stage"] == "MT" or any(on < b and on + d > a0 for a0, b in mt_iv):
            r["excluded"] = "MT"
        elif z > n or a < 0:
            r["excluded"] = "outside_edf"
        else:
            p, q = ph[a:z], am[a:z]
            r["cycles"] = ncycles(p)
            if r["cycles"] <= 2:
                r["excluded"] = "le2_delta_cycles"
            else:
                r["mi_raw"] = mi(p, q)
                if full:
                    r["floor"] = floor(p, q, rng)
                    r["mi_debias"] = r["mi_raw"] - r["floor"]
                    for L, pos in WINDOWS:
                        if d < L:
                            continue
                        k = int(round(L * fs))
                        s0 = a if pos == "first" else a + (z - a - k) // 2
                        pw, qw = ph[s0:s0 + k], am[s0:s0 + k]
                        if ncycles(pw) > 2:
                            r[f"mi_{pos}{L:g}"] = mi(pw, qw)
        rows.append(r)
    return rows


def one(sid):
    x, fs, ch, start = load_signal(sid, PRIMARY)
    rows = segments(sid, x, fs, start)
    for r in rows:
        r.update(channel=ch, fs=fs)
    key = {(round(r["onset"], 3), r["subtype"]): r for r in rows}
    # exploratory: delta 1-2.5 Hz (the paper's 1-50 Hz prefilter) and an F4-C4 bipolar derivation
    for r in segments(sid, x, fs, start, phase_band=(1.0, 2.5), full=False):
        if "mi_raw" in r:
            key[(round(r["onset"], 3), r["subtype"])]["mi_delta1"] = r["mi_raw"]
    try:
        xb, fsb, _, _ = load_signal(sid, ["F4-C4"])
        for r in segments(sid, xb, fsb, start, full=False):
            if "mi_raw" in r:
                key[(round(r["onset"], 3), r["subtype"])]["mi_f4c4"] = r["mi_raw"]
    except StopIteration:  # no F4-C4 in this montage
        pass
    return rows


def paired(d, seed=0):
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    n, m, s = len(d), d.mean(), d.std(ddof=1)
    tc = stats.t.ppf(0.975, n - 1) * s / np.sqrt(n)
    bs = np.random.default_rng(seed).choice(d, (10000, n))
    dz_bs = bs.mean(1) / bs.std(1, ddof=1)
    t = m / (s / np.sqrt(n))
    return dict(n=n, mean=m, ci=[m - tc, m + tc], dz=m / s,
                dz_ci=[float(np.percentile(dz_bs, 2.5)), float(np.percentile(dz_bs, 97.5))],
                t=t, p=float(2 * stats.t.sf(abs(t), n - 1)), wilcoxon_p=float(stats.wilcoxon(d).pvalue))


def contrast(seg, col, a="A1", b="A3", minseg=MIN_SEG):
    s = seg[np.isfinite(seg[col])]
    g = s.groupby(["subject", "subtype"])[col].agg(["mean", "count"]).unstack("subtype")
    g = g[(g["count"][a] >= minseg) & (g["count"][b] >= minseg)]
    res = paired(g["mean"][a] - g["mean"][b])
    res.update(mean_a=float(g["mean"][a].mean()), mean_b=float(g["mean"][b].mean()), subjects=list(g.index))
    return res


def fmt(r):
    return (f"{r['mean']:+.5f} [{r['ci'][0]:+.5f}, {r['ci'][1]:+.5f}]  d_z {r['dz']:+.2f} "
            f"[{r['dz_ci'][0]:+.2f}, {r['dz_ci'][1]:+.2f}]  t{r['n'] - 1}={r['t']:.2f} p={r['p']:.2g} "
            f"(W p={r['wilcoxon_p']:.2g})  n={r['n']}  a={r['mean_a']:.5f} b={r['mean_b']:.5f}")


def main():
    OUT.mkdir(exist_ok=True)
    with ProcessPoolExecutor(int(os.environ.get("WORKERS", 3))) as ex:
        rows = [r for rs in ex.map(one, SUBJECTS) for r in rs]
    allseg = pd.DataFrame(rows)
    allseg.to_csv(OUT / "segments.csv", index=False)
    seg = allseg[allseg["excluded"] == ""].copy()
    print("phase-A events by subtype:", allseg.groupby("subtype").size().to_dict())
    print("excluded:", allseg[allseg.excluded != ""].groupby(["subtype", "excluded"]).size().to_dict())
    print("included (paper Table S2 Control: A1 2741, A2 829, A3 820):", seg.groupby("subtype").size().to_dict())
    print("channel/fs by subject:", allseg.groupby("subject")[["channel", "fs"]].first().to_dict("index"))
    m = {"included": seg.groupby("subtype").size().to_dict()}

    # RAW
    raw = contrast(seg, "mi_raw")
    m["raw_A1_A3"] = raw
    print("\nRAW  A1-A3 MI:", fmt(raw))
    for a, b in [("A1", "A2"), ("A2", "A3")]:
        m[f"raw_{a}_{b}"] = contrast(seg, "mi_raw", a, b)
        print(f"RAW  {a}-{b} MI:", fmt(m[f"raw_{a}_{b}"]))
    print("subject-mean MI by subtype:",
          seg.groupby(["subject", "subtype"])["mi_raw"].mean().unstack().mean().round(5).to_dict())
    import statsmodels.formula.api as smf
    md = smf.mixedlm("mi_raw ~ C(subtype, Treatment('A3'))", seg, groups=seg["subject"]).fit()
    m["mixedlm"] = {k: [float(md.params[k]), float(md.pvalues[k])] for k in md.params.index if "subtype" in k}
    print("segment-level mixed model (ref A3):", {k: f"{v[0]:+.5f} p={v[1]:.2g}" for k, v in m["mixedlm"].items()})
    d_raw = raw["mean"]

    # PREMISE
    dur, fl = contrast(seg, "dur"), contrast(seg, "floor")
    m["premise_duration_A1_A3"], m["premise_floor_A1_A3"] = dur, fl
    print("\nPREMISE duration A1-A3 (s):", fmt(dur))
    print("PREMISE floor    A1-A3 MI:", fmt(fl), f" floor/d_raw = {fl['mean'] / d_raw:.2f}")
    prem = bool(dur["ci"][1] < 0 and fl["ci"][0] > 0 and fl["mean"] >= 0.25 * d_raw)
    m["premise_holds"] = prem
    print("PREMISE holds:", prem)

    # CTRL
    crop, deb = contrast(seg, "mi_first4"), contrast(seg, "mi_debias")
    m["ctrl_crop4_A1_A3"], m["ctrl_debias_A1_A3"] = crop, deb
    print("\nCTRL C-crop (first 4 s) A1-A3:", fmt(crop), f" ratio {crop['mean'] / d_raw:.2f}")
    print("CTRL C-debias          A1-A3:", fmt(deb), f" ratio {deb['mean'] / d_raw:.2f}")
    accounts = all(c["mean"] <= 0.25 * d_raw and c["ci"][1] < 0.5 * d_raw for c in (crop, deb))
    persists = all(c["ci"][0] > 0 and c["mean"] >= 0.5 * d_raw for c in (crop, deb))
    rawok = bool(raw["mean"] > 0 and raw["ci"][0] > 0)
    verdict = ("not reproduced" if not rawok else "length bias accounts" if accounts and prem
               else "coupling difference persists" if persists else "unresolved")
    m.update(raw_reproduces=rawok, ctrl_accounts=accounts, ctrl_persists=persists, verdict=verdict)
    print(f"\nVERDICT: RAW reproduces={rawok}  PREMISE={prem}  accounts={accounts}  persists={persists}  -> {verdict}")

    # exploratory (outside the decision)
    print("\n--- exploratory (not part of the decision) ---")
    ex = {}
    for col in ["mi_first3", "mi_first5", "mi_first6", "mi_mid4", "mi_delta1", "mi_f4c4"]:
        if col in seg and seg[col].notna().sum():
            try:
                ex[col] = contrast(seg, col)
                print(f"{col:10s} A1-A3:", fmt(ex[col]))
            except Exception as e:  # e.g. too few subjects with the derivation
                print(f"{col:10s} A1-A3: n/a ({e})")
    for col in ["mi_raw", "mi_first4", "mi_debias"]:
        for a, b in [("A1", "A2"), ("A2", "A3")]:
            ex[f"{col}_{a}_{b}"] = contrast(seg, col, a, b)
            print(f"{col:10s} {a}-{b}:", fmt(ex[f'{col}_{a}_{b}']))
    s2 = seg[(seg.dur >= 4) & (seg.dur < 10) & seg.subtype.isin(["A1", "A3"])].assign(bin=lambda d: np.floor(d.dur))
    g = s2.groupby(["subject", "bin", "subtype"])["mi_raw"].mean().unstack().dropna()
    ex["duration_matched_A1_A3"] = r = paired(g["A1"].sub(g["A3"]).groupby("subject").mean().values)
    print(f"duration-matched (1-s bins, 4-10 s) A1-A3: {r['mean']:+.5f} [{r['ci'][0]:+.5f}, {r['ci'][1]:+.5f}] "
          f"d_z {r['dz']:+.2f} n={r['n']}")
    slopes = {}
    for st in SUBTYPES:
        sl = [stats.linregress(1 / d.dur, d.mi_raw).slope for _, d in seg[seg.subtype == st].groupby("subject")
              if len(d) >= MIN_SEG]
        slopes[st] = r = paired(sl)
        print(f"MI ~ 1/duration slope within {st}: {r['mean']:+.4f} [{r['ci'][0]:+.4f}, {r['ci'][1]:+.4f}] n={r['n']}")
    ex["mi_vs_invdur_slope"] = slopes
    a1 = seg[seg.subtype == "A1"].assign(subtype=lambda d: d.stage)
    for col in ["mi_raw", "mi_first4", "mi_debias", "dur"]:
        try:
            ex[f"A1_S2_S4_{col}"] = contrast(a1, col, "S2", "S4")
            print(f"A1 S2-S4 {col:9s}:", fmt(ex[f'A1_S2_S4_{col}']))
        except Exception as e:
            print(f"A1 S2-S4 {col:9s}: n/a ({e})")
    m["exploratory"] = ex

    per = seg.groupby(["subject", "subtype"]).agg(
        n=("mi_raw", "size"), dur=("dur", "mean"), mi_raw=("mi_raw", "mean"), floor=("floor", "mean"),
        mi_first4=("mi_first4", "mean"), n_first4=("mi_first4", "count"), mi_debias=("mi_debias", "mean"))
    per.to_csv(OUT / "participants.csv")
    (OUT / "metrics.json").write_text(json.dumps(m, indent=1, default=float))


if __name__ == "__main__":
    main()
