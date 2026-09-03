import argparse
import asyncio
import json
import subprocess
import tempfile
from pathlib import Path

import torch

from app.training.video.dataset import read_video_frames
from app.training.video.model import ai_video_classifier

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

def mask_frame(video, frame_index):
    masked = video.clone()
    masked[:, frame_index, :, :, :] = 0.0
    return masked

def calculate_decision_importance(original_probability, masked_probability, prediction):
    if prediction == "AI-generated":
        return original_probability - masked_probability
        
    return masked_probability-original_probability

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

def build_explanation(prediction, probability, frame_results):
    strongest_frame = max(frame_results, key=lambda x: x["importance"])

    if prediction == "AI-generated":
        explanation = f"The visual model classified this video as AI-generated with {probability * 100:.2f}% probability."
    else:
        explanation = f"The visual model classified this video as authentic with {(1.0 - probability) * 100:.2f}% probability."

    if strongest_frame["importance"] <= 0:
        return explanation + " The frame occlusion analysis did not identify a sampled frame that positively supported the visual prediction."

    explanation += (
        f" The most influential sampled frame was frame {strongest_frame['sampled_frame'] + 1}. "
        f"Masking this frame changed the AI-generated probability to {strongest_frame['masked_probability'] * 100:.2f}%."
    )

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
