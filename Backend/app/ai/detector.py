from __future__ import annotations
from pathlib import Path
import torch
from app.training.model import AIImageDetector as TrainedAIImageDetector
from app.training.prediction import predict_and_explain

MODEL_PATH = Path("app/ai/best_model.pth")

class AIImageDetector:
    def __init__(self) -> None:
        self.device = torch.device(
            "cuda"
            if torch.cuda.is_available() 
            else "cpu"
        )

        self.model = TrainedAIImageDetector(
            freeze_features=False,
            use_pretrained_weights=False
        )

        checkpoint = torch.load(
            MODEL_PATH,
            map_location=self.device,
            weights_only=True
        )

        self.model.load_state_dict(
            checkpoint["model_state_dict"]
        )

        self.model = self.model.to(self.device)
        self.model.eval()

    def analyse_image(self, image_path: str | Path, output_directory: str | Path | None = None) -> dict:
        if output_directory is None:
            output_directory = image_path.parent / "outputs"

        result = predict_and_explain(
            model=self.model,
            image_path=image_path,
            device=self.device,
            output_directory=output_directory
        )

        risk_mapping = {
            "LOW": 1,
            "MEDIUM": 2,
            "HIGH": 3
        }

        result["risk_level"] = risk_mapping[result["risk_level"]]
        return result