from pathlib import Path
import pytest
import torch
from PIL import Image
from torch.utils.data import RandomSampler, SequentialSampler
from torchvision.datasets import ImageFolder

from training.data import (
    EXPECTED_CLASS_MAPPING,
    _validate_dataset,
    create_data_loaders,
    get_evaluation_transform,
    get_train_transform
)

def create_test_image(
        image_path: Path,
        colour: tuple[int, int, int] = (255,0,0)
) -> None:
    image_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    image = Image.new(
        mode="RGB",
        size=(256,256),
        color=colour
    )

    image.save(image_path)

def create_test_dataset(root_directory: Path) -> None:
    splits = [
        "train",
        "validation",
        "test"
    ]

    for split in splits:
        for index in range(2):
            create_test_image(
                root_directory
                / split
                / "0_authentic"
                / f"authentic_{index}.jpg",
                colour=(255,0,0)
            )

            create_test_image(
                root_directory
                / split
                / "1_ai"
                / f"ai_{index}.jpg",
                colour=(0, 0, 255)
            )

def test_expected_class_mapping() -> None:
    assert EXPECTED_CLASS_MAPPING == {
        "0_authentic": 0,
        "1_ai": 1
    }

def test_train_transform_returns_correc_shape() -> None:
    image = Image.new(
        mode="RGB",
        size=(300,300),
        color=(100,150,200)
    )

    transform = get_train_transform()
    transformed_image= transform(image)

    assert isinstance(transformed_image, torch.Tensor)
    assert transformed_image.shape == (3,224,224)

