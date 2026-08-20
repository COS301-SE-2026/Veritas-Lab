import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from PIL import Image
import Backend.app.training.image.predict_validation as predict_validation

def create_test_image(path: Path) -> None:
    Image.new(
        mode="RGB",
        size=(50,50),
        color=(100,150,200)
    ).save(path)

def test_main_processes_validation_images(tmp_path: Path):
    dataset_directory = tmp_path / "validation"
    authentic_directory = dataset_directory / "0_authentic"
    ai_directory = dataset_directory/ "1_ai"

    authentic_directory.mkdir(parents=True)
    ai_directory.mkdir(parents=True)

    create_test_image(authentic_directory / "authentic.jpg")
    create_test_image(ai_directory / "ai.jpg")

    output_directory = tmp_path / "outputs"
    model_path = tmp_path / "best_model.pth"

    mock_model = MagicMock()
    mock_model.to.return_value = mock_model

    def mock_prediction(model, image_path, device, output_directory):
        return {
            "image": str(image_path),
            "ai_probability": 80
        }

    with (
        patch.object(predict_validation, "DATASET_DIRECTORY", dataset_directory),
        patch.object(predict_validation, "OUTPUT_DIRECTORY", output_directory),
        patch.object(predict_validation, "MODEL_PATH", model_path),
        patch("app.training.predict_validation.AIImageDetector", return_value=mock_model) as mock_model_class,
        patch("app.training.predict_validation.torch.load", return_value={"model_state_dict": MagicMock()}) as mock_load,
        patch("app.training.predict_validation.predict_and_explain", side_effect=mock_prediction) as mock_predict
    ):
        predict_validation.main()

    mock_model_class.assert_called_once_with(
        freeze_features=False,
        use_pretrained_weights=False
    )

    mock_load.assert_called_once()

    mock_model.load_state_dict.assert_called_once()
    mock_model.eval.assert_called_once()

    assert mock_predict.call_count == 2

    results_path = (output_directory / "validation_results.json")

    assert results_path.exists()
    with results_path.open(
        "r",
        encoding="utf-8"
    ) as file:
        results = json.load(file)

    assert len(results) == 2

    actual_classes = {
        result["actual_class"]
        for result in results
    }

    assert actual_classes == {
        "0_authentic",
        "1_ai"
    }

def test_main_continues_when_image_prediction_fails(tmp_path: Path):
    dataset_directory = tmp_path / "validation"
    ai_directory = dataset_directory/"1_ai"
    ai_directory.mkdir(parents=True)

    create_test_image(ai_directory/"broken.jpg")

    output_directory = tmp_path/"outputs"

    mock_model = MagicMock()
    mock_model.to.return_value = mock_model

    with (
        patch.object(predict_validation, "DATASET_DIRECTORY", dataset_directory),
        patch.object(predict_validation, "OUTPUT_DIRECTORY", output_directory),
        patch("app.training.predict_validation.AIImageDetector",  return_value=mock_model),
        patch("app.training.predict_validation.torch.load", return_value={"model_state_dict": MagicMock()}),
        patch("app.training.predict_validation.predict_and_explain", side_effect=RuntimeError("Prediction failed"))
    ):
        predict_validation.main()

    results_path = (output_directory / "validation_results.json")

    assert results_path.exists()
    with results_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        results = json.load(file)

    assert results == []