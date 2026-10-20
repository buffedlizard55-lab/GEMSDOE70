# H33: what the archived file shows — and what it cannot prove

> **Current status: DO NOT SUBMIT.** The archived Phase-4 TIFF is review-only because its final-dot
> raster fails the literal one-way registry-overlap rule. This page is a historical analysis, not
> a current method assignment or promotion decision.

## The reported leaderboard value is not verified here

The value **0.2778** was supplied by the user as the historical H33 result. There is no submission-page
receipt for it in this repository, so it is **not ORGANIZER-CONFIRMED**. The other leaderboard values
in the retained prompt conflict and were not freshly fetched from the official competition page in
this sandbox. The [official competition problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
and [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
are provided for manual review. No claim here guarantees that a new method can exceed H33.

## What the archived H33 raster actually is

`evidence/h33_audit.json` records comparisons of the archived raster bytes, not competition scores:

| Archived field | Positive pixels | Measured relation |
|---|---:|---|
| D28 (`dotted-d2-8`) | 44,090 | 300 m Poisson dots, minimum catalogue distance 1 px |
| H27 | 40,199 | the 3,891 D28 dots at 1 px removed |
| H33 B2 | 37,654 | the 2,545 H27 dots at √2 or 2 px removed |

These are counts and set relations, not DTI scores. The byte-level audit indicates H33 is a sparse
sample of the mapped-fault halo with the closest distance shells removed. The artifact itself does
not establish that those dots correspond to undiscovered faults or geothermal vents.

## A plausible metric explanation, not a causal finding

The local evaluator implements a pooled DTI whose true-positive credit saturates per truth cell,
while prediction mass and false-positive penalties depend on emitted dots. Consequently, spreading
fixed prediction mass across distinct truth neighborhoods can outperform crowding many dots into the
same neighborhoods. Removing dots very close to known traces can also reduce wasted prediction mass
when the hidden positives do not follow those traces exactly.

That algebra makes sparse coverage a plausible explanation for why the archived H33 pattern might
score well. It does **not** identify why the organizer returned the user-reported 0.2778: the hidden
labels, a controlled organizer ablation, and the corresponding submission receipt are unavailable.
Other explanations—including label construction, mask rules, and the distribution of hidden traces—
remain possible. The physical interpretation is especially limited: the target is fault detection,
not a verified map of vents, permeability, fluid temperature, or commercial geothermal resources.

The evaluator implementation is local and version-pinned; for source/manual review see the
[organizer reference repository](https://github.com/drivendataorg/gems-prize-reference-solution)
and the competition problem page. Availability of the public reference repository does not prove
that the historical H33 value came from a particular hidden-label mechanism.

## Archived HOLDOUT-DTI evidence — not leaderboard scores

The Phase-4 receipts use evaluator `gems57-pooled-hide-v2`; both entries below are **HOLDOUT-DTI**
from archived internal holdouts, not ORGANIZER-CONFIRMED competition results. Instrument A withholds
catalogue components. Instrument B′ withholds SGMC-derived proxy positives; it is not organizer
hidden truth. Neither result was recomputed in the current review.

- Instrument A candidate: **HOLDOUT-DTI 0.0730**, 95% CI [0.0667, 0.0790], 11,321 withheld catalogue-positive pixels.
- Instrument B′ candidate: **HOLDOUT-DTI 0.0812**, 95% CI [0.0723, 0.0900], 59,937 withheld SGMC-proxy-positive pixels.
- Paired B′ candidate-minus-H33 difference: **HOLDOUT-DTI Δ −0.0126**, 95% CI [−0.0241, −0.0018], 59,937 withheld SGMC-proxy-positive pixels.

The pre-registered proxy comparison was negative. The full receipts, including reference arms and
implementation details, are linked from the [archived results page](results.html). These internal
holdouts neither estimate the organizer score nor authorize a weekly submission slot.

## Current protocol status and next work

The user-specified literal one-way registry rule is controlling for this review. The archived
Phase-4 final dots have four forward-overlap witnesses in the 62-raster accessible inventory, with
maximum overlap 1.00 (**REGISTRY-MEASUREMENT**, not a score). The inventory is not exhaustive. The
prior mutual-overlap clearance is not clearance under the current prompt; no new surface was created,
so no surface-stage pass is claimed. The TIFF is therefore downloadable for review only and must not
be submitted.

Three unvalidated research hypotheses are ranked in the
[current protocol review](protocol-review.html). The top proposal was not tested because the current
stop is active and no single method paragraph assigns a lane. A future experiment requires an
explicit protocol ruling and lane assignment, a restored and hashed feature cache, feature-alone
leakage canaries, whole-segment buffered spatial holdout, surface uniqueness before placement, final
dot uniqueness after placement, and comparison to the current best on the same split. No weekly slot
should be selected before those gates pass.

## Official-source links and limits

- [DrivenData competition problem and rules](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — not freshly fetched in this sandbox.
- [DrivenData leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) — not freshly fetched; no organizer receipt was available.
- [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) — official provenance link for manual review; not newly verified or downloaded here.
- [Organizer reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) — GitHub-hosted reference; its public repository availability is not itself verification of the H33 submission result.
