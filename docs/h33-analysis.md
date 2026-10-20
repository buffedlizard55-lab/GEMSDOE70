# H33: verified archive structure, plausible mechanism, and limits

## What can be established

The historical score **0.2778 is user-reported, not ORGANIZER-CONFIRMED in this repository**. Without a submission-page receipt and hidden labels, we cannot establish that it was the highest score, identify its causal advantage, or guarantee a better score. The prompt supplies several different leaderboard values; they must not be treated as a single current verified benchmark.

The existing [byte-audit receipt](downloads/h33_audit.json) records these archive measurements (not competition scores):

| Archive | Positive pixels | Relation measured in the historical audit |
|---|---:|---|
| D28 | 44,090 | Sparse binary field near mapped faults |
| H27 | 40,199 | D28 with 3,891 dots removed; removed dots were one pixel from catalogue |
| H33 B2 | 37,654 | H27 with 2,545 dots removed; removed distances were square-root-two or two pixels |

No new dots were added by either transition. H33's median catalogue distance was about 1.965 km; only about 5.77% of its dots were within 300 m. These support an emission-geometry interpretation, not evidence that the archive is an independently learned geological detector. This session did not re-download these predecessor rasters; the linked historical receipt supplies pinned source paths and hashes.

## Plausible explanation — not a causal proof

The shared local metric uses a 300 m triangular kernel and `DTI = T / (T + 0.2 FP + 0.8 FN)`. For binary dots, `FP = S − M` and `FN = N − T`, where `T` is the maximum kernel credit summed over truth pixels, `S` is emitted dot count, `M` is nearest-truth credit summed over dots, and `N` is truth count. `T` saturates per truth pixel; adding redundant dots can increase false-positive mass without enough additional truth credit.

Thus a sparse spread can be more efficient than dense overlapping emissions. Removing dots near already mapped traces could help **if** those dots add little credit on additional hidden faults. That conditional mechanism is consistent with the reported archive sequence; it is not verified hidden-label behavior. It does not imply that nearby unmapped faults are absent, or that distance from the catalogue alone is sufficient.

## What the controlled evidence says

The published P4 candidate's historical **HOLDOUT-DTI**, evaluator `gems57-pooled-hide-v2`, is **0.0730423**, 95% spatial-bootstrap CI **[0.0667399, 0.0789950]**, with **11,321 withheld positive pixels**. [Instrument-A receipt](downloads/instrumentA_holdout.json).

The separate off-catalogue SGMC experiment is a **proxy**, not the requested catalogue holdout or an organizer score. Its recorded paired P4-minus-H33 difference has a confidence interval below zero: [target-like proxy receipt](downloads/instrumentB_prime.json). This is evidence against promoting P4 on that pre-registered proxy, not evidence that no possible model can improve.

Catalogue recovery and independent-fault discovery need not reward the same method. A model beating H33 on a catalogue holdout alone therefore does not establish a leaderboard improvement. Likewise, an SGMC compilation can share traces and mapping biases with the visible catalogue. Neither instrument is hidden competition truth.

## Can we beat the reported score?

Possibly, but the evidence here does not demonstrate it. Better within-halo information is a testable direction, not the only possible route or a quantified score forecast. The [current review](protocol-review.html) ranks four conditional hypotheses and specifies buffered validation, leakage canaries, paired comparisons and the separate selector step.

**Current result: negative; do not submit.** The archived P4 final-dot evidence fails the user's forward-overlap stop rule. This run stops without generating a replacement TIFF or spending a slot. Pruning, jittering or renaming H33 is not a new scientific method and is not used here.
