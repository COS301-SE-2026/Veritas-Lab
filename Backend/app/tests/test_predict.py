from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock, patch


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
    assert args.low_threshold == pytest.approx(0.4)

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

# Helpers for main

def _make_mock_prediction_result() -> dict:
    return {
        "prediction": "ai-generated",
        "confidence": 0.85,
        "label": 1,
    }

@pytest.fixture
def predict_mocks():
    mock_result = _make_mock_prediction_result()
    with (
        patch("app.training.predict.AIImageDetector") as mock_model_class,
        patch("app.training.predict.torch.load") as mock_torch_load,
        patch("app.training.predict.predict_and_explain") as mock_predict,
    ):
        mock_model = MagicMock()
        mock_model.to.return_value = mock_model
        mock_model_class.return_value = mock_model
        mock_torch_load.return_value = {"model_state_dict": MagicMock()}
        mock_predict.return_value = mock_result

        yield {
            "mock_model": mock_model,
            "mock_model_class": mock_model_class,
            "mock_torch_load": mock_torch_load,
            "mock_predict": mock_predict,
            "mock_result": mock_result,
        }

def test_main_calls_predict_and_explain(predict_mocks) -> None:
    with patch("sys.argv", ["predict.py", "images/test.jpg"]):
        main()
    predict_mocks["mock_predict"].assert_called_once()

def test_main_passes_image_path_to_predict_and_explain(predict_mocks) -> None:
    with patch("sys.argv", ["predict.py", "images/test.jpg"]):
        main()
    call_kwargs = predict_mocks["mock_predict"].call_args.kwargs
    assert call_kwargs["image_path"] == "images/test.jpg"

def test_main_passes_output_dir_to_predict_and_explain(predict_mocks) -> None:
    with patch("sys.argv", ["predict.py", "img.jpg", "--output-dir", "results"]):
        main()
    call_kwargs = predict_mocks["mock_predict"].call_args.kwargs
    assert call_kwargs["output_directory"] == "results"

def test_main_passes_low_threshold_to_predict_and_explain(predict_mocks) -> None:
    with patch("sys.argv", ["predict.py", "img.jpg", "--low-threshold", "0.30"]):
        main()
    call_kwargs = predict_mocks["mock_predict"].call_args.kwargs
    assert call_kwargs["low_threshold"] == pytest.approx(0.30)

def test_main_passes_high_threshold_to_predict_and_explain(predict_mocks) -> None:
    with patch("sys.argv", ["predict.py", "img.jpg", "--high-threshold", "0.75"]):
        main()
    call_kwargs = predict_mocks["mock_predict"].call_args.kwargs
    assert call_kwargs["high_threshold"] == pytest.approx(0.75)

def test_main_loads_checkpoint_from_model_path(predict_mocks) -> None:
    with patch("sys.argv", ["predict.py", "img.jpg", "--model-path", "my_model.pth"]):
        main()
    predict_mocks["mock_torch_load"].assert_called_once()
    assert str(predict_mocks["mock_torch_load"].call_args.args[0]) == "my_model.pth"


def test_main_loads_model_state_dict_from_checkpoint(predict_mocks) -> None:
    mock_state = predict_mocks["mock_torch_load"].return_value["model_state_dict"]
    with patch("sys.argv", ["predict.py", "img.jpg"]):
        main()
    predict_mocks["mock_model"].load_state_dict.assert_called_once_with(mock_state)

def test_main_creates_model_with_pretrained_weights_disabled(predict_mocks) -> None:
    with patch("sys.argv", ["predict.py", "img.jpg"]):
        main()
    predict_mocks["mock_model_class"].assert_called_once_with(
        freeze_features = False,
        use_pretrained_weights = False,
    )

def test_main_prints_json_result(predict_mocks, capsys) -> None:
    with patch("sys.argv", ["predict.py", "img.jpg"]):
        main()
    captured = capsys.readouterr().out
    printed_json = json.loads(captured)
    assert printed_json == predict_mocks["mock_result"]

def test_main_passes_model_to_predict_and_explain(predict_mocks) -> None:
    with patch("sys.argv", ["predict.py", "img.jpg"]):
        main()
    call_kwargs = predict_mocks["mock_predict"].call_args.kwargs
    assert call_kwargs["model"] == predict_mocks["mock_model"]