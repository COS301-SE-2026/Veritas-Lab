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
def test_audio_classifier_initialisation(mock_feature_extractor_from_pretrained, mock_model_from_pretrained):
    mock_model = MagicMock()
    mock_model.to.return_value = mock_model
    mock_model_from_pretrained.return_value = mock_model

    classifier = ai_audio_classifier(model_path="fake/path", sample_rate=16000, duration_seconds=4)

    mock_feature_extractor_from_pretrained.assert_called_once()
    mock_model_from_pretrained.assert_called_once()
    mock_model.eval.assert_called_once()
    assert classifier.device == torch.device("cpu")

@patch("app.training.video.analyser.librosa.load")
@patch("app.training.video.analyser.AutoForAudioClassification.from_pretrained")
@patch("app.training.video.analyser.AutoFeatureExtractor.from_pretrained")
def test_audio_classifier_predict(mock_feature_extractor_from_pretrained, mock_model_from_pretrained, mock_librosa_load):
    mock_model = MagicMock()
    mock_model.to.return_value = mock_model
    mock_model_from_pretrained.return_value = mock_model

    # Mock the feature extractor to return a tensor
    mock_feature_extractor = MagicMock()
    mock_feature_extractor.return_value = {"input_values": torch.zeros((1, 4))}
    mock_feature_extractor_from_pretrained.return_value = mock_feature_extractor

    mock_librosa_load.return_value = (np.zeros(6, dtype=np.float32), 4)

    output1 = MagicMock()
    output1.logits = torch.tensor()

    # Mock the model's forward pass to return logits
    mock_model.return_value = torch.tensor([[0.1, 0.9]])

    result = classifier.predict("fake/audio/path")

    mock_librosa_load.assert_called_once_with("fake/audio/path", sr=16000, mono=True)
    mock_feature_extractor.assert_called()
    mock_model.assert_called()