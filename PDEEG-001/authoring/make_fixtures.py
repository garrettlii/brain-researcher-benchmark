"""Build calibration/fixtures/ from an oracle run (solution/solve.sh output directory).

    python authoring/make_fixtures.py <oracle_output_dir>

_base/ gets the oracle's outputs; each other fixture overrides one or two files. All
adversarial fixtures are manufactured from the oracle outputs (no agent run yet), and each
expect.toml says so.
"""
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

src = Path(sys.argv[1])
fx = Path(__file__).resolve().parents[1] / "calibration" / "fixtures"
for d in fx.iterdir():
    if d.is_dir():
        shutil.rmtree(d)
base = fx / "_base"
base.mkdir()
for f in ("segments.csv", "cv_predictions.csv", "evaluations.json", "run_metadata.json", "findings.md"):
    shutil.copy2(src / f, base / f)
ev = json.loads((src / "evaluations.json").read_text())
acc = {e["evaluation_id"]: e for e in ev["evaluations"]}
F_TEST, E_TEST = "test_features_and_paper_evaluation", "test_estimate_comes_from_unseen_participants"


def fixture(name, note, expect, files):
    d = fx / name
    d.mkdir()
    lines = [f'note = "{note}"', "[expect]"] + [f'{k} = "{v}"' if k != "*" else f'"*" = "{v}"' for k, v in expect.items()]
    (d / "expect.toml").write_text("\n".join(lines) + "\n")
    for fname, content in files.items():
        if isinstance(content, pd.DataFrame):
            content.to_csv(d / fname, index=False)
        elif isinstance(content, dict):
            (d / fname).write_text(json.dumps(content, indent=2))
        else:
            (d / fname).write_text(content)


def with_estimate(eid, a, keep=None):
    e = json.loads(json.dumps(ev))
    e["estimate"] = {"evaluation_id": eid, "accuracy": a}
    if keep is not None:
        e["evaluations"] = [x for x in e["evaluations"] if x["evaluation_id"] in keep]
    return e


fixture("reference", "reference: oracle output unchanged (solution/solve.sh, local run 2026-10-08)", {"*": "pass"}, {})
fixture("estimate-participant-vote", "manufactured: oracle output, estimate given as the leave-one-participant-out majority-vote accuracy",
        {"*": "pass"}, {"evaluations.json": with_estimate("leave_one_participant_out",
                                                           acc["leave_one_participant_out"]["participant_majority_vote_accuracy"])})
fixture("estimate-grouped-percent", "manufactured: oracle output, estimate from the participant-grouped 10 x 10 CV, written in percent",
        {"*": "pass"}, {"evaluations.json": with_estimate("participant_grouped_10x10",
                                                           round(100 * acc["participant_grouped_10x10"]["accuracy"], 2))})
fixture("estimate-from-paper-cv",
        "manufactured, targeted failure: all evaluations reported, but the headline estimate is the paper's segment-level 99.7%",
        {F_TEST: "pass", E_TEST: "fail"},
        {"evaluations.json": with_estimate("paper_segment_10x10", acc["paper_segment_10x10"]["accuracy"])})
pred = pd.read_csv(src / "cv_predictions.csv")
fixture("paper-cv-only",
        "manufactured, targeted failure: only the paper's 10 x 10-fold CV is run and its accuracy is the estimate",
        {F_TEST: "pass", E_TEST: "fail"},
        {"evaluations.json": with_estimate("paper_segment_10x10", acc["paper_segment_10x10"]["accuracy"],
                                           keep={"paper_segment_10x10"}),
         "cv_predictions.csv": pred[pred.evaluation_id == "paper_segment_10x10"]})
fixture("estimate-mismatched",
        "manufactured: estimate names the leave-one-participant-out evaluation but quotes the segment-level 99.7%",
        {F_TEST: "pass", E_TEST: "fail"},
        {"evaluations.json": with_estimate("leave_one_participant_out", acc["paper_segment_10x10"]["accuracy"])})
seg = pd.read_csv(src / "segments.csv")
fake = pred.copy()
lopo = fake.evaluation_id == "leave_one_participant_out"
fake.loc[lopo, "predicted_group"] = fake.loc[lopo, "segment_id"].map(dict(zip(seg.segment_id, seg.group)))
fake_ev = with_estimate("leave_one_participant_out", 1.0)
for e in fake_ev["evaluations"]:
    if e["evaluation_id"] == "leave_one_participant_out":
        e["accuracy"] = 1.0
fixture("fabricated-held-out-predictions",
        "manufactured: leave-one-participant-out predictions replaced by the true labels (not what the KNN pipeline predicts)",
        {F_TEST: "pass", E_TEST: "fail"}, {"evaluations.json": fake_ev, "cv_predictions.csv": fake})
feat = [c for c in seg.columns if c[-2:] in ("D1", "D2", "D3", "D4", "A4") or c.endswith("_X")]
volts = seg.copy()
volts[feat] = 0.0
fixture("features-threshold-in-volts",
        "manufactured: threshold 0.2 applied to signals in volts, so every count is zero",
        {F_TEST: "fail"}, {"segments.csv": volts})
print(sorted(d.name for d in fx.iterdir() if d.is_dir()))
