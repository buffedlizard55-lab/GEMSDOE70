"""Current user policy applied to frozen measurements; not a metric implementation."""
import math


def strict_gate(audit):
    """Fail closed; reapply stated thresholds to recorded raw measurements."""
    audit = audit if isinstance(audit, dict) else {}
    rows = audit.get('rows', [])
    witnesses, errors = [], []
    if not isinstance(rows, list):
        rows = []
        errors.append('Registry rows must be a list')
    if not rows:
        errors.append('No registry rows')
    for row in rows:
        if not isinstance(row, dict):
            errors.append('Registry row must be an object')
            continue
        rho = row.get('spearman_full_footprint')
        overlap = row.get('my_dots_within_3px_of_theirs')
        if (row.get('error') or type(rho) not in (int, float)
                or type(overlap) not in (int, float)
                or not math.isfinite(rho) or not math.isfinite(overlap)
                or not -1 <= rho <= 1 or not 0 <= overlap <= 1):
            errors.append(row.get('submission', 'Malformed registry row'))
            continue
        if rho > .90 or overlap > .70 or row.get('identical_bytes') or row.get('identical_decoded_predictions'):
            witnesses.append({k: row.get(k) for k in (
                'submission', 'sha256', 'spearman_full_footprint',
                'my_dots_within_3px_of_theirs', 'their_dots_within_3px_of_mine')})
    complete = (audit.get('complete_accessible_scan') is True
                and type(audit.get('registry_rasters_expected')) is int
                and audit['registry_rasters_expected'] == len(rows)
                and not audit.get('source_errors') and not errors)
    return {'rule': 'Spearman > 0.90 OR candidate dots within 3px of registry dots > 0.70',
            'policy': 'Forward overlap, not mutual; exact threshold equality does not trigger.',
            'witnesses': witnesses, 'measurement_errors': errors,
            'historical_scan_complete': complete,
            'stop_required': bool(witnesses or not complete),
            'current_registry_clearance': False,
            'scope': 'Frozen historical rows only; not a refreshed all-repository inventory.'}

