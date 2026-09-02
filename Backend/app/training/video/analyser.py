from __future__ import annotations
import librosa
import asyncio
from pathlib import Path
import torch
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

from app.training.audio.predict import predict_audio
from app.training.video.dataset import read_video_frames
from app.training.video.model import ai_video_classifier
from app.training.video.predict import analyse_audio, predict_probability, calculate_frame_importance, build_explanation,  extract_audio_from_video

VIDEO_MODEL_PATH = Path("app/ai/best_video_model.pt")
AUDIO_MODEL_PATH = Path("app/ai/audio")
VISUAL_WEIGHT = 0.7
AUDIO_WEIGHT = 0.3

class ai_audio_classifier:
    def __init__(self, model_path: str | Path = AUDIO_MODEL_PATH, sample_rate: int = 16000, duration_seconds: int = 4) -> None:
        self.device = torch.device("cpu")
        self.model_path = Path(model_path)
        self.sample_rate = sample_rate
        self.duration_seconds = duration_seconds
        self.feature_extractor = AutoFeatureExtractor.from_pretrained(self.model_path)
        self.model = AutoModelForAudioClassification.from_pretrained(self.model_path)
        self.model = self.model.to(self.device)
        self.model.eval()

    def predict(self, audio_path: str | Path) -> dict:
        audio_path = Path(audio_path)

        waveform, _ = librosa.load(
            audio_path,
            sr=self.sample_rate,
            mono=True
        )

        chunk_size = self.sample_rate * self.duration_seconds
        chunk_ai_probabilities = []
        chunk_lengths = []

        for start in range(0, len(waveform), chunk_size):
            chunk = waveform[start:start + chunk_size]

            actual_length = len(chunk)
            if actual_length == 0:
                continue

            inputs = self.feature_extractor(
                chunk,
                sampling_rate=self.sample_rate,
                return_tensors="pt",
                padding="max_length",
                truncation=True,
                max_length=chunk_size
            )

            inputs = {
                key: value.to(self.device)
                for key, value in inputs.items()
            }

            with torch.no_grad():
                outputs = self.model(**inputs)

            probabilities = torch.softmax(outputs.logits, dim=-1)[0]
            ai_probability = probabilities[1].item()
            chunk_ai_probabilities.append(ai_probability)
            chunk_lengths.append(actual_length)

        if not chunk_ai_probabilities:
            raise RuntimeError(f"No usable audio found in {audio_path}")

        total_length = sum(chunk_lengths)

        ai_probability = sum(
            probability * length
            for probability, length in zip(chunk_ai_probabilities, chunk_lengths)
        ) / total_length

        authentic_probability = 1.0 - ai_probability

        if ai_probability >= 0.5:
            prediction = "AI-generated"
            confidence = ai_probability
        else:
            prediction = "Authentic"
            confidence = authentic_probability

        return {
            "prediction": prediction,
            "confidence": confidence,
            "authentic_probability": authentic_probability,
            "ai_probability": ai_probability
        }


class video_combined_analysis:
    def __init__(self, model_path: str | Path = VIDEO_MODEL_PATH) -> None:
        self.device = torch.device("cpu")
        self.model_path = Path(model_path)

        checkpoint = torch.load(
            self.model_path,
            map_location=self.device,
            weights_only=True
        )

        self.num_frames = checkpoint.get("num_frames", 8)
        self.zones = checkpoint.get("zones", 2)
        temporal_hidden_dim = checkpoint.get("temporal_hidden_dim", 256)

        classifier_hidden_dim = checkpoint.get("classifier_hidden_dim", 256)

        self.visual_model = ai_video_classifier(
            num_frames=self.num_frames,
            zones_per_dim=self.zones,
            freeze_encoder=True,
            temporal_hidden_dim=temporal_hidden_dim,
            classifier_hidden_dim=classifier_hidden_dim
        )

        self.visual_model.load_state_dict(checkpoint["model_state_dict"])
        self.visual_model = self.visual_model.to(self.device)
        self.visual_model.eval()
        self.audio_model = ai_audio_classifier()

    async def analyse(self, video_path: str | Path, threshold: float = 0.5) -> dict:
        video_path = Path(video_path)

        video = read_video_frames(video_path, num_frames=self.num_frames)

        video = video.unsqueeze(0).to(self.device)

        audio_path = extract_audio_from_video(video_path)

        visual_task = asyncio.to_thread(
            predict_probability,
            self.visual_model,
            video
        )

        if audio_path is not None:
            try:
                audio_task = asyncio.to_thread(
                    self.audio_model.predict,
                    audio_path
                )

                visual_probability, audio_result = await asyncio.gather(visual_task, audio_task)
                

            except Exception as exc:
                print(
                    f"Audio analysis failed: {exc}"
                )

                visual_probability = (
                    await visual_task
                )

                audio_result = None

            finally:
                Path(audio_path).unlink(missing_ok=True)

        else:
            visual_probability = await visual_task
            audio_result = None

        visual_prediction = "AI-generated" if visual_probability >= threshold else "Authentic"
        
        if audio_result is not None:
            audio_probability = float(audio_result["ai_probability"])
            final_probability = VISUAL_WEIGHT*visual_probability+AUDIO_WEIGHT*audio_probability
            
            visual_weight = VISUAL_WEIGHT
            audio_weight = AUDIO_WEIGHT

        else:
            audio_probability = None

            final_probability = (
                visual_probability
            )

            visual_weight = 1.0
            audio_weight = 0.0

        final_prediction = (
            "AI-generated"
            if final_probability >= threshold
            else "Authentic"
        )

        frame_results = calculate_frame_importance(
                self.visual_model,
                video,
                visual_probability,
                visual_prediction
            )

        visual_explanation = build_explanation(
            visual_prediction,
            visual_probability,
            frame_results
        )
        
        strongest_frame = max(frame_results, key=lambda item: item["importance"])

        return {
            "prediction":final_prediction,
            "ai_probability": final_probability,
            "authentic_probability": 1.0 - final_probability,

            "visual": {
                "prediction": visual_prediction,
                "ai_probability": visual_probability,
                "authentic_probability": 1.0 - visual_probability,
                "explanation": visual_explanation,
                "most_influential_frame": strongest_frame,
                "frame_importance": frame_results
            },

            "audio": (
                audio_result
                if audio_result is not None
                else {
                    "available": False
                }
            ),

            "fusion": {
                "visual_weight": visual_weight,
                "audio_weight": audio_weight
            }
        }

