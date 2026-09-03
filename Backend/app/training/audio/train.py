from pathlib import Path

import torch
from torch.utils.data import DataLoader
from torch.optim import AdamW

from app.training.audio.model import model, feature_extractor, device
from app.training.audio.dataset import audio_dataset

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATASET_ROOT = PROJECT_ROOT/ "dataset"/ "audio"

TRAIN_DIR = DATASET_ROOT / "train"
VALIDATION_DIR = DATASET_ROOT / "validation"

OUTPUT_DIR = PROJECT_ROOT/ "models"/ "audio"

BATCH_SIZE = 16
EPOCHS = 3
LEARNING_RATE = 3e-5

train_dataset = audio_dataset(TRAIN_DIR, feature_extractor)
validation_dataset = audio_dataset(VALIDATION_DIR, feature_extractor)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
validation_loader = DataLoader(validation_dataset, batch_size=BATCH_SIZE, shuffle=False)

optimizer = AdamW(model.parameters(),lr=LEARNING_RATE)

def validate():
    model.eval()
    correct = 0
    total = 0

    with torch.no_grad():
        for batch in validation_loader:
            input_values = batch["input_values"].to(device)

            labels = batch["labels"].to(device)
            outputs = model(input_values=input_values)
            predictions = outputs.logits.argmax(dim=-1)

            correct += (predictions == labels).sum().item()
            total += labels.size(0)

    if total == 0:
        raise ValueError("Validation dataset is empty")

    accuracy = correct / total

    print(f"Validation accuracy: {accuracy:.4f}")
    return accuracy
          

def train():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if len(train_loader) == 0:
        raise ValueError("Training dataset is empty")
    best_accuracy = 0
    print(f"Training on: {device}")
    for epoch in range(EPOCHS):
        print(f"\nEpoch {epoch + 1}/{EPOCHS}")
        model.train()

        total_loss = 0

        for batch_number, batch in enumerate(train_loader):
            input_values = batch["input_values"].to(device)
            labels = batch["labels"].to(device)

            optimizer.zero_grad()

            outputs = model(input_values=input_values, labels=labels)

            loss = outputs.loss
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

            if batch_number % 50 == 0:
                print(f"Batch {batch_number} Loss: {loss.item():.4f}")

        average_loss = total_loss / len(train_loader)

        print(f"Training loss: {average_loss:.4f}")

        accuracy = validate()

        if accuracy > best_accuracy:
            best_accuracy = accuracy
            print("Saving best model...")
            model.save_pretrained(OUTPUT_DIR)
            feature_extractor.save_pretrained(OUTPUT_DIR)

    print("\nTraining complete.")
    print(f"Best validation accuracy: {best_accuracy:.4f}")

if __name__ == "__main__":
    train()