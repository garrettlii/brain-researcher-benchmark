"""Post-hoc diagnostic for the verifier design (2026-10-09, after run.log; not part of the Step-0 decision).

A routine alternative an agent may take: keep raw MI and adjust the subtype contrast for segment duration as a
covariate. Segment-level mixed models MI ~ subtype + f(duration) + (1 | subject) with f = none, linear, 1/duration and
log duration, plus a subject-level contrast of MI residualised on 1/duration within each subject.

    python -I step0/posthoc_covariate.py 2>&1 | tee step0/outputs/posthoc_covariate.log
"""
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

warnings.simplefilter("ignore")
s = pd.read_csv(Path(__file__).resolve().parent / "outputs/segments.csv")
s = s[s.excluded.isna() | (s.excluded == "")].assign(inv=lambda d: 1 / d.dur, logd=lambda d: np.log(d.dur))
k = "C(subtype, Treatment('A3'))[T.A1]"
for f in ["", " + dur", " + inv", " + logd"]:
    md = smf.mixedlm("mi_raw ~ C(subtype, Treatment('A3'))" + f, s, groups=s["subject"]).fit()
    print(f"mixedlm MI ~ subtype{f:7s}  A1-A3 {md.params[k]:+.5f}  p = {md.pvalues[k]:.2g}")
r = []
for _, d in s.groupby("subject"):
    b = np.polyfit(d.inv, d.mi_raw, 1)
    g = d.assign(res=d.mi_raw - np.polyval(b, d.inv)).groupby("subtype").res.mean()
    r.append(g["A1"] - g["A3"])
t = stats.ttest_1samp(r, 0)
print(f"subject-level, MI residualised on 1/duration within subject: A1-A3 {np.mean(r):+.5f}  t15 = {t.statistic:.2f}  p = {t.pvalue:.2g}")
