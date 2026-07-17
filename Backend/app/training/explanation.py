from __future__ import annotations
from pathlib import Path
from typing import Any
import numpy as np
import torch
from PIL import ExifTags, Image, ImageFilter
from torch import nn

class GradCAM:

    def _save_activations(self, module: nn.Module, input: tuple[torch.Tensor | None,...], output: torch.Tensor):
        self.activations = output.detach()
    
    def _save_gradients(self, module: nn.Module, grad_input: tuple[torch.Tensor | None ,...], grad_output: tuple[torch.Tensor | None,...]):
        if grad_output and grad_output[0] is not None:
            self.gradients = grad_output[0].detach()

    def generate(self, image_tensor: torch.Tensor)->tuple[np.ndarray, float]:
        self.activations = None
        self.gradients = None

        self.model.eval()
        self.model.zero_grad(set_to_none=True)

        if image_tensor.ndim != 4:
            raise ValueError("The image tensor must have shape (batch, channels, height, width).")
        
        if image_tensor.shape[0] != 1:
            raise ValueError("Grad-CAM can only explain one image at a time.")
        
        logit = self.model(image_tensor)

        if logit.numel() != 1:
            raise ValueError("Grad-CAM expects a single image and one binary-classification logit.")
        
        probability = torch.sigmoid(logit).item()

        target_score = logit if probability >= 0.5 else -logit
        target_score.sum().backward()

        if self.activations is None or self.gradients is None:
            raise RuntimeError("Grad-CAM could not capture activations or gradients.")
        
        if self.activations.ndim != 4 or self.gradients.ndim != 4:
            raise RuntimeError("The selected Grad-CAM layer must produce a four-dimensional feature map.")
        
        if self.activations.shape != self.gradients.shape:
            raise RuntimeError("Grad-CAM activations and gradients must have matching shapes.")

        weights = self.gradients.mean(dim=(2,3), keepdim=True)
        heatmap = (weights * self.activations).sum(dim=1)
        heatmap = torch.relu(heatmap)

        minimum = heatmap.min()
        maximum = heatmap.max()

        if maximum > minimum:
            heatmap = (heatmap - minimum) / (maximum - minimum)
        else:
            heatmap = torch.zeros_like(heatmap)

        heatmap_array = heatmap[0].cpu().numpy()
        return heatmap_array, probability
    
    def remove_hooks(self)->None:
        self.forward_handle.remove()
        self.backward_handle.remove()

    def __init__(self, model: nn.Module, target_layer: nn.Module)->None:
        self.model = model
        self.target_layer = target_layer
        self.activations: torch.Tensor | None=None
        self.gradients: torch.Tensor | None = None

        self.forward_handle = target_layer.register_forward_hook(self._save_activations)
        self.backward_handle = target_layer.register_full_backward_hook(self._save_gradients)

def calculate_laplacian_variance(image: Image.Image) -> float:
    grayscale = np.asarray(image.convert("L"), dtype=np.float32)
    padded = np.pad(grayscale, pad_width=1, mode="edge")

    laplacian = (padded[:-2, 1:-1] + padded[2:, 1:-1] + padded[1:-1, :-2] + padded[1:-1, 2:] - 4 * padded[1:-1, 1:-1])
    return float(np.var(laplacian))

def calculate_noise_level(image: Image.Image) -> float:
    grayscale = image.convert("L")
    blurred = grayscale.filter(ImageFilter.GaussianBlur(radius=2))

    original_array = np.asarray(grayscale, dtype=np.float32)
    blurred_array = np.asarray(blurred, dtype=np.float32)

    return float(np.std(original_array - blurred_array))

def calculate_colour_statistics(image: Image.Image) -> dict[str, float]:
    rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    channel_std = rgb.std(axis=(0, 1))
    saturation_range = rgb.max(axis=2) - rgb.min(axis=2)

    return {
        "red_std": float(channel_std[0]),
        "green_std": float(channel_std[1]),
        "blue_std": float(channel_std[2]),
        "mean_saturation_range": float(saturation_range.mean())
    }

def extract_metadata(image: Image.Image) -> dict[str, Any]:
    metadata: dict[str, Any] = {}

    exif = image.getexif()

    if exif:
        for tag_id, value in exif.items():
            tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))

            if isinstance(value, bytes):
                metadata[tag_name] = f"<{len(value)} bytes>"
            elif isinstance(value, (str, int, float)):
                metadata[tag_name] = value
            else:
                metadata[tag_name] = str(value)
    
    for key, value in image.info.items():
        if isinstance(value, bytes):
            metadata[key] = f"<{len(value)} bytes>"
        elif isinstance(value, (str, int, float)):
            metadata[key] = value
    
    return metadata

def analyse_metadata(metadata: dict[str, Any]) -> list[dict[str, str]]:
    reasons: list[dict[str, str]] = []

    camera_make = metadata.get("Make")
    camera_model = metadata.get("Model")
    software = metadata.get("Software")

    if camera_make or camera_model:
        camera = " ".join(
            str(value)
            for value in (camera_make, camera_model)
            if value
        )

        reasons.append(
            {
                "type": "metadata",
                "message": f"Camera metadata was found: {camera}.",
                "importance": "low",
                "supports": "AUTHENTIC"
            }
        )
    else:
        reasons.append(
            {
                "type": "metadata",
                "message": "No camera make or model was found. This is only a weak indicator because websites and messaging apps often remove metadata.",
                "importance": "low",
                "supports": "INCONCLUSIVE"
            }
        )
    
    if software:
        reasons.append(
            {
                "type": "metadata",
                "message": "The metadata records image-processing software: " f"{software}.",
                "importance": "medium",
                "supports": "INCONCLUSIVE"
            }
        )
    
    return reasons

def generate_probability_reason(probability: float, low_threshold: float = 0.4, high_threshold: float = 0.7) -> dict[str, str]:
    if not 0.0 <= probability <= 1:
        raise ValueError("Probability must be between 0.0 and 1.0.")
    
    if not 0.0 < low_threshold < high_threshold < 1.0:
        raise ValueError("Thresholds must satisfy 0 < low_threshold < high_threshold < 1.")
    
    if probability >= high_threshold:
        return {
            "type": "model",
            "message": "The classifier detected strong visual patterns associated with the AI-generated or AI-modified class.",
            "importance": "high",
            "supports": "AI"
        }
    
    if probability >= low_threshold:
        return {
            "type": "model",
            "message": "The classifier found mixed evidence and could not clearly distinguish between the authentic and AI classes.",
            "importance": "medium",
            "supports": "INCONCLUSIVE"
        }
    
    return {
        "type": "model",
        "message": "The classifier detected stronger visual patterns associated with the authentic-image class.",
        "importance": "high",
        "supports": "AUTHENTIC"
    }

def generate_statistical_reasons(edge_variance: float, noise_level: float, colour_statistics: dict[str, float]) -> list[dict[str, str]]:
    reasons: list[dict[str, str]] = []

    if noise_level < 4.0:
        reasons.append(
            {
                "type": "visual",
                "message": "The image contains very smooth regions with limited high-frequency noise. This may occur in synthetic or heavily denoised images.",
                "importance": "medium",
                "supports": "AI"
            }
        )
    elif noise_level > 25.0:
        reasons.append(
            {
                "type": "visual",
                "message": "The image contains a high level of fine-grained noise or compression artefacts.",
                "importance": "low",
                "supports": "INCONCLUSIVE"
            }
        )
    else:
        reasons.append(
            {
                "type": "visual",
                "message": "The image contains a moderate level of fine detail and noise.",
                "importance": "low",
                "supports": "AUTHENTIC"
            }
        )
    
    if edge_variance > 2500.0:
        reasons.append(
            {
                "type": "visual",
                "message": "The image contains unusually strong edge patterns. This can result from artificial sharpening, editing, or generation artefacts.",
                "importance": "medium",
                "supports": "AI"
            }
        )
    elif edge_variance < 40.0:
        reasons.append(
            {
                "type": "visual",
                "message": "The image contains very little fine edge detail. This can result from blur, smoothing, or compression.",
                "importance": "low",
                "supports": "INCONCLUSIVE"
            }
        )
    if colour_statistics["mean_saturation_range"] > 100.0:
        reasons.append(
            {
                "type": "visual",
                "message": "The image contains unusually strong colour separation or saturation.",
                "importance": "low",
                "supports": "AI"
            }
        )
    
    return reasons

def validate_heatmap(heatmap: np.ndarray) -> None:
    if heatmap.ndim != 2:
        raise ValueError("The heatmap must be a two-dimensional array.")
    
    if heatmap.size == 0:
        raise ValueError("The heatmap cannot be empty.")
    
    if not np.isfinite(heatmap).all():
        raise ValueError("The heatmap contains NaN or infinite values.")

def calculate_attention_statistics(heatmap: np.ndarray) -> dict[str, float]:
    validate_heatmap(heatmap)

    return {
        "strong_attention_ratio": float((heatmap >= 0.70).mean()),
        "moderate_attention_ratio": float((heatmap >= 0.40).mean()),
        "maximum_attention": float(heatmap.max()),
        "mean_attention": float(heatmap.mean())
    }

def generate_attention_reason(attention_statistics: dict[str, float]) -> dict[str, str]:
    ratio = attention_statistics["strong_attention_ratio"]

    if ratio < 0.05:
        message = "The model concentrated most of its attention on a small number of localised image regions."
    elif ratio > 0.4:
        message = "The model's decision was influenced by patterns spread across a large part of the image."
    else:
        message = "The model relied on several image regions when making its classification."
    
    return {
        "type": "model_attention",
        "message": message,
        "importance": "medium",
        "supports": "INCONCLUSIVE"
    }

def create_heatmap_overlay(original_image: Image.Image, heatmap: np.ndarray, output_path: str| Path, opacity: float = 0.45) -> Path:
    validate_heatmap(heatmap)
    
    if not 0.0 <= opacity <= 1.0:
        raise ValueError("Opacity must be between 0.0 and 1.0.")
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    original = original_image.convert("RGB")

    heatmap_image = Image.fromarray(
        np.uint8(np.clip(heatmap, 0.0, 1.0) * 255),
        mode="L"
    )

    heatmap_image = heatmap_image.resize(
        original.size,
        resample=Image.Resampling.BILINEAR
    )

    heatmap_array = np.asarray(heatmap_image, dtype=np.uint8)
    red_overlay = np.zeros(
        (heatmap_array.shape[0], heatmap_array.shape[1], 3),
        dtype=np.uint8
    )

    red_overlay[:, :, 0] = heatmap_array

    overlay = Image.fromarray(red_overlay, mode="RGB")
    combined = Image.blend(original, overlay, alpha=opacity)
    combined.save(output_path)

    return output_path
