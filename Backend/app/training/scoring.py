from __future__ import annotations

def probability_to_risk_level(probability: float, low_threshold: float = 0.40, high_threshold: float = 0.70) -> str:
    probability = max(0.0, min(1.0, float(probability)))

    if not 0.0 < low_threshold < high_threshold < 1.0:
        raise ValueError("Thresholds must satisfy: 0 < low_threshold < high_threshold < 1")
    
    if probability < low_threshold:
        return "LOW"
    
    if probability < high_threshold:
        return "MEDIUM"

    return "HIGH"

def risk_level_to_classification(risk_level: str) -> str:
    classifications = {
        "LOW": "Likely authentic",
        "MEDIUM": "Inconclusive",
        "HIGH": "Likely AI-generated or modified"
    }

    try:
        return classifications[risk_level.upper()]
    except KeyError as error:
        raise ValueError(f"Unknown risk level: {risk_level}") from error