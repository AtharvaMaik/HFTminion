from services.scorer.scoring import ReliabilityInputs, classify_status, compute_weighted_trust_score


def test_weighted_trust_score_prefers_strong_operating_feed():
    score = compute_weighted_trust_score(
        ReliabilityInputs(
            freshness=96,
            completeness=95,
            schema_stability=90,
            entity_coverage=91,
            revision_rate=87,
            drift_anomaly_score=92,
        )
    )
    assert score == 92.4
    assert classify_status(score) == "healthy"


def test_weighted_trust_score_flags_degraded_feed():
    score = compute_weighted_trust_score(
        ReliabilityInputs(
            freshness=38,
            completeness=59,
            schema_stability=52,
            entity_coverage=47,
            revision_rate=41,
            drift_anomaly_score=44,
        )
    )
    assert score == 46.84
    assert classify_status(score) == "critical"
