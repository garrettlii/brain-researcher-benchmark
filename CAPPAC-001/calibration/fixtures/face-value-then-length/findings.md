# CAP phase-A PAC reproduction

## Summary
Yeh & Shi (2018) report that delta-alpha/low-beta coupling is strongest in A1 and weakest in A3, and they interpret this as alpha/low-beta activity locking to synchronised high-voltage delta waves.

## Reproduction
| Subtype | n segments | mean MI |
|---|---|---|
| A1 | 3923 | 0.0122 |
| A2 | 1314 | 0.0096 |
| A3 | 1145 | 0.0072 |

The ordering A1 > A2 > A3 reproduces (A1 - A3 = +0.0050, 95% CI +0.0040 to +0.0061, t15 = 10.2, p = 4e-8), consistent with the paper's conclusion at face value.

## Segment length
Tort's MI has a positive bias for short data. A1 segments average 6.0 s and A3 13.2 s. I recomputed MI on the first 4 s of every segment: A1 - A3 = +0.0009 (95% CI -0.0007 to +0.0024, p = 0.25), 17% of the raw difference. Subtracting each segment's circular-shift surrogate mean gives +0.0008 (p = 0.01).

## Conclusion
The MI ordering reproduces but is mostly a segment-length effect; above the floor only a small A1 > A3 difference remains. Raw MI should not be read as coupling strength.
