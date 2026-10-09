# Parkinson's disease detection from resting-state EEG entropy features (PDEEG-001)

## Scientific context

Aljalal, Aldosari, Molinas, AlSharabi & Alturki (2022), *Detection of Parkinson's disease
from EEG signals using discrete wavelet transform, different entropy measures, and machine
learning techniques*, Scientific Reports 12:22547
([doi:10.1038/s41598-022-26644-7](https://doi.org/10.1038/s41598-022-26644-7)), classify
Parkinson's disease patients off medication versus healthy controls from resting-state EEG
in the UC San Diego dataset (OpenNeuro ds002778). Entropy measures of discrete-wavelet
sub-bands, fed to a k-nearest-neighbour classifier, reach 99.7–99.9% accuracy under
10 × 10-fold cross-validation over 10 s segments. Threshold entropy gives 99.72%. The
authors present these features as biomarkers for PD detection.

## Task

The data are staged, offline, under `/app/data/ds002778`, and `/app/source_manifest.json`
lists their identities. They comprise `participants.tsv` and the resting recordings of the
16 healthy controls (`ses-hc`) and the 15 patients off medication (`ses-off`). Do not fetch
substitute data. Keep the literal `participant_id` values, and join by identity rather than
by position.

**Reproduce the threshold-entropy result, and report whether it holds on these data and
what accuracy it supports for this pipeline as a PD-vs-control classifier.**

The paper's pipeline, with the details it leaves open for these files fixed here:

1. Channels: the 32 scalp electrodes `Fp1, AF3, F7, F3, FC1, FC5, T7, C3, CP1, CP5, P7, P3,
   Pz, PO3, O1, Oz, O2, PO4, P4, P8, CP6, CP2, C4, T8, FC6, FC2, F4, F8, AF4, Fp2, Fz, Cz`,
   in µV. Remove each channel's mean over the recording, then re-reference to the average
   of these 32 channels.
2. Segments: consecutive non-overlapping 10 s windows (5120 samples at 512 Hz) from sample
   0 of each recording. Discard the incomplete tail.
3. Filtering, per segment: a 5th-order Butterworth band-pass at 0.5–32 Hz, applied
   zero-phase (forward–backward) in second-order sections.
4. Decomposition: a 4-level `db4` discrete wavelet transform with symmetric extension
   (MATLAB `'sym'`, PyWavelets `'symmetric'`). Reconstruct each of D1, D2, D3, D4 and A4
   separately at full segment length (MATLAB `wrcoef`). Together with the filtered segment
   itself (X), this gives 6 signals per channel.
5. Feature: the threshold entropy of each signal, i.e. the number of samples with
   |x| > 0.2 µV (MATLAB `wentropy(x, 'threshold', 0.2)`). That gives 32 × 6 = 192 features
   per segment.
6. Classifier: k-nearest neighbours, k = 3, Euclidean distance on the unscaled features,
   majority vote.
7. The paper's evaluation: 10 repetitions of stratified 10-fold cross-validation over the
   segments, reporting the mean accuracy.

Any implementation choices the description leaves open should follow common practice.

Report, in plain terms, whether the result reproduces on these data and what it supports,
stating only what your analysis actually shows.

## Output Location

Write all outputs to `${OUTPUT_DIR}` (default `/app/output`). `/app/output_schema.json`
gives the exact columns and fields.

## Required Outputs

- `segments.csv`: one row per segment with `segment_id, participant_id, group, start_sample`
  and the 192 features as `<channel>_<signal>` columns (`Fp1_D1` … `Cz_X`).
- `cv_predictions.csv`: for every cross-validation you report, the out-of-fold prediction
  for every segment as `evaluation_id, repeat, fold, segment_id, predicted_group`.
- `evaluations.json`: an `evaluations` list, one entry per cross-validation in
  `cv_predictions.csv` (`evaluation_id`, `description`, mean `accuracy`). Also an `estimate`
  object: the `accuracy` you would report for this pipeline as a PD-vs-control classifier,
  and the `evaluation_id` it comes from.
- `run_metadata.json`: dataset id, counts, the implementation choices you made, and
  software versions.
- `findings.md`: a short write-up of the results and what they support.

Numerically equivalent implementations are accepted.

## Failure handling

If a precondition fails (missing or altered staged data, for example), keep whatever
evidence you have, exit non-zero, and write `failure_report.json` with
`"status": "failed_precondition"` and a non-empty `reason`. Do not change the inputs.
