import argparse
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from app.training.video.dataset import video_binary_dataset
from app.training.video.model import ai_video_classifier

def calculate_accuracy(logits, labels):
    predictions = (torch.sigmoid(logits) >= 0.5).float()
    return (predictions == labels).float().mean().item()

def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()

    total_loss = 0.0
    total_accuracy = 0.0

    for batch in loader:
        videos = batch["video"].to(device)
        labels = batch["label"].to(device)

        optimizer.zero_grad()

        logits = model(videos)

        loss = criterion(logits, labels)

        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        total_accuracy += calculate_accuracy(logits, labels)

    return (
        total_loss/len(loader),
        total_accuracy/len(loader)
    )

def validate(model, loader, criterion, device):
    model.eval()

    total_loss = 0.0
    total_accuracy = 0.0

    with torch.no_grad():
        for batch in loader:
            videos = batch["video"].to(device)
            labels = batch["label"].to(device)

            logits = model(videos)

            loss = criterion(logits, labels)

            total_loss += loss.item()
            total_accuracy += calculate_accuracy(logits, labels)

    return (
        total_loss/len(loader),
        total_accuracy/len(loader)
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", default="dataset/video")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--num-frames", type=int, default=8)
    parser.add_argument("--zones", type=int, default=2)
    parser.add_argument("--checkpoint", default="best_video_model.pt")

    args = parser.parse_args()
    device = torch.device("cpu")
    print(f"Device: {device}")

    data_root = Path(args.data_root)
    train_dataset = video_binary_dataset(data_root/"train", num_frames=args.num_frames)
    validation_dataset = video_binary_dataset(data_root / "validation", num_frames=args.num_frames)
    test_dataset = video_binary_dataset(data_root/"test", num_frames=args.num_frames)

    print(f"Training videos: {len(train_dataset)}")
    print(f"Validation videos: {len(validation_dataset)}")
    print(f"Test videos: {len(test_dataset)}")

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0
    )

    validation_loader = DataLoader(
        validation_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0
    )

    model = ai_video_classifier(
        num_frames=args.num_frames,
        zones_per_dim=args.zones,
        freeze_encoder=True,
        temporal_hidden_dim=256,
        classifier_hidden_dim=256
    )

    model.to(device)
    criterion = nn.BCEWithLogitsLoss()

    optimizer = torch.optim.AdamW(
        (
            parameter
            for parameter in model.parameters()
            if parameter.requires_grad
        ),
        lr=args.learning_rate,
        weight_decay=1e-4
    )

    best_validation_loss = float("inf")

    for epoch in range(1, args.epochs + 1):
        train_loss, train_accuracy = train_one_epoch(model, train_loader, criterion, optimizer, device)
        validation_loss, validation_accuracy = validate(model, validation_loader, criterion, device)

        print(
            f"Epoch {epoch}/{args.epochs}\n"
            f"Train loss: {train_loss:.4f}\n"
            f"Train accuracy: {train_accuracy * 100:.2f}%\n"
            f"Validation loss: {validation_loss:.4f}\n"
            f"Validation accuracy: {validation_accuracy * 100:.2f}%\n"
        )

        if validation_loss < best_validation_loss:
            best_validation_loss = validation_loss

            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "num_frames": args.num_frames,
                    "zones": args.zones,
                    "temporal_hidden_dim": 256,
                    "classifier_hidden_dim": 256,
                    "validation_loss": validation_loss,
                    "epoch": epoch
                },
                args.checkpoint
            )

            print(f"Saved best model: {args.checkpoint}")


    print("\nLoading best checkpoint...")
    checkpoint = torch.load(args.checkpoint, map_location=device, weights_only=True)

    model.load_state_dict(checkpoint["model_state_dict"])
    test_loss, test_accuracy = validate(model, test_loader, criterion, device)

    print("\nTEST RESULTS")
    print(f"Loss: {test_loss:.4f}")
    print(f"Accuracy: {test_accuracy * 100:.2f}%")

if __name__ == "__main__":
    main()