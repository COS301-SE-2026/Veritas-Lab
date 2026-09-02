import argparse
import asyncio
import json
import subprocess
import tempfile
from pathlib import Path

import torch
from PIL import Image, ImageDraw

from app.training.audio.predict import predict_audio
from app.training.video.dataset import read_video_frames
from app.training.video.model import ai_video_classifier

CLIP_MEAN = torch.tensor([0.48145466, 0.4578275, 0.40821073]).view(1, 3, 1, 1)
CLIP_STD = torch.tensor([0.26862954, 0.26130258, 0.27577711]).view(1, 3, 1, 1)

VISUAL_WEIGHT = 0.7
AUDIO_WEIGHT = 0.3

def predict_probability(model, video_batch):
    with torch.no_grad():
        logit = model(video_batch)
        return torch.sigmoid(logit).item()

def extract_audio_from_video(video_path):
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)

    temp_path = temp_file.name
    temp_file.close()

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        temp_path
    ]

    result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if result.returncode != 0:
        Path(temp_path).unlink(
            missing_ok=True
        )

        return None

    return temp_path

def analyse_audio(video_path):
    audio_path = extract_audio_from_video(video_path)
    if audio_path is None:
        return None

    try:
        return predict_audio(audio_path)

    except Exception as exc:
        print(f"Audio analysis failed: {exc}")
        return None

    finally:
        Path(audio_path).unlink(
            missing_ok=True
        )

def mask_region(video, row, col, zones_per_dim):
    masked = video.clone()

    _, _, _, h, w = masked.shape

    rh = h // zones_per_dim
    rw = w // zones_per_dim

    y1 = row * rh
    y2 = h if row == zones_per_dim - 1 else (row + 1) * rh
    
    x1 = col * rw
    x2 = w if col == zones_per_dim - 1 else (col + 1) * rw

    masked[:, :, :, y1:y2, x1:x2] = 0.0
    return masked

def mask_frame(video, frame_index):
    masked = video.clone()
    masked[:, frame_index, :, :, :] = 0.0
    return masked

def mask_frame_region(
    video,
    frame_index,
    row,
    col,
    zones_per_dim
):
    masked = video.clone()

    _, _, _, h, w = masked.shape

    rh = h // zones_per_dim
    rw = w // zones_per_dim

    y1 = row * rh
    y2 = h if row == zones_per_dim - 1 else (row + 1) * rh
    
    x1 = col * rw
    x2 = w if col == zones_per_dim - 1 else (col + 1) * rw
    
    masked[:, frame_index, :, y1:y2, x1:x2] = 0.0
    return masked

def calculate_decision_importance(original_probability, masked_probability, prediction):
    if prediction == "AI-generated":
        return original_probability - masked_probability
        
    return masked_probability-original_probability
    
def calculate_region_importance(
    model,
    video,
    original_probability,
    zones_per_dim,
    prediction
):
    results = []

    for row in range(zones_per_dim):
        for col in range(zones_per_dim):
            masked = mask_region(video, row, col, zones_per_dim)

            masked_probability = (
                predict_probability(
                    model,
                    masked
                )
            )

            importance = (
                calculate_decision_importance(
                    original_probability,
                    masked_probability,
                    prediction
                )
            )

            results.append(
                {
                    "row": row,
                    "col": col,
                    "masked_probability":
                        masked_probability,
                    "importance":
                        importance
                }
            )

    return results

def calculate_frame_importance(
    model,
    video,
    original_probability,
    prediction
):
    results = []

    num_frames = video.shape[1]

    for frame_index in range(num_frames):
        masked = mask_frame(video, frame_index)

        masked_probability = predict_probability(model, masked)
        

        importance = calculate_decision_importance(original_probability, masked_probability, prediction)
        

        results.append(
            {
                "sampled_frame":
                    frame_index,
                "masked_probability":
                    masked_probability,
                "importance":
                    importance
            }
        )

    return results

def calculate_spatiotemporal_importance(
    model,
    video,
    original_probability,
    zones_per_dim,
    prediction
):
    results = []

    num_frames = video.shape[1]

    for frame_index in range(
        num_frames
    ):
        for row in range(
            zones_per_dim
        ):
            for col in range(
                zones_per_dim
            ):
                masked = (
                    mask_frame_region(
                        video,
                        frame_index,
                        row,
                        col,
                        zones_per_dim
                    )
                )

                masked_probability = (
                    predict_probability(
                        model,
                        masked
                    )
                )

                importance = (
                    calculate_decision_importance(
                        original_probability,
                        masked_probability,
                        prediction
                    )
                )

                results.append(
                    {
                        "sampled_frame": frame_index,
                        "row": row,
                        "col": col,
                        "masked_probability": masked_probability,
                        "importance": importance
                    }
                )

    return results

def region_name(row, col, zones_per_dim):
    if zones_per_dim == 2:
        names = {
            (0, 0): "top-left",
            (0, 1): "top-right",
            (1, 0): "bottom-left",
            (1, 1): "bottom-right"
        }

        return names[(row, col)]

    return f"row {row + 1}, column {col + 1}"

def normalize_positive_importances(items):
    positives = [max(0.0, item["importance"]) for item in items]

    total = sum(positives)

    if total <= 1e-12:
        return [0.0 for _ in items]

    return [
        (value/total) * 100.0
        for value in positives
    ]

