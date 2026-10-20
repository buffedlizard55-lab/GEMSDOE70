# H33: measured geometry, plausible metric benefit, unproven causation

**The reported leaderboard value 0.2778 is a user-supplied historical claim, not HOLDOUT-DTI and not ORGANIZER-CONFIRMED.**
There is no authenticated submission-page receipt for it in this repository. Conflicting leader
values in the retained brief cannot establish the current leader or predict a new score.

## What the archived bytes show

The historical byte audit (`evidence/h33_audit.json`, linked below) reports:

| Archived raster | Binary dots | Relationship |
|---|---:|---|
| D28 | 44,090 | sparse off-catalogue field |
| H27 | 40,199 | D28 with 3,891 dots at 1 pixel from the catalogue removed; no additions |
| H33 B2 | 37,654 | H27 with 2,545 dots at sqrt(2) or 2 pixels removed; no additions |

H33's median catalogue distance is 1,964.69m; 5.77% of its dots lie within 300m of a mapped
trace. This establishes a sparse halo-sampling geometry and exact subset relationships. It does
**not** establish how much of the reported score comes from geometry, geological information or
properties of hidden labels. Calling H33 a newly learned fault detector is unsupported; calling it
necessarily geology-free is also stronger than the lineage audit alone proves.

## Why the geometry could help

For the shared local DTI implementation,
`DTI = T / (T + 0.2*(S-M) + 0.8*(N-T))`.
Here `T` sums distance-weighted truth coverage, `S` is emitted mass, `M` is nearest-truth credit
at prediction cells, and `N` is truth count. The 300m triangular kernel makes concentrated,
redundant predictions potentially less efficient than well-spaced coverage. Deleting dots that
obtain little hidden-truth credit can reduce false-positive cost. These are plausible explanations
for the user-reported changes, **not a controlled causal explanation of the organizer score**.
Sparse spacing alone does not guarantee improvement: dropping a useful dot can reduce recall.

## What the local comparison actually says

Historical **HOLDOUT-DTI**, evaluator `gems57-pooled-hide-v2`, 11,321 withheld catalogue positives:
P4 0.07304, 95% CI [0.06674, 0.07899], versus H33 0.00370, CI [0.00304, 0.00450].
This measures recovery of hidden catalogue segments, not the organizer's newly mapped faults.
A large win here does not imply a leaderboard win.

The separate historical **SGMC PROXY-DTI** B′ comparison uses 59,937 proxy-positive pixels at
least 3 pixels from the catalogue: P4 0.08116, CI [0.07235, 0.09002], versus H33 0.09377,
CI [0.08375, 0.10403]. Paired delta −0.01261, CI [−0.02407, −0.00180]. This proxy is not a
catalogue holdout or an organizer score. Nearby SGMC/QFaults traces can be re-digitizations;
removing a narrow band does not establish independence.

## Can a new method beat the reported 0.2778?

Possibly, but no current result demonstrates it. The deferred supervised residual-ranking lane
could contribute new information beyond emission geometry. It needs nested spatial validation,
feature-alone canaries, a matched current-best baseline, and the literal uniqueness gates first.
The fresh review found that all published TIFFs fail the current prompt's forward-overlap gate;
no new TIFF was generated after that stop. We will not prune, rename or jitter H33 to call it unique.

- [Historical H33 byte audit](downloads/h33_audit.json)
- [Historical HOLDOUT-DTI receipt, including evaluator/count/CI](downloads/instrumentA_holdout.json)
- [Historical B′ proxy receipt](downloads/instrumentB_prime.json)
- [Current literal-protocol audit and proposed research](protocol-review.html)
- [Organizer fault-detection reference](https://github.com/drivendataorg/gems-prize-reference-solution)
