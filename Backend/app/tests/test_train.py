from __future__ import annotations

import sys
import pytest
from unittest.mock import MagicMock, patch

for _mod in ["torch", "torch.nn", "torch.optim", "src", "src.data","src.model", "src.metrics", "src.training"]:
    sys.modules.setdefault(_mod, MagicMock())

from app.training.train import parse_arguments, main

def test_parse_arguments_returns_default_data_dir() -> None:
    with patch("sys.argv", ["train.py"]):
        args = parse_arguments()
    assert args.data_dir == "data"

def test_parse_arguments_returns_default_model_path() -> None:
    with patch("sys.argv", ["train.py"]):
        args = parse_arguments()
    assert args.model_path == "models/best_model.pth"

def test_parse_arguments_returns_default_epochs() -> None:
    with patch("sys.argv", ["train.py"]):
        args = parse_arguments()
    assert args.epochs == 10

def test_parse_arguments_returns_default_batch_size() -> None:
    with patch("sys.argv", ["train.py"]):
        args = parse_arguments()
    assert args.batch_size == 16

def test_parse_arguments_returns_default_learning_rate() -> None:
    with patch("sys.argv", ["train.py"]):
        args = parse_arguments()
    assert args.learning_rate == pytest.approx(0.001)

def test_parse_arguments_returns_default_num_workers() -> None:
    with patch("sys.argv", ["train.py"]):
        args = parse_arguments()
    assert args.num_workers == 0

def test_parse_arguments_returns_default_unfreeze_after() -> None:
    with patch("sys.argv", ["train.py"]):
        args = parse_arguments()
    assert args.unfreeze_after == 5

def test_parse_arguments_accepts_custom_data_dir() -> None:
    with patch("sys.argv", ["train.py", "--data-dir", "custom/data"]):
        args = parse_arguments()
    assert args.data_dir == "custom/data"

def test_parse_arguments_accepts_custom_model_path() -> None:
    with patch("sys.argv", ["train.py", "--model-path", "custom/model.pth"]):
        args = parse_arguments()
    assert args.model_path == "custom/model.pth"

def test_parse_arguments_accepts_custom_epochs() -> None:
    with patch("sys.argv", ["train.py", "--epochs", "20"]):
        args = parse_arguments()
    assert args.epochs == 20

def test_parse_arguments_accepts_custom_batch_size() -> None:
    with patch("sys.argv", ["train.py", "--batch-size", "32"]):
        args = parse_arguments()
    assert args.batch_size == 32

def test_parse_arguments_accepts_custom_learning_rate() -> None:
    with patch("sys.argv", ["train.py", "--learning-rate", "0.0001"]):
        args = parse_arguments()
    assert args.learning_rate == pytest.approx(0.0001)

def test_parse_arguments_accepts_custom_num_workers() -> None:
    with patch("sys.argv", ["train.py", "--num-workers", "4"]):
        args = parse_arguments()
    assert args.num_workers == 4

def test_parse_arguments_accepts_custom_unfreeze_after() -> None:
    with patch("sys.argv", ["train.py", "--unfreeze-after", "3"]):
        args = parse_arguments()
    assert args.unfreeze_after == 3

def test_parse_arguments_epochs_is_an_integer() -> None:
    with patch("sys.argv", ["train.py", "--epochs", "5"]):
        args = parse_arguments()
    assert isinstance(args.epochs, int)

def test_parse_arguments_batch_size_is_an_integer() -> None:
    with patch("sys.argv", ["train.py", "--batch-size", "8"]):
        args = parse_arguments()
    assert isinstance(args.batch_size, int)

def test_parse_arguments_learning_rate_is_a_float() -> None:
    with patch("sys.argv", ["train.py", "--learning-rate", "0.0001"]):
        args = parse_arguments()
    assert isinstance(args.learning_rate, float)

def test_parse_arguments_num_workers_is_an_integer() -> None:
    with patch("sys.argv", ["train.py", "--num-workers", "4"]):
        args = parse_arguments()
    assert isinstance(args.num_workers, int)

def test_parse_arguments_unfreeze_after_is_an_integer() -> None:
    with patch("sys.argv", ["train.py", "--unfreeze-after", "3"]):
        args = parse_arguments()
    assert isinstance(args.unfreeze_after, int)

def _make_mock_validation_result(loss: float = 0.30) -> MagicMock:
    result = MagicMock()
    result.loss = loss
    result.accuracy = 0.88
    result.f1 = 0.87
    return result

@pytest.fixture()
def train_mocks():
    mock_train_loader = MagicMock()
    mock_val_loader = MagicMock()
    mock_validation_result = _make_mock_validation_result()

    with (
        patch("app.training.train.create_data_loaders") as mock_loaders,
        patch("app.training.train.AIImageDetector") as mock_model_class,
        patch("app.training.train.Adam") as mock_adam,
        patch("app.training.train.train_one_epoch") as mock_train_epoch,
        patch("app.training.train.evaluate_model") as mock_evaluate_model,
        patch("app.training.train.torch.save") as mock_torch_save,
    ):
        mock_loaders.return_value = (mock_train_loader, mock_val_loader, MagicMock())
        mock_model = MagicMock()
        mock_model_class.return_value.to.return_value = mock_model
        mock_train_epoch.return_value = 0.35
        mock_evaluate_model.return_value = mock_validation_result

        yield {
            "mock_loaders": mock_loaders,
            "mock_model_class": mock_model_class,
            "mock_adam": mock_adam,
            "mock_model": mock_model,
            "mock_train_epoch": mock_train_epoch,
            "mock_evaluate_model": mock_evaluate_model,
            "mock_torch_save": mock_torch_save,
            "mock_train_loader": mock_train_loader,
            "mock_val_loader": mock_val_loader,
            "mock_validation_result": mock_validation_result,
        }

def test_main_creates_model_with_frozen_features_enabled(train_mocks, tmp_path) -> None:
    with patch("sys.argv", ["train.py", "--data-dir", str(tmp_path), "--model-path", str(tmp_path / "model.pth"), "--epochs", "1"]):
        main()
    train_mocks["mock_model_class"].assert_called_once_with(
        freeze_features=True,
        use_pretrained_weights=True,
    )

def test_main_calls_train_one_epoch_each_epoch(train_mocks, tmp_path) -> None:
    with patch("sys.argv", ["train.py", "--data-dir", str(tmp_path), "--model-path", str(tmp_path / "model.pth"), "--epochs", "3", "--unfreeze-after", "10"]):
        main()
    assert train_mocks["mock_train_epoch"].call_count == 3

def test_main_calls_evaluate_model_each_epoch(train_mocks, tmp_path) -> None:
    with patch("sys.argv", ["train.py", "--data-dir", str(tmp_path), "--model-path", str(tmp_path / "model.pth"), "--epochs", "3", "--unfreeze-after", "10"]):
        main()
    assert train_mocks["mock_evaluate_model"].call_count == 3

def test_main_passes_train_loader_to_train_one_epoch(train_mocks, tmp_path) -> None:
    with patch("sys.argv", ["train.py", "--data-dir", str(tmp_path), "--model-path", str(tmp_path / "model.pth"), "--epochs", "1", "--unfreeze-after", "10"]):
        main()
    call_kwargs = train_mocks["mock_train_epoch"].call_args.kwargs
    assert call_kwargs["data_loader"] is train_mocks["mock_train_loader"]


def test_main_passes_val_loader_to_evaluate_model(train_mocks, tmp_path) -> None:
    with patch("sys.argv", ["train.py", "--data-dir", str(tmp_path), "--model-path", str(tmp_path / "model.pth"), "--epochs", "1", "--unfreeze-after", "10"]):
        main()
    call_kwargs = train_mocks["mock_evaluate_model"].call_args.kwargs
    assert call_kwargs["data_loader"] is train_mocks["mock_val_loader"]

def test_main_saves_model_when_validation_loss_improves(train_mocks, tmp_path) -> None:
    train_mocks["mock_validation_result"].loss = 0.25
    with patch("sys.argv", ["train.py", "--data-dir", str(tmp_path), "--model-path", str(tmp_path / "model.pth"), "--epochs", "1", "--unfreeze-after", "10"]):
        main()
    train_mocks["mock_torch_save"].assert_called_once()

def test_main_saves_model_state_dict_in_checkout(train_mocks, tmp_path) -> None:
    model_path = tmp_path / "model.pth"
    with patch("sys.argv", ["train.py", "--data-dir", str(tmp_path), "--model-path", str(tmp_path / "model.pth"), "--epochs", "1", "--unfreeze-after", "10"]):
        main()
    saved_state_dict = train_mocks["mock_torch_save"].call_args.args[0]
    assert "model_state_dict" in saved_state_dict
    
def test_main_unfreezes_features_after_specified_epoch(train_mocks, tmp_path) -> None:
    with patch("sys.argv", ["train.py", "--data-dir", str(tmp_path), "--model-path", str(tmp_path / "model.pth"), "--epochs", "4", "--unfreeze-after", "2"]):
        main()
    train_mocks["mock_model"].unfreeze_features.assert_called_once()


def test_main_does_not_unfreeze_features_before_specified_epoch(train_mocks, tmp_path) -> None:
    with patch("sys.argv", ["train.py", "--data-dir", str(tmp_path), "--model-path", str(tmp_path / "model.pth"), "--epochs", "2", "--unfreeze-after", "5"]):
        main()
    train_mocks["mock_model"].unfreeze_features.assert_not_called()

def test_main_passes_batch_size_to_create_data_loaders(train_mocks, tmp_path) -> None:
    with patch("sys.argv", ["train.py", "--data-dir", str(tmp_path), "--model-path", str(tmp_path / "model.pth"), "--epochs", "1", "--unfreeze-after", "5"]):
        main()
    call_kwargs = train_mocks["mock_loaders"].call_args.kwargs
    assert call_kwargs["batch_size"] == 16

def test_main_checkout_includes_epoch_number(train_mocks, tmp_path) -> None:
    model_path = tmp_path / "model.pth"
    with patch("sys.argv", ["train.py", "--data-dir", str(tmp_path), "--model-path", str(model_path), "--epochs", "1", "--unfreeze-after", "10"]):
        main()
    saved_state_dict = train_mocks["mock_torch_save"].call_args.args[0]
    assert "epoch" in saved_state_dict

def test_main_checkout_includes_class_mapping(train_mocks, tmp_path) -> None:
    model_path = tmp_path / "model.pth"
    with patch("sys.argv", ["train.py", "--data-dir", str(tmp_path), "--model-path", str(model_path), "--epochs", "1", "--unfreeze-after", "10"]):
        main()
    saved_state_dict = train_mocks["mock_torch_save"].call_args.args[0]
    assert saved_state_dict["class_mapping"] == {"0_authentic": 0, "1_ai": 1}