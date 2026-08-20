from pathlib import Path
from unittest.mock import MagicMock
import numpy as np
import pytest
import torch
from PIL import Image
import app.training.image.prediction as prediction

class DummyModel:
    def __init__(self) -> None:
        self.network = MagicMock()
        self.network.features = [
            MagicMock(),
            MagicMock()
        ]
        self.device = None
        self.eval_called = False

    def to(self, device: torch.device) -> "DummyModel":
        self.device = device
        return self

    def eval(self)-> "DummyModel":
        self.eval_called =True
        return self
    
class DummyTransform:
    def __call__(self, image: Image.Image)-> torch.Tensor:
        return torch.zeros(3,224,224,dtype=torch.float32)

class DummyWeights:
    @staticmethod
    def transforms() -> DummyTransform:
        return DummyTransform()

class DummyWeightsContainer:
    DEFAULT = DummyWeights()

class DummyGradCAM:
    last_instance = None

    def __init__(self, model, target_layer) -> None:
        self.model = model
        self.target_layer = target_layer
        self.hooks_removed = False

        DummyGradCAM.last_instance = self
    
    def generate(self, image_tensor: torch.Tensor) -> tuple[np.ndarray, float]:
        return (
            np.full((7,7), 0.5, dtype=np.float32),
            0.8
        )
    
    def remove_hooks(self) -> None:
        self.hooks_removed = True

@pytest.fixture
def mock_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, object]:

    monkeypatch.setattr(prediction, "EfficientNet_B0_Weights", DummyWeightsContainer)

    monkeypatch.setattr(prediction, "GradCAM", DummyGradCAM)

    monkeypatch.setattr(prediction, "extract_metadata", lambda image: {
        "Make": "Test_Camera",
        "Software": "Test_Software"
    })

    monkeypatch.setattr(
        prediction,
        "calculate_laplacian_variance",
        lambda image: 123.456789
    )

    monkeypatch.setattr(
        prediction,
        "calculate_noise_level",
        lambda image: 7.654321
    )

    monkeypatch.setattr(prediction, "calculate_colour_statistics", lambda image: {
        "red_std": 1.23456,
        "green_std": 2.34567,
        "blue_std": 3.45678,
        "mean_saturation_range": 50.98765
    })

    monkeypatch.setattr(
        prediction,
        "calculate_attention_statistics",
        lambda heatmap: {
            "strong_attention_ratio": 0.25,
            "moderate_attention_ratio": 0.5,
            "maximum_attention": 0.9,
            "mean_attention": 0.4
        }
    )

    monkeypatch.setattr(
        prediction,
        "generate_probability_reason",
        lambda **kwargs: {
            "type": "model",
            "importance": "high",
            "supports": "AI",
            "message": "High AI probability"
        }
    )

    monkeypatch.setattr(
        prediction,
        "generate_attention_reason",
        lambda statistics: {
            "type": "model_attention",
            "importance": "medium",
            "supports": "INCONCLUSIVE",
            "message": "Attention reason"
        }
    )

    monkeypatch.setattr(
        prediction,
        "generate_statistical_reasons",
        lambda ** kwargs: [
            {
                "type": "statistics",
                "importance": "medium",
                "supports": "AI",
                "message": "Statistical reason"
            }
        ]
    )

    monkeypatch.setattr(
        prediction,
        "analyse_metadata",
        lambda metadata: [
            {
                "type": "metadata",
                "importance": "low",
                "supports": "AUTHENTIC",
                "message": "Metadata reason"
            }
        ]
    )

    monkeypatch.setattr(
        prediction,
        "probability_to_risk_level",
        lambda **kwargs: "HIGH"
    )

    monkeypatch.setattr(
        prediction,
        "risk_level_to_classification",
        lambda risk_level: "Likely AI-generated or modified"
    )

    def mock_create_heatmap_overlay(
            original_image,
            heatmap,
            output_path
    )-> Path:
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        output_path.touch()

        return output_path

    monkeypatch.setattr(prediction, "create_heatmap_overlay", mock_create_heatmap_overlay)
def create_test_image(path: Path) -> None:
    Image.new(
        mode="RGB",
        size=(100,100),
        color=(100,150,200)
    ).save(path)

def test_predict_and_explain_success(tmp_path: Path, mock_dependencies) -> None:
    image_path = tmp_path / "image.png"
    
    create_test_image(image_path)

    model = DummyModel()
    device = torch.device("cpu")

    result = prediction.predict_and_explain(
        model=model,
        image_path=image_path,
        device=device,
        output_directory=tmp_path / "outputs",
        low_threshold=0.3,
        high_threshold=0.6
    )

    assert result["image"] == str(image_path)
    assert result["ai_probability"] == 80
    assert result["confidence_percentage"] == 80
    assert result["risk_level"] == "HIGH"

    assert (result["classification"] == "Likely AI-generated or modified")
    assert len(result["reasons"]) == 4
    assert result["technical_details"]["edge_variance"] == 123.4568
    assert result["technical_details"]["estimated_noise_level"] == 7.6543
    assert result["technical_details"]["metadata_fields_found"] == ["Make", "Software"]
    assert Path(result["heatmap_path"]).exists()
    assert model.device == device
    assert model.eval_called is True
    assert DummyGradCAM.last_instance is not None
    assert DummyGradCAM.last_instance.hooks_removed is True

def test_predict_and_explain_missing_image(tmp_path: Path) -> None:
    model=DummyModel()
    image_path= tmp_path / "missing.png"
    device = torch.device("cpu")

    with pytest.raises(
        FileNotFoundError,
        match="Image does not exist"
    ):
        prediction.predict_and_explain(
            model=model,
            image_path=image_path,
            device=device
        )

def test_predict_and_explain_invalid_image(tmp_path: Path) -> None:
    image_path = tmp_path / "invalid.png"

    image_path.write_text(
        "not an image",
        encoding="utf-8"
    )

    model = DummyModel()
    device = torch.device("cpu")

    with pytest.raises(
        ValueError,
        match="Could not read image"
    ):
        prediction.predict_and_explain(
            model=model,
            image_path=image_path,
            device=device
        )

def test_gradcam_hooks_removed_when_generation_fails(tmp_path: Path, mock_dependencies, monkeypatch: pytest.MonkeyPatch) -> None:
    image_path = tmp_path / "image.png"

    Image.new(
        mode="RGB",
        size=(100,100)
    ).save(image_path)

    class FailingGradCAM(DummyGradCAM):
        def generate(self, image_tensor: torch.Tensor) -> tuple[np.ndarray, float]:
            raise RuntimeError("Grad-CAM failed")
        
    monkeypatch.setattr(prediction, "GradCAM", FailingGradCAM)

    model = DummyModel()
    device=torch.device("cpu")
    output_directory = tmp_path / "outputs"

    with pytest.raises(
        RuntimeError,
        match="Grad-CAM failed"
    ):
        prediction.predict_and_explain(
            model=model,
            image_path=image_path,
            device=device,
            output_directory=output_directory
        )

    assert DummyGradCAM.last_instance is not None
    assert DummyGradCAM.last_instance.hooks_removed is True
