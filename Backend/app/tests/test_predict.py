from __future__ import annotations

import sys
import json
import pytest
from unittest.mock import MagicMock, patch


for _mod in ["torch", "torch.nn", "src", "src.data","src.model", "src.prediction"]:
    sys.modules.setdefault(_mod, MagicMock())

from app.training.predict import parse_arguments, main

def test_parse_arguments_accepts_image_path() -> None:
    with patch("sys.argv", ["predict.py", "images/test.jpg"]):
        args = parse_arguments()
    assert args.image_path == "images/test.jpg"

def test_parse_image_path_is_positional_and_required() -> None:
    with patch("sys.argv", ["predict.py"]):
        with pytest.raises(SystemExit):
            parse_arguments()

def test_parse_arguments_returns_default_model_path() -> None:
    with patch("sys.argv", ["predict.py", "img.jpg"]):
        args = parse_arguments()
    assert args.model_path == "models/best_model.pth"

def test_parse_arguments_returns_default_output_dir() -> None:
    with patch("sys.argv", ["predict.py", "img.jpg"]):
        args = parse_arguments()
    assert args.output_dir == "outputs"

def test_parse_arguments_returns_default_low_threshold() -> None:
    with patch("sys.argv", ["predict.py", "img.jpg"]):
        args = parse_arguments()
    assert args.low_threshold == pytest.approx(0.48)

def test_parse_arguments_returns_default_high_threshold() -> None:
    with patch("sys.argv", ["predict.py", "img.jpg"]):
        args = parse_arguments()
    assert args.high_threshold == pytest.approx(0.70)

def test_parse_arguments_accepts_custom_model_path() -> None:
    with patch("sys.argv", ["predict.py", "img.jpg", "--model-path", "custom/model.pth"]):
        args = parse_arguments()
    assert args.model_path == "custom/model.pth"

def test_parse_arguments_accepts_custom_output_dir() -> None:
    with patch("sys.argv", ["predict.py", "img.jpg", "--output-dir", "results"]):
        args = parse_arguments()
    assert args.output_dir == "results"

def test_parse_arguments_accepts_custom_low_threshold() -> None:
    with patch("sys.argv", ["predict.py", "img.jpg", "--low-threshold", "0.3"]):
        args = parse_arguments()
    assert args.low_threshold == pytest.approx(0.3)

def test_parse_arguments_accepts_custom_high_threshold() -> None:
    with patch("sys.argv", ["predict.py", "img.jpg", "--high-threshold", "0.8"]):
        args = parse_arguments()
    assert args.high_threshold == pytest.approx(0.8)

def test_parse_arguments_low_threshold_is_float() -> None:
    with patch("sys.argv", ["predict.py", "img.jpg", "--low-threshold", "0.50"]):
        args = parse_arguments()
    assert isinstance(args.low_threshold, float)

def test_parse_arguments_high_threshold_is_float() -> None:
    with patch("sys.argv", ["predict.py", "img.jpg", "--high-threshold", "0.75"]):
        args = parse_arguments()
    assert isinstance(args.high_threshold, float)