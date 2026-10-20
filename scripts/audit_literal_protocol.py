"""Reinterpret archived candidate audits using the user's literal one-way stop rule.

This is a policy/reporting audit, not a model experiment. It checks the historical
Phase-4 artifact and the E3 artifact added by merged PR #17, validates their exact
published TIFF bytes locally, and preserves the distinct scope of each registry receipt.
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
    """Apply only the requested strict thresholds to recorded comparison rows."""
    rows = audit.get('rows', [])
    witnesses = []
    invalid = []
    for row in rows:
        if not isinstance(row, dict):
            invalid.append(None)
            continue
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
    return {
        'rule': 'Spearman > 0.90 OR candidate dots within 3 px > 0.70 (forward-only)',
        'duplicate': bool(witnesses),
        'stop': bool(witnesses) or not complete,
        'complete_accessible_scan': complete,
        'registry_rasters_expected': audit.get('registry_rasters_expected'),
        'registry_rasters_checked': len(rows),
        'invalid_rows': invalid,
        'witnesses': witnesses,
        'scope': audit.get('scope', 'Scope unavailable in archived receipt.'),
        'source_errors': audit.get('source_errors', []),
    }


def _sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def _p4_review():
    audit = json.loads((ROOT / 'evidence/phase4/uniqueness.json').read_text())
    old = json.loads((ROOT / 'evidence/run_card.json').read_text())
    gate = literal_gate(audit)
    artifact = ROOT / old['artifact']
    sha = _sha(artifact)
    if sha != old['raster_sha256'] or sha != audit['candidate_file_sha256']:
        raise ValueError('P4 TIFF and uniqueness receipt are not byte-hash-linked')
    validation = run_validation(artifact)
    if validation.get('local_format_pass') is not True:
        raise ValueError('Archived P4 TIFF failed fresh local byte-level validation')
    holdout_a = {'evidence_class': 'HOLDOUT-DTI',
                 'evaluator_version': 'gems57-pooled-hide-v2',
                 **old['instrument_a_holdout']['candidate'],
                 'provenance': 'Archived phase4 instrument A; not rerun this review'}
    holdout_b_prime = {'evidence_class': 'HOLDOUT-DTI',
                       'evaluator_version': 'gems57-pooled-hide-v2',
                       **old['instrument_b_prime_proxy']['candidate'],
                       'provenance': 'Archived phase4 instrument B-prime proxy; not rerun this review'}
    return {
        'candidate_origin': 'Historical Phase-4 artifact already in the repository',
        'hypothesis': old['hypothesis'],
        'mechanism': old['mechanism'],
        'non_fault_mimic': 'Depositional basin margins correlated with mapped-fault habitat',
        'holdout_dti': {'instrument_a': holdout_a, 'instrument_b_prime': holdout_b_prime},
        'correlation_overlap_vs_registry': gate,
        'preplacement_surface_audit': {
            'status': 'not_recorded_for_phase4_candidate',
            'required_by_prompt': True,
            'cleared': False,
            'note': 'The archived P4 receipt covers final dots; no pre-placement surface receipt was found.'
        },
        'raster_sha256': sha,
        'validator_output': validation['shared_validator'],
        'sample_comparison': validation['sample_comparison'],
        'validator_receipt': validation,
        'validator_provenance': 'Fresh local shared-validator run on archived P4 TIFF bytes; not organizer acceptance',
        'submission_name': old['submission_name'],
        'submission_note': old['submission_note'],
        'submission_note_chars': len(old['submission_note']),
        'verdict': 'negative',
        'download_ok_for_review': True,
        'submit_recommended': False,
        'source_receipts': ['evidence/phase4/uniqueness.json', 'evidence/run_card.json'],
    }


def _e3_review():
    card = json.loads((ROOT / 'evidence/run_card_e3_amended.json').read_text())
    surface = json.loads((ROOT / 'evidence/surface_uniqueness_e3.json').read_text())
    final = json.loads((ROOT / 'evidence/final_uniqueness_e3.json').read_text())
    artifact = ROOT / 'docs/downloads' / f"{card['submission_name']}.tif"
    raster_sha = _sha(artifact)
    if raster_sha != card['raster_sha256']:
        raise ValueError('Merged PR #17 E3 TIFF does not match its amended run-card SHA-256')

    validation = run_validation(artifact)
    if validation.get('local_format_pass') is not True:
        raise ValueError('Merged PR #17 E3 TIFF failed fresh local byte-level validation')
    if validation.get('artifact_sha256') != raster_sha:
        raise ValueError('Fresh E3 validator receipt is not linked to the published TIFF bytes')

    # Hash the decoded float32 values using the same convention as the shared
    # uniqueness tool, so the surface and final-dot measurements are identity-checked.
    import numpy as np
    import rasterio
    with rasterio.open(artifact) as src:
        decoded = src.read(1)
    decoded_sha = hashlib.sha256(np.ascontiguousarray(decoded).tobytes()).hexdigest()
    surface_hash_linked = (
        surface['audit'].get('candidate_decoded_sha256')
        == card.get('surface_decoded_float32_sha256'))
    final_hash_linked = (
        final['audit'].get('candidate_decoded_sha256') == decoded_sha
        and int(final['audit'].get('my_dots', -1)) == int(card['n_final_dots']))
    surface_gate = literal_gate(surface['audit'])
    final_gate = literal_gate(final['audit'])
    # Even a candidate that passes the lane's adjusted release checker cannot
    # override a literal forward-overlap witness in the user's prompt.
    adjusted = {
        'surface_duplicate_adjusted': surface.get('adjusted', {}).get('duplicate_adjusted'),
        'final_duplicate_adjusted': final.get('adjusted', {}).get('duplicate_adjusted'),
        'governs_user_prompt': False,
        'reconciliation': 'Saturation-adjusted/Jaccard exclusions are not a substitute for the prompt\'s one-way >0.70 forward stop.',
    }
    holdout = dict(card['holdout_dti'])
    holdout['provenance'] = 'Merged PR #17 archived E3 seed-40 holdout; not recomputed this review'
    return {
        'candidate_origin': 'Parallel E3 lane from merged PR #17; no experiment run in this review',
        'hypothesis': card['hypothesis'],
        'mechanism': card['mechanism'],
        'non_fault_mimic': card['non_fault_mimic'],
        'holdout_dti': holdout,
        'correlation_overlap_vs_registry': final_gate,
        'preplacement_surface_audit': {
            **surface_gate,
            'receipt': 'evidence/surface_uniqueness_e3.json',
            'decoded_surface_sha256': card['surface_decoded_float32_sha256'],
            'hash_linked_to_receipt': surface_hash_linked,
            'candidate_clear': False,
        },
        'final_dot_audit': {
            **final_gate,
            'receipt': 'evidence/final_uniqueness_e3.json',
            'decoded_tiff_sha256': decoded_sha,
            'hash_linked_to_receipt': final_hash_linked,
            'candidate_clear': False,
        },
        'adjusted_lane_receipts': adjusted,
        'registry_scope': {
            'locally_checked': final['audit'].get('registry_rasters_checked'),
            'local_expected': final['audit'].get('registry_rasters_expected'),
            'complete_accessible_scan': final['audit'].get('complete_accessible_scan'),
            'inherited_inventory_count': 862,
            'full_registry_scan_complete': False,
            'scope_note': final['audit'].get('scope'),
        },
        'raster_sha256': raster_sha,
        'validator_output': validation['shared_validator'],
        'sample_comparison': validation['sample_comparison'],
        'validator_receipt': validation,
        'validator_provenance': 'Fresh local shared-validator run on merged E3 TIFF bytes; not organizer acceptance',
        'submission_name': card['submission_name'],
        'submission_note': card['submission_note'],
        'submission_note_chars': len(card['submission_note']),
        'verdict': 'negative',
        'download_ok_for_review': True,
        'submit_recommended': False,
        'organizer_confirmed_score': None,
        'instrument_b_prime_status': 'not scored in the E3 receipt',
        'parallel_experiment_count': card['experiment_count'],
        'weekly_slots_used': card['weekly_slots_used'],
        'source_receipts': [
            'evidence/run_card_e3_amended.json',
            'evidence/surface_uniqueness_e3.json',
            'evidence/final_uniqueness_e3.json',
            'evidence/validator_e3.json',
        ],
    }


def main():
    p4 = _p4_review()
    e3 = _e3_review()
    result = {
        'evidence_class': 'PROMPT-PROTOCOL-REVIEW',
        'hypothesis': e3['hypothesis'],
        'mechanism': e3['mechanism'],
        'non_fault_mimic': e3['non_fault_mimic'],
        'holdout_dti': e3['holdout_dti'],
        'correlation_overlap_vs_registry': e3['correlation_overlap_vs_registry'],
        'preplacement_surface_audit': e3['preplacement_surface_audit'],
        'final_dot_audit': e3['final_dot_audit'],
        'adjusted_lane_receipts': e3['adjusted_lane_receipts'],
        'registry_scope': e3['registry_scope'],
        'raster_sha256': e3['raster_sha256'],
        'validator_output': e3['validator_output'],
        'sample_comparison': e3['sample_comparison'],
        'validator_receipt': e3['validator_receipt'],
        'validator_provenance': e3['validator_provenance'],
        'submission_name': e3['submission_name'],
        'submission_note': e3['submission_note'],
        'submission_note_chars': e3['submission_note_chars'],
        'verdict': 'negative',
        'download_ok': True,
        'download_ok_for_review': True,
        'submit_recommended': False,
        'submit_ok': False,
        'candidate_origin': e3['candidate_origin'],
        'new_candidate_generated': False,
        'experiments_this_review': 0,
        'parallel_experiment_count': e3['parallel_experiment_count'],
        'weekly_slots_used': e3['weekly_slots_used'],
        'instrument_b_prime_status': e3['instrument_b_prime_status'],
        'organizer_score': None,
        'organizer_score_status': 'NOT-REPORTED; no organizer submission-page receipt is present',
        'previous_p4_review': p4,
        'limitation': 'No single method paragraph assigns this review a lane. E3 is a parallel archived candidate, fails the literal forward stop, and does not authorize another experiment or a weekly slot.',
        'source_receipts': e3['source_receipts'] + p4['source_receipts'],
    }
    (ROOT / 'evidence/literal_protocol_review.json').write_text(json.dumps(result, indent=2) + '\n')
    (ROOT / 'evidence/review-e3-format-validation.json').write_text(
        json.dumps(e3['validator_receipt'], indent=2, allow_nan=False) + '\n')
    (ROOT / 'evidence/review-literal-protocol-format-validation.json').write_text(
        json.dumps(p4['validator_receipt'], indent=2, allow_nan=False) + '\n')
    print(json.dumps({
        'e3_surface_gate': e3['preplacement_surface_audit'],
        'e3_final_dot_gate': e3['correlation_overlap_vs_registry'],
        'p4_final_dot_gate': p4['correlation_overlap_vs_registry'],
        'verdict': result['verdict'],
        'submit_recommended': result['submit_recommended'],
    }, indent=2))


if __name__ == '__main__':
    main()
