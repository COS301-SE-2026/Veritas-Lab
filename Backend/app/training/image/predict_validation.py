from __future__ import annotations
import json
from pathlib import Path
import torch
from Backend.app.training.image.model import AIImageDetector
from Backend.app.training.image.prediction import predict_and_explain

DATASET_DIRECTORY =Path("../dataset/validation")
MODEL_PATH = Path("app/ai/best_model.pth")
OUTPUT_DIRECTORY = Path("outputs/validation")

IMAGE_EXTENSIONS = {
    ".jpg",
    ".png",
    ".jpeg",
    ".webp",
    ".bmp"
}

def main()-> None:
    device = torch.device(
        "cuda"
        if torch.cuda.is_available() else
        "cpu"
    )

    print(f"Using device: {device}")

    model = AIImageDetector(
        freeze_features=False,
        use_pretrained_weights=False
    )

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=device,
        weights_only=True
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model=model.to(device)
    model.eval()

    image_paths = [
        path
        for path in DATASET_DIRECTORY.rglob("*")
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
    ]

    print(f"Found {len(image_paths)} images.")

    results = []

    for index, image_path in enumerate(
        image_paths,
        start=1
    ):
        print(
            f"[{index}/{len(image_paths)}] "
            f"Processing {image_path}"
        )

        try:
            class_output_directory = (OUTPUT_DIRECTORY / image_path.parent.name)

            result = predict_and_explain(
                model=model,
                image_path=image_path,
                device=device,
                output_directory=class_output_directory
            )

            result["actual_class"] = image_path.parent.name
            results.append(result)

        except Exception as error:
            print(
                f"Failed to process {image_path}: "
                f"{error}"
            )

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    results_path = (OUTPUT_DIRECTORY / "validation_results.json")

    with results_path.open(
        "w",
        encoding="utf-8"
    )as file:
        json.dump(
            results,
            file,
            indent=2
        )

    print()
    print("Finished.")
    print(f"Results saved to: {results_path}")

if __name__ == "__main__":
    main()