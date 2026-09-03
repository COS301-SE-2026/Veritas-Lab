import math
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import torch

from app.training.video.analyser import ai_audio_classifier, video_combined_analysis

def make_checkpoint(num_frames=2, zones=2, temporal_hidden_dim=4, classifier_hidden_dim=4):
    return {
        "num_frames": num_frames,
        "zones": zones,
        "temporal_hidden_dim": temporal_hidden_dim,
        "classifier_hidden_dim": classifier_hidden_dim,
        "model_state_dict": {}
    }

@patch("app.training.video.analyser.AutoModelForAudioClassification.from_pretrained")
@patch("app.training.video.analyser.AutoFeatureExtractor.from_pretrained")
def test_audio_classifier_initialises(mock_feature_extractor_from_pretrained, mock_model_from_pretrained):
    mock_model = MagicMock()
    mock_model.to.return_value = mock_model
    mock_model_from_pretrained.return_value = mock_model

    classifier = ai_audio_classifier(model_path="fake/path", sample_rate=16000, duration_seconds=4)

    mock_feature_extractor_from_pretrained.assert_called_once()
    mock_model_from_pretrained.assert_called_once()
    mock_model.eval.assert_called_once()
    assert classifier.device == torch.device("cpu")

@patch("app.training.video.analyser.librosa.load")
@patch("app.training.video.analyser.AutoModelForAudioClassification.from_pretrained")
@patch("app.training.video.analyser.AutoFeatureExtractor.from_pretrained")
def test_audio_classifier_predict_weight_average(mock_feature_extractor_from_pretrained, mock_model_from_pretrained, mock_librosa_load):
    mock_model = MagicMock()
    mock_model.to.return_value = mock_model
    mock_model_from_pretrained.return_value = mock_model

    # Mock the feature extractor to return a tensor
    mock_feature_extractor = MagicMock()
    mock_feature_extractor.return_value = {"input_values": torch.zeros((1, 4))}
    mock_feature_extractor_from_pretrained.return_value = mock_feature_extractor

    mock_librosa_load.return_value = (np.zeros(6, dtype=np.float32), 4)

    output1 = MagicMock()
    output1.logits = torch.tensor([[math.log(0.2), math.log(0.8)]])

    output2 = MagicMock()
    output2.logits = torch.tensor([[math.log(0.8), math.log(0.2)]])

    mock_model.side_effect = [output1, output2]

    classifier = ai_audio_classifier(model_path="fake/path", sample_rate=4, duration_seconds=1)
    result = classifier.predict("audio.wav")

    assert result["available"] is True
    assert result["prediction"] == "AI-generated"
    assert result["ai_probability"] == pytest.approx(0.6)
    assert result["authentic_probability"] == pytest.approx(0.4)
    assert result["confidence"] == pytest.approx(0.6)

@patch("app.training.video.analyser.librosa.load")
@patch("app.training.video.analyser.AutoModelForAudioClassification.from_pretrained")
@patch("app.training.video.analyser.AutoFeatureExtractor.from_pretrained")
def test_audio_classifier_predict_authentic(
    mock_feature_extractor_from_pretrained,
    mock_model_from_pretrained,
    mock_librosa_load
):
    mock_model = MagicMock()
    mock_model.to.return_value = mock_model
    mock_model_from_pretrained.return_value = mock_model

    mock_feature_extractor = MagicMock()
    mock_feature_extractor.return_value = {"input_values": torch.zeros((1, 4))}
    mock_feature_extractor_from_pretrained.return_value = mock_feature_extractor

    mock_librosa_load.return_value = (np.zeros(4, dtype=np.float32), 4)

    output = MagicMock()
    output.logits = torch.tensor([[math.log(0.9), math.log(0.1)]])
    mock_model.return_value = output

    classifier = ai_audio_classifier(model_path="fake/path", sample_rate=4, duration_seconds=1)
    result = classifier.predict("audio.wav")

    assert result["prediction"] is "Authentic"
    assert result["confidence"] == pytest.approx(0.9)