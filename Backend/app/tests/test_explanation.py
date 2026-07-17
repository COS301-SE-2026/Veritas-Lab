from pathlib import Path
import numpy as np
import pytest
import torch
from PIL import Image
from torch import nn

from app.training.explanation import (
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

def create_rgb_image(size: tuple[int, int] = (100, 100), colour: tuple[int, int, int] = (100, 150, 200)) -> Image:
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
