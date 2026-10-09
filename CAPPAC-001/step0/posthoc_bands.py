"""Post-hoc robustness of the length controls outside the pinned scope (not part of the Step-0 decision, written
after run.log): the predeclared C-crop (first 4 s) and C-debias contrasts recomputed for the exploratory
1-2.5 Hz delta band and, where the montage has it, the F4-C4 bipolar derivation.

    DATA_DIR=~/.cache/brb/capslpdb python -I step0/posthoc_bands.py 2>&1 | tee step0/outputs/posthoc_bands.log
"""
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe as P  # noqa: E402


def one(sid):
    x, fs, _, start = P.load_signal(sid, P.PRIMARY)
    rows = [dict(r, variant="delta1") for r in P.segments(sid, x, fs, start, phase_band=(1.0, 2.5))]
    try:
        xb, fsb, _, _ = P.load_signal(sid, ["F4-C4"])
        rows += [dict(r, variant="f4c4") for r in P.segments(sid, xb, fsb, start)]
    except StopIteration:  # no F4-C4 in this montage
        pass
    return rows


def main():
    with ProcessPoolExecutor(int(os.environ.get("WORKERS", 3))) as ex:
        seg = pd.DataFrame([r for rs in ex.map(one, P.SUBJECTS) for r in rs])
    seg = seg[seg["excluded"] == ""]
    out = {}
    for v, s in seg.groupby("variant"):
        raw = P.contrast(s, "mi_raw")
        for col in ["mi_raw", "floor", "mi_first4", "mi_debias"]:
            out[f"{v}_{col}"] = r = P.contrast(s, col)
            print(f"{v:6s} {col:9s} A1-A3:", P.fmt(r), f" ratio {r['mean'] / raw['mean']:.2f}")
    (P.OUT / "posthoc_bands.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
