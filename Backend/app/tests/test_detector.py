from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import torch
from app.ai.detector import AIImageDetector

@pytest.fixture
def mock_detector_dependencies():
    mock_model = MagicMock()
    mock_model.to.return_value = mock_model

    mock_state_dict = MagicMock()

    with(
        patch(
            "app.ai.detector.TrainedAIImageDetector",
            return_value=mock_model
        ) as mock_model_class,
        patch(
            "app.ai.detector.torch.load",
            return_value={
                "model_state_dict": mock_state_dict
            }
        ) as mock_torch_load
    ):
        yield{
            "model": mock_model,
            "model_class": mock_model_class,
            "torch_load": mock_torch_load,
            "state_dict": mock_state_dict
        }

def test_detector_initialises_model(mock_detector_dependencies) -> None:
    detector = AIImageDetector()

    mock_detector_dependencies["model_class"].assert_called_once_with(
        freeze_features=False,
        use_pretrained_weights=False
    )

    mock_detector_dependencies["model"].load_state_dict.assert_called_once_with(
        mock_detector_dependencies["state_dict"]
    )

    mock_detector_dependencies["model"].to.assert_called_once_with(
        detector.device
    )

    mock_detector_dependencies["model"].eval.assert_called_once()

def test_detector_loads_checkpoint(mock_detector_dependencies) -> None:
    detector = AIImageDetector()

    mock_detector_dependencies["torch_load"].assert_called_once_with(
        Path("app/ai/best_model.pth"),
        map_location=detector.device,
        weights_only=True
    )

@pytest.mark.parametrize(
    ("risk_level", "expected"),
    [
        ("LOW", 1),
        ("MEDIUM", 2),
        ("HIGH", 3)
    ]
)
def test_analyse_image_maps_risk_level(mock_detector_dependencies, risk_level: str, expected: int):
    detector = AIImageDetector()

    prediction_result = {
        "risk_level": risk_level,
        "ai_probability": 80,
        "classification": "Test",
        "reasons": []
    }

    with patch(
        "app.ai.detector.predict_and_explain",
        return_value=prediction_result
    ) as mock_predict:
        result = detector.analyse_image(Path("image.jpg"))

        assert result["risk_level"] == expected
        image_path = Path("image.jpg")
        mock_predict.assert_called_once_with(
            model=detector.model,
            image_path=image_path,
            device=detector.device,
            output_directory=image_path.parent / "outputs"
        )

def test_analyse_image_preserves_other_result_fields(mock_detector_dependencies) -> None:
    detector = AIImageDetector()

    prediction_result = {
        "risk_level": "HIGH",
        "ai_probability": 92.5,
        "confidence_percentage": 92.5,
        "classification": "Likely AI-generated or modified",
        "reasons": [
            {
                "message": "Test reason"
            }
        ]
    }

    image_path = Path("image.jpg")

    with patch(
        "app.ai.detector.predict_and_explain",
        return_value=prediction_result
    ):
        result = detector.analyse_image(image_path)

    assert result["risk_level"] == 3
    assert result["ai_probability"] == 92.5
    assert result["confidence_percentage"] == 92.5
    assert result["classification"] == "Likely AI-generated or modified"
    assert result["reasons"] == [
        {
            "message": "Test reason"
        }
    ]

def test_analyse_image_raises_key_error_for_unknown_risk(mock_detector_dependencies) -> None:
    detector = AIImageDetector()

    prediction_result = {
        "risk_level": "UNKNOWN"
    }

    image_path = Path("image.jpg")

    with patch(
        "app.ai.detector.predict_and_explain",
        return_value=prediction_result
    ):
        with pytest.raises(KeyError):
            detector.analyse_image(image_path)
        