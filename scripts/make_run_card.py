#!/usr/bin/env python3
"""Write the evidence-bound NEGATIVE card; never fabricate a scientific result."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def main():
    proof = json.loads((ROOT / 'evidence/preflight.json').read_text())
    if proof['verdict'] != 'negative' or not proof['coverage']['strictly_positive_on_entire_footprint']:
        raise ValueError('negative preflight proof missing')
    card = dict(
        schema_version=1, repository='buffedlizard55-lab/GEMSDOE70', date_utc='2026-10-20',
        hypothesis='No method lane supplied; signed gravity/conductance edge-sidedness is a deferred research proposal only.',
        mechanism='Proposed: persistent side-ordered density/electrical contrasts across a connected edge could indicate a concealed structural boundary. Not implemented or tested.',
        non_fault_mimic='Sedimentary facies contact or intrusive margin without displacement.',
        holdout=dict(evidence_class='HOLDOUT-DTI', status='NOT RUN — mandatory preflight stop',
                     evaluator_version='gems57-pooled-hide-v2 (available, not run on real holdout)',
                     withheld_positives=None, dti=None, ci95=None, current_best_same_evaluator=None),
        leakage_canary=dict(status='NOT RUN — no features fitted or trusted', feature_auc=None),
        registry=dict(evidence_class='REGISTRY-MEASUREMENT',
                      status='UNIVERSAL DUPLICATE OBSTRUCTION; no candidate-specific clearance',
                      spearman=None, candidate_dot_overlap=None,
                      minimum_overlap_for_any_nonempty_in_footprint_candidate=1.0,
                      limit=.70, witness_sha256=proof['witness_sha256'],
                      evidence='evidence/preflight.json',
                      scope='One hash-verified member of an inherited owner registry; not a complete current registry scan.',
                      surface_check='Blocked before surface construction/placement by universal support proof.',
                      final_dot_check='NOT RUN — no final dots created.'),
        raster_sha256=None,
        validator=dict(status='NOT RUN — no submission raster exists', no_nan_inside_footprint=None,
                       values_in_0_1=None, crs_match=None, shape_match=None, transform_match=None,
                       grid_reference_only=dict(crs=proof['crs'], shape=proof['shape'], transform=proof['transform']),
                       organizer_acceptance=False),
        submission_name=None,
        proposed_name_prefix='gems70-signededge (reserved concept, no file)',
        note='NEGATIVE: no TIFF. Lane absent; a dense registry member forces 100% overlap under the literal duplicate rule.',
        download_available=False, approved_for_weekly_slot=False,
        scientific_experiments_run=0, submission_slots_used=0, verdict='negative')
    if len(card['note']) > 140:
        raise ValueError('run-card note too long')
    (ROOT / 'evidence/run_card.json').write_text(json.dumps(card, indent=2, allow_nan=False) + '\n')
    print('Wrote negative run card; no raster or scientific score exists.')


if __name__ == '__main__':
    main()
