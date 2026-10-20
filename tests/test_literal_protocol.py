"""The current prompt must not be weakened by historical mutual or saturation gates."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('literal_audit', ROOT / 'scripts/audit_literal_protocol.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
release_spec = importlib.util.spec_from_file_location('review_release_gate', ROOT / 'scripts/release_gate.py')
release_cli = importlib.util.module_from_spec(release_spec)
release_spec.loader.exec_module(release_cli)


def audit(rho=0, overlap=0):
    return {'rows': [{'submission': 'witness.tif', 'spearman_full_footprint': rho,
                      'my_dots_within_3px_of_theirs': overlap}],
            'complete_accessible_scan': True, 'missing_or_invalid': 0,
            'registry_rasters_expected': 1}


def test_thresholds_are_strict_and_forward_only():
    assert not module.literal_gate(audit(.90, .70))['stop']
    assert module.literal_gate(audit(0, .700001))['duplicate']
    assert module.literal_gate(audit(.900001, 0))['duplicate']
    assert not module.literal_gate(audit(-.99, 0))['stop']


def test_fail_closed_for_missing_nonfinite_and_wrong_type():
    assert module.literal_gate({})['stop']
    for value in (None, True, float('nan'), float('inf'), -1, 1.01):
        assert module.literal_gate(audit(overlap=value))['stop']
    incomplete = audit()
    incomplete['registry_rasters_expected'] = 2
    assert module.literal_gate(incomplete)['stop']


def test_current_card_is_negative_and_reviews_merged_e3_candidate():
    card = json.loads((ROOT / 'evidence/literal_protocol_review.json').read_text())
    assert card['verdict'] == 'negative'
    assert card['candidate_origin'].startswith('Parallel E3 lane from merged PR #17')
    assert card['download_ok'] is True
    assert card['download_ok_for_review'] is True
    assert card['submit_recommended'] is False
    assert card['submit_ok'] is False
    assert card['new_candidate_generated'] is False
    assert card['experiments_this_review'] == 0
    assert card['parallel_experiment_count'] == 3
    assert card['weekly_slots_used'] == 0
    assert card['instrument_b_prime_status'] == 'not scored in the E3 receipt'
    assert card['organizer_score'] is None
    assert card['submission_name'] == 'gems70e3-scarpcurv-60k-ex3-20261020-zeros'
    assert card['submission_note_chars'] == len(card['submission_note']) == 107
    assert card['holdout_dti']['evidence_class'] == 'HOLDOUT-DTI'
    assert card['holdout_dti']['evaluator_version'] == 'gems57-pooled-hide-v2'
    assert card['holdout_dti']['withheld_positive_pixels'] == 11437
    assert card['holdout_dti']['ci95'] == [0.07823978274866633, 0.1109296257279242]

    final = card['correlation_overlap_vs_registry']
    assert final['duplicate'] is True and final['stop'] is True
    assert final['complete_accessible_scan'] is False
    assert final['registry_rasters_checked'] == 63
    assert final['registry_rasters_expected'] == 63
    assert len(final['witnesses']) == 5
    assert max(row['forward_overlap'] for row in final['witnesses']) == 1.0
    surface = card['preplacement_surface_audit']
    assert surface['duplicate'] is True and surface['stop'] is True
    assert surface['hash_linked_to_receipt'] is True
    assert card['final_dot_audit']['hash_linked_to_receipt'] is True
    assert card['adjusted_lane_receipts']['governs_user_prompt'] is False
    assert card['registry_scope']['inherited_inventory_count'] == 862
    assert card['registry_scope']['full_registry_scan_complete'] is False

    validator = card['validator_output']
    assert validator['all_checks_passed'] is True
    assert validator['checks']['in_footprint_all_finite'] is True
    assert validator['checks']['in_footprint_range_0_1'] is True
    assert validator['checks']['no_nan_anywhere'] is True
    assert validator['meta']['crs'] == 'EPSG:32611'
    assert validator['meta']['shape'] == [3730, 3292]
    assert validator['meta']['transform'] == [100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0]
    assert card['previous_p4_review']['correlation_overlap_vs_registry']['duplicate'] is True
    assert card['previous_p4_review']['preplacement_surface_audit']['cleared'] is False


def test_generated_pages_show_current_stop():
    for name in ('index.html', 'submission.html', 'results.html', 'protocol-review.html', 'e3-candidate.html'):
        text = (ROOT / 'docs' / name).read_text()
        assert 'DO NOT SUBMIT — literal protocol stop' in text
    assert 'CURRENT REVIEW: DO NOT SUBMIT' in (ROOT / 'README.md').read_text()
    e3_page = (ROOT / 'docs/e3-candidate.html').read_text()
    assert 'Submit: NO under the current literal forward-overlap rule.' in e3_page
    assert 'Surface audit: 5 forward-overlap witnesses.' in e3_page


def test_release_api_and_cli_enforce_current_stop():
    from gems70.release import release_status
    status = release_status(ROOT)
    assert status['submit_recommended'] is False
    assert any('literal one-way' in reason for reason in status['reasons'])
    assert release_cli.status()['status'] == 'REVIEW DOWNLOAD ONLY — DO NOT SUBMIT'
