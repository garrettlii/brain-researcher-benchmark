# CAPPAC-001: delta-alpha/low-beta coupling across CAP phase-A subtypes

## The result at face value
With the paper's estimator on its own healthy recordings (n = 16; 3923 A1,
1314 A2 and 1145 A3 segments), subject-mean MI is A1 0.0122,
A2 0.0096 and A3 0.0072, close to the paper's Fig. 3a. A1 - A3 = +0.00503 [+0.00398, +0.00609]
(paired t15 = 10.16, p = 4e-08, d_z = 2.54); A1 - A2 and A2 - A3 are also positive
(p = 0.00083 and 0.0005). The ordering A1 > A2 > A3 reproduces.

## How much of the MI is coupling?
Tort's MI is positive even without coupling, and that floor is larger for shorter segments. The
authors knew phase-A durations differ and analysed only segments with more than two delta cycles,
partly to limit this. After that rule the subtypes still differ two-fold in length: A1 segments last
6.0 s on average and A3 segments 13.2 s (paired difference -7.2 s, shorter in every subject).
Within every subtype, MI rises with 1/duration (slopes +0.053, +0.054, +0.038; all p < .001).

- No-coupling floor (MI after circularly shifting the amplitude inside each segment, 50 shifts): A1
  0.0113, A2 0.0091, A3 0.0071, i.e. 93%, 95%, 99% of the mean MI. Its A1 - A3
  difference is +0.00422 [+0.00328, +0.00517], 84% of the raw difference.
- MI minus each segment's floor: A1 0.00091, A2 0.00050, A3 0.00010.
  A1 - A3 = +0.00081 [+0.00022, +0.00139], p = 0.0099, 16% of the raw difference;
  A1 - A2 (p = 0.087) and A2 - A3 (p = 0.066) are not significant.
- MI on the first 4 s of every segment (the same length for every subtype): A1 - A3 = +0.00088
  [-0.00068, +0.00243], p = 0.25, 17% of the raw difference. This is about the same size as the
  floor-subtracted difference, estimated less precisely.

## Conclusion
The paper's MI values and their ordering reproduce, but raw MI here is mostly the estimator's
length-dependent floor: the two-cycle rule leaves A1 segments half as long as A3 segments, and the
floor alone gives 84% of the A1 - A3 difference. Above the floor a small A1 > A2 > A3 ordering
remains, about 16% of the raw difference (significant only for A1 - A3 after floor subtraction;
the equal-length estimate is the same size but imprecise). Raw MI therefore overstates the subtype
difference about 6-fold and cannot be read as coupling strength. These data are consistent with
slightly stronger coupling in A1 than in A3, but not with the paper's reading of the MI differences
as a substantial difference in coupling strength between subtypes.
