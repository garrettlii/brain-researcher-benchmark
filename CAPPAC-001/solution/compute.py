"""Reference solution for CAPPAC-001: delta-alpha/low-beta phase-amplitude coupling across CAP
phase-A subtypes in the 16 healthy recordings of the PhysioNet CAP Sleep Database, following
Yeh & Shi 2018 (Sci Rep 8:3049).

Pinned analysis (instruction.md): C4-A1 (C3-A2 for n6-n9) at its native rate; whole-night
zero-phase 4th-order Butterworth band-pass at 0.25-2.5 Hz (phase) and 10-17 Hz (amplitude) and
Hilbert transform; every MCAP-A1/A2/A3 event outside movement time and inside the recording,
kept if the delta phase advances more than two cycles; Tort MI with 20 bins per segment;
subject means per subtype; paired t-tests across subjects.

What the reference also asks: how much of the MI ordering is coupling, and how much is the
amount of data in each segment? The MI of a finite segment is positive even with no coupling,
and the floor shrinks roughly with 1/length (Tort et al. 2010). The authors knew phase-A
durations differ and kept only segments with more than two delta cycles partly for that
reason; the reference checks whether that rule is enough. A1 segments stay about half as long
as A3, so it compares lengths, estimates each segment's no-coupling floor from 50 circular
shifts of the amplitude series inside the segment, and recomputes MI on the first 4 s of every
segment >= 4 s.

Validated numbers (Step 0, step0/evidence.json; n = 16 subjects, 3923 / 1314 / 1145 segments):
  RAW      subject-mean MI A1 .01222, A2 .00956, A3 .00719; A1 - A3 +0.00503
           [+0.00398, +0.00609], d_z 2.54, t15 = 10.16, p = 4e-8              (paper: A1 > A2 > A3)
  PREMISE  duration A1 6.0 s vs A3 13.2 s (t15 = -14.75); the no-coupling floor is 93% (A1),
           95% (A2) and 99% (A3) of mean MI, and its A1 - A3 difference is +0.00422
           [+0.00328, +0.00517], 84% of the raw difference
  CTRL     MI minus floor:  A1 .00091 > A2 .00050 > A3 .00010; A1 - A3 +0.00081
                            [+0.00022, +0.00139], p = .0099 (16% of raw); A1 - A2 p = .087,
                            A2 - A3 p = .066
           first 4 s:       A1 - A3 +0.00088 [-0.00068, +0.00243], p = .25 (17% of raw; the
                            same size, less precise)
           -> raw MI is mostly the length-dependent floor and overstates the subtype difference
              about sixfold; above the floor a small A1 > A2 > A3 ordering remains
              (significant only for A1 - A3). The predeclared rule's margin is narrow: the
              first-4-s upper CI is 48% of raw against a 50% bound (step0/evidence.json).

    OUTPUT_DIR=/app/output CAPSLPDB_DIR=/app/data/capslpdb python3 compute.py
"""
import json
import os
import platform
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

OUT = Path(os.environ.get("OUTPUT_DIR", "/app/output"))
SRC = Path(os.environ.get("CAPSLPDB_DIR", "/app/data/capslpdb"))
TASK_ID = "CAPPAC-001"
DATASET_ID = "PhysioNet CAP Sleep Database 1.0.0 (capslpdb), healthy recordings n1-n16"
SUBJECTS = [f"n{i}" for i in range(1, 17)]
CHANNELS = ["C4-A1", "C4A1", "C3-A2", "C3A2"]
PHASE_BAND, AMP_BAND = (0.25, 2.5), (10.0, 17.0)
NBINS, NSURR, MIN_SEG, CROP = 20, 50, 5, 4.0
SUBTYPES = ["A1", "A2", "A3"]
PAIRS = [("A1", "A3"), ("A1", "A2"), ("A2", "A3")]


def wj(name, payload):
    (OUT / name).write_text(json.dumps(payload, indent=2, default=float), encoding="utf-8")


def fail(reason):
    """Failure handling as promised in instruction.md: parseable outputs, non-zero exit."""
    OUT.mkdir(parents=True, exist_ok=True)
    wj("run_metadata.json", {"task_id": TASK_ID, "dataset_id": DATASET_ID, "status": "failed_precondition", "reason": reason})
    wj("subtype_effects.json", {"status": "failed_precondition", "reason": reason})
    (OUT / "findings.md").write_text(f"# Failed precondition\n\nfailed_precondition: {reason}\n", encoding="utf-8")
    sys.stderr.write(f"failed_precondition: {reason}\n")
    sys.exit(1)


try:
    import numpy as np
    import pandas as pd
    import scipy
    from scipy import stats
    from scipy.fft import next_fast_len
    from scipy.signal import butter, hilbert, sosfiltfilt
except ImportError as e:  # pragma: no cover
    fail(f"missing dependency: {e}")


# ---------------------------------------------------------------- load_substrate
def read_events(sid):
    lines = (SRC / f"{sid}.txt").read_text(errors="replace").splitlines()
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
    """One EDF channel at its own sampling rate (some files mix rates across channels)."""
    with open(path, "rb") as f:
        h = f.read(256)
        hb, nrec, rdur, ns = int(h[184:192]), int(h[236:244]), float(h[244:252]), int(h[252:256])
        h2 = f.read(ns * 256)
    field = lambda off, w: [h2[ns * off + w * k: ns * off + w * (k + 1)].decode().strip() for k in range(ns)]  # noqa: E731
    labels = field(0, 16)
    pmin, pmax = list(map(float, field(104, 8))), list(map(float, field(112, 8)))
    dmin, dmax = list(map(float, field(120, 8))), list(map(float, field(128, 8)))
    spr = list(map(int, field(216, 8)))
    ci = next(labels.index(c) for c in prefer if c in labels)
    tot = sum(spr)
    if nrec < 0:
        nrec = (Path(path).stat().st_size - hb) // (2 * tot)
    d = np.memmap(path, dtype="<i2", mode="r", offset=hb, shape=(nrec, tot))
    o = sum(spr[:ci])
    x = np.asarray(d[:, o:o + spr[ci]], dtype=float).ravel()
    x = (x - dmin[ci]) * (pmax[ci] - pmin[ci]) / (dmax[ci] - dmin[ci]) + pmin[ci]
    hh, mm, ss = (int(v) for v in h[176:184].decode().split("."))
    return x, spr[ci] / rdur, labels[ci], hh * 3600 + mm * 60 + ss


# ---------------------------------------------------------------- primary_analysis
def analytic(x, fs, band):
    y = sosfiltfilt(butter(4, band, btype="band", fs=fs, output="sos"), x)
    return hilbert(y, next_fast_len(len(y)))[:len(y)]


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
    """No-coupling MI at this segment's length: amplitude circularly shifted inside the segment."""
    n = len(amp)
    lags = rng.integers(int(0.2 * n), max(int(0.8 * n), int(0.2 * n) + 1), NSURR)
    return float(np.mean([mi(phase, np.roll(amp, k)) for k in lags]))


def subject(sid):
    x, fs, ch, start = read_edf_channel(SRC / f"{sid}.edf", CHANNELS)
    ev = read_events(sid)
    ph = np.angle(analytic(x, fs, PHASE_BAND))
    am = np.abs(analytic(x, fs, AMP_BAND))
    ev["onset"] = (ev["tod"] - start) % 86400
    mt = ev[ev["stage"].str.strip() == "MT"]
    mt_iv = list(zip(mt["onset"], mt["onset"] + mt["dur"]))
    rng = np.random.default_rng(int(sid[1:]))
    rows = []
    for _, e in ev[ev["event"].str.startswith("MCAP-A")].iterrows():
        on, d = float(e["onset"]), float(e["dur"])
        a, z = int(round(on * fs)), int(round((on + d) * fs))
        r = dict(subject=sid, channel=ch, fs=fs, subtype=e["event"][-2:], stage=e["stage"].strip(), onset_s=on, dur_s=d,
                 excluded="")
        if r["stage"] == "MT" or any(on < b and on + d > a0 for a0, b in mt_iv):
            r["excluded"] = "movement_time"
        elif z > len(x) or a < 0:
            r["excluded"] = "outside_recording"
        else:
            p, q = ph[a:z], am[a:z]
            if ncycles(p) <= 2:
                r["excluded"] = "two_or_fewer_delta_cycles"
            else:
                r["mi"] = mi(p, q)
                # volunteered: the segment's no-coupling floor, and MI on its first 4 s
                r["floor"] = floor(p, q, rng)
                r["mi_minus_floor"] = r["mi"] - r["floor"]
                if d >= CROP:
                    k = int(round(CROP * fs))
                    if ncycles(p[:k]) > 2:
                        r["mi_first4s"] = mi(p[:k], q[:k])
        rows.append(r)
    return rows


# ---------------------------------------------------------------- primary_stats
def paired(d, seed=0):
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    n, m, s = len(d), d.mean(), d.std(ddof=1)
    tc = stats.t.ppf(0.975, n - 1) * s / np.sqrt(n)
    bs = np.random.default_rng(seed).choice(d, (10000, n))
    dz_bs = bs.mean(1) / bs.std(1, ddof=1)
    t = m / (s / np.sqrt(n))
    return dict(n_subjects=n, difference=m, ci_low=m - tc, ci_high=m + tc, t=t, p=float(2 * stats.t.sf(abs(t), n - 1)),
                cohens_dz=m / s, dz_ci=[float(np.percentile(dz_bs, 2.5)), float(np.percentile(dz_bs, 97.5))],
                wilcoxon_p=float(stats.wilcoxon(d).pvalue))


def contrast(seg, col, a, b):
    s = seg[np.isfinite(seg[col])]
    g = s.groupby(["subject", "subtype"])[col].agg(["mean", "count"]).unstack("subtype")
    g = g[(g["count"][a] >= MIN_SEG) & (g["count"][b] >= MIN_SEG)]
    return paired((g["mean"][a] - g["mean"][b]).values) | {f"mean_{a}": float(g["mean"][a].mean()),
                                                           f"mean_{b}": float(g["mean"][b].mean())}


def primary_stats(seg):
    sm = seg.groupby(["subject", "subtype"])["mi"].mean().unstack()
    return {"n_subjects": int(sm.notna().all(axis=1).sum()),
            "n_segments": {k: int(v) for k, v in seg.groupby("subtype").size().items()},
            "mean_mi": {k: float(sm[k].mean()) for k in SUBTYPES}} | {f"{a}-{b}": contrast(seg, "mi", a, b) for a, b in PAIRS}


# ---------------------------------------------------------------- volunteered_check
def volunteered_check(seg):
    """Not asked for: does the ordering survive once segment length is taken out of the MI?"""
    slopes = {}
    for st in SUBTYPES:
        sl = [stats.linregress(1 / d.dur_s, d.mi).slope for _, d in seg[seg.subtype == st].groupby("subject")
              if len(d) >= MIN_SEG]
        slopes[st] = paired(sl)
    sm = seg.groupby(["subject", "subtype"])[["mi", "floor", "mi_minus_floor"]].mean()
    n = seg.groupby(["subject", "subtype"]).size()
    sm = sm[n >= MIN_SEG]
    by = {st: {"mean_mi": float(sm.xs(st, level="subtype")["mi"].mean()),
               "mean_floor": float(sm.xs(st, level="subtype")["floor"].mean()),
               "mean_mi_minus_floor": float(sm.xs(st, level="subtype")["mi_minus_floor"].mean())} for st in SUBTYPES}
    for v in by.values():
        v["floor_share_of_mi"] = v["mean_floor"] / v["mean_mi"]
    return {"by_subtype": by,
            "duration_s": {f"{a}-{b}": contrast(seg, "dur_s", a, b) for a, b in PAIRS},
            "no_coupling_floor": {f"{a}-{b}": contrast(seg, "floor", a, b) for a, b in PAIRS},
            "mi_first_4s": {f"{a}-{b}": contrast(seg, "mi_first4s", a, b) for a, b in PAIRS},
            "mi_minus_floor": {f"{a}-{b}": contrast(seg, "mi_minus_floor", a, b) for a, b in PAIRS},
            "slope_mi_vs_inverse_duration": slopes,
            "n_segments_first_4s": {k: int(v) for k, v in seg.dropna(subset=["mi_first4s"]).groupby("subtype").size().items()},
            "method": ("floor = mean MI over 50 circular shifts of the amplitude series inside each segment (lag uniform in "
                       "20-80% of its length); first 4 s = MI on the first 4.0 s of every segment >= 4 s with > 2 delta cycles "
                       "in that window; same subject-level paired tests")}


# ---------------------------------------------------------------- write_findings
def write_findings(prim, chk):
    c, d, f = prim["A1-A3"], chk["duration_s"]["A1-A3"], chk["no_coupling_floor"]["A1-A3"]
    k, b = chk["mi_first_4s"]["A1-A3"], chk["mi_minus_floor"]["A1-A3"]
    b12, b23 = chk["mi_minus_floor"]["A1-A2"], chk["mi_minus_floor"]["A2-A3"]
    mm, n, by = prim["mean_mi"], prim["n_subjects"], chk["by_subtype"]
    raw = c["difference"]
    ci = lambda r: f"[{r['ci_low']:+.5f}, {r['ci_high']:+.5f}]"  # noqa: E731
    sl = chk["slope_mi_vs_inverse_duration"]
    share = ", ".join(f"{by[st]['floor_share_of_mi']:.0%}" for st in SUBTYPES)
    (OUT / "findings.md").write_text(f"""# CAPPAC-001: delta-alpha/low-beta coupling across CAP phase-A subtypes

## The result at face value
With the paper's estimator on its own healthy recordings (n = {n}; {prim['n_segments']['A1']} A1,
{prim['n_segments']['A2']} A2 and {prim['n_segments']['A3']} A3 segments), subject-mean MI is A1 {mm['A1']:.4f},
A2 {mm['A2']:.4f} and A3 {mm['A3']:.4f}, close to the paper's Fig. 3a. A1 - A3 = {raw:+.5f} {ci(c)}
(paired t{n - 1} = {c['t']:.2f}, p = {c['p']:.1g}, d_z = {c['cohens_dz']:.2f}); A1 - A2 and A2 - A3 are also positive
(p = {prim['A1-A2']['p']:.2g} and {prim['A2-A3']['p']:.2g}). The ordering A1 > A2 > A3 reproduces.

## How much of the MI is coupling?
Tort's MI is positive even without coupling, and that floor is larger for shorter segments. The
authors knew phase-A durations differ and analysed only segments with more than two delta cycles,
partly to limit this. After that rule the subtypes still differ two-fold in length: A1 segments last
{d['mean_A1']:.1f} s on average and A3 segments {d['mean_A3']:.1f} s (paired difference {d['difference']:+.1f} s, shorter in every subject).
Within every subtype, MI rises with 1/duration (slopes {sl['A1']['difference']:+.3f}, {sl['A2']['difference']:+.3f}, {sl['A3']['difference']:+.3f}; all p < .001).

- No-coupling floor (MI after circularly shifting the amplitude inside each segment, 50 shifts): A1
  {by['A1']['mean_floor']:.4f}, A2 {by['A2']['mean_floor']:.4f}, A3 {by['A3']['mean_floor']:.4f}, i.e. {share} of the mean MI. Its A1 - A3
  difference is {f['difference']:+.5f} {ci(f)}, {f['difference'] / raw:.0%} of the raw difference.
- MI minus each segment's floor: A1 {by['A1']['mean_mi_minus_floor']:.5f}, A2 {by['A2']['mean_mi_minus_floor']:.5f}, A3 {by['A3']['mean_mi_minus_floor']:.5f}.
  A1 - A3 = {b['difference']:+.5f} {ci(b)}, p = {b['p']:.2g}, {b['difference'] / raw:.0%} of the raw difference;
  A1 - A2 (p = {b12['p']:.2g}) and A2 - A3 (p = {b23['p']:.2g}) are not significant.
- MI on the first 4 s of every segment (the same length for every subtype): A1 - A3 = {k['difference']:+.5f}
  {ci(k)}, p = {k['p']:.2g}, {k['difference'] / raw:.0%} of the raw difference. This is about the same size as the
  floor-subtracted difference, estimated less precisely.

## Conclusion
The paper's MI values and their ordering reproduce, but raw MI here is mostly the estimator's
length-dependent floor: the two-cycle rule leaves A1 segments half as long as A3 segments, and the
floor alone gives {f['difference'] / raw:.0%} of the A1 - A3 difference. Above the floor a small A1 > A2 > A3 ordering
remains, about {b['difference'] / raw:.0%} of the raw difference (significant only for A1 - A3 after floor subtraction;
the equal-length estimate is the same size but imprecise). Raw MI therefore overstates the subtype
difference about {raw / b['difference']:.0f}-fold and cannot be read as coupling strength. These data are consistent with
slightly stronger coupling in A1 than in A3, but not with the paper's reading of the MI differences
as a substantial difference in coupling strength between subtypes.
""", encoding="utf-8")


def main():
    t0 = time.time()
    missing = [f"{s}.{e}" for s in SUBJECTS for e in ("edf", "txt") if not (SRC / f"{s}.{e}").is_file()]
    if missing:
        fail(f"staged CAP Sleep Database files not found under {SRC}: {missing[:4]}")
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        with ProcessPoolExecutor(int(os.environ.get("WORKERS", 2))) as ex:
            allseg = pd.DataFrame([r for rs in ex.map(subject, SUBJECTS) for r in rs])
    except Exception as e:  # noqa: BLE001
        fail(f"could not read the staged recordings: {e!r}")
    seg = allseg[allseg["excluded"] == ""].copy()
    if seg["subject"].nunique() < 16:
        fail(f"only {seg['subject'].nunique()} recordings produced segments")

    # required outputs
    per = seg.groupby(["subject", "channel", "subtype"]).agg(n_segments=("mi", "size"), mean_mi=("mi", "mean")).reset_index()
    per["order"] = per["subject"].str[1:].astype(int)
    per.sort_values(["order", "subtype"]).drop(columns="order").to_csv(OUT / "subject_mi.csv", index=False)
    prim = primary_stats(seg)
    wj("subtype_effects.json", prim)
    # the numbers behind the length check in findings.md
    chk = volunteered_check(seg)
    wj("length_check.json", chk)
    seg[["subject", "subtype", "stage", "onset_s", "dur_s", "mi", "floor", "mi_first4s"]].to_csv(OUT / "segment_mi.csv", index=False)
    rec = allseg.groupby("subject")[["channel", "fs"]].first()
    wj("run_metadata.json", {
        "task_id": TASK_ID, "status": "ok", "dataset_id": DATASET_ID, "source_dir": str(SRC),
        "recordings": {s: {"channel": rec.loc[s, "channel"], "fs_hz": float(rec.loc[s, "fs"])} for s in SUBJECTS},
        "phase_a_events": {k: int(v) for k, v in allseg.groupby("subtype").size().items()},
        "excluded": {f"{a}:{b}": int(v) for (a, b), v in allseg[allseg.excluded != ""].groupby(["subtype", "excluded"]).size().items()},
        "analysed_segments": prim["n_segments"],
        "settings": {"phase_band_hz": PHASE_BAND, "amplitude_band_hz": AMP_BAND, "filter": "Butterworth order 4, sosfiltfilt, whole night",
                     "phase_bins": NBINS, "inclusion": "delta phase advances > 2 cycles", "min_segments_per_subtype": MIN_SEG,
                     "statistics": "paired t across subjects, 95% t CI"},
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__, "pandas": pd.__version__},
        "runtime_s": round(time.time() - t0, 1)})
    write_findings(prim, chk)
    c = prim["A1-A3"]
    print(f"OK: n={prim['n_subjects']} mean_mi={ {k: round(v, 5) for k, v in prim['mean_mi'].items()} } "
          f"A1-A3 {c['difference']:+.5f} p={c['p']:.2g} | first4s {chk['mi_first_4s']['A1-A3']['difference']:+.5f} "
          f"minus_floor {chk['mi_minus_floor']['A1-A3']['difference']:+.5f} ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
