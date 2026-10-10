"""Write CAPPAC-001/step0/evidence.json from the probe outputs (run from the task directory).

    python -I step0/write_evidence.py
"""
import json
import sys

sys.path.insert(0, "../tools")
from artifact_ref import artifact_ref as R  # noqa: E402

m = json.load(open("step0/outputs/metrics.json"))
z = json.load(open("step0/outputs/posthoc_z.json"))
bands = json.load(open("step0/outputs/posthoc_bands.json"))
M, LOG, CSV, MAN, FREEZE = (R(p) for p in ("step0/outputs/metrics.json", "step0/run.log", "step0/outputs/participants.csv",
                                            "step0/outputs/capslpdb_manifest.tsv", "step0/outputs/pip_freeze.txt"))
SEG = R("step0/outputs/segments.csv")
PZ, PZLOG, PZJ = R("step0/posthoc_z.py"), R("step0/outputs/posthoc_z.log"), R("step0/outputs/posthoc_z.json")
PB, PBLOG, PBJ = R("step0/posthoc_bands.py"), R("step0/outputs/posthoc_bands.log"), R("step0/outputs/posthoc_bands.json")
PC, PCLOG = R("step0/posthoc_covariate.py"), R("step0/outputs/posthoc_covariate.log")
PS, PSLOG, ADD = R("step0/posthoc_sigonly.py"), R("step0/outputs/posthoc_sigonly.log"), R("step0/claim_scope_addendum.md")
raw, dur, fl, crop, deb, ex = (m[k] for k in ("raw_A1_A3", "premise_duration_A1_A3", "premise_floor_A1_A3",
                                               "ctrl_crop4_A1_A3", "ctrl_debias_A1_A3", "exploratory"))
d_raw = raw["mean"]
# F4 (review of ba56a10): how close the predeclared 50%-of-raw upper-CI bound was, and what other windows would have given.
MARGIN = {"rule": "point estimate <= 25% and upper 95% CI < 50% of the raw A1 - A3 difference (claim_scope.md)",
          "crop_first4s_upper_ratio": round(crop["ci"][1] / d_raw, 3),
          "same_rule_other_windows_upper_ratio": {k: round(ex[k]["ci"][1] / d_raw, 3) for k in ("mi_first3", "mi_first5", "mi_first6", "mi_mid4")}
          | {"duration_matched_1s_bins": round(ex["duration_matched_A1_A3"]["ci"][1] / d_raw, 3)},
          "reading": ("The verdict rests on the predeclared 4-s crop, whose upper CI is 48% of raw against a 50% bound. Under the same rule "
                      "the 3-s crop (54%), duration-matched 1-s bins (54%) and the middle 4 s (49.9%) would have been unresolved, while 5-s "
                      "and 6-s crops clear it easily. L = 4 s was fixed before the probe, so the verdict stands, but the margin is narrow "
                      "and the key is worded accordingly: most of the ordering is length, a small residual remains.")}


def s(r, nd=5):
    return (f"{r['mean']:+.{nd}f} [{r['ci'][0]:+.{nd}f}, {r['ci'][1]:+.{nd}f}], d_z {r['dz']:+.2f}, "
            f"t{r['n'] - 1} = {r['t']:.2f}, p = {r['p']:.2g}")


def small(r):
    keep = ("n", "mean", "ci", "dz", "dz_ci", "t", "p", "wilcoxon_p", "mean_a", "mean_b")
    rnd = lambda v: round(v, 6) if isinstance(v, float) else [round(x, 6) for x in v] if isinstance(v, list) else v  # noqa: E731
    return {k: rnd(r[k]) for k in keep if k in r}


ev = {
    "schema_version": "step0-evidence-v1",
    "task_id": "CAPPAC-001",
    "opportunity_id": "adhoc:CAPPAC-001",
    "_comment": ("Step-0 record. EvidenceItem/ArtifactRef shapes follow contracts/curation/curation-contracts-v1.schema.json. "
                 "This file names the hidden lever, so like solution/ it is author_private."),
    "intake_route": ["advance_to_step0"],
    "intake_reason": ("Primary empirical sleep-EEG paper with an exact estimator (Tort modulation index, 20 bins) and an exact contrast "
                      "(Control group: delta(0.25-2.5 Hz)-alpha/low-beta(10-17 Hz) MI highest in CAP phase A1, lowest in A3; Fig. 3a). "
                      "The substrate is the paper's own open dataset (PhysioNet CAP Sleep Database 1.0.0, ODC-By, no login; healthy "
                      "recordings n1-n16 with RemLogic CAP annotations). Lane E (EEG). Candidate lever: the MI of a short segment has a "
                      "positive finite-sample floor, and A1 segments are about half as long as A3."),
    "claim_scope_review": {
        "status": "verified",
        "reviewed_on": "2026-10-09",
        "timing": "pre_probe",
        "decision": "proceed_paper_aligned",
        "reason": ("Claim, bands, cohort and estimator checked against the full text (PMC5805690) and Supplementary Information "
                   "(Tables S1-S2) before any MI was computed; committed alone (ac20e19) before the probe (6a12fa7). The authors' "
                   "existing duration control (>2 delta-cycle inclusion rule) is recorded and kept in the measurement. Adaptations "
                   "(filter-Hilbert in place of masking EMD, one central-mastoid derivation, subject-level inference) justified "
                   "before local results."),
        "record_ref": R("step0/claim_scope.md"),
    },
    "paper": {
        "paper_id": "10.1038/s41598-018-21013-9",
        "paper_kind": "primary_empirical",
        "claim_and_contrast": ("Yeh & Shi 2018 (Sci Rep 8:3049): in the CAP database's healthy controls, delta-alpha/low-beta phase-amplitude "
                               "coupling (Tort MI) during phase A is highest in subtype A1 and lowest in A3 (A1 > A2 > A3), read as stronger "
                               "coupling / synchronisation in A1 and proposed as a sleep-microstructure biomarker."),
        "target_measurement": ("Tort MI (20 phase bins) of delta (0.25-2.5 Hz) phase vs 10-17 Hz amplitude per phase-A segment with more "
                               "than two delta cycles; subject means per subtype; paired A1 - A3 across the 16 controls."),
        "reported_values": [
            {"field": "subtype_ordering_control", "status": "reported", "evidence_refs": [],
             "value": "Control group: subtype effect p < 0.0001 (GLMM), Tukey A1 > A2 > A3 (Results; Fig. 3a)"},
            {"field": "fig3a_bar_heights_control", "status": "reported", "evidence_refs": [],
             "value": "read from Fig. 3a: A1 ~0.0118, A2 ~0.0100, A3 ~0.0065 (mean MI over segments)"},
            {"field": "segment_counts_control", "status": "reported", "evidence_refs": [],
             "value": "Table S2, Control: A1 2741, A2 829, A3 820 segments"},
            {"field": "duration_control_in_paper", "status": "reported", "evidence_refs": [],
             "value": ("only sequences with more than two delta cycles analysed, 'to both reduce the differences in MIs due to different "
                       "phase-A durations as well as the impacts of artifacts in large time scales' (Surrogate data testing; Limitations)")},
        ],
    },
    "substrate": {
        "dataset_id": "PhysioNet CAP Sleep Database 1.0.0 (capslpdb; Terzano et al. 2001, Goldberger et al. 2000), healthy recordings n1-n16",
        "fetcher": ("step0/fetch_capslpdb.py ~/.cache/brb/capslpdb: PhysioNet's public AWS mirror "
                    "https://physionet-open.s3.amazonaws.com/capslpdb/1.0.0/, every file checked against the release SHA256SUMS.txt"),
        "version_pin": ("capslpdb 1.0.0 (32 files, 3,816,746,073 bytes; sha256 per file in step0/outputs/capslpdb_manifest.tsv); "
                        "numpy==2.5.3 scipy==1.18.1 pandas==3.0.6 statsmodels==0.14.5"),
        "cohort": ("16 healthy controls (Table S1); C4-A1 (n1-n5, n10-n12, n16), C4A1 (n13-n15), C3-A2 (n6-n9, no C4-A1); "
                   "fs 100-512 Hz; included segments " + ", ".join(f"{k} {v}" for k, v in m["included"].items())),
        "access": "public (Open Data Commons Attribution 1.0)",
    },
    "probe": {
        "script": "step0/probe.py",
        "fetcher": "step0/fetch_capslpdb.py",
        "command": ("python -I step0/fetch_capslpdb.py ~/.cache/brb/capslpdb 6; "
                    "DATA_DIR=~/.cache/brb/capslpdb WORKERS=3 python -I step0/probe.py 2>&1 | tee step0/run.log"),
        "log": "step0/run.log",
        "outputs": ["step0/outputs/metrics.json", "step0/outputs/segments.csv", "step0/outputs/participants.csv",
                    "step0/outputs/capslpdb_manifest.tsv", "step0/outputs/pip_freeze.txt"],
        "ran_on": "2026-10-09, macOS arm64 (Darwin 24.6), Python 3.14.7, 33 s wall on 3 processes",
    },
    "deviations_from_claim_scope": [
        "None in the primary comparisons. The EDFs are read with a small native-rate reader (validated against mne.io.read_raw_edf on "
        "n4, n6, n8: identical samples up to the unit scale) because mne resamples mixed-rate records to the highest channel rate.",
        "More segments are included than in the paper's Table S2 (A1 3923 vs 2741, A2 1314 vs 829, A3 1145 vs 820); the paper does not "
        "say what else it excluded. The per-subtype mean MI nonetheless matches the Fig. 3a bars closely (see raw_effect).",
    ],
    "results": [
        {"field": "raw_effect", "status": "measured", "evidence_refs": [M, LOG, CSV, SEG, MAN, FREEZE],
         "value": {"A1_A3": small(raw), "A1_A2": small(m["raw_A1_A2"]), "A2_A3": small(m["raw_A2_A3"]),
                   "subject_mean_mi": {"A1": round(raw["mean_a"], 5), "A2": round(m["raw_A1_A2"]["mean_b"], 5), "A3": round(raw["mean_b"], 5)},
                   "mixedlm_ref_A3": m["mixedlm"], "RAW_reproduced": m["raw_reproduces"],
                   "summary": (f"Reproduced (n = 16). Subject-mean MI A1 {raw['mean_a']:.4f}, A2 {m['raw_A1_A2']['mean_b']:.4f}, "
                               f"A3 {raw['mean_b']:.4f} (Fig. 3a ~.0118 / .0100 / .0065). A1 - A3 {s(raw)}; "
                               f"A1 - A2 {s(m['raw_A1_A2'])}; A2 - A3 {s(m['raw_A2_A3'])}. Segment-level mixed model agrees.")}},
        {"field": "lever_premise", "status": "measured", "evidence_refs": [M, LOG, CSV, SEG],
         "value": {"duration_A1_A3_s": small(dur), "floor_A1_A3": small(fl), "floor_over_d_raw": round(fl["mean"] / d_raw, 3),
                   "PREMISE_holds": m["premise_holds"],
                   "summary": (f"Included A1 segments are shorter than A3 ({dur['mean_a']:.1f} vs {dur['mean_b']:.1f} s; {s(dur, 2)}). "
                               f"The length floor (mean MI of 50 within-segment circular-shift surrogates) is A1 {fl['mean_a']:.4f} vs "
                               f"A3 {fl['mean_b']:.4f}: {s(fl)}, i.e. {fl['mean'] / d_raw:.0%} of the raw A1 - A3 difference. "
                               f"Within every subtype MI rises with 1/duration (slopes +0.038 to +0.054, all CIs > 0).")}},
        {"field": "controlled_effect", "status": "measured", "evidence_refs": [M, LOG, CSV, SEG],
         "value": {"crop_first4s_A1_A3": small(crop), "debias_A1_A3": small(deb),
                   "crop_ratio": round(crop["mean"] / d_raw, 3), "crop_upper_ratio": round(crop["ci"][1] / d_raw, 3),
                   "debias_ratio": round(deb["mean"] / d_raw, 3), "debias_upper_ratio": round(deb["ci"][1] / d_raw, 3),
                   "verdict_rule": m["verdict"], "rule_margin": MARGIN,
                   "summary": (f"Length bias accounts for the subtype difference under the predeclared rule. C-crop (first 4 s of every "
                               f"segment >= 4 s): {s(crop)}, {crop['mean'] / d_raw:.0%} of raw (upper CI {crop['ci'][1] / d_raw:.0%}). "
                               f"C-debias (MI minus floor): {s(deb)}, {deb['mean'] / d_raw:.0%} of raw (upper CI {deb['ci'][1] / d_raw:.0%}). "
                               f"Both point estimates <= 25% and upper CIs < 50% of raw. A small debiased residual remains (p = {deb['p']:.2g}). "
                               f"Margin: the crop's upper CI is {crop['ci'][1] / d_raw:.1%} of raw against the 50% bound (rule_margin).")}},
    ],
    "exploratory": {
        "status": "measured", "evidence_refs": [M, LOG, PZ, PZLOG, PZJ, PB, PBLOG, PBJ, PC, PCLOG, PS, PSLOG],
        "note": "Predeclared exploratory analyses (run.log) plus four post-hoc diagnostics written after run.log; none used for the decision.",
        "value": {
            "crop_windows_A1_A3": {k: small(ex[k]) for k in ("mi_first3", "mi_first5", "mi_first6", "mi_mid4")},
            "duration_matched_1s_bins_4_10s": small(ex["duration_matched_A1_A3"]),
            "A1_S2_minus_S4": {k: small(ex[f"A1_S2_S4_{k}"]) for k in ("mi_raw", "mi_first4", "mi_debias", "dur")},
            "mi_debias_A1_A2": small(ex["mi_debias_A1_A2"]), "mi_debias_A2_A3": small(ex["mi_debias_A2_A3"]),
            "posthoc_surrogate_z_A1_A3": {k: small(z[k]) for k in ("z_circ", "z_swap", "sig_swap")},
            "posthoc_delta_1_2.5Hz": {k: small(bands[f"delta1_{k}"]) for k in ("mi_raw", "floor", "mi_first4", "mi_debias")},
            "posthoc_F4C4": {k: small(bands[f"f4c4_{k}"]) for k in ("mi_raw", "floor", "mi_first4", "mi_debias")},
            "posthoc_duration_covariate_mixedlm_A1_A3": {"none": "+0.00524 p=2.3e-72", "linear": "+0.00137 p=1.7e-05",
                                                        "inverse": "+0.00085 p=0.0033", "log": "+0.00017 p=0.57",
                                                        "subject_level_residualised_on_inverse": "+0.00060 t15=1.49 p=0.16"},
            "posthoc_surrogate_significant_only_subject_means": {"all_segments": {"A1": 0.0122, "A2": 0.0096, "A3": 0.0072},
                                                                 "significant_only": {"A1": 0.0218, "A2": 0.0178, "A3": 0.0147},
                                                                 "fig3a_read": {"A1": 0.0118, "A2": 0.0100, "A3": 0.0065}},
        },
        "reading": ("Every other crop length (3, 5, 6 s) and the middle 4 s give A1 - A3 within +-0.0008 (all p > .3); 1-s duration "
                    "bins give +0.0013 [-0.0002, +0.0027]. Surrogate z-scored MI shows no significant subtype difference, same direction (circular shifts p = .09, "
                    "the paper's block-swap surrogates p = .17), and only 7-8% of segments of any subtype exceed the 95th percentile "
                    "of their block-swap surrogates. With delta 1-2.5 Hz or the F4-C4 derivation the floor is 94-96% of the raw "
                    "difference and neither control is significant (4-16% of raw, p > .13). The paper's secondary 'light > deep' reading "
                    "behaves the same way within A1: S2 - S4 raw +0.0035 (p = .0001), cropped -0.0004 (p = .59), debiased -0.0001. "
                    "Adjusting for duration as a covariate (segment-level mixed model) shrinks A1 - A3 by 74% (linear), 84% (1/duration) "
                    "or 97% (log duration); the linear and inverse fits stay significant only at the segment level (pseudo-replication), "
                    "and the subject-level residualised contrast is +0.0006 (p = .16). Fig. 3a matches the all-segment means; means over "
                    "surrogate-significant segments only would be about twice as high (claim_scope_addendum.md)."),
    },
    "lever": {
        "name": ("data length: the Tort MI of a short segment has a positive finite-sample floor (~1/length), and A1 segments are about "
                 "half as long as A3, so raw MI ranks subtypes by duration"),
        "flips_result": True,
        "variants_tried": ["C-crop first 4 s (primary)", "C-debias MI minus circular-shift floor (secondary)", "crop 3/5/6 s and middle 4 s",
                           "duration-matched 1-s bins", "MI ~ 1/duration within subtype", "surrogate z (circular shift; block swap)",
                           "delta 1-2.5 Hz", "F4-C4 derivation", "A1 S2 vs S4"],
        "honesty_notes": [
            ("Raw MI here is mostly the estimator's length-dependent floor: the floor is 93% (A1), 95% (A2) and 99% (A3) of mean MI, "
             f"and its A1 - A3 difference is {fl['mean'] / d_raw:.0%} of the raw one. Above the floor a small A1 > A2 > A3 ordering remains "
             f"(MI minus floor .00091 / .00050 / .00010; A1 - A3 {deb['mean']:+.5f}, p = {deb['p']:.2g}; A1 - A2 p = .087, A2 - A3 p = .066). "
             f"The equal-length estimate ({crop['mean']:+.5f}) is the same size, only less precise; its p = {crop['p']:.2g} is not evidence of no "
             "effect. Duration-matched bins (+.00125) and surrogate z point the same way. So every control agrees on the direction and on "
             "a small residual, and differs only in precision. The key therefore reads: raw MI overstates the subtype difference about "
             "sixfold and cannot be read as coupling strength; the direction survives above the floor. 'Entirely an artefact' or 'no "
             "coupling difference' is stronger than the evidence, and the grader fails it (review of ba56a10, F1)."),
            "The authors did address duration: they kept only segments with more than two delta cycles for that reason. The point is that "
            "this rule leaves A1 segments at half the length of A3 and does not remove the floor, not that duration was ignored.",
            "The paper extracts components with masking EMD and its settings are under-specified; filter-Hilbert is substituted. The raw "
            "MI levels still match Fig. 3a within about 0.001, and the floor argument concerns the MI histogram, not the decomposition.",
            "Segment counts exceed Table S2's; whatever else the paper excluded, the length gap between subtypes is large (7.2 s) and "
            "present in every subject.",
        ],
    },
    "failure_axis": "wrong cause (measurement artefact): a segment-length bias of the MI estimator read as a subtype difference in coupling strength",
    "critical_path_test": {
        "question": "Does the stated method, output schema, or a routine evaluation recipe already prescribe or determine the decisive diagnostic?",
        "answer": "no (judgement beyond routine execution, still necessary for the public question)",
        "rationale": ("The pinned method (whole-night filter-Hilbert, per-segment Tort MI, the paper's >2-cycle inclusion rule, subject means, "
                      "paired subtype contrasts) runs end to end and reproduces A1 > A2 > A3 without ever comparing segment lengths, "
                      "computing a null floor, or equalising windows; the required outputs are per-subject subtype means and contrasts. "
                      "Routine enumeration of the other contrasts (A1-A2, A2-A3, stage) repeats the same ordering, because every contrast "
                      "is confounded with length. The public question (does the MI ordering show a difference in coupling strength?) "
                      "makes the check necessary: MI is only comparable across conditions at matched data length."),
    },
    "agent_headroom_hypothesis": (
        "Agents implement Tort MI as pinned, get the paper's numbers almost exactly with a very large effect (d_z 2.5, p = 4e-8), and "
        "confirm that A1 shows the strongest coupling, adding generic PAC caveats (volume conduction, non-sinusoidal waveforms, spectral "
        "power, small n). Seeing that the subtypes differ two-fold in length and that the estimator's floor scales with length requires "
        "interrogating the measure against the annotation, not running more contrasts. Risks: PAC-literate agents may z-score against "
        "surrogates as a habit; routine per-segment significance testing shows coupling barely above chance (7-8% of segments pass "
        "the 95th percentile in every subtype); the paper's Methods give the duration rationale for the >2-cycle rule, which an agent "
        "recalling the paper may follow up (the task runs offline). All of these are accepted as sufficient routes when linked to the "
        "subtype ordering: equal-length windows, floor/surrogate subtraction or z-scores, duration-matched pairs or bins, MI vs "
        "duration slopes within subtype, duration as a covariate, and an equal share of surrogate-significant segments. The required "
        "outputs ask for no significance-against-chance quantity. Stage 5 decides."),
    "cue_terms": ["debias", "de-bias", "bias", "floor", "surrogate", "normalis", "normaliz", "z-scor", "chance", "equal-length",
                  "equal length", "fixed-length", "fixed length", "length-matched", "duration-matched", "matched duration",
                  "data length", "segment length", "sample size", "number of samples", "crop", "truncat", "window length"],
    "verdict": "build_hard_candidate",
    "verdict_reason": (
        f"The paper's ordering reproduces on its own data with its estimator (A1 {raw['mean_a']:.4f} > A2 > A3 {raw['mean_b']:.4f}; "
        f"A1 - A3 {raw['mean']:+.5f}, d_z {raw['dz']:.2f}, p = {raw['p']:.1g}) and the predeclared rule gives 'length bias accounts': "
        f"the finite-sample floor alone is {fl['mean'] / d_raw:.0%} of the difference, and at equal 4-s length or after subtracting the "
        f"floor A1 - A3 falls to {crop['mean'] / d_raw:.0%} / {deb['mean'] / d_raw:.0%} of raw, leaving a small A1 > A3 residual "
        f"(p = {deb['p']:.2g} after floor subtraction). The rule's margin is narrow (crop upper CI {crop['ci'][1] / d_raw:.0%} of raw against "
        "50%; rule_margin). The direction of the reduction holds across crop lengths, the 1-2.5 Hz band, F4-C4 and surrogate z. Off the requested execution path and un-cued; fair because MI's length dependence is a "
        "documented property of the estimator and the paper's own inclusion rule shows the authors considered duration."),
}
ev["retrospective_notes"] = [{
    "date": "2026-10-09", "timing": "post_probe", "record_ref": ADD, "evidence_refs": [PS, PSLOG],
    "note": ("Which segments Fig. 3a averages (open in claim_scope.md): all analysed segments; surrogate-significant-only means would "
             "be about twice the bars. The paper's per-segment surrogate significance test is therefore left out of the pinned "
             "method and of the instruction; the paper is never described as lacking surrogate testing. The >2-cycle rule is stated "
             "neutrally in the instruction; its stated purpose (reducing duration-related MI differences) is omitted there because it "
             "names the diagnostic and is not needed to state the objective or run the method, and the task runs offline. Duration is "
             "described in the oracle, proposal and evidence as acknowledged and partly addressed by the authors.")}]
json.dump(ev, open("step0/evidence.json", "w"), indent=1)
print("wrote step0/evidence.json")
