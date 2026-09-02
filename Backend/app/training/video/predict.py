import argparse
import asyncio
import json
import subprocess
import tempfile
from pathlib import Path

import torch

from app.training.audio.predict import predict_audio
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

async def main():
    parser = argparse.ArgumentParser(description="Predict Authentic vs AI-generated video using visual and audio analysis.")
    parser.add_argument("video", help="Path to the file")
    parser.add_argument(
        "--checkpoint",
        required=True,
        help="Path to the trained video .pt checkpoint"
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="AI classification threshold (default: 0.5)"   
    )

    parser.add_argument(
        "--output-dir",
        default="explanations",
        help="Directory for explanation JSON"
    )

    args = parser.parse_args()
    device = torch.device("cpu")
    print(f"Device: {device}")

    checkpoint = torch.load(args.checkpoint, map_location=device)
    num_frames = checkpoint.get("num_frames", 8)

    zones = checkpoint.get("zones",2)

    temporal_hidden_dim = checkpoint.get("temporal_hidden_dim", 256)
    classifier_hidden_dim = checkpoint.get("classifier_hidden_dim",256)

    model = ai_video_classifier(
        num_frames=num_frames,
        zones_per_dim=zones,
        freeze_encoder=True,
        temporal_hidden_dim=(temporal_hidden_dim),
        classifier_hidden_dim=(classifier_hidden_dim)
    )

    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    video = read_video_frames(args.video, num_frames=num_frames)
    video = video.unsqueeze(0).to(device)
    
    print("\nRunning visual and audio analysis...")

    visual_task = asyncio.to_thread(predict_probability, model, video)
    audio_task = asyncio.to_thread(analyse_audio, args.video)
    visual_probability, audio_result = await asyncio.gather(visual_task, audio_task)

    visual_prediction = "AI-generated" if visual_probability >= args.threshold else "Authentic"
    if audio_result is not None:
        audio_probability = audio_result["ai_probability"]

        final_probability = VISUAL_WEIGHT * visual_probability + AUDIO_WEIGHT * audio_probability
        effective_visual_weight = VISUAL_WEIGHT

        effective_audio_weight = AUDIO_WEIGHT

    else:
        audio_probability = None
        final_probability = visual_probability
        effective_visual_weight = 1.0
        effective_audio_weight = 0.0
    
    final_prediction = "AI-generated" if final_probability >= args.threshold else "Authentic"

    print("\nRunning visual explainability analysis...")

    frame_results = calculate_frame_importance(
        model,
        video,
        visual_probability,
        visual_prediction
    )
        
    output_dir = Path(args.output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    visual_explanation = build_explanation(
        visual_prediction,
        visual_probability,
        frame_results
    )

    multimodal_summary = build_multimodal_summary(
        final_prediction,
        final_probability,
        visual_prediction,
        visual_probability,
        audio_result
    )

    strongest_frame = max(frame_results, key=lambda x: x["importance"])  

    report = {
        "video":str(args.video),
        "prediction": final_prediction,
        "ai_probability": final_probability,
        "authentic_probability": 1.0- final_probability,
        "threshold": args.threshold,
        "summary": multimodal_summary,

        "visual_analysis": {
            "prediction": visual_prediction,
            "ai_probability": visual_probability,
            "authentic_probability": 1.0- visual_probability,
            "explanation_method":"frame occlusion sensitivity",
            "summary":visual_explanation,

            "most_influential_sampled_frame": {
                "sampled_frame": strongest_frame["sampled_frame"],
                "display_frame_number": strongest_frame["sampled_frame"] + 1,
                "importance": strongest_frame["importance"],
                "masked_ai_probability": strongest_frame["masked_probability"]
            },

            "frame_importance": frame_results
        },

        "audio_analysis": (
            audio_result
            if audio_result is not None
            else {
                "available": False
            }
        ),

        "fusion": {
            "visual_weight": effective_visual_weight,

            "audio_weight": effective_audio_weight
        }
    }

    json_path = output_dir/ "explanation.json"

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print("\nVIDEO AUTHENTICITY RESULT")
    print()
    print(f"Final prediction: {final_prediction}")
    print(f"Final AI probability: {final_probability * 100:.2f}%")
    print(f"Final Authentic probability: {(1.0 - final_probability) * 100:.2f}%")
    print(f"Threshold: {args.threshold:.2f}")
    print("\nVISUAL ANALYSIS")
    print(f"Prediction: {visual_prediction}")
    print(f"AI probability: {visual_probability * 100:.2f}%")
    print(f"Authentic probability: {(1.0 - visual_probability) * 100:.2f}%")
    print("\nAUDIO ANALYSIS")

    if audio_result is not None:
        audio_prediction = ("AI-generated" if audio_probability >= 0.5 else "Authentic")
        print(f"Prediction: {audio_prediction}")
        print(f"AI probability: {audio_probability * 100:.2f}%")

        print(f"Authentic probability: {(1.0 - audio_probability) * 100:.2f}%")

    else:
        print("No usable audio track was found.")

    print("\nMULTIMODAL SUMMARY")
    print()
    print(multimodal_summary)

    print("\nVISUAL EXPLANATION")
    print()
    print(visual_explanation)

    print("\nMOST INFLUENTIAL SAMPLED FRAMES")
    print()

    for item in sorted(frame_results, key=lambda x: x["importance"], reverse=True)[:3]:
        print(
            f"Frame {item['sampled_frame'] + 1}: "
            f"importance={item['importance']:.4f}, "
            f"AI score after masking={item['masked_probability'] * 100:.2f}%"
        )

    print(f"\nExplanation JSON: {json_path}")

if __name__ == "__main__":
    asyncio.run(main())