# Threshold-entropy PD classification on ds002778 (off medication vs controls)

**The paper's number reproduces, but it does not measure PD detection.** With the pinned
pipeline and the paper's 10 x 10-fold cross-validation over segments, KNN accuracy is
99.7% (paper: 99.72%). When the participant being classified is held out of
training, the same pipeline is at chance: leave-one-participant-out 45.4% of
segments, 13/31 participants correct by majority vote
(exact 95% CI 0.25-0.61), participant-grouped 10 x 10-fold 47.0%.
A participant-level label permutation gives p = 0.6414 (null mean 48.3%).
The accuracy I would report for this pipeline as a PD-vs-control classifier is the held-out-
participant segment accuracy, 45.4%: no better than chance on these 31 people.

## Why the segment-level number is high

The paper's folds are drawn over the 593 segments, so each test segment has about 16
segments from the same recording in the training set. The features fingerprint
individuals:

- 31-way participant identification from a single segment:
  99.3% (chance 3.2%).
- The same segment-level CV with *random* participant-level labels (no disease information,
  100 assignments): mean 99.5%,
  range 98.8%-100.0%.

Any participant-level label is "classified" at ~99% under this design, so the 99.7% says the
features recognise a person seen in training, not that they carry a PD signature.

## Uncertainty and limits

- n = 31 (15 PD, 16 HC). The held-out estimate is imprecise: the majority-vote CI spans
  25%-61%, so a modest real effect (e.g. 60% accuracy) cannot be excluded. What is
  excluded is anything near the reported 99.7%.
- This tests one feature (threshold entropy) and one classifier as pinned. In Step-0 runs
  the other seven metrics from the paper gave 78.7-99.7% under segment-level CV and
  39.0-53.3% with participants held out; other classifiers or feature selection were not
  explored here.
- Filtering each segment follows the paper's Methods and Results; its pipeline overview
  filters the recording before segmenting. In Step 0 that order gave the same picture
  (99.7% segment-level, 45.2% held-out).
- Segment counts differ slightly from the paper (593 vs 606); the paper does not say which
  segments it kept or rejected.
- Off-medication only; the on-medication sessions were not analysed.


Reported estimate: 45.4% (segment_accuracy).
