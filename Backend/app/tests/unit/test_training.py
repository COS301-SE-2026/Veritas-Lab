from pathlib import Path
import pytest
import torch
from torch import nn
from PIL import Image
from torch.utils.data import RandomSampler, SequentialSampler, DataLoader, TensorDataset
from torchvision.datasets import ImageFolder
from unittest.mock import MagicMock
from Backend.app.training.image.training import train_one_epoch

from Backend.app.training.image.data import (
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

def test_evaluation_transform_returns_correct_shape() -> None:
    image = Image.new(
        mode="RGB",
        size=(300,300),
        color=(100,150,200)
    )

    transform = get_evaluation_transform()
    transformed_image = transform(image)

    assert isinstance(transformed_image, torch.Tensor)
    assert transformed_image.shape == (3,224,224)

def test_validate_dataset_success(tmp_path: Path) -> None:
    create_test_dataset(tmp_path)
    
    dataset = ImageFolder(
        root=tmp_path / "train",
        transform=get_evaluation_transform()
    )

    _validate_dataset(
        dataset,
        "training"
    )

    assert dataset.class_to_idx == EXPECTED_CLASS_MAPPING
    assert len(dataset) == 4

def test_validate_dataset_rejects_incorrect_folder_names(tmp_path: Path) -> None:
    create_test_image(
        tmp_path
        / "train"
        / "authentic"
        / "ai"
        / "ai.jpg"
    )

    dataset = ImageFolder(
        root=tmp_path/ "train",
        transform=get_evaluation_transform()
    )

    with pytest.raises(
        ValueError,
        match="Incorrect class folders"
    ):
        _validate_dataset(
            dataset,
            "training"
        )

def test_validate_dataset_rejects_empty_dataset() -> None:
    dataset = MagicMock(spec=ImageFolder)

    dataset.class_to_idx = EXPECTED_CLASS_MAPPING
    dataset.__len__.return_value = 0

    with pytest.raises(
        ValueError,
        match="No images found"
    ):
        _validate_dataset(
            dataset,
            "training"
        )

def test_create_dataloaders(tmp_path: Path) -> None:
    create_test_dataset(tmp_path)

    train_loader, validation_loader, test_loader = (
        create_data_loaders(
            data_directory=tmp_path,
            batch_size=2,
            num_workers=0
        )
    )

    assert len(train_loader.dataset) == 4
    assert len(validation_loader.dataset) == 4
    assert len(test_loader.dataset) == 4

    assert train_loader.batch_size == 2
    assert validation_loader.batch_size == 2
    assert test_loader.batch_size == 2

def test_data_loader_class_mapping(tmp_path: Path) ->None:
    create_test_dataset(tmp_path)

    train_loader, validation_loader, test_loader = (
        create_data_loaders(
            data_directory=tmp_path,
            batch_size=2,
            num_workers=0
        )
    )

    assert (train_loader.dataset.class_to_idx == EXPECTED_CLASS_MAPPING)
    assert (validation_loader.dataset.class_to_idx == EXPECTED_CLASS_MAPPING)
    assert (test_loader.dataset.class_to_idx == EXPECTED_CLASS_MAPPING)

def test_training_loader_uses_shuffle(tmp_path: Path)->None:
    create_test_dataset(tmp_path)

    train_loader,_,_ = create_data_loaders(
        data_directory=tmp_path,
        batch_size=2,
        num_workers=0
    )

    assert isinstance(
        train_loader.sampler,
        RandomSampler
    )

def test_validation_loader_does_not_shuffle(tmp_path: Path)->None:
    create_test_dataset(tmp_path)

    _,validation_loader,_ = create_data_loaders(
        data_directory=tmp_path,
        batch_size=2,
        num_workers=0
    )

    assert isinstance(
        validation_loader.sampler,
        SequentialSampler
    )

def test_training_batch_shape(tmp_path: Path)->None:
    create_test_dataset(tmp_path)

    train_loader,_,_ = create_data_loaders(
        data_directory=tmp_path,
        batch_size=2,
        num_workers=0
    )

    images, labels = next(iter(train_loader))

    assert isinstance(images, torch.Tensor)
    assert isinstance(labels, torch.Tensor)

    assert images.shape == (2,3,224,224)

    assert labels.shape == (2,)

def test_validation_batch_shape(tmp_path: Path)->None:
    create_test_dataset(tmp_path)

    _,validation_loader, _ = create_data_loaders(
        data_directory=tmp_path,
        batch_size=2,
        num_workers=0
    )

    images,labels= next(iter(validation_loader))

    assert images.shape == (2,3,224,224)
    assert labels.shape == (2,)

def test_batch_shape(tmp_path: Path)->None:
    create_test_dataset(tmp_path)

    _,_,test_loader = create_data_loaders(
        data_directory=tmp_path,
        batch_size=2,
        num_workers=0
    )

    images, labels = next(iter(test_loader))

    assert images.shape == (2,3,224,224)
    assert labels.shape == (2,)

def test_dataset_labels_are_binary(tmp_path: Path) -> None:
    create_test_dataset(tmp_path)

    train_loader,_,_ = (
        create_data_loaders(
            data_directory=tmp_path,
            batch_size=4,
            num_workers=0
        )
    )

    _, labels = next(iter(train_loader))

    assert set(labels.tolist()).issubset({0,1})

def test_batch_size_is_used(tmp_path: Path) -> None:
    create_test_dataset(tmp_path)

    train_loader,_,_ = (
        create_data_loaders(
            data_directory=tmp_path,
            batch_size=3,
            num_workers=0
        )
    )

    images, labels = next(iter(train_loader))

    assert images.shape[0] == 3
    assert labels.shape[0] == 3

def test_test_loader_does_not_shuffle(tmp_path: Path)->None:
    create_test_dataset(tmp_path)

    _,_,test_loader = create_data_loaders(
        data_directory=tmp_path,
        batch_size=2,
        num_workers=0
    )

    assert isinstance(
        test_loader.sampler,
        SequentialSampler
    )

def test_data_loader_uses_requested_number_of_workers(tmp_path: Path) -> None:
    create_test_dataset(tmp_path)

    train_loader,validation_loader,test_loader = (
        create_data_loaders(
            data_directory=tmp_path,
            batch_size=2,
            num_workers=0
        )
    )

    assert train_loader.num_workers == 0
    assert validation_loader.num_workers == 0
    assert test_loader.num_workers == 0

def test_invalid_dataset_directory_raises_error(tmp_path: Path) -> None:
    missing_directory = tmp_path / "missing_dataset"

    with pytest.raises(
        (FileNotFoundError, RuntimeError)
    ):
        create_data_loaders(
            data_directory=missing_directory,
            batch_size=2,
            num_workers=0
        )

def create_loader() -> DataLoader:
    images = torch.tensor(
        [
            [0.0, 0.0],
            [1.0, 1.0],
            [2.0, 2.0],
            [3.0, 3.0]
        ],
        dtype=torch.float32
    )

    labels = torch.tensor([0, 0, 1, 1], dtype=torch.long)

    return DataLoader(
        TensorDataset(images, labels),
        batch_size=2,
        shuffle=False,
    )

def test_train_one_epoch_returns_average_loss():
    model = nn.Linear(2,1)
    loader = create_loader()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)

    loss = train_one_epoch(
        model=model,
        data_loader=loader,
        loss_function=nn.BCEWithLogitsLoss(),
        optimizer=optimizer,
        device=torch.device("cpu")
    )

    assert isinstance(loss, float)
    assert loss >= 0.0
    assert model.training is True

def test_train_one_epoch_updates_model_parameters():
    model = nn.Linear(2,1)
    loader = create_loader()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)

    parameters_before = [
        parameter.detach().clone()
        for parameter in model.parameters()
    ]

    train_one_epoch(
        model=model,
        data_loader=loader,
        loss_function=nn.BCEWithLogitsLoss(),
        optimizer=optimizer,
        device=torch.device("cpu")
    )

    parameters_after = list(model.parameters())

    assert any(
        not torch.equal(before,after)
        for before, after in zip(parameters_before, parameters_after)
    )