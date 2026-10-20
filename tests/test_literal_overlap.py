"""Small-array software tests plus bounds from the saved registry-stop receipt.

These are not new HOLDOUT-DTI experiments and do not certify another TIFF.
The CI script separately recomputes all three archived raster comparisons.
"""
import json
from pathlib import Path
import sys

import numpy as np
import pytest
from gems57 import uniqueness

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from audit_literal_overlap import budget_lower_bound, coverage_stats


def test_forward_criterion_is_not_a_mutual_overlap_criterion():
    old = np.zeros((10, 10), np.float32)
    old[1, 1] = old[1, 8] = old[8, 1] = old[8, 8] = 1
    ours = np.zeros_like(old)
    ours[1, 1] = ours[1, 2] = ours[2, 1] = ours[2, 2] = 1
    forward = uniqueness.dot_overlap(ours, old)
    reverse = uniqueness.dot_overlap(old, ours)
    # Independent tiny-array Euclidean oracle, not the shared dilation routine.
    def brute(mine, theirs):
        my_xy, their_xy = np.argwhere(mine == 1), np.argwhere(theirs == 1)
        return sum(any(np.sum((a - b) ** 2) <= 9 for b in their_xy)
                   for a in my_xy) / len(my_xy)
    assert forward == brute(ours, old) == 1.0 > uniqueness.OVERLAP_LIMIT
    assert reverse == brute(old, ours) == 0.25 < uniqueness.OVERLAP_LIMIT
    assert min(forward, reverse) == 0.25
    # The user's OR-stop fires regardless of a low correlation or reverse.


def test_optimistic_bound_does_not_claim_universal_coverage():
    assert budget_lower_bound(6514, 37654) == pytest.approx(.8270037711796887)
    assert budget_lower_bound(6514, 21713) <= .70
    assert budget_lower_bound(6514, 21714) > .70
    assert budget_lower_bound(6514, 6000) == 0
    with pytest.raises(ValueError):
        budget_lower_bound(-1, 100)
    footprint = np.ones((3, 4), bool)
    cat = np.zeros_like(footprint)
    cat[0, 0] = True
    halo = footprint.copy()
    halo[2, 2] = halo[2, 3] = False
    stats = coverage_stats(halo, footprint, cat, 10)
    assert stats['off_catalogue_cells'] == 11
    assert stats['witness_halo_uncovered_off_catalogue'] == 2
    assert stats['largest_budget_not_ruled_out_by_this_witness_alone'] == 6
    assert stats['min_possible_forward_overlap_at_archived_budget'] == .8


def test_saved_negative_is_specific_to_one_binary_witness_and_archives():
    result = json.loads((ROOT / 'evidence/literal_overlap_stop.json').read_text())
    assert result['witness']['binary_dot_count'] == 206895
    assert result['witness']['dot_rule'] == 'shared binary 1.0 support'
    stats = result['coverage']
    assert stats['witness_halo_uncovered_off_catalogue'] == 6514
    assert stats['off_catalogue_cells'] == 5106385
    assert stats['witness_halo_covered_off_catalogue'] + 6514 == 5106385
    assert stats['witness_halo_fraction_off_catalogue'] < 1
    assert all(r['forward_overlap_within_3px'] == 1.0
               and r['shared_validator']['all_checks_passed']
               for r in result['archive_checks'])
    assert result['new_surface_checked'] is result['new_final_dots_checked'] is False
    assert result['new_raster_generated'] is result['new_holdout_run'] is False
