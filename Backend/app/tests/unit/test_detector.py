from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch 

import pytest
import torch
from app.ai.detector import AIImageDetector
from app.ai.detector import AIVideoDetector

@pytest.fixture
def mock_video_detector_dependencies():
    mock_analysis_model = MagicMock()
    mock_analysis_model.analyse = AsyncMock()

    with patch(
        "app.ai.detector.video_combined_analysis",
        return_value=mock_analysis_model
    ) as mock_analysis_class:
        yield {
            "model": mock_analysis_model,
            "model_class": mock_analysis_class
        }

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

def test_video_detector_initialises_model(mock_video_detector_dependencies) -> None:
    detector = AIVideoDetector()

    mock_video_detector_dependencies["model_class"].assert_called_once_with()
    assert detector.model is mock_video_detector_dependencies["model"]

@pytest.mark.asyncio
async def test_analyze_video_converts_to_path_object(mock_video_detector_dependencies) -> None:
    detector = AIVideoDetector()

    mock_video_detector_dependencies["model"].analyse.return_value = {
        "prediction": "AI-generated",
        "ai_probability": 0.9,
        "authentic_probability": 0.1
    }

    await detector.analyse_video("video.mp4")

    mock_video_detector_dependencies["model"].analyse.assert_called_once_with(
        Path("video.mp4")
    )

@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("prediction", "ai_probability", "authentic_probability", "expected_risk_level"),
    [
        ("AI-generated", 0.85, 0.15, 3),
        ("AI-generated", 0.65, 0.35, 2),
        ("AI-generated", 0.40, 0.60, 1),
        ("Authentic", 0.15, 0.85, 3),
        ("Authentic", 0.35, 0.65, 2),
        ("Authentic", 0.45, 0.55, 1)
    ]
)
async def test_analyse_video_maps_risk_level(
    mock_video_detector_dependencies,
    prediction: str,
    ai_probability: float,
    authentic_probability: float,
    expected_risk_level: int
) -> None:
    detector = AIVideoDetector()

    mock_video_detector_dependencies["model"].analyse.return_value = {
        "prediction": prediction,
        "ai_probability": ai_probability,
        "authentic_probability": authentic_probability
    }

    result = await detector.analyse_video((Path("video.mp4")))

    assert result["risk_level"] == expected_risk_level

@pytest.mark.asyncio
async def test_analyse_video_preserves_other_result_fields(mock_video_detector_dependencies) -> None:
    detector = AIVideoDetector()

    mock_video_detector_dependencies["model"].analyse.return_value = {
        "prediction": "AI-generated",
        "ai_probability": 0.92,
        "authentic_probability": 0.08,
        "visual": {"prediction": "AI-generated", "ai_probability": 0.95},
        "audio": {"available": False},
        "fusion": {"visual_weight": 1.0, "audio_weight": 0.0}
    }

    result = await detector.analyse_video(Path("video.mp4"))

    assert result["risk_level"] == 3
    assert result["visual"] ["ai_probability"] == 0.95
    assert result["audio"] == {"available": False}
    assert result["fusion"] == {"visual_weight": 1.0, "audio_weight": 0.0}