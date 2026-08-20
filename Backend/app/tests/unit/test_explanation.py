from pathlib import Path
import numpy as np
import pytest
import torch
from PIL import Image
from torch import nn

from Backend.app.training.image.explanation import (
    GradCAM,
    analyse_metadata,
    calculate_attention_statistics,
    calculate_colour_statistics,
    calculate_laplacian_variance,
    calculate_noise_level,
    create_heatmap_overlay,
    extract_metadata,
    validate_heatmap,
    generate_attention_reason,
    generate_probability_reason,
    generate_statistical_reasons,
)

class SmallBinaryModel(nn.Module):

    def __init__(self) -> None:
        super().__init__()

        self.features = nn.Sequential(
            nn.Conv2d(
                in_channels=3,
                out_channels=4,
                kernel_size=3,
                padding=1
            ),
            nn.ReLU()
        )

        self.pool = nn.AdaptiveAvgPool2d((1,1))
        self.classifier = nn.Linear(4,1)
    
    def forward(self, images: torch.Tensor) -> torch.Tensor:
        features = self.features(images)
        pooled = self.pool(features)
        flattened = torch.flatten(pooled, start_dim=1)

        return self.classifier(flattened)

class MultipleOutputModel(nn.Module):

    def __init__(self) -> None:
        super().__init__()

        self.features = nn.Conv2d(
            in_channels=3,
            out_channels=4,
            kernel_size=3,
            padding=1
        )

        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier = nn.Linear(4, 2)
    
    def forward(self, images: torch.Tensor) -> torch.Tensor:
        features = self.features(images)
        pooled = self.pool(features)
        flattened = torch.flatten(pooled, start_dim=1)

        return self.classifier(flattened)

def create_rgb_image(size: tuple[int, int] = (100, 100), colour: tuple[int, int, int] = (100, 150, 200)) -> Image.Image:
    return Image.new(
        mode="RGB",
        size=size,
        color=colour
    )

def test_calculate_laplacian_variance_returns_float() -> None:
    image = create_rgb_image()

    result = calculate_laplacian_variance(image)

    assert isinstance(result, float)
    assert result >= 0

def test_uniform_image_has_zero_laplacian_variance() -> None:
    image = create_rgb_image(colour=(100, 100, 100))

    result = calculate_laplacian_variance(image)
    assert result == pytest.approx(0.0)

def test_calculate_noise_level_returns_float() -> None:
    image = create_rgb_image()

    result = calculate_noise_level(image)
    assert result == pytest.approx(0.0)

def test_uniform_image_has_zero_noise() -> None:
    image = create_rgb_image(colour=(100, 100, 100))

    result = calculate_noise_level(image)
    assert result == pytest.approx(0.0)

def test_calculate_colour_statistics() -> None:
    image= create_rgb_image(colour=(100, 150, 200))

    result = calculate_colour_statistics(image)
    assert set(result.keys()) == {
        "red_std",
        "green_std",
        "blue_std",
        "mean_saturation_range"
    }

    assert result["red_std"] == pytest.approx(0.0)
    assert result["green_std"] == pytest.approx(0.0)
    assert result["blue_std"] == pytest.approx(0.0)
    assert result["mean_saturation_range"] == pytest.approx(100.0)

def test_extract_metadata_from_image_without_exif() -> None:
    image = create_rgb_image()
    image.info["Software"] = "Test Editor"

    metadata = extract_metadata(image)
    assert metadata["Software"] == "Test Editor"

def test_analyse_metadata_with_camera_information() -> None:
    metadata = {
        "Make": "Samsung",
        "Model": "Test Camera"
    }

    reasons = analyse_metadata(metadata)

    assert len(reasons) == 1
    reason = reasons[0]

    assert reason["type"] == "metadata"
    assert reason["importance"] == "low"
    assert reason["supports"] == "AUTHENTIC"
    assert "Samsung Test Camera" in reason["message"]

def test_analyse_metadata_with_software() -> None:
    metadata = {"Software": "Image Editor"}

    reasons = analyse_metadata(metadata)

    assert len(reasons) == 2
    software_reason = reasons[1]

    assert software_reason["type"] == "metadata"
    assert software_reason["importance"] == "medium"
    assert software_reason["supports"] == "INCONCLUSIVE"
    assert "Image Editor" in software_reason["message"]

@pytest.mark.parametrize(
    ("probability", "expected_support", "expected_importance"),
    [
        (0.10, "AUTHENTIC", "high"),
        (0.39, "AUTHENTIC", "high"),
        (0.40, "INCONCLUSIVE", "medium"),
        (0.69, "INCONCLUSIVE", "medium"),
        (0.70, "AI", "high"),
        (0.95, "AI", "high")
    ]
)
def test_generate_probability_reason(probability: float, expected_support: str, expected_importance: str) ->None:
    reason = generate_probability_reason(probability)\
    
    assert reason["type"] == "model"
    assert reason["supports"] == expected_support
    assert reason["importance"] == expected_importance

@pytest.mark.parametrize(
    "probability",
    [
        -0.01,
        1.01
    ]
)
def test_probability_reason_rejects_invalid_probability(probability: float) -> None:
    with pytest.raises(
        ValueError,
        match="Probability must be between"
    ):
        generate_probability_reason(probability)

@pytest.mark.parametrize(
    ("low_threshold", "high_threshold"),
    [
        (0.0, 0.7),
        (0.4, 1.0),
        (0.7, 0.4),
        (0.5, 0.5)
    ]
)
def test_probability_reason_rejects_invalid_thresholds(low_threshold: float, high_threshold: float) -> None:
    with pytest.raises(
        ValueError,
        match="Thresholds must satisfy"
    ):
        generate_probability_reason(probability=0.6, low_threshold=low_threshold, high_threshold=high_threshold)
    
def test_probability_reason_uses_custom_thresholds() -> None:
    reason = generate_probability_reason(probability=0.6, low_threshold=0.3, high_threshold=0.6)
    assert reason["supports"] == "AI"

def test_statistical_reasons_for_low_noise() -> None:
    reasons = generate_statistical_reasons(edge_variance=500.0, noise_level=2.0, colour_statistics={"mean_saturation_range": 50.0}) 

    assert reasons[0]["supports"] == "AI"
    assert reasons[0]["importance"] == "medium"

def test_statistical_reasons_for_moderate_noise() -> None:
    reasons = generate_statistical_reasons(edge_variance=500.0, noise_level=10.0, colour_statistics={"mean_saturation_range": 50.0})

    assert reasons[0]["supports"] == "AUTHENTIC"
    assert reasons[0]["importance"] == "low"

def test_statistical_reasons_for_high_noise() -> None:
    reasons = generate_statistical_reasons(edge_variance=500.0, noise_level=30.0, colour_statistics={"mean_saturation_range": 50.0})
    assert len(reasons) == 1
    noise_reason = reasons[0]

    assert noise_reason["supports"] == "INCONCLUSIVE"
    assert noise_reason["importance"] == "low"

def test_statistical_reasons_for_low_edge_variance() -> None:
    reasons = generate_statistical_reasons(edge_variance=20.0, noise_level=10.0, colour_statistics={"mean_saturation_range": 50.0})

    edge_reason = reasons[1]

    assert edge_reason["supports"] == "INCONCLUSIVE"
    assert edge_reason["importance"] == "low"

def test_statistical_reasons_for_high_saturation() -> None:
    reasons = generate_statistical_reasons(edge_variance=500, noise_level=10, colour_statistics={"mean_saturation_range": 150.0})

    saturation_reason = reasons[-1]

    assert saturation_reason["supports"] == "AI"
    assert "saturation" in saturation_reason["message"]

def test_validate_heatmap_accepts_valid_heatmap() -> None:
    heatmap = np.zeros((10, 10), dtype=np.float32)
    validate_heatmap(heatmap)

def test_validate_heatmap_rejects_non_two_dimensional_array() -> None:
    heatmap = np.zeros((1, 10, 10), dtype=np.float32)

    with pytest.raises(
        ValueError,
        match="two-dimensional"
    ):
        validate_heatmap(heatmap)
    
def test_validate_heatmap_rejects_empty_array() -> None:
    heatmap = np.array(
        [],
        dtype=np.float32
    ).reshape(0,0)

    with pytest.raises(
        ValueError,
        match="cannot be empty"
    ):
        validate_heatmap(heatmap)

@pytest.mark.parametrize(
    "invalid_value",
    [
        np.nan,
        np.inf,
        -np.inf
    ]
)
def test_validate_heatmap_rejects_non_finite_values(invalid_value: float)-> None:
    heatmap = np.zeros((10, 10), dtype=np.float32)

    heatmap[0,0] = invalid_value

    with pytest.raises(
        ValueError,
        match="NaN or infinite"
    ):
        validate_heatmap(heatmap)
    
def test_calculate_attention_statistics() -> None:
    heatmap = np.array(
        [
            [0.0, 0.4],
            [0.7, 1.0]
        ],
        dtype=np.float32
    )

    result = calculate_attention_statistics(heatmap)

    assert result["strong_attention_ratio"] == pytest.approx(0.5)
    assert result["moderate_attention_ratio"] == pytest.approx(0.75)
    assert result["maximum_attention"] == pytest.approx(1.0)
    assert result["mean_attention"] == pytest.approx(0.525)

@pytest.mark.parametrize(
    ("ratio", "expected_text"),
    [
        (0.01, "small number"),
        (0.20, "several image regions"),
        (0.60, "large part")
    ]
)
def test_generate_attention_reason(ratio: float, expected_text: str) -> None:
    reason = generate_attention_reason(
        {
            "strong_attention_ratio": ratio
        }
    )

    assert reason["type"] == "model_attention"
    assert reason["importance"] == "medium"
    assert reason["supports"] == "INCONCLUSIVE"
    assert expected_text in reason["message"]

def test_create_heatmap_overlay(tmp_path: Path) -> None:
    original = create_rgb_image(size=(100, 80))

    heatmap = np.ones((10, 10), dtype=np.float32)

    output_path = (tmp_path / "outputs" / "heatmap.png")

    result = create_heatmap_overlay(
        original_image=original,
        heatmap=heatmap,
        output_path=output_path,
        opacity=0.45
    )

    assert result == output_path
    assert output_path.exists()

    with Image.open(output_path) as output_image:
        assert output_image.size == original.size
        assert output_image.mode == "RGB"

@pytest.mark.parametrize(
    "opacity",
    [
        -0.1,
        1.1
    ]
)
def test_create_heatmap_overlay_rejects_invalid_opacity(tmp_path: Path, opacity: float) -> None:
    original = create_rgb_image()

    heatmap = np.zeros((10,10), dtype=np.float32)

    with pytest.raises(
        ValueError,
        match="Opacity must be between"
    ):
        create_heatmap_overlay(
            original_image=original,
            heatmap=heatmap,
            output_path=tmp_path / "heatmap.png",
            opacity=opacity
        )

def test_gradcam_generates_heatmap_and_probability() -> None:
    model = SmallBinaryModel()
    target_layer = model.features[0]

    grad_cam = GradCAM(model=model, target_layer=target_layer)

    image_tensor = torch.rand(1,3,32,32,requires_grad=True)

    try:
        heatmap, probability = grad_cam.generate(image_tensor)
    finally:
        grad_cam.remove_hooks()
    
    assert isinstance(heatmap, np.ndarray)
    assert heatmap.shape == (32, 32)
    assert isinstance(probability, float)
    assert 0.0 <= probability <= 1.0
    assert np.isfinite(heatmap).all()
    assert heatmap.min() >= 0.0
    assert heatmap.max() <= 1.0

def test_gradcam_rejects_tensor_without_batch_dimension() -> None:
    model = SmallBinaryModel()

    grad_cam = GradCAM(model=model, target_layer=model.features[0])
    image_tensor = torch.rand(3,32,32, requires_grad=True)

    try:
        with pytest.raises(
            ValueError,
            match="must have shape"
        ):
            grad_cam.generate(image_tensor)
    finally:
        grad_cam.remove_hooks()
    
def test_gradcam_rejects_multiple_logits() -> None:
    model = MultipleOutputModel()

    grad_cam = GradCAM(model=model, target_layer=model.features)
    image_tensor = torch.rand(1,3,32,32, requires_grad=True)

    try:
        with pytest.raises(
            ValueError,
            match="one binary-classification logit"
        ):
            grad_cam.generate(image_tensor)
    finally:
        grad_cam.remove_hooks()

def test_gradcam_remove_hooks() -> None:
    model = SmallBinaryModel()

    grad_cam = GradCAM(
        model=model,
        target_layer=model.features[0]
    )

    grad_cam.remove_hooks()

    assert grad_cam.forward_handle.id not in model.features[0]._forward_hooks
    assert grad_cam.backward_handle.id not in model.features[0]._backward_hooks

