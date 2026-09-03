import importlib
import sys
from unittest.mock import MagicMock, patch

import torch
MODULE_PATH = "app.training.audio.predict"

def load_inference_module():
    sys.modules.pop(MODULE_PATH, None)

    with patch("transformers.AutoFeatureExtractor.from_pretrained") as mock_feature_loader, patch("transformers.AutoModelForAudioClassification.from_pretrained") as mock_model_loader:
        mock_feature_extractor = MagicMock()
        mock_model = MagicMock()
        mock_feature_loader.return_value = mock_feature_extractor
        mock_model_loader.return_value = mock_model
        module = importlib.import_module(MODULE_PATH)

    return module

def test_load_model():
    module = load_inference_module()

    mock_model = MagicMock()
    mock_feature_extractor = MagicMock()

    with patch.object(module.AutoFeatureExtractor, "from_pretrained", return_value=mock_feature_extractor) as mock_feature_loader, patch.object(
        module.AutoModelForAudioClassification,
        "from_pretrained",
        return_value=mock_model
    ) as mock_model_loader:
        model, feature_extractor = module.load_model()

    mock_feature_loader.assert_called_once_with(module.OUTPUT_DIR)
    mock_model_loader.assert_called_once_with(module.OUTPUT_DIR)
    mock_model.to.assert_called_once_with(torch.device("cpu"))
    mock_model.eval.assert_called_once()

    assert model is mock_model
    assert feature_extractor is mock_feature_extractor

def test_device_is_cpu():
    module = load_inference_module()
    assert module.device == torch.device("cpu")

def test_output_directory():
    module = load_inference_module()
    assert module.OUTPUT_DIR == (module.PROJECT_ROOT / "models" / "audio")

def test_predict_audio():
    module = load_inference_module()

    fake_audio = [0.1, 0.2, 0.3]

    mock_feature_extractor = MagicMock()
    mock_model = MagicMock()

    input_values = MagicMock()
    attention_mask = MagicMock()

    moved_input_values = MagicMock()
    moved_attention_mask = MagicMock()

    input_values.to.return_value = moved_input_values
    attention_mask.to.return_value = moved_attention_mask

    mock_feature_extractor.return_value = {
        "input_values": input_values,
        "attention_mask": attention_mask
    }

    outputs = MagicMock()
    outputs.logits = torch.tensor([[2.0, 1.0]], dtype=torch.float32)

    mock_model.return_value = outputs

    mock_model.config.id2label = {
        0: "AUTHENTIC",
        1: "AI"
    }

    module.feature_extractor = mock_feature_extractor
    module.model = mock_model

    with patch.object(module.librosa, "load", return_value=(fake_audio, 16000)) as mock_librosa:
        result = module.predict_audio("test.wav")

    mock_librosa.assert_called_once_with("test.wav", sr=16000, mono=True)

    mock_feature_extractor.assert_called_once_with(
        fake_audio,
        sampling_rate=16000,
        return_tensors="pt",
        padding="max_length",
        max_length=64000,
        truncation=True
    )

    input_values.to.assert_called_once_with(torch.device("cpu"))
    attention_mask.to.assert_called_once_with(torch.device("cpu"))
    mock_model.assert_called_once_with(input_values=moved_input_values, attention_mask=moved_attention_mask)

    assert result["label"] == "AUTHENTIC"
    assert result["confidence"] > 0
    assert result["authentic_probability"] > result["ai_probability"]

def test_predict_audio_ai_result():
    module = load_inference_module()

    module.feature_extractor = MagicMock(
        return_value={
            "input_values": torch.tensor([[0.1, 0.2]])
        }
    )

    mock_model = MagicMock()

    outputs = MagicMock()
    outputs.logits = torch.tensor([[0.5, 3.0]], dtype=torch.float32)

    mock_model.return_value = outputs

    mock_model.config.id2label = {
        0: "AUTHENTIC",
        1: "AI"
    }

    module.model = mock_model

    with patch.object(module.librosa, "load", return_value=([0.1, 0.2], 16000)):
        result = module.predict_audio("ai.wav")

    assert result["label"] == "AI"
    assert result["ai_probability"] > result["authentic_probability"]
    assert result["confidence"] == result["ai_probability"]