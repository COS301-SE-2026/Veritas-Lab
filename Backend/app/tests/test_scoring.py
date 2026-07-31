import pytest
from app.training.scoring import probability_to_risk_level, risk_level_to_classification

@pytest.mark.parametrize(
    ("probability", "expected_risk"),
    [
        (0.00, "LOW"),
        (0.10, "LOW"),
        (0.39, "LOW"),
        (0.40, "MEDIUM"),
        (0.50, "MEDIUM"),
        (0.69, "MEDIUM"),
        (0.70, "HIGH"),
        (0.90, "HIGH"),
        (1.00, "HIGH")
    ]
)
def test_probability_to_risk_level(probability: float, expected_risk: str) -> None:
    result = probability_to_risk_level(probability)

    assert result == expected_risk

def test_probability_below_zero_is_clamped() -> None:
    result = probability_to_risk_level(-0.5)
    assert result == "LOW"

def test_probability_above_one_is_clamped() -> None:
    result = probability_to_risk_level(1.5)
    assert result == "HIGH"

@pytest.mark.parametrize(
    ("probability", "expected_risk"),
    [
        (0.19, "LOW"),
        (0.20, "MEDIUM"),
        (0.79, "MEDIUM"),
        (0.80, "HIGH")
    ]
)
def test_probability_to_risk_level_uses_custom_thresholds(probability: float, expected_risk: str) ->None:
    result = probability_to_risk_level(probability=probability, low_threshold=0.2, high_threshold=0.8)

    assert result == expected_risk

@pytest.mark.parametrize(
    ("low_threshold", "high_threshold"),
    [
        (0.0, 0.70),
        (-0.1, 0.70),
        (0.40, 1.0),
        (0.40, 1.1),
        (0.70, 0.40),
        (0.50, 0.50)
    ]
)
def test_probability_to_risk_level_rejects_invalid_thresholds(low_threshold: float, high_threshold: float) -> None:
    with pytest.raises(
        ValueError,
        match="Thresholds must satisfy"
    ):
        probability_to_risk_level(
            probability=0.5, 
            low_threshold=low_threshold, 
            high_threshold=high_threshold
        )

@pytest.mark.parametrize(
    ("risk_level", "expected_classification"),
    [
        ("LOW", "Likely authentic"),
        ("MEDIUM", "Inconclusive"),
        ("HIGH", "Likely AI-generated or modified")
    ]
)
def test_risk_level_to_classification(risk_level: str, expected_classification: str) -> None:
    result = risk_level_to_classification(risk_level)

    assert result == expected_classification

@pytest.mark.parametrize(
    ("risk_level", "expected_classification"),
    [
        ("low", "Likely authentic"),
        ("medium", "Inconclusive"),
        ("high", "Likely AI-generated or modified"),
        ("Low", "Likely authentic"),
        ("Medium", "Inconclusive"),
        ("High", "Likely AI-generated or modified")
    ]
)
def test_test_risk_level_to_classification_is_case_insensitive(risk_level: str, expected_classification: str) -> None:
    result = risk_level_to_classification(risk_level)
    assert result == expected_classification

@pytest.mark.parametrize(
    "risk_level",
    [
        "",
        "UNKNOWN",
        "CRITICAL",
        "AUTHENTIC"
    ]
)
def test_risk_level_to_classification_rejects_unknown_level(risk_level: str) -> None:
    with pytest.raises(
        ValueError,
        match=f"Unknown risk level: {risk_level}"
    ):
        risk_level_to_classification(risk_level)