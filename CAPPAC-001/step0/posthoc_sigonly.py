"""Retrospective note (2026-10-09, after run.log; not part of the Step-0 decision): which segments does Fig. 3a average?

claim_scope.md left open whether the paper's GLMM / Fig. 3a used every segment's MI or only segments whose MI passed the
surrogate significance test. Re-uses posthoc_z.one (same seeds) and compares the subject-mean MI over all included segments
with the mean over segments whose MI exceeds the 95th percentile of their 100 block-swap surrogates.

    DATA_DIR=~/.cache/brb/capslpdb python -I step0/posthoc_sigonly.py 2>&1 | tee step0/outputs/posthoc_sigonly.log
"""
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import posthoc_z as Z  # noqa: E402
import probe as P  # noqa: E402

if __name__ == "__main__":
    with ProcessPoolExecutor(int(os.environ.get("WORKERS", 3))) as ex:
        seg = pd.DataFrame([r for rs in ex.map(Z.one, P.SUBJECTS) for r in rs])
    allm = seg.groupby(["subject", "subtype"])["mi_raw"].mean().unstack().mean()
    sig = seg[seg.sig_swap == 1]
    sigm = sig.groupby(["subject", "subtype"])["mi_raw"].mean().unstack().mean()
    print("Fig. 3a (read off the bars): A1 ~0.0118, A2 ~0.0100, A3 ~0.0065")
    print("all included segments, subject means:", allm.round(4).to_dict())
    print("surrogate-significant segments only, subject means:", sigm.round(4).to_dict(),
          "| n segments", sig.groupby("subtype").size().to_dict())
    print("pooled segment means (Fig. 3a bars are segment means +- SEM): all", seg.groupby("subtype")["mi_raw"].mean().round(4).to_dict(),
          "significant only", sig.groupby("subtype")["mi_raw"].mean().round(4).to_dict())
