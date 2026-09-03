from __future__ import annotations
from pathlib import Path
import torch
from app.training.image.model import AIImageDetector as TrainedAIImageDetector
from app.training.image.prediction import predict_and_explain
from app.training.pdf.explain import explain_pdf, load_detector
from app.training.video.analyser import video_combined_analysis

MODEL_PATH = Path("app/ai/best_model.pth")
PDF_MODEL_PATH = Path("app/ai/pdf_detector.pt")

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

class AIPDFDetector:
    def __init__(self) -> None:
        self.model_path = PDF_MODEL_PATH
        load_detector(str(self.model_path))

    def analyse_pdf(self, pdf_path: str | Path):
        pdf_path = Path(pdf_path)

        result = explain_pdf(pdf_path, str(self.model_path))

        ai_probability = result["ai_probability"]

        if ai_probability >= 0.80:
            risk_level = 3
        elif ai_probability >= 0.60:
            risk_level = 2
        else:
            risk_level = 1

        result["risk_level"] = risk_level
        return result

class AIVideoDetector:
    def __init__(self) -> None:
        self.model = video_combined_analysis()

    async def analyse_video(self, video_path: str | Path) -> dict:
        video_path = Path(video_path)
        result = await self.model.analyse(video_path)

        ai_probability = result["ai_probability"]

        if ai_probability >= 0.80:
            risk_level = 3
        elif ai_probability >= 0.60:
            risk_level = 2
        else:
            risk_level = 1

        result["risk_level"] = risk_level

        return result