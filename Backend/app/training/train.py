from __future__ import annotations

import argparse
from pathlib import Path
import torch
from torch import nn
import torch optim import Adam

from src.data import create_data_loaders
from src.metrics import evaluate_model
from src.model import AIImageDetector
from src.training import train_one_epoch

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description = "Train the AI image detector.")
    parser.add_argument("--dta-dir", default = "data")
    parser.add_argument("--model-path", default = "models/best_model.pth")
    parser.add_argument("--epochs", type = int, default = 10)
    parser.add_argument("--batch-size", type = int, default = 16)
    parser.add_argument("--learning-rate", type = float, default = 0.001)
    parser.add_argument("--num-workers", type = int, default = 0)
    parser.add_argument(
        "--unfreeze-after",
        type = int,
        default = 5,
        help = "Epoch after which EfficientNet feature layers are unfrozen.",
    )
    return parser.parse_args()

    def main() -> None:
        args = parse_arguments()

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {device}")

        train_loader, validation_loader, _ = create_data_loaders(
            data_directory = args.data_dir,
            batch_size = args.batch_size,
            num_workers = args.num_workers,
        )

        model = AIImageDetector(
            freeze_features = True,
            use_pretrained_weights = True,
        ).to(device) # move the model to the device that we chose

        loss_function = nn.BCEWithLogitsLoss()
        optimizer = Adam(
            filter(lambda paramter: parameter.requires_grad, model.parameters()),
            lr = args.learning_rate,
            #Here we say which parts of the model that's allowed to learn to updtae
        )

        best_validation_loss = float ("inf")
        model_path = Path(args.model_path)
        model_path.parent.mkdir(parents = True, exist_ok = True)

       