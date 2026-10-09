"""Write PDEEG-001/step0/evidence.json (run from the task directory; needs tools/artifact_ref.py)."""
import json
import sys

sys.path.insert(0, "../tools")
from artifact_ref import artifact_ref as R  # noqa: E402

m = json.load(open("step0/outputs/metrics.json"))
M, LOG, QC, FEAT, PROBE = (R("step0/outputs/metrics.json"), R("step0/run.log"), R("step0/outputs/recording_qc.csv"),
                           R("step0/outputs/segment_features_ThEn.csv"), R("step0/probe.py"))
U = json.load(open("step0/outputs/metrics_unm.json"))["configs"]
MU, LOGU1, LOGU2 = R("step0/outputs/metrics_unm.json"), R("step0/run_unm.log"), R("step0/run_unm_on.log")
SHA, CONS = R("step0/outputs/unm_d002_sha256.tsv"), R("step0/outputs/unm_run1_run2_consistency.json")
bf = m["by_feature"]
P = m["primary_feature"]
wv = m["variants_primary"]["filter_whole_recording_then_segment"]
pct = lambda v: round(100 * v, 2)  # noqa: E731

ev = {
    "schema_version": "step0-evidence-v1",
    "task_id": "PDEEG-001",
    "opportunity_id": "adhoc:PDEEG-001",
    "_comment": "Step-0 record. EvidenceItem/ArtifactRef shapes follow contracts/curation/curation-contracts-v1.schema.json. Status vocabulary: reported | verified | measured | planned | missing. This file names the hidden lever (segment-level vs subject-level evaluation), so like solution/ it is author_private for any held-out task.",
    "intake_route": ["advance_to_step0"],
    "intake_reason": "Primary empirical paper with an exact, fully specified pipeline and headline (PD off-medication vs HC from resting EEG, 99.7-99.9% accuracy, KNN on DWT entropy features, 10 x 10-fold CV over 10 s segments). Fixed public substrate: OpenNeuro ds002778 (CC0; no credentials; data unchanged since the v1.0.2 the paper used, later versions edited README/citations only). Classical ML, minutes of CPU. Truth is a measurement on that substrate. The scientific concern is concrete: the folds are over segments, so each test segment's subject (about 19 segments each) also has ~16 other segments in the training set, while the paper presents the features as PD biomarkers for detection.",
    "paper": {
        "paper_id": "10.1038/s41598-022-26644-7",
        "paper_kind": "primary_empirical",
        "claim_and_contrast": "Aljalal, Aldosari, Molinas, AlSharabi & Alturki 2022 (Sci Rep 12:22547): off-medication PD vs HC on the SanDiego resting EEG set (15 PD, 16 HC, 32 channels, 512 Hz); 10 s non-overlapping segments, 0.5-32 Hz 5th-order Butterworth, db4 level-4 DWT with each sub-band reconstructed (cD1-cD4, cA4) plus the segment, one metric per signal per channel (192 features), KNN k=3 Euclidean, 10 x 10-fold CV over segments; best 99.89% (TShEn), ThEn 99.72%, SuEn 99.66%, LogEn 97.94%. The paper frames the features as 'good biomarkers for PD detection'.",
        "target_measurement": "Cross-validated off-PD vs HC accuracy of the paper's KNN pipeline under (a) the paper's segment-level 10 x 10-fold CV and (b) subject-independent evaluation (leave-one-subject-out; subject-grouped 10-fold), with per-subject majority-vote accuracy, exact binomial CI and a subject-level label-permutation test.",
        "reported_values": [
            {"field": "seg_10x10fold_knn_accuracy_pct", "status": "reported", "evidence_refs": [], "value": m["paper_reported_10x10fold_knn"]},
            {"field": "segment_counts", "status": "reported", "evidence_refs": [], "value": {"off_PD": 300, "HC": 306, "features": 192}},
            {"field": "paper_on_leakage", "status": "reported", "evidence_refs": [],
             "value": "Leave-one-subject-out was run only on the separate UNM cohort (54 subjects), reaching 85-88.6% after greedy forward channel selection that maximises that same LOSO accuracy. The Discussion attributes the LOSO-vs-k-fold gap to segments from the same subjects being in training and test ('data leakage problem') and calls k-fold 'intra-subject classification'. No subject-independent result is reported for the SanDiego set behind the 99.7-99.9% headline."},
            {"field": "dataset_curator_warning", "status": "verified", "evidence_refs": [],
             "value": "The ds002778 README warns that a high PD-vs-HC machine-learning accuracy obtained without cross-validation and without validation on another dataset could mislead patients and the public."}
        ]
    },
    "substrate": {
        "dataset_id": "ds002778",
        "fetcher": "public S3 https://s3.amazonaws.com/openneuro.org/ds002778/ (no credentials, 571 MB): sub-hc*/ses-hc/eeg/*_eeg.bdf and sub-pd*/ses-off/eeg/*_eeg.bdf, participants.tsv",
        "version_pin": "OpenNeuro ds002778 1.0.4 as served on 2026-10-08 (data identical to 1.0.2); mne==1.13.2 pywavelets==1.10.0 scikit-learn==1.9.1 numpy==2.5.3 scipy==1.18.1 pandas==3.0.6",
        "cohort": f"{m['n_hc']} HC (ses-hc) + {m['n_pd']} PD off medication (ses-off); 32 scalp channels (EXG excluded), CAR; {m['n_segments']} segments ({m['n_pd_segments']} PD, {m['n_hc_segments']} HC; paper 300/306, difference from recording lengths: sub-pd14 alone gives 29 segments)",
        "access": "public"
    },
    "probe": {
        "script": "step0/probe.py",
        "command": "DS002778_DIR=<ds002778> python step0/probe.py > step0/run.log 2>&1; python step0/fetch_unm_d002.py <d002>; UNM_D002_DIR=<d002> python step0/probe_unm.py > step0/run_unm.log 2>&1 (resumed after a session restart into step0/run_unm_on.log; probe_unm.py skips configs already in metrics_unm.json)",
        "log": "step0/run.log",
        "outputs": ["step0/outputs/metrics.json", "step0/outputs/recording_qc.csv", "step0/outputs/segment_features_ThEn.csv", "step0/outputs/pip_freeze.txt",
                    "step0/outputs/metrics_unm.json", "step0/outputs/unm_d002_sha256.tsv", "step0/outputs/unm_run1_run2_consistency.json"],
        "ran_on": "2026-10-08, macOS arm64 (Darwin 24.6), Python 3.14.7; SanDiego 101 s; UNM ~45 min per medication condition (8 processes)",
        "reproducibility": "After a session restart wiped the scratch environment, the venv was rebuilt from step0/outputs/pip_freeze.txt and both datasets re-fetched: probe.py reproduced metrics.json and segment_features_ThEn.csv byte-identically, and the re-extracted UNM features reproduced every run-1 off-PD SEG and LOSO value exactly (unm_run1_run2_consistency.json, computed with scikit-learn LOSO, which also cross-checks probe_unm.py's distance-matrix LOSO)."
    },
    "results": [
        {"field": "raw_effect", "status": "measured", "evidence_refs": [M, LOG],
         "value": {"seg_10x10fold_knn_accuracy_pct": {k: pct(v["SEG_10x10fold_acc_mean_sd_over_folds"][0]) for k, v in bf.items()},
                   "summary": f"The paper-motivated analysis reproduces: segment-level 10 x 10-fold KNN accuracy {pct(bf[P]['SEG_10x10fold_acc_mean_sd_over_folds'][0])}% for {P} (paper 99.72%), 99.3-99.7% for SuEn, LogEn and LBP. TShEn reaches only {pct(bf['TShEn']['SEG_10x10fold_acc_mean_sd_over_folds'][0])}% because Eqs. 8-9 are ambiguous (unique-value normalisation); it is not used as the primary feature."}},
        {"field": "lever_premise", "status": "measured", "evidence_refs": [M, LOG],
         "value": {"subject_independent": {k: {"loso_segment_acc_pct": pct(v["SUBJ_loso"]["segment_acc"]),
                                               "loso_subject_vote": f"{v['SUBJ_loso']['subject_vote_correct']}/{v['SUBJ_loso']['n_subjects']}",
                                               "loso_subject_vote_ci95": v["SUBJ_loso"]["subject_vote_ci95_exact"],
                                               "grouped_10x10fold_acc_pct": pct(v["SUBJ_grouped_10x10fold_acc_mean_sd_over_repeats"][0])} for k, v in bf.items()},
                   "primary_loso_permutation": m["SUBJ_loso_permutation"],
                   "summary": f"Evaluated on held-out subjects, the same pipeline is at chance for every feature: {P} LOSO {pct(bf[P]['SUBJ_loso']['segment_acc'])}% of segments, {bf[P]['SUBJ_loso']['subject_vote_correct']}/31 subjects by majority vote (exact 95% CI {bf[P]['SUBJ_loso']['subject_vote_ci95_exact']}), subject-grouped 10-fold {pct(bf[P]['SUBJ_grouped_10x10fold_acc_mean_sd_over_repeats'][0])}%; subject-level permutation p={m['SUBJ_loso_permutation']['p']} (null mean {m['SUBJ_loso_permutation']['null_mean']})."}},
        {"field": "controlled_effect", "status": "measured", "evidence_refs": [M],
         "value": {"IDENT": m["IDENT"],
                   "summary": f"Subject fingerprinting accounts for the segment-level number: with RANDOM subject-level labels (no disease information) the paper's segment-level CV still scores {pct(m['IDENT']['SEG_10fold_acc_with_random_subject_labels']['mean'])}% (range {pct(m['IDENT']['SEG_10fold_acc_with_random_subject_labels']['min'])}-{pct(m['IDENT']['SEG_10fold_acc_with_random_subject_labels']['max'])}% over 100 assignments), and the features identify which of 31 subjects a segment came from at {pct(m['IDENT']['subject_id_31way_SEG_10fold_acc'])}% (chance 3.2%). The segment-level accuracy therefore measures recognition of a person seen in training, not detection of PD in a new person."}},
        {"field": "alternative_explanations", "status": "measured", "evidence_refs": [M, QC],
         "value": {"BAND": m["BAND"], "variants_primary": m["variants_primary"],
                   "summary": f"Neither frequency range generalises across subjects: 0-32 Hz sub-bands and the 32-256 Hz sub-bands above the paper's own low-pass both give ~99% segment-level and ~43-49% LOSO; the band-passed segment alone, without the DWT sub-bands, gives 90.6% and 55.1% (17/31, CI 0.36-0.73). 60 Hz line-noise ratio does not differ by group (p=.35); 64-128 Hz power is nominally higher in PD (p=.055) but does not yield subject-level accuracy. Causal filtering and z-scored features change nothing material (segment-level 99.2-99.7%, LOSO 38-40%). Filter order does not matter either: band-passing the whole recording before segmenting (the paper's overview order) gives segment-level {wv['SEG_10x10fold'][0]:.2%}, LOSO {wv['SUBJ_loso']['segment_acc']:.2%} ({wv['SUBJ_loso']['subject_vote_correct']}/31), subject-grouped {wv['SUBJ_grouped_10x10fold'][0]:.2%}, against 99.73% / 45.36% (13/31) / 46.96% with per-segment filtering."}},
        {"field": "unm_paper_loso_claim", "status": "measured", "evidence_refs": [MU, LOGU1, LOGU2, SHA, CONS],
         "value": {"configs": U,
                   "summary": ("UNM cohort (PRED+CT d002, 27 PD / 27 HC, 2 s segments, 32 SanDiego channels; segment counts match the paper's Table 10 to within one segment). "
                               "(1) Segment-level 10 x 10-fold reproduces: 94.9-98.9% for ThEn/SuEn/LogEn (paper 95.8-99.5%). "
                               "(2) The paper's LOSO numbers (Table 12: KNN 82.4-85.2%, LDA+SuEn 88.6%) are not reproduced even with the paper's own procedure, forward channel selection scored by LOSO on all 54 subjects: KNN 65.6-80.6%, LDA+SuEn 73.6-81.3%, highest for on-PD eyes closed (the condition named in the paper's text). "
                               "(3) That procedure is optimistic: for off-PD eyes-open ThEn it gives 71.5%, but the same procedure on subject-level permuted labels gives mean 66.1%, 95th percentile 73.6% (p=.12, 100 permutations). "
                               "(4) Nested inside each held-out subject's fold, the same selection gives 55.5-58.9% (ThEn: off open/closed, on open) and 73.4% for on-PD eyes closed (42/54 subjects, exact CI 0.64-0.88). "
                               "(5) Without selection, LOSO is near chance with eyes open (46-61% of segments; 23-39/54 subjects) and modestly above chance with eyes closed (59-71%; 33-43/54 subjects; e.g. off-PD LogEn 43/54, binomial p~1e-5). "
                               "So UNM shows modest subject-independent discrimination, mainly eyes closed, far below the ~99% segment-level figures and below the paper's selected LOSO numbers.")}}
    ],
    "lever": {
        "name": "evaluation unit: segment-level k-fold (subjects shared across train/test) vs subject-independent CV",
        "flips_result": True,
        "variants_tried": [
            "8 feature metrics (LogEn, ThEn, SuEn, NoEn, ShEn, Eng, LBP, TShEn best-effort) x {segment 10x10-fold, LOSO, subject-grouped 10x10-fold}",
            "subject-level label permutation of LOSO (1000)",
            "random subject-level labels under segment-level CV (100); 31-way subject identification",
            "sub-band subsets: cA4+cD4 (0-32 Hz), cD1-cD3 (32-256 Hz), segment only",
            "zero-phase vs causal Butterworth; raw vs z-scored features (scaler fit inside folds)",
            "filter order: band-pass per 10 s segment (paper Methods and Results) vs whole recording before segmenting (paper overview)"
        ],
        "honesty_notes": [
            "Uncertainty: with 31 subjects the subject-level CI upper bound is ~0.61, so a modest true subject-level accuracy with these features is not excluded; the result shows the 99.7% is not evidence of PD detection in new subjects, not that resting EEG carries no PD information (group-level differences in this dataset are reported elsewhere, e.g. beta-band measures).",
            "Several LOSO values fall below 50% (z-scored ThEn: 9/31 subjects). For the primary pipeline the observed LOSO accuracy lies inside the subject-level permutation null (null mean 0.48, p=.65); below-chance cross-validated accuracy is a known small-sample/KNN artefact, so it is not interpreted as anti-signal.",
            "SanDiego (chance at subject level) and UNM (modest above-chance subject-level accuracy with eyes closed) differ. The honest general statement is that segment-level accuracy overstates subject-independent performance by roughly 25-50 points on both cohorts, not that resting EEG cannot separate PD from controls.",
            "UNM caveats: preprocessing for UNM is unstated in the paper (here: file average reference, per-segment demeaning); Table 12's caption says off-PD but its text says on-PD and the eyes state is not given, so all four combinations are reported; only ThEn got the nested estimate and only off-PD eyes-open ThEn got the permutation null; 16 KNN configs plus 4 LDA cells were examined, so single configs near p=.05 are not interpreted.",
            "UNM data provenance: the PRED+CT d002 link resolves to a SharePoint guest-access folder that also contains unrelated third-party uploads; only <id>_<session>_PD_REST.mat and IMPORT_ME_REST.xlsx were used, and their sha256 are recorded (unm_d002_sha256.tsv). sub 821's on-medication file contains the rest block twice; it is kept, which reproduces the paper's 840 on-PD segments.",
            "The paper is internally inconsistent on filter order: the overview of the pipeline says the band-pass is applied before segmentation, while the preprocessing Methods and the SanDiego Results both say the 10 s segments are filtered. The task follows the Methods/Results order and states this in instruction.md; the other order gives the same result (variants_primary.filter_whole_recording_then_segment).",
            "Manual artefact rejection by the original authors cannot be replicated on the raw BDFs; segment counts differ slightly (593 vs 606). The segment-level result reproduces regardless."
        ]
    },
    "failure_axis": "leakage (statistical inference / evaluation design): participant leakage in segment-level CV; the symptom is an over-claim, a leaked segment-level accuracy reported as PD detection",
    "critical_path_test": {
        "question": "To complete exactly what the instruction asks, must a competent agent already make this correction or choice?",
        "answer": "no, as built: instruction.md pins the paper's 10 x 10-fold CV over segments; the participant-held-out evaluation is required only by the estimate check, which the instruction does not describe",
        "rationale": "If the instruction leaves the CV unit open, choosing subject-grouped CV is on the requested path and is a well-known correction (the workflow skill lists subject-grouped CV as usually telegraphed), so the task would likely be an easy control. If the instruction faithfully pins the paper's procedure (10 x 10-fold over segments) and asks whether the result holds and what it supports, computing the requested number does not require any subject-level evaluation; recognising that the number does not support detection in new patients, and measuring that, is off the execution path."
    },
    "agent_headroom_hypothesis": "With the paper's segment-level CV pinned, agents reproduce ~99.7% and report that the result reproduces, possibly with a generic 'small sample' or 'leakage may inflate' caveat but without a subject-independent number. Risks that shrink the gap: subject leakage in EEG is a widely known pitfall, the paper itself names it, and the dataset README warns about high-accuracy claims, so a careful agent may volunteer LOSO. Calibration must decide; as built, the verifier requires the reported estimate to come from a replayable cross-validation in which no participant is in both training and test (tests/test_outputs.py), not a caveat. The instruction's estimate field ('the accuracy you would report for this pipeline as a PD-vs-control classifier') and the required participant_id column are residual cues.",
    "cue_terms": ["leakage", "leave-one-subject-out", "LOSO", "subject-wise", "subject-level", "grouped", "GroupKFold", "cross-subject", "inter-subject", "new patients", "generaliz"],
    "verdict": "build_hard_candidate",
    "verdict_reason": "The scientific issue is supported on both cohorts. SanDiego (the task substrate): the paper's segment-level 10 x 10-fold accuracy reproduces (99.7%), the same pipeline is at chance on held-out subjects for all eight feature metrics (primary LOSO 45%, 13/31 subjects, permutation p=.65), and the segment-level CV scores 99.5% with random subject labels while identifying subjects at 99.2%, so the headline measures subject recognition, not PD detection. Alternative explanations tested (non-neural high-band cues, line noise, filter, scaling) do not change this. UNM (the paper's own subject-independent check): segment-level ~99% reproduces, but the paper's 82-88.6% LOSO is not reproduced even with its selection-on-test procedure (65.6-81.3%), nested selection gives 55-73%, and no-selection LOSO is 46-71%; so subject-independent performance there is modest, not absent. Benchmark fit is uncertain: hard only if the instruction pins the paper's segment-level procedure so the subject-level check is off the execution path; subject leakage is well known, so an easy-control outcome is a real risk that only agent calibration can settle."
}
open("step0/evidence.json", "w").write(json.dumps(ev, indent=2, ensure_ascii=False) + "\n")
print("ok")
