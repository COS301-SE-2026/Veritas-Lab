from __future__ import annotations
from pathlib import Path
from typing import Any
from PIL import Image
import torch
from torchvision.models import EfficientNet_B0_Weights

from explanation import (
    GradCAM,
    analyse_metadata,
    calculate_attention_statistics,
    calculate_colour_statistics,
    calculate_laplacian_variance,
    calculate_noise_level,
    create_heatmap_overlay,
    extract_metadata,
    generate_attention_reason,
    generate_probability_reason,
    generate_statistical_reasons
)
from model import AIImageDetector
from scoring import probability_to_risk_level, risk_level_to_classification

def predict_and_explain(
    model: AIImageDetector,
    image_path: str|Path,
    device: torch.device,
    output_directory: str| Path = "outputs",
    low_threshold: float = 0.4,
    high_threshold: float = 0.7
) -> dict[str, Any]:
    image_path = Path(image_path)
    output_directory= Path(output_directory)

    if not image_path.exists():
        raise FileNotFoundError(f"Image does not exist: {image_path}")
    
    try:
        with Image.open(image_path) as opened_image:
            metadata = extract_metadata(opened_image)
            image = opened_image.convert("RGB")
    except Exception as error:
        raise ValueError(f"Could not read image: {image_path}") from error
    
    transform = EfficientNet_B0_Weights.DEFAULT.transforms()
    image_tensor = transform(image).unsqueeze(0).to(device)

    model = model.to(device)
    model.eval()

    target_layer = model.network.features[-1]
    grad_cam = GradCAM(model=model, target_layer=target_layer)

    try:
        heatmap, probability = grad_cam.generate(image_tensor)
    finally:
        grad_cam.remove_hooks()
    
    risk_level = probability_to_risk_level(probability=probability, low_threshold=low_threshold, high_threshold=high_threshold)

    edge_variance = calculate_laplacian_variance(image)
    noise_level = calculate_noise_level(image)
    colour_statistics = calculate_colour_statistics(image)
    attention_statistics = calculate_attention_statistics(heatmap)

    reasons: list[dict[str,str]] = [
        generate_probability_reason(probability=probability, low_threshold=low_threshold, high_threshold=high_threshold),
        generate_attention_reason(attention_statistics)
    ]
    reasons.extend(
        generate_statistical_reasons(
            edge_variance=edge_variance,
            noise_level=noise_level,
            colour_statistics=colour_statistics
        )
    )
    reasons.extend(analyse_metadata(metadata))

    heatmap_path = create_heatmap_overlay(
        original_image=image,
        heatmap=heatmap,
        output_path=output_directory / f"{image_path.stem}_gradcam.png"
    )

    confidence = max(probability, 1.0 - probability)

    return {
        "image": str(image_path),
        "ai_probability": round(probability * 100, 2),
        "confidence_percentage": round(confidence * 100, 2),
        "risk_level": risk_level,
        "classification": risk_level_to_classification(risk_level),
        "reasons": reasons,
        "technical_details": {
            "edge_variance": round(edge_variance,4),
            "estimated_noise_level": round(noise_level, 4),
            "colour_statistics": {
                key: round(value,4)
                for key, value in colour_statistics.items()
            },
            "attention_statistics": {
                key: round(value, 4)
                for key, value in attention_statistics.items()
            },
            "metadata_fields_found": sorted(metadata.keys()),
        },
        "heatmap_path": str(heatmap_path),
        "warning": "The risk level and reasons are supporting indicators, not definitive proof that an image is authentic or AI-generated."
    }