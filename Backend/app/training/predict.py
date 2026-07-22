from __future__ import annotations

import argparse
import json
import torch

from src.model import AIImageDetector
from app.training.paths import validate_model_path
from src.prediction import predict_and_explain

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description = "Predict whether one image is AI-generated or modified."
    )
    parser.add_argument("image_path")
    parser.add_argument("--model-path", default = "models/best_model.pth")
    parser.add_argument("--output-dir", default = "outputs")
    parser.add_argument("--low-threshold", type = float, default = 0.48)
    parser.add_argument("--high-threshold", type = float, default = 0.70)
    return parser.parse_args()

def main() -> None:
    args = parse_arguments()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = AIImageDetector(
        freeze_features = False,
        use_pretrained_weights = False,
    )

    validate_model_path(args.model_path)
    checkpoint = torch.load(
        args.model_path,
        map_location = device,
        weights_only = True,
    )
    model.load_state_dict(checkpoint["model_state_dict"])

    result = predict_and_explain(
        model = model,
        image_path = args.image_path,
        device = device,
        output_directory = args.output_dir,
        low_threshold = args.low_threshold,
        high_threshold = args.high_threshold,
    )

    print(json.dumps(result, indent = 2))

    if __name__ == "__main__":
        main()