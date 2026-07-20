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

