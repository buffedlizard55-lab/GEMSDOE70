"""Reinterpret archived measurements using the user's literal one-way stop rule.

This is a policy audit, not a new evaluator or a new raster experiment. Frozen
scientific receipts and the shared template are deliberately left unchanged.
"""
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_submission import run_validation


def literal_gate(audit):
    rows = audit.get('rows', [])
    witnesses = []
    invalid = []
    for row in rows:
        rho = row.get('spearman_full_footprint')
        overlap = row.get('my_dots_within_3px_of_theirs')
        if (type(rho) not in (int, float) or not math.isfinite(rho)
                or not -1 <= rho <= 1 or type(overlap) not in (int, float)
                or not math.isfinite(overlap) or not 0 <= overlap <= 1):
            invalid.append(row.get('submission'))
            continue
        if rho > .90 or overlap > .70:
            witnesses.append({'submission': row['submission'],
                              'spearman': rho, 'forward_overlap': overlap})
    complete = (audit.get('complete_accessible_scan') is True
                and audit.get('missing_or_invalid') == 0
                and len(rows) == audit.get('registry_rasters_expected')
                and len(rows) > 0 and not invalid)
    return {'rule': 'spearman > 0.90 OR candidate dots within 3 px > 0.70',
            'duplicate': bool(witnesses), 'stop': bool(witnesses) or not complete,
            'complete_accessible_scan': complete, 'invalid_rows': invalid,
            'witnesses': witnesses, 'registry_rasters_checked': len(rows)}


def main():
    audit = json.loads((ROOT / 'evidence/phase4/uniqueness.json').read_text())
    old = json.loads((ROOT / 'evidence/run_card.json').read_text())
    gate = literal_gate(audit)
    artifact = ROOT / old['artifact']
    sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
    if sha != old['raster_sha256'] or sha != audit['candidate_file_sha256']:
        raise ValueError('Archived candidate and uniqueness receipt are not hash-linked')
    validation = run_validation(artifact)
    if validation.get('local_format_pass') is not True:
        raise ValueError('Archived TIFF failed fresh local byte-level validation')
    holdout_a = {'evidence_class': 'HOLDOUT-DTI',
                 'evaluator_version': 'gems57-pooled-hide-v2',
                 **old['instrument_a_holdout']['candidate'],
                 'provenance': 'Archived phase4 instrument A; not rerun this session'}
    holdout_b_prime = {'evidence_class': 'HOLDOUT-DTI',
                       'evaluator_version': 'gems57-pooled-hide-v2',
                       **old['instrument_b_prime_proxy']['candidate'],
                       'provenance': 'Archived phase4 instrument B-prime proxy; not rerun this session'}
    submission_note = old['submission_note']
    result = {
        'evidence_class': 'PROMPT-PROTOCOL-REVIEW',
        'hypothesis': 'Protocol audit of the archived coverage-stratified halo candidate; no new experiment',
        'mechanism': 'Sparse coverage may reduce redundant truth-cell credit; this is not proof of geothermal activity',
        'non_fault_mimic': 'Depositional basin margins correlated with mapped-fault habitat',
        'holdout_dti': {'instrument_a': holdout_a, 'instrument_b_prime': holdout_b_prime},
        'correlation_overlap_vs_registry': gate,
        'preplacement_surface_audit': {
            'status': 'not_recorded_for_phase4_candidate',
            'required_by_prompt': True,
            'cleared': False,
            'note': 'The archived P4 audit covers final dots; no pre-placement surface receipt was found.'
        },
        'raster_sha256': sha,
        'validator_output': validation['shared_validator'],
        'sample_comparison': validation['sample_comparison'],
        'validator_provenance': 'Fresh local shared-validator run on archived TIFF bytes during this review; not organizer acceptance',
        'submission_name': old['submission_name'],
        'submission_note': submission_note,
        'submission_note_chars': len(submission_note),
        'review_note': 'Archived review only. Literal one-way overlap gate fails; DO NOT SUBMIT. No new candidate generated.',
        'verdict': 'negative', 'download_ok': True, 'download_ok_for_review': True,
        'submit_recommended': False, 'submit_ok': False,
        'new_candidate_generated': False, 'experiments_this_session': 0,
        'weekly_slots_used': 0,
        'limitation': 'No single method paragraph assigns this session a lane. Stop on existing duplicate witness; do not invent a new lane.',
        'source_receipt': 'evidence/phase4/uniqueness.json'
    }
    (ROOT / 'evidence/literal_protocol_review.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(gate, indent=2))


if __name__ == '__main__':
    main()
