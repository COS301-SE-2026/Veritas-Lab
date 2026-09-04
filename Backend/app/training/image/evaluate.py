from __future__ import annotations

import argparse

import torch
from torch import nn

from app.training.image.data import create_data_loaders
from app.training.image.metrics import evaluate_model
from app.training.image.model import AIImageDetector

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate the AI detector.")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--model-path", default="models/best_model.pth")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--num-workers", type=int, default=0)
    return parser.parse_args()

def main() ->None:
    args = parse_arguments()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    _, _, test_loader = create_data_loaders(
        data_directory=args.data_dir,
        batch_size=args.batch_size,
        num_workers=args.num_workers
    )

    model = AIImageDetector(
        freeze_features=False,
        use_pretrained_weights=False,
    ).to(device)

    checkpoint = torch.load(
        args.model_path,
        map_location=device,
        weights_only=True,
    )
    model.load_state_dict(checkpoint["model_state_dict"])

    model.eval()

    result = evaluate_model(
        model = model,
        data_loader = test_loader,
        loss_function = nn.BCEWithLogitsLoss(),
        device = device,
    )

    print(f"Loss: {result.loss:.4f}")
    print(f"Accuracy: {result.accuracy:.4f}")
    print(f"Precision: {result.precision:.4f}")
    print(f"Recall: {result.recall:.4f}")
    print(f"F1: {result.f1:.4f}")
    print(
        "ROC AUC:   " +
        (f"{result.roc_auc:.4f}"
        if result.roc_auc is not None
        else "Unavailable"
        )
    )

    print(f"Confusion matrix: {result.confusion_matrix}")
    print("\nClassification report:")
    print(result.classification_report)


if __name__ == "__main__":
    main()