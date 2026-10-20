"""Apply the user's literal lane policy to shared-tool measurements.

This is a decision adapter, not another overlap or correlation implementation.
The shared tool reports forward overlap even when its inherited mutual-overlap
verdict ignores it. A single verified exceedance rejects; an incomplete scan
can never certify uniqueness. Reverse overlap is diagnostic, not an exemption.
"""
from __future__ import annotations

import math

RHO_LIMIT = 0.90
OVERLAP_LIMIT = 0.70


def _number(value):
    return type(value) in (int, float) and math.isfinite(value)


def literal_lane_status(audit):
    if not isinstance(audit, dict):
        audit = {}
    rows = audit.get('rows')
    rows = rows if isinstance(rows, list) else []
    failures, invalid = [], []
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            invalid.append(str(i))
            continue
        name = row.get('submission', str(i))
        forward = row.get('my_dots_within_3px_of_theirs')
        rho = row.get('spearman_full_footprint')
        if (row.get('error') or not _number(forward) or not 0 <= forward <= 1
                or not _number(rho) or not -1 <= rho <= 1):
            invalid.append(name)
        # Still honor a valid positive witness even if another field is missing.
        if ((_number(forward) and forward > OVERLAP_LIMIT)
                or (_number(rho) and rho > RHO_LIMIT)
                or row.get('identical_bytes') is True
                or row.get('identical_decoded_predictions') is True):
            failures.append(name)
    complete = (bool(rows) and audit.get('complete_accessible_scan') is True
                and type(audit.get('registry_rasters_expected')) is int
                and len(rows) == audit['registry_rasters_expected']
                and not invalid and not audit.get('source_errors'))
    return {
        'policy': 'literal-forward-v1',
        'overlap_limit': OVERLAP_LIMIT,
        'rho_limit': RHO_LIMIT,
        'stop_required': bool(failures),
        'protocol_unique': bool(complete and not failures),
        'complete_scan': bool(complete),
        'duplicate_witnesses': failures,
        'invalid_rows': invalid,
        'scope': 'Only the supplied shared-tool measurements; no organizer/private registry claim.',
    }
