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
| PDEEG-001 | garrettl | Aljalal 2022 Sci Rep (PD vs HC resting EEG, DWT entropy + KNN, 99.7–99.9%) | EEG (ds002778) | over-claim (generalization) | evaluation unit (segment vs participant CV) | 3-v0+oracle | paper's segment-level 10×10-fold reproduces (ThEn 99.73% vs 99.72%) → held-out participants at chance for all 8 features (LOPO 45%, 13/31, perm p=.64); segment CV scores 99.5% with RANDOM participant labels and IDs participants at 99.3% → measures person recognition, not PD detection. UNM (paper's own LOSO claim, 54 people): segment CV 98–99% vs LOSO 46–68% without selection; paper-style channel selection (scored by LOSO itself) 70–81% vs paper 85–88.6%, nested 55–73% | local oracle passes (130 s); 8/8 offline fixtures as expected (typed estimate must come from a replayable participant-disjoint CV); Harbor/Docker build not run | not run | 2026-10-08 |

<!-- add rows below; keep newest work at the bottom of its lane -->
