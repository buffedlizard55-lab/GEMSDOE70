"""Reinterpret archived measurements using the user's literal one-way stop rule.

This is a policy audit, not a new evaluator or a new raster experiment. Frozen
scientific receipts and the shared template are deliberately left unchanged.
"""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def literal_gate(audit):
    rows = audit.get('rows', [])
    witnesses = []
    invalid = []
    for row in rows:
        if not isinstance(row, dict):
            invalid.append(None)
            continue
        rho = row.get('spearman_full_footprint')
        overlap = row.get('my_dots_within_3px_of_theirs')
        submission = row.get('submission')
        if (not isinstance(submission, str) or not submission.strip()
                or type(rho) not in (int, float) or not math.isfinite(rho)
                or not -1 <= rho <= 1 or type(overlap) not in (int, float)
                or not math.isfinite(overlap) or not 0 <= overlap <= 1):
            invalid.append(submission)
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
    result = {
        'hypothesis': 'Protocol audit of the archived coverage-stratified halo candidate; no new experiment',
        'mechanism': 'Sparse coverage avoids redundant truth-cell credit; not proof of geothermal activity',
        'non_fault_mimic': 'Depositional basin margins correlated with mapped-fault habitat',
        'holdout': {'evidence_class': 'HOLDOUT-DTI',
                    'evaluator_version': 'gems57-pooled-hide-v2',
                    **old['instrument_a_holdout']['candidate'],
                    'provenance': 'Archived phase4 instrument A, not rerun this session'},
        'correlation_overlap_vs_registry': gate,
        'surface_check': {
            'status': 'not_run',
            'reason': ('No new candidate surface was generated in this review. The archived final-dot '
                       'witness is a stop condition; no surface pass is claimed.')
        },
        'raster_sha256': sha,
        'validator_output': old['validator_output'],
        'validator_provenance': 'Archived shared-validator receipt; not a new data restoration',
        'submission_name': old['submission_name'],
        'note': 'Archived review only. Literal one-way overlap gate fails; DO NOT SUBMIT. No new candidate generated.',
        'verdict': 'negative', 'download_ok': True,
        'download_for_review_only': bool(gate['stop']),
        'literal_uniqueness_stop': bool(gate['stop']),
        'download_purpose': 'review only' if gate['stop'] else 'candidate file',
        'submit_recommended': False,
        'new_candidate_generated': False, 'experiments_this_session': 0,
        'weekly_slots_used': 0,
        'limitation': 'No single method paragraph assigns this session a lane. Stop on existing duplicate witness; do not invent a new lane.',
        'source_receipt': 'evidence/phase4/uniqueness.json'
    }
    (ROOT / 'evidence/literal_protocol_review.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(gate, indent=2))


if __name__ == '__main__':
    main()
