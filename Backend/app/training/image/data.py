from __future__ import annotations
from pathlib import Path
import torch 
from torch.utils.data import DataLoader
from torchvision import transforms
from torchvision.datasets import ImageFolder
from torchvision.models import EfficientNet_B0_Weights

# The Batch Size is the no. of images it loads at a time. So 100 images with batch size = 10 will be 100/10 = 10 loads

EXPECTED_CLASS_MAPPING = {
    "0_authentic":0,
    "1_ai": 1
}

def get_train_transform() ->transforms.Compose:
    weights = EfficientNet_B0_Weights.DEFAULT
    evaluation_transform = weights.transforms()

    return transforms.Compose(
        [
            transforms.RandomResizedCrop(224, scale=(0.75, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(degrees=5),
            transforms.ColorJitter(
                brightness=0.1,
                contrast=0.1,
                saturation=0.1,
                hue=0.02
            ),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=evaluation_transform.mean,
                std=evaluation_transform.std
            )
        ]
    )

def get_evaluation_transform() -> transforms.Compose:
    return EfficientNet_B0_Weights.DEFAULT.transforms()

def _validate_dataset(dataset: ImageFolder, split_name: str) -> None:
    if dataset.class_to_idx != EXPECTED_CLASS_MAPPING:
        raise ValueError(
            f"Incorrect class folders for {split_name}. "
            f"Expected {EXPECTED_CLASS_MAPPING}, "
            f"but found {dataset.class_to_idx}."
        )
    
    if len(dataset) == 0:
        raise ValueError(f"No images found in the {split_name} dataset.")
    
def create_data_loaders(
    data_directory: str | Path,
    batch_size: int = 16,
    num_workers: int = 0
) -> tuple[DataLoader, DataLoader, DataLoader]:
    data_directory = Path(data_directory)

    train_dataset = ImageFolder(
        data_directory / "train",
        transform=get_train_transform()
    )

    validation_dataset = ImageFolder(
        data_directory / "validation",
        transform=get_evaluation_transform()
    )

    test_dataset = ImageFolder(
        data_directory / "test",
        transform=get_evaluation_transform()
    )

    _validate_dataset(train_dataset, "training")
    _validate_dataset(validation_dataset, "validation")
    _validate_dataset(test_dataset, "test")

    pin_memory = torch.cuda.is_available()

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=pin_memory
    )

    validation_loader = DataLoader(
        validation_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory
    )

    return train_loader, validation_loader, test_loader

    
