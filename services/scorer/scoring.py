from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReliabilityInputs:
    freshness: float
    completeness: float
    schema_stability: float
    entity_coverage: float
    revision_rate: float
    drift_anomaly_score: float


WEIGHTS = {
    "freshness": 0.24,
    "completeness": 0.2,
    "schema_stability": 0.16,
    "entity_coverage": 0.14,
    "revision_rate": 0.14,
    "drift_anomaly_score": 0.12,
}


def clamp_score(value: float) -> float:
    return max(0.0, min(100.0, round(value, 2)))


def compute_weighted_trust_score(inputs: ReliabilityInputs) -> float:
    score = (
        inputs.freshness * WEIGHTS["freshness"]
        + inputs.completeness * WEIGHTS["completeness"]
        + inputs.schema_stability * WEIGHTS["schema_stability"]
        + inputs.entity_coverage * WEIGHTS["entity_coverage"]
        + inputs.revision_rate * WEIGHTS["revision_rate"]
        + inputs.drift_anomaly_score * WEIGHTS["drift_anomaly_score"]
    )
    return clamp_score(score)


def classify_status(weighted_trust_score: float) -> str:
    if weighted_trust_score >= 85:
        return "healthy"
    if weighted_trust_score >= 65:
        return "warning"
    return "critical"

