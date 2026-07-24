from __future__ import annotations
from pathlib import Path
import torch
from app.training.model import AIImageDetector
from app.training.prediction import predict_and_explain

MODEL_PATH = Path("app/ai/best_model.pth")

class AIDetector:
    def __init__(self) -> None:
        self.device = torch.device(
            "cuda"
            if torch.cuda.is_available() 
            else "cpu"
        )

        self.model = AIImageDetector(
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

    def analyse_image(self, image_path: str | Path) -> dict:
        return predict_and_explain(
            model=self.model,
            image_path=image_path,
            device=self.device
        )