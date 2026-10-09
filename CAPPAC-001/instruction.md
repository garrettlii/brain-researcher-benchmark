# Reproducing phase–amplitude coupling across CAP phase-A subtypes (CAPPAC-001)

## Scientific context

The cyclic alternating pattern (CAP) is the periodic EEG activity of NREM sleep. Phases of
transient activation (phase A, 2–60 s) alternate with returns to background (phase B). Phase A
is classified into one of three subtypes:
- **A1:** mostly synchronised high-voltage slow waves, such as K-complex sequences and delta
  bursts.
- **A3:** mostly low-voltage fast rhythms.
- **A2:** a mixture of the two.

Yeh & Shi 2018 (*Sci Rep* 8:3049, doi:10.1038/s41598-018-21013-9) studied the PhysioNet CAP
Sleep Database. Within each phase-A segment they measured phase–amplitude coupling between the
phase of δ activity (0.25–2.5 Hz) and the amplitude of α/low-β activity (10–17 Hz), using
Tort's modulation index (MI). They analysed only segments in which the δ activity completed
more than two cycles.

**Result in the 16 healthy controls:**
- MI was highest in A1 and lowest in A3 (A1 > A2 > A3).
- The subtype effect was significant at p < 0.0001.
- Mean MI in their Fig. 3a was about 0.012 (A1), 0.010 (A2) and 0.0065 (A3).
- The authors conclude that δ–α/low-β coupling is strongest in A1, where α/low-β activity
  locks to synchronised high-voltage δ waves, and weakest in A3.
- They propose this coupling as a marker of sleep microstructure.

## Task

Using the 16 healthy-control recordings of the CAP Sleep Database (`n1`–`n16`), staged
read-only under `/app/data/capslpdb`, **reproduce this result and report whether it holds on
these data.**

The staged files are listed with their sha256 in `/app/source_manifest.json`:

- `nN.edf`: the overnight polysomnogram (EDF).
  - Sampling rates differ between recordings (100–512 Hz).
  - In some files the rate also differs between channels.
- `nN.txt`: the RemLogic event export.
  - After a short preamble, the line beginning `Sleep Stage` is a tab-separated header:
    `Sleep Stage`, sometimes `Position`, `Time [hh:mm:ss]`, `Event`, `Duration[s]`, `Location`.
  - Each following line is one event.
  - Sleep stages are given for 30 s epochs (`W`, `S1`–`S4`, `R`, `MT` for movement time).
  - CAP phase-A events are `MCAP-A1`, `MCAP-A2` and `MCAP-A3`. Their `Sleep Stage` field gives
    the stage in which they occur.

Use the staged data only. The analysis, as pinned for this reproduction:

1. **Channel.** Use C4-A1, labelled `C4-A1` or `C4A1`. Recordings n6–n9 have no C4-A1; use
   C3-A2 for them. Read each channel at its own sampling rate.
2. **Events.** Onset is the event's clock time minus the recording start time in the EDF header,
   modulo 24 h.
   - Use every `MCAP-A1`, `MCAP-A2` and `MCAP-A3` event at any sleep stage.
   - Exclude events that fall in, or overlap, an `MT` epoch.
   - Exclude events that extend beyond the recording.
3. **Signals.** Band-pass the whole-night signal twice with a zero-phase 4th-order Butterworth
   filter (`scipy.signal.butter(4, band, btype="band", fs=fs, output="sos")` with `sosfiltfilt`):
   - 0.25–2.5 Hz (δ);
   - 10–17 Hz (α/low-β).

   Take the Hilbert transform of each whole-night band: the δ phase is its angle and the
   α/low-β amplitude is its modulus. Cut the phase-A segments out of these series.
4. **Inclusion.** As in the paper, analyse a segment only if its unwrapped δ phase advances by
   more than two full cycles (more than 4π) from its first to its last sample.
5. **MI.** For each segment:
   - assign every sample to one of 20 equal δ-phase bins over [−π, π);
   - average the α/low-β amplitude within each bin;
   - divide the 20 bin averages by their sum to obtain P;
   - compute MI = (ln 20 − H(P)) / ln 20, where H(P) = −Σ P ln P.
6. **Statistics.** Average MI per subject and subtype. A subject enters a comparison if it has
   at least 5 analysed segments of each of the two subtypes.
   - Compare subtypes with paired t-tests across subjects: A1 − A3 (primary), A1 − A2 and
     A2 − A3.
   - Report the mean difference, its 95% confidence interval, t and p.

Anything the analysis leaves open should follow common practice in sleep EEG and
phase–amplitude coupling work. The image has `numpy`, `scipy` and `pandas`.

Report, in plain terms, **whether these data show the paper's subtype ordering and support its
conclusion that δ–α/low-β coupling is strongest in A1 and weakest in A3**, stating only what
your analysis actually supports.

## Output Location

Write all outputs to `${OUTPUT_DIR}` (default `/app/output`).

## Required Outputs

- `subject_mi.csv`: one row for each subject and subtype:
  `subject, channel, subtype, n_segments, mean_mi`.
- `subtype_effects.json`: `n_subjects`, the mean MI of each subtype over subjects, and
  `{"A1-A3": {"difference": ..., "ci_low": ..., "ci_high": ..., "t": ..., "p": ...}, "A1-A2": {...}, "A2-A3": {...}}`.
- `run_metadata.json`: the dataset id, the channel and sampling rate used for each recording,
  the number of phase-A events found, excluded (by reason) and analysed for each subtype, the
  analysis settings, and library versions.
- `findings.md`: a short written summary stating whether the paper's subtype ordering and its
  conclusion hold on these data. State only what your analysis actually supports. If
  `findings.md` relies on further analyses, save their numbers as additional files in
  `${OUTPUT_DIR}`.

## Failure handling

If the staged data cannot be read, exit non-zero with `failed_precondition` and a non-empty
reason, and still write parseable `run_metadata.json`, `subtype_effects.json`, and `findings.md`.
