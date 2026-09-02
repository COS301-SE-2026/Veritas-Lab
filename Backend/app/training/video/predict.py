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

def tensor_frames_to_uint8(video):
    frames = video[0].detach().cpu()

    mean = CLIP_MEAN[0]
    std = CLIP_STD[0]

    frames = frames * std +mean
    frames = frames.clamp(0.0, 1.0)
    frames = (frames * 255.0).byte()
    frames = frames.permute(0,2,3,1).numpy()

    return frames

def save_explanation_images(
    video,
    spatiotemporal_results,
    output_dir,
    zones_per_dim,
    top_k=3
):
    output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    frames = tensor_frames_to_uint8(video)

    ranked = sorted(
        [
            item for item in spatiotemporal_results
            if item["importance"] > 0
        ],
        key=lambda x: x["importance"],
        reverse=True
    )

    saved = []

    for rank, item in enumerate(ranked[:top_k], start=1):
        frame_index = item["sampled_frame"]

        row = item["row"]
        col = item["col"]

        image = Image.fromarray(frames[frame_index].copy())
        draw = ImageDraw.Draw(image)
        w, h = image.size

        rw = w // zones_per_dim
        rh = h// zones_per_dim
        x1 = col * rw
        y1 = row * rh

        x2 = w - 1 if col == zones_per_dim - 1 else (col + 1) * rw - 1

        y2 = h - 1 if row == zones_per_dim - 1 else (row + 1) * rh - 1
        
        draw.rectangle(
            (
                x1,
                y1,
                x2,
                y2
            ),
            outline=(
                255,
                0,
                0
            ),
            width=5
        )

        filename = (
            f"evidence_{rank}"
            f"_frame_"
            f"{frame_index + 1}.jpg"
        )

        path = (
            output_dir
            / filename
        )

        image.save(
            path,
            quality=95
        )

        saved.append(
            {
                "rank":
                    rank,
                "sampled_frame":
                    frame_index,
                "region":
                    region_name(
                        row,
                        col,
                        zones_per_dim
                    ),
                "importance":
                    item[
                        "importance"
                    ],
                "file":
                    str(path)
            }
        )

    return saved

def build_explanation(
    prediction,
    probability,
    region_results,
    frame_results,
    spatiotemporal_results,
    zones_per_dim
):
    strongest_region = max(region_results, key=lambda x: x["importance"])
    strongest_frame = max(frame_results, key=lambda x: x["importance"])
    strongest_local = max(spatiotemporal_results, key=lambda x: x["importance"])

    if prediction == "AI-generated":
        explanation = f"The visual model classified this video as AI-generated with a {probability * 100:.2f}% probability."

    else:
        explanation = f"The visual model classified this video as authentic with a {(1.0 - probability) * 100:.2f}% probability."

    no_positive_evidence = strongest_region["importance"] <= 0 and strongest_frame["importance"] <= 0 and strongest_local["importance"] <= 0
    
    if no_positive_evidence:
        return explanation + " The occlusion analysis did not identify a specific region or sampled frame that positively supported the visual prediction."
        
    if strongest_region["importance"] > 0:
        region = region_name(strongest_region["row"],strongest_region["col"],zones_per_dim)

        if prediction == "AI-generated":
            explanation += (
                f" The strongest spatial evidence came from the {region} region. "
                f"Masking this region changed the AI-generated probability from {probability * 100:.2f}% to {strongest_region['masked_probability'] * 100:.2f}%."
            )

        else:
            explanation += (
                f" The strongest spatial evidence supporting authenticity came from the {region} region. "
                f"When this region was masked, the AI-generated probability increased from {probability * 100:.2f}% to {strongest_region['masked_probability'] * 100:.2f}%."
            )

    if (strongest_frame["importance"] > 0):
        explanation += f" The most influential sampled frame was frame {strongest_frame['sampled_frame'] + 1}."

    if (strongest_local["importance"] > 0):
        local_region = region_name(
            strongest_local["row"],
            strongest_local["col"],
            zones_per_dim
        )

        explanation += f" The strongest combined space-time evidence occurred in the {local_region} region of sampled frame {strongest_local['sampled_frame'] + 1}."

    return explanation

def build_multimodal_summary(
    final_prediction,
    final_probability,
    visual_prediction,
    visual_probability,
    audio_result
):
    summary = f"The final multimodal classification is {final_prediction} with {final_probability * 100:.2f}% AI-generated probability. "
    
    summary += f"The visual model predicted {visual_prediction} with {visual_probability * 100:.2f}% AI-generated probability. "
    

    if audio_result is None:
        summary += "No usable audio analysis was available, so the final result was based on the visual model only."
        return summary

    audio_probability = audio_result["ai_probability"]
    audio_prediction = "AI-generated" if audio_probability >= 0.5 else "Authentic"

    summary += f"The audio model predicted {audio_prediction} with {audio_probability * 100:.2f}% AI-generated probability. "

    if visual_prediction != audio_prediction:
        summary += "The visual and audio models disagreed, so the configured fusion weights were used to determine the final result."
   
    else:
        summary += "The visual and audio models agreed on the classification."

    return summary