from __future__ import annotations

import sys
import pytest
from unittest.mock import MagicMock, patch

for _mod in ["torch", "torch.nn", "src", "src.data","src.model", "src.metrics"]:
    sys.modules.setdefault(_mod, MagicMock())

from app.training.evaluate import parse_arguments, main

def test_parse_arguments_returns_default_data_dir() -> None:
    with patch("sys.argv", ["evaluate.py"]):
        args = parse_arguments()
    assert args.data_dir == "data"

def test_parse_arguments_returns_default_model_path() -> None:
    with patch("sys.argv", ["evaluate.py"]):
        args = parse_arguments()
    assert args.model_path == "models/best_model.pth"

def test_parse_arguments_returns_default_batch_size() -> None:
    with patch("sys.argv", ["evaluate.py"]):
        args = parse_arguments()
    assert args.batch_size == 16

def test_parse_arguments_returns_default_num_workers() -> None:
    with patch("sys.argv", ["evaluate.py"]):
        args = parse_arguments()
    assert args.num_workers == 0

def test_parse_arguments_accepts_custom_data_dir() -> None:
    with patch("sys.argv", ["evaluate.py", "--data-dir", "custom/data"]):
        args = parse_arguments()
    assert args.data_dir == "custom/data"

def test_parse_arguments_accepts_custom_model_path() -> None:
    with patch("sys.argv", ["evaluate.py", "--model-path", "custom/model.pth"]):
        args = parse_arguments()
    assert args.model_path == "custom/model.pth"

def test_parse_arguments_accepts_custom_batch_size() -> None:
    with patch("sys.argv", ["evaluate.py", "--batch-size", "32"]):
        args = parse_arguments()
    assert args.batch_size == 32

def test_parse_arguments_accepts_custom_num_workers() -> None:
    with patch("sys.argv", ["evaluate.py", "--num-workers", "4"]):
        args = parse_arguments()
    assert args.num_workers == 4

def test_parse_arguments_batch_size_is_integer() -> None:
    with patch("sys.argv", ["evaluate.py", "--batch-size", "8"]):
        args = parse_arguments()
    assert isinstance(args.batch_size, int)

def test_parse_arguments_num_workers_is_integer() -> None:
    with patch("sys.argv", ["evaluate.py", "--num-workers", "2"]):
        args = parse_arguments()
    assert isinstance(args.num_workers, int)

def _make_mock_evaluation_result(roc_auc: float | None = 0.95) -> MagicMock:
    result = MagicMock()
    result.loss = 0.25
    result.accuracy = 0.92
    result.precision = 0.91
    result.recall = 0.90
    result.f1 = 0.905
    result.roc_auc = roc_auc
    result.confusion_matrix = [[10, 1], [2, 9]]
    result.classification_report = "mock classification report"
    return result


@pytest.fixture
def evaluate_mocks():
    mock_train = MagicMock()
    mock_val = MagicMock()
    mock_test = MagicMock()
    mock_result = _make_mock_evaluation_result()

    with (
        patch("app.training.evaluate.create_data_loaders") as mock_loaders,
        patch("app.training.evaluate.AIImageDetector") as mock_model_class,
        patch("app.training.evaluate.torch.load") as mock_torch_load,
        patch("app.training.evaluate.evaluate_model") as mock_evaluate_model,
    ):
        mock_loaders.return_value = (mock_train, mock_val, mock_test)
        mock_model = MagicMock()
        mock_model_class.return_value.to.return_value = mock_model
        mock_torch_load.return_value = {"model_state_dict": MagicMock()}
        mock_evaluate_model.return_value = mock_result

        yield {
            "mock_loaders": mock_loaders,
            "mock_model": mock_model,
            "mock_model_class": mock_model_class,
            "mock_torch_load": mock_torch_load,
            "mock_evaluate_model": mock_evaluate_model,
            "mock_test_loader": mock_test,
            "mock_result": mock_result,
        }

def test_main_calls_evaluate_model(evaluate_mocks, tmp_path) -> None:
    with patch("sys.argv", ["evaluate.py", "--data-dir", str(tmp_path), "--model-path", "model.pth"]):
        main()
    evaluate_mocks["mock_evaluate_model"].assert_called_once()

def test_main_passes_test_loader_to_evaluate_model(evaluate_mocks, tmp_path) -> None:
    with patch("sys.argv", ["evaluate.py", "--data-dir", str(tmp_path), "--model-path", "model.pth"]):
        main()
    call_kwargs = evaluate_mocks["mock_evaluate_model"].call_args.kwargs
    assert call_kwargs["data_loader"] == evaluate_mocks["mock_test_loader"]

def test_main_loads_checkpoint_from_model_path(evaluate_mocks, tmp_path) -> None:
    with patch("sys.argv", ["evaluate.py", "--data-dir", str(tmp_path), "--model-path", "my_model.pth"]):
        main()
    evaluate_mocks["mock_torch_load"].assert_called_once()
    assert evaluate_mocks["mock_torch_load"].call_args.args[0] == "my_model.pth"