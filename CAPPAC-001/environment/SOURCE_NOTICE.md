# Source notice: PhysioNet CAP Sleep Database 1.0.0

**Dataset:** the CAP Sleep Database (Terzano MG et al. 2001, *Sleep Med* 3:187-199,
doi:10.1016/S1389-9457(01)00149-6), distributed by PhysioNet (Goldberger AL et al. 2000,
*Circulation* 101:e215-e220) at https://physionet.org/content/capslpdb/1.0.0/ and its public
AWS mirror `https://physionet-open.s3.amazonaws.com/capslpdb/1.0.0/`.
**License:** Open Data Commons Attribution License v1.0. Please cite Terzano et al. 2001 and
Goldberger et al. 2000 when using the data.

**What is staged:** 32 files (3,816,746,073 bytes), listed with size and sha256 in
`source_manifest.json`. The sha256 values are those in the release's `SHA256SUMS.txt`. The files
are the overnight recordings `nN.edf` and RemLogic event exports `nN.txt` of the 16 healthy
controls n1-n16. They are downloaded unchanged at image build time (captured 2026-10-09), and the
build fails if any byte differs. No recordings of the patient groups are staged.

**Paper:** Yeh C-H, Shi W (2018). Identifying phase-amplitude coupling in cyclic alternating
pattern using masking signals. *Sci Rep* 8:3049. doi:10.1038/s41598-018-21013-9 (CC BY 4.0).
The paper's text is not redistributed here.
