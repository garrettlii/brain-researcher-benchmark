# CAPPAC-001: source claim and planned Step-0 scope

Author-private record. Completed before writing or running the probe (TASK_WORKFLOW
Stage 0.5). The dated pre-probe version is kept; later changes go in as new revisions.
Source inspection is not a measured result, and passing this gate does not establish
benchmark difficulty.

## Source inspection

- **Review date and timing:** 2026-10-09, pre-probe. No modulation index (MI) or other EEG
  quantity has been computed on CAP Sleep Database signals before this file was committed.
- **Exposure before writing:**
  - A screening agent tabulated phase-A durations by subtype from the 16 healthy annotation
    files (n1–n16.txt):
    - A1: mean 6.0 s, median 5 s.
    - A2: mean 8.0 s, median 7 s.
    - A3: mean 13.4 s, median 11 s.
    - A1 is shorter than A3 in all 16 subjects.
  - The same agent simulated the MI floor on pink noise. MI fell from about 0.009 at
    4.6 s to about 0.003 at 14 s.
  - It read the bar heights in Fig. 3.
  - I read the 16 EDF headers, for channel labels and sampling rates only.
  - The duration half of PREMISE is therefore known in advance and is not a blind test.
- **Primary paper:** Yeh C-H & Shi W (2018), "Identifying Phase-Amplitude Coupling in
  Cyclic Alternating Pattern using Masking Signals", *Sci Rep* 8:3049,
  doi:10.1038/s41598-018-21013-9, PMC5805690, CC BY 4.0.
  - Full text: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC5805690/fullTextXML
  - Supplement: https://static-content.springer.com/esm/art%3A10.1038%2Fs41598-018-21013-9/MediaObjects/41598_2018_21013_MOESM1_ESM.pdf
- **Material inspected:**
  - Abstract.
  - Results:
    - "Time-frequency analysis and phase-amplitude frequency plane" (Fig. 1).
    - "Phase-amplitude dependence" (Fig. 2).
    - "Subtype A1 shows higher δ-α/low β MPACs" (Fig. 3a,b).
    - "Effects of pathophysiological factors" (Fig. 3c).
    - "Light sleep shows stronger δ-α/low β MPACs than deep sleep" (Fig. 3d).
  - Discussion.
  - Methods: Materials, Signal preprocessing, Masking decomposition, Modulation index,
    Cycle-Frequency, Surrogate data testing, Statistical Analysis.
  - Limitations of the Study.
  - Supplementary Information:
    - CAP definitions.
    - Table S1: 16 controls, plus pathologies.
    - Table S2: n per cell; Control A1 2741, A2 829, A3 820.
    - Table S3 and Figs S1–S2 (EMD demo).
- **Data:** PhysioNet CAP Sleep Database 1.0.0 (https://physionet.org/content/capslpdb/1.0.0/),
  Open Data Commons Attribution 1.0, no login. Healthy recordings n1–n16 (`nN.edf` plus the
  `nN.txt` RemLogic event export).
- **Missing source material:**
  - The masking-EMD settings needed to reimplement the decomposition exactly: mask
    amplitudes per level beyond "standard deviation of the input", the number of phase steps,
    which IMFs form "δ" and "α/low β", and the Fast EMD stopping rules.
  - Whether the GLMM used every segment's MI or only surrogate-significant MIs.
  - Which electrodes entered the GLMM ("location of electrodes" is a random factor).
  - None of these blocks a test of the claim, because the claim is stated for the MI
    estimator. See the departures below.

## Source-to-task comparison

| Dimension | Paper's claim/method (locator) | Planned task | Match or departure, and rationale |
|---|---|---|---|
| Population and inclusion/exclusion | 108 CAP-database recordings; the Control group is 16 healthy subjects with no neurological, psychiatric or medical disorder (Methods: Materials; Table S1). | The same 16 healthy recordings, n1–n16. | Match for the Control group. The other seven pathology groups are not used (data volume). The claim tested is the Control-group bar set in Fig. 3a, which the paper reports separately. |
| Condition and acquisition | All-night PSG, scored with R&K stages and the Terzano CAP atlas; EEG at 100 or 512 Hz; MT-annotated segments excluded (Materials). | Same recordings and annotations; phase-A events MCAP-A1/A2/A3; segments in, or overlapping, an MT-scored epoch excluded. | Match. Some EDFs are actually 128/200 Hz; MI is computed within subject, so the rate does not enter the contrasts. |
| Preprocessing, estimator, normalization | 1–50 Hz 6th-order Butterworth; PCA (95%) then FastICA, removing ICs with \|r\| > 0.5 to EOG/ECG; masking EMD on "the total length of the analyzed sequences"; Hilbert phase/amplitude; Tort MI with 20 bins, MI = KL(P,U)/log N (Preprocessing; Masking decomposition; Modulation index). | One central–mastoid derivation per subject: C4-A1, or C3-A2 for n6–n9, which lack C4-A1. Zero-phase Butterworth band-pass on the whole-night continuous signal: δ 0.25–2.5 Hz for phase, 10–17 Hz for amplitude. Hilbert transform. Tort MI with 20 bins, computed per phase-A segment. | **Disclosed adaptation.** Masking EMD is replaced by filter–Hilbert because its settings are not specified enough to reimplement (above). The MI step is identical. The MI histogram's dependence on the number of samples/cycles is a property of the estimator, not of how the components are extracted. The 1–50 Hz prefilter is omitted because it contradicts the 0.25 Hz lower edge of the paper's own δ band; a 1–2.5 Hz δ variant is exploratory. PCA/ICA is omitted because a single referential derivation is analysed. |
| Time/scale/frequency range and units | Phase band δ 0.25–2.5 Hz; amplitude band α/low β 10–17 Hz (Introduction; Results). Comodulograms are computed over 0.1–3 × 5–30 Hz, but the claim is stated for δ–α/low β. Unit: one phase-A segment, 2–60 s (Suppl. CAP definition). Inclusion: "only the sequences with more than two cycles in δ activities" (Surrogate data testing; Limitations). | δ 0.25–2.5 Hz × 10–17 Hz. A segment is included if its δ phase advances by more than 2 full cycles (unwrapped phase > 4π) inside the analysed window. | Match to the claimed bands. The comodulogram range is not the claim and is not tested. |
| Region, outcome, and aggregation | MI per segment; GLMM over segments with stage, pathology, subject and electrode as random factors; bars show mean ± SEM over segments (Statistical Analysis; Fig. 3). | MI per segment, averaged per subject × subtype; inference across subjects (n = 16). A segment-level mixed model, MI ~ subtype + (1 \| subject), is reported as secondary. | **Disclosed adaptation.** The subject is the unit of generalisation; segment-level SEMs treat about 4,000 segments from 16 people as independent. The mixed model mirrors the paper's GLMM. |
| Contrast, direction, statistic, uncertainty | Control: subtype effect p < 0.0001, Tukey A1 > A2 > A3 (Results; Fig. 3a). Bar reading: A1 ≈ 0.0118, A2 ≈ 0.0100, A3 ≈ 0.0065. | Primary contrast A1 − A3 (paired across subjects): mean, 95% CI, d_z with bootstrap CI. A1 − A2 and A2 − A3 are secondary. | Match in direction and contrast; the paper's largest pair is primary. |
| Interpretation and qualifications | "Coupling intensity is generally the highest in subtype A1 and lowest in A3" and "an elevated δ-α/low β MPAC can reflect some synchronization in CAP" (Abstract). MPAC is offered as a sleep-microstructure biomarker. The authors attribute the A1 effect to α/low-β becoming locked by high-voltage δ synchronization (Discussion). | The scientific question is whether δ–α/low-β coupling strength differs between subtypes, as the paper interprets the MI difference. | Match. |

## Controls and limitations already in the paper

- **Duration (the lever):** the authors acknowledge phase-A duration differences. Their one
  step is the inclusion rule of more than two δ cycles, applied "to both reduce the
  differences in MIs due to different phase-A durations as well as the impacts of artifacts
  in large time scales" (Surrogate data testing), restated in Limitations.
  - They do not equalise segment length or debias MI for length.
  - Raw MI, not a normalised value, is what Fig. 3 plots and the GLMM tests.
  - The task must therefore describe the duration issue as **acknowledged and partly
    addressed by an inclusion threshold**, not as an omission.
- **Surrogates:** 100 block-permutation surrogates per segment pair are used only to
  threshold significance (z-score with Bonferroni). They are not used to normalise MI.
- **SNR:** acknowledged as "a complicated confounding factor" with no specific control
  (Discussion).
- **Spectral power:** the authors argue that α/low-β power peaks do not coincide with the
  comodulogram peaks, so MI is not just power (Discussion). This is a qualitative check
  only.
- **Other limitations:** open-database provenance (Limitations).

## Planned measurement before local outcomes

### Target claim and attribution

The claim is source-aligned. In healthy sleepers, δ(0.25–2.5 Hz)–α/low-β(10–17 Hz) MI is
highest in phase-A1 and lowest in A3 (Yeh & Shi 2018, Fig. 3a, Control). This is read as
a difference in coupling strength.

### Disclosed adaptations

Filter–Hilbert in place of masking EMD; one central–mastoid derivation; no 1–50 Hz
prefilter or PCA/ICA; subject-level inference. Each is justified above, independently of
the outcome.

### Common definitions

- **Segments:** every MCAP-A1/A2/A3 event in `nN.txt`, at any sleep stage, as in Fig. 3a,
  excluding:
  - events in, or overlapping, an MT-scored epoch;
  - events extending beyond the EDF;
  - events failing the >2 δ-cycle rule in the analysed window.
- **Timing:** onsets come from the clock times, aligned to the EDF header start time
  modulo 24 h.
- **Filters:** 4th-order Butterworth applied forward–backward with sosfiltfilt, on the
  whole night, before segmentation. δ is 0.25–2.5 Hz; amplitude is 10–17 Hz.
  - Phase = angle(hilbert(δ)); amplitude = |hilbert(10–17 Hz)|.
  - The Hilbert transform is computed on the whole night before segmentation, so no
    segment has edge effects.
- **MI:** Tort MI with 20 phase bins, MI = (log 20 − H(P)) / log 20.
- **Per-subject aggregation:** mean MI per subtype. A subject enters a contrast only if it
  has ≥ 5 included segments of each subtype in that contrast.
- **Statistics:**
  - Paired differences across subjects: mean, 95% t-CI, Wilcoxon p.
  - d_z with a percentile bootstrap CI: 10,000 resamples of subjects, seed 0.

### RAW (primary)

- MI on each full included segment.
- Contrast: subject-level A1 − A3 (Δraw).
- **Reproduces** if Δraw > 0 and its 95% CI excludes 0.
- Secondary:
  - A1 − A2 and A2 − A3;
  - the segment-level mixed model MI ~ subtype + (1 | subject).

### PREMISE

Both of the following must hold:
1. **Duration:** subject-level mean duration of included A1 segments < A3 (paired;
   known in advance, see Exposure).
2. **Length floor:** the MI floor differs by subtype, by at least 25% of Δraw.
   - Floor for each full segment: the mean MI over 50 within-segment surrogates.
   - Each surrogate circularly shifts the amplitude series inside the segment, by a
     uniform random lag in [0.2 L, 0.8 L]. This keeps both marginals and breaks their
     temporal alignment.
   - The criterion: floor(A1) − floor(A3) > 0, with CI excluding 0, and ≥ 0.25 Δraw.

### CTRL, two estimates of the same quantity

Both estimate the length-unbiased subtype difference in coupling.

- **C-crop (primary):** MI on the first L = 4.0 s of every included segment lasting ≥ 4 s.
  The >2-δ-cycle rule is applied inside the 4-s window. Contrast A1 − A3 = Δcrop.
- **C-debias (secondary):** full-length MI minus that segment's surrogate floor (defined
  under PREMISE). Contrast A1 − A3 = Δdebias.

The two controls attack the same mechanism in two ways: equalising the sample size, and
subtracting the size-specific floor. The verdict requires them to agree.

### Decision rules

- **Length bias accounts for the subtype difference.** Both of these hold for BOTH Δcrop
  and Δdebias:
  - the point estimate is ≤ 0.25 Δraw (negative included);
  - the upper 95% CI is < 0.5 Δraw.
- **Coupling difference persists.** Both of these hold for BOTH controls:
  - the lower 95% CI is > 0;
  - the point estimate is ≥ 0.5 Δraw.
- **Anything else is unresolved.** That includes the two controls disagreeing, or a
  partial reduction with the CI excluding 0. Unresolved means archive.
- **RAW fails:** if RAW does not reproduce, record "not reproduced in this
  dataset/analysis" and archive. CTRL does not rescue it.

### Exploratory, outside the decision

- L = 3, 5 and 6 s, and the middle L s instead of the first.
- Duration-matched A1/A3 pairs.
- δ 1–2.5 Hz.
- The F4-C4/Fp2-F4 bipolar derivations, where available.
- Within-subtype stage contrast (A1: S2 vs S4) raw and cropped. This is the paper's
  "light > deep" claim, which Fig. 3d tests pooled over all 108 recordings; here it is
  run on controls only.
- MI vs duration slopes, and the A2 contrasts.

### Stop/reframe condition

The verdict is decided only by the primary RAW contrast, the predeclared PREMISE and the
two predeclared controls at L = 4 s. If the rule outcome is unresolved, a different L,
window position, band or derivation cannot be substituted after seeing results.

## Decision

**proceed_paper_aligned.** The target is the paper's Control-group subtype ordering of
δ–α/low-β MI, on the paper's own dataset and cohort. The method departures are disclosed
and are justified by missing source specification and by the unit of inference. The
source's existing duration control (the inclusion threshold) is recorded and kept in the
measurement, so the lever tests whether that control is sufficient. It is not presented as
an omission.
