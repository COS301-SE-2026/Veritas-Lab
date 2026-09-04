import importlib
import sys
from unittest.mock import MagicMock, patch

import torch

def load_model_module():
    sys.modules.pop("app.training.audio.model", None)
    return importlib.import_module("app.training.audio.model")

@patch("transformers.AutoModelForAudioClassification.from_pretrained")
@patch("transformers.AutoFeatureExtractor.from_pretrained")
def test_model_initialisation(mock_feature_extractor_from_pretrained, mock_model_from_pretrained):
    mock_feature_extractor = MagicMock()
    mock_model = MagicMock()
    mock_feature_extractor_from_pretrained.return_value = mock_feature_extractor
    mock_model_from_pretrained.return_value = mock_model
    mock_model.wavlm.parameters.return_value = []
    module = load_model_module()
    mock_feature_extractor_from_pretrained.assert_called_once_with("microsoft/wavlm-base")
    mock_model_from_pretrained.assert_called_once_with("microsoft/wavlm-base", num_labels=2)

    assert module.feature_extractor is mock_feature_extractor
    assert module.model is mock_model
    assert module.device == torch.device("cpu")

@patch("transformers.AutoModelForAudioClassification.from_pretrained")
@patch("transformers.AutoFeatureExtractor.from_pretrained")
def test_model_configuration(mock_feature_extractor_from_pretrained, mock_model_from_pretrained):
    mock_model = MagicMock()
    mock_model_from_pretrained.return_value = mock_model

    param1 = MagicMock()
    param2 = MagicMock()

    param1.requires_grad = True
    param2.requires_grad = True

    mock_model.wavlm.parameters.return_value = [param1, param2]

    module = load_model_module()

    assert module.model.config.id2label == {
        0: "AUTHENTIC",
        1: "AI"
    }

    assert module.model.config.label2id == {
        "AUTHENTIC": 0,
        "AI": 1
    }

    assert param1.requires_grad is False
    assert param2.requires_grad is False

@patch("transformers.AutoModelForAudioClassification.from_pretrained")
@patch("transformers.AutoFeatureExtractor.from_pretrained")
def test_model_moved_to_cpu(mock_feature_extractor_from_pretrained, mock_model_from_pretrained):
    mock_model = MagicMock()
    mock_model_from_pretrained.return_value = mock_model
    mock_model.wavlm.parameters.return_value = []
    load_model_module()
    mock_model.to.assert_called_once_with(torch.device("cpu"))