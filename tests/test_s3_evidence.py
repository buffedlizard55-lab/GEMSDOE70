"""Session-3 evidence must stay internally consistent and never read as a submit approval."""
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
E1 = json.loads((ROOT / 'evidence/s3/run_card.json').read_text())
E1RAW = json.loads((ROOT / 'evidence/s3/run_card_raw.json').read_text())
E2 = json.loads((ROOT / 'evidence/s3/e2/run_card.json').read_text())
CAL = json.loads((ROOT / 'evidence/s3/proxy_calibration.json').read_text())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def test_no_session3_file_is_a_submit_approval():
    for card in (E1, E2):
        assert card['verdict'] == 'negative'
        assert card['submit_recommended'] is False and card['download_and_submit_ok'] is False
        assert card['download_ok'] is True
        assert 'DO-NOT-SUBMIT' in card['artifact'] and 'DO-NOT-SUBMIT' in card['submission_name']
        assert card['organizer_confirmed_score'] is None and card['weekly_slots_used'] == 0
        assert len(card['submission_note']) <= 140


def test_veto_is_recorded_and_raw_card_preserved():
    assert E1RAW['verdict'] == 'promote'
    assert E1['preregistered_rule_verdict'] == 'promote'
    assert E1['post_hoc_veto']['applied'] is True
    assert CAL['spearman_live_vs_b_prime'] < 0.3 and CAL['n'] == 18


def test_artifacts_match_cards_and_are_valid_binary_rasters():
    for card in (E1, E2):
        path = ROOT / card['artifact']
        assert sha(path) == card['raster_sha256']
        with rasterio.open(path) as src:
            a = src.read(1)
            assert src.count == 1 and src.dtypes[0] == 'float32'
            assert (src.height, src.width) == (3730, 3292) and str(src.crs) == 'EPSG:32611'
            assert tuple(src.transform)[:6] == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
        assert np.isfinite(a).all() and set(np.unique(a)).issubset({0.0, 1.0})
        assert int((a > 0).sum()) == 37654


def test_gates_follow_the_recorded_numbers():
    d = E1['paired_b_prime']['h33_reference']
    assert d['delta'] > 0 and d['ci95'][0] > 0          # E1 passed its frozen proxy gate
    r = E2['paired_b_prime']['random_stratified']
    h = E2['paired_b_prime']['h33_reference']
    assert r['ci95'][0] <= 0 and h['ci95'][0] <= 0       # E2 failed both
    assert E2['gates']['b_prime_beats_h33'] is False
    assert E2['gates']['b_prime_beats_random_stratified'] is False


def test_uniqueness_against_registry():
    for card in (E1, E2):
        u = card['correlation_overlap_vs_registry']
        assert u['final_rasters_checked'] == 62 and u['duplicate'] is False
        assert u['final_worst_mutual_overlap'] <= 0.70
        assert u['final_worst_spearman'] <= 0.90 and u['surface_worst_spearman'] <= 0.90


def test_method_hashes_are_reproducible():
    b = (ROOT / 'src/gems70/supervised.py').read_bytes()
    prefix = b[:b.index(b'\n\n# ----------------------------- S3-E2: marginal-matched placement')]
    assert hashlib.sha256(prefix).hexdigest() == E1RAW['method_source_sha256']['src/gems70/supervised.py']
    assert sha(ROOT / 'scripts/run_experiment_s3.py') == E1RAW['method_source_sha256']['scripts/run_experiment_s3.py']
    for rel, h in E2['method_source_sha256'].items():
        assert sha(ROOT / rel) == h


def test_preregistrations_exist_and_canaries_clear():
    assert (ROOT / 'docs/preregistration-s3.md').is_file()
    assert (ROOT / 'docs/preregistration-s3-e2.md').is_file()
    can = json.loads((ROOT / 'evidence/s3/canaries.json').read_text())
    assert can['alarms'] == [] and all(v['strength'] <= 0.90 for v in can['features'].values())
