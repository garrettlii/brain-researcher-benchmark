# Task board

One row per paper in the pipeline. Stages: `1-assigned → 2-step0 → 3-v0+oracle →
4-agent-gate → 5-ratchet → 6-merge`. A paper dropped at Step-0 stays here with
`stage=dropped` and the reason — that's a logged success, not a deletion. See
`INTERN_GUIDE.md` for the contract, `ASSIGNMENT_QUEUE.md` for lanes.

| task_id | author | paper | lane | failure axis | lever | stage | step-0 result | oracle | agent verdict | updated |
|---|---|---|---|---|---|---|---|---|---|---|
| GRADIENT-001 | zjc | Vos de Wael 2020 / Margulies 2016 (gradients) | rest-conn (ds000228) | over-claim | none (rigor genre) | 6-merge | apex NOT robustly reproducible → rigor genre | 1.0 | GPT-5.5 FAIL 0.46; Claude FAIL 0.365 (un-cued overclaim) | 2026-06-24 |
| SOCIALBRAIN-001 | zjc | Richardson 2018 Nat Commun (ToM–pain anticorrelation) | rest-conn (ds000228) | confident-refutation | GSR | 6-merge | reproduces ONLY under GSR (−0.07 n.s. → −0.34) | 1.0 | GPT-5.5 FAIL; Claude FAIL (flat verdict, never try GSR) | 2026-06-24 |
| DEVCONN-001 | zjc | Fair 2009 PLoS CB (local→distributed developmental connectivity) | rest-conn (ds000228) | wrong-cause | head motion / QC-FC | 6-merge | dev effect real (seg child>adult p=0.030; age~short r_s=−0.205 p=0.011) → COLLAPSES under motion control (partial\|FD p=0.68; matched p=0.61); kids move 2× (FD 0.371 vs 0.187) | 1.0 | GPT-5.5 4/4 FAIL + Claude 3/3 FAIL (all compute it, none volunteer the motion check) | 2026-07-02 |

<!-- add rows below; keep newest work at the bottom of its lane -->
| CAPPAC-001 | garrettl | Yeh & Shi 2018 Sci Rep (CAP phase-A δ–α/low-β PAC: A1 > A2 > A3) | sleep-EEG (PhysioNet capslpdb 1.0.0, n1–n16) | wrong-cause | segment length (finite-sample MI floor) | 3-v1+oracle (review revisions) | RAW reproduces (A1−A3 +0.0050, d_z 2.54, p=4e-8; MI .0122/.0096/.0072 vs Fig 3a ~.0118/.0100/.0065); A1 segments 6.0 s vs A3 13.2 s, no-coupling floor = 84% of the difference → length controls: first 4 s +0.0009 (p=.25, 17%), MI−floor +0.0008 (p=.0099, 16%) → "length bias accounts" (predeclared; crop upper CI 48% vs 50% bound); floor 93–99% of MI, small A1>A2>A3 residual above it | local 1.0 (46–80 s; Harbor not run) | not run | 2026-10-09 |
