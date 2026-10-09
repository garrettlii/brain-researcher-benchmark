# Source notice: ds002778

**Dataset:** UC San Diego Resting State EEG Data from Patients with Parkinson's Disease,
OpenNeuro ds002778 (doi:10.18112/openneuro.ds002778.v1.0.4). Curated by Alexander P.
Rockhill; data collected by Nicko Jackson, Jobi George, Adam Aron and Nicole C. Swann.
**License:** CC0 (from `dataset_description.json`).

**What is staged:** 98 files (382,438,767 bytes), listed with size and sha256 in
`source_manifest.json`. They are the dataset-level `README`, `CHANGES`,
`dataset_description.json`, `participants.tsv` and `participants.json`, plus the BDF
recording, `_eeg.json` and `_channels.tsv` for the 16 control sessions (`ses-hc`) and
the 15 off-medication sessions (`ses-off`). The on-medication sessions are not staged.
Files are taken unchanged from the public bucket `s3://openneuro.org/ds002778/` at image
build time (captured 2026-10-08, version 1.0.4). Versions 1.0.2–1.0.4 differ only in
README and citation text, and the build fails if any byte differs from the manifest.

**Use conditions stated by the curators (README):** they ask users to cite the dataset
papers (Jackson et al. 2019, eNeuro; Swann et al. 2015, Ann Neurol; George et al. 2013,
NeuroImage Clin), and to email the curator before submitting a manuscript that uses the
data. Those are requests, not access conditions. This task produces no manuscript.

**Paper:** Aljalal M, Aldosari SA, Molinas M, AlSharabi K, Alturki FA (2022). Detection
of Parkinson's disease from EEG signals using discrete wavelet transform, different
entropy measures, and machine learning techniques. Scientific Reports 12:22547.
doi:10.1038/s41598-022-26644-7. The paper's text is not redistributed here.
