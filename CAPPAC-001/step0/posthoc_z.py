"""Post-hoc diagnostic for the Stage-2 assessment (not part of the Step-0 decision, written after run.log).

Question: what would a routine surrogate-normalised PAC route report? Per included segment, MI is z-scored
against 50 within-segment circular-shift surrogates (the same surrogates as the floor), and the paper's
block-swap surrogate (cut the amplitude series at one random point and swap the two parts; 100 per segment)
is used for a second z. Subject-level A1 - A3 contrasts as in probe.py.

    DATA_DIR=~/.cache/brb/capslpdb python -I step0/posthoc_z.py 2>&1 | tee step0/outputs/posthoc_z.log
"""
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe as P  # noqa: E402


def one(sid):
    x, fs, ch, start = P.load_signal(sid, P.PRIMARY)
    ev = P.read_events(sid)
    ph = np.angle(P.analytic(x, fs, P.PHASE_BAND))
    am = np.abs(P.analytic(x, fs, P.AMP_BAND))
    ev["onset"] = (ev["tod"] - start) % 86400
    mt = ev[ev["stage"].str.strip() == "MT"]
    mt_iv = list(zip(mt["onset"], mt["onset"] + mt["dur"]))
    rng = np.random.default_rng(1000 + int(sid[1:]))
    rows = []
    for _, e in ev[ev["event"].str.startswith("MCAP-A")].iterrows():
        on, d = float(e["onset"]), float(e["dur"])
        a, z = int(round(on * fs)), int(round((on + d) * fs))
        if e["stage"].strip() == "MT" or any(on < b and on + d > a0 for a0, b in mt_iv) or z > len(x) or a < 0:
            continue
        p, q = ph[a:z], am[a:z]
        if P.ncycles(p) <= 2:
            continue
        n = len(q)
        m0 = P.mi(p, q)
        circ = [P.mi(p, np.roll(q, k)) for k in rng.integers(int(0.2 * n), int(0.8 * n), 50)]
        swap = [P.mi(p, np.concatenate([q[k:], q[:k]])) for k in rng.integers(1, n - 1, 100)]
        rows.append(dict(subject=sid, subtype=e["event"][-2:], dur=d, mi_raw=m0,
                         z_circ=(m0 - np.mean(circ)) / np.std(circ), z_swap=(m0 - np.mean(swap)) / np.std(swap),
                         sig_swap=float(m0 > np.percentile(swap, 95))))
    return rows


def main():
    with ProcessPoolExecutor(int(os.environ.get("WORKERS", 3))) as ex:
        seg = pd.DataFrame([r for rs in ex.map(one, P.SUBJECTS) for r in rs])
    out = {}
    for col in ["mi_raw", "z_circ", "z_swap", "sig_swap"]:
        out[col] = r = P.contrast(seg, col)
        print(f"{col:9s} A1-A3:", P.fmt(r))
    print("segments:", seg.groupby("subtype").size().to_dict())
    print("share of segments with MI > 95th pct of block-swap surrogates:", seg.groupby("subtype")["sig_swap"].mean().round(3).to_dict())
    (P.OUT / "posthoc_z.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
