# Official-source reading log — 2026-10-20 UTC

These are manually transcribed excerpts returned by the research-page tool, not
raw archived HTML or authenticated competition-account receipts. Source changes
may occur. None establishes a score for a specific GEMSDOE artifact.

## DrivenData problem description
https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
Both returned chunks were read.

> For this challenge, your task is to develop models and algorithms that provide accurate information about the presence of structures that are indicative of geothermal resources—namely, geological faults.

> For this competition, we set α=0.2 and β=0.8

> For this challenge, you will submit a GeoTIFF raster with fault predictions represented as pixel-wise probabilities or confidence scores between 0 and 1.

The triangular kernel has 300 m support. The submission-format section specifies
single-layer float32, EPSG:32611, 100 m, matching bounds, and null or NaN outside
the bounds. The official page does not establish that NaNs caused the user's
reported portal error. A numeric sentinel outside [0,1] would violate range;
that general observation is not a diagnosis of the unavailable rejected file.

## Official September 2026 rules PDF
https://docs.nlr.gov/docs/fy26osti/96647.pdf
Read returned chunks 0, 2 and 3 (not the full PDF). Sections 3.1–3.6 contain the
relevant entry/submission/testing requirements. These are the cited excerpts:

> You must submit a single GeoTIFF with a single raster layer at 100-meter resolution containing your model’s predictions of fault locations for the entirety of the GeoDAWN study area.

> You can make multiple submissions, subject to the limits specified on the competition website (three submissions per week).

The rules require generative-AI-use disclosure in the narrative when applicable,
reproducible code and documentation from finalists, and a single final selection
for both prize rounds. The authenticated page's *remaining* weekly quota was not
accessible or checked. The published limit is not an authorization to use a slot.

## DrivenData public leaderboard
https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
Read returned chunk 0. PUBLIC-LEADERBOARD-OBSERVATION, NOT A SUBMISSION RECEIPT:
the first displayed row was xiaofanhu with displayed value "0.4413". This resolves
which of the brief's conflicting historical targets matched the page when read.
It does not identify a score for the H33 TIFF. The protocol's strict
ORGANIZER-CONFIRMED class requires a submission-page receipt, which is absent.

## USGS GeoDAWN
https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
Read chunk 0 (data description, processing, citation, rights). Page links data
release DOI 10.5066/P93LGLVQ, documents variable terrain clearance and survey-block
acquisition/processing, and marks this work CC0. A readable release description
is not a completed binary download.

## INGENIOUS project and GDR
https://gbcge.org/current-projects/ingenious/
https://gdr.openei.org/submissions/1391
Read chunk 0 from each. GDR describes the regional data compilation and links
resources including shallow temperature probes, paleogeothermal features,
conductance, geodetics, gravity/magnetics, fault traces, and spring/well chemistry.
The GDR landing page labels its collection publicly accessible with CC-BY 4.0.
Layer-specific licensing, binary checksums, datum conversion and coverage remain
to be checked before use.

## DrivenData rules landing page
https://www.drivendata.org/competitions/306/competition-doe-gems/rules/
Returned one short page linking to the official rules resource at
https://www.herox.com/GEMSPrize/resource/2274 . No account access was inferred.
