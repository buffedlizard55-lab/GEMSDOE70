"""Reinterpret archived measurements using the user's literal one-way stop rule.

This is a policy audit, not a new evaluator or a new raster experiment. Frozen
scientific receipts and the shared template are deliberately left unchanged.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def literal_gate(audit):
    # One policy implementation across the historical and freshly measured audits.
    import sys
    sys.path.insert(0, str(ROOT / 'src'))
    from gems70.protocol import literal_lane_status
    result = literal_lane_status(audit)
    witnesses = [
        {'submission': row['submission'], 'spearman': row['spearman_full_footprint'],
         'forward_overlap': row['my_dots_within_3px_of_theirs']}
        for row in audit.get('rows', []) if isinstance(row, dict)
        and row.get('submission') in result['duplicate_witnesses']]
    return {'rule': 'spearman > 0.90 OR candidate dots within 3 px > 0.70',
            'duplicate': result['stop_required'], 'stop': not result['protocol_unique'],
            'complete_accessible_scan': result['complete_scan'],
            'invalid_rows': result['invalid_rows'], 'witnesses': witnesses,
            'registry_rasters_checked': len(audit.get('rows', []))}


def main():
    audit = json.loads((ROOT / 'evidence/phase4/uniqueness.json').read_text())
    old = json.loads((ROOT / 'evidence/phase4/run_card.json').read_text())
    gate = literal_gate(audit)
    artifact = ROOT / 'docs/downloads' / (old['submission_name'] + '.tif')
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
        'raster_sha256': sha,
        'validator_output': old['validator_output'],
        'validator_provenance': 'Archived shared-validator receipt; not a new data restoration',
        'submission_name': old['submission_name'],
        'note': 'Archived review only. Literal one-way overlap gate fails; DO NOT SUBMIT. No new candidate generated.',
        'verdict': 'negative', 'download_ok': True, 'submit_recommended': False,
        'new_candidate_generated': False, 'experiments_this_session': 0,
        'weekly_slots_used': 0,
        'limitation': 'No single method paragraph assigns this session a lane. Stop on existing duplicate witness; do not invent a new lane.',
        'source_receipt': 'evidence/phase4/uniqueness.json'
    }
    (ROOT / 'evidence/literal_protocol_review.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(gate, indent=2))


if __name__ == '__main__':
    main()
