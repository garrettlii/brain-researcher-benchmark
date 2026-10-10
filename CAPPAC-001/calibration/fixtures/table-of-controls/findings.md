# CAP phase-A PAC reproduction

## Summary
Yeh & Shi (2018) report that delta-alpha/low-beta coupling is strongest in A1 and weakest in A3, and they interpret this as alpha/low-beta activity locking to synchronised high-voltage delta waves.

## Reproduction
| Subtype | n segments | mean MI |
|---|---|---|
| A1 | 3923 | 0.0122 |
| A2 | 1314 | 0.0096 |
| A3 | 1145 | 0.0072 |

## Controls for segment length

| Analysis | A1 - A3 | 95% CI | p |
|---|---|---|---|
| Raw MI | +0.0050 | +0.0040, +0.0061 | 4e-8 |
| First 4 s only | +0.0009 | -0.0007, +0.0024 | 0.25 |
| MI minus surrogate floor | +0.0008 | +0.0002, +0.0014 | 0.01 |

With length controlled, the A1 - A3 difference drops by more than 80%. The paper's reading of the MI ordering as coupling strength is not supported; at most a small difference remains.
