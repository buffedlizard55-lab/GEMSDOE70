"""Verify saved arithmetic without rerunning/tuning the stopped scientific experiment."""
import json
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]


def test_saved_pooled_scores_match_fold_terms():
    summary=json.loads((ROOT/'evidence/holdout.json').read_text())
    folds=json.loads((ROOT/'evidence/holdout_folds.json').read_text())
    for arm,rows in folds.items():
        score=summary['scores'][arm]
        tp=sum(r['tp'] for r in rows)
        fp=sum(r['fp'] for r in rows)
        fn=sum(r['fn'] for r in rows)
        assert score['dti']==pytest.approx(tp/(tp+.2*fp+.8*fn+1e-12),abs=1e-12)
        assert score['withheld_positive_pixels']==sum(r['n_truth'] for r in rows)
        assert score['withheld_positive_pixels']==11321
        assert len(score['ci95'])==2
        assert 0<=score['ci95'][0]<=score['ci95'][1]<=1
    assert summary['scores']['candidate']['dti']<summary['scores']['random_control']['dti']
    assert summary['paired_differences']['random_control']['ci95'][1]<0


def test_certificate_does_not_claim_complete_registry_clearance():
    audit=json.loads((ROOT/'evidence/surface_uniqueness.json').read_text())
    cert=json.loads((ROOT/'evidence/registry_saturation.json').read_text())
    assert audit['registry_rasters_checked']==1
    assert audit['complete_accessible_scan'] is False
    assert audit['unique'] is False
    assert audit['stop_required']
    assert audit['worst_dot_overlap']==1
    assert cert['universal_overlap_blocker']
    assert cert['uncovered_allowed_pixels']==0
    assert cert['positive_pixels']==5167373


def test_no_historical_projection_is_current_score():
    card=json.loads((ROOT/'evidence/run_card.json').read_text())
    assert card['organizer_confirmed_score'] is None
    audit=json.loads((ROOT/'evidence/h33_audit.json').read_text())
    assert audit['organizer_confirmed_scores'] is None
    assert audit['files']['h33']['positive_pixels']==37654
    assert audit['comparisons']['h27_to_h33']['exactly_old_with_distance_gt_2']
    assert audit['comparisons']['h27_to_h33']['removed']==2545
