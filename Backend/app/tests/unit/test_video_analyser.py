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

@patch("app.training.video.analyser.ai_audio_classifier")
@patch("app.training.video.analyser.ai_video_classifier")
@patch("app.training.video.analyser.torch.load")
def test_video_combined_analysis(mock_torch_load, mock_video_classifier_class, mock_audio_classifier_class):
    checkpoint = make_checkpoint()
    mock_torch_load.return_value = checkpoint

    mock_visual_model = MagicMock()
    mock_visual_model.to.return_value = mock_visual_model
    mock_video_classifier_class.return_value = mock_visual_model

    mock_audio_model = MagicMock()
    mock_audio_classifier_class.return_value = mock_audio_model

    analysis = video_combined_analysis(model_path="fake/video.pt")

    mock_torch_load.assert_called_once_with(
        Path("fake/video.pt"),
        map_location=torch.device("cpu"),
        weights_only=True
    )

    mock_video_classifier_class.assert_called_once_with(
        num_frames=2,
        zones_per_dim=2,
        freeze_encoder=True,
        temporal_hidden_dim=4,
        classifier_hidden_dim=4
    )

    mock_visual_model.load_state_dict.assert_called_once_with(checkpoint["model_state_dict"])
    mock_visual_model.to.assert_called_once()
    assert analysis.visual_model is mock_visual_model
    assert analysis.audio_model is mock_audio_model
    assert analysis.num_frames == 2
    assert analysis.zones == 2

@patch("app.training.video.analyser.librosa.load")
@patch("app.training.video.analyser.AutoModelForAudioClassification.from_pretrained")
@patch("app.training.video.analyser.AutoFeatureExtractor.from_pretrained")
def test_audio_classifier_predict_raises_for_empty_audio(
    mock_feature_extractor_from_pretrained,
    mock_model_from_pretrained,
    mock_librosa_load
):
    mock_model_from_pretrained.return_value = MagicMock()
    mock_feature_extractor_from_pretrained.return_value = MagicMock()
    mock_librosa_load.return_value = (np.zeros(0, dtype=np.float32), 4)

    classifier = ai_audio_classifier(model_path="fake/path", sample_rate=4, duration_seconds=1)

    with pytest.raises(RuntimeError, match="No usable audio found"):
        classifier.predict("empty_audio.wav")
    
@pytest.fixture
def analysis_instance():
    checkpoint = make_checkpoint()

    mock_visual_model = MagicMock()
    mock_visual_model.to.return_value = mock_visual_model

    mock_audio_model = MagicMock()

    with patch(
        "app.training.video.analyser.torch.load",
        return_value=checkpoint
    ), patch(
        "app.training.video.analyser.ai_video_classifier",
        return_value=mock_visual_model
    ), patch(
        "app.training.video.analyser.ai_audio_classifier",
        return_value=mock_audio_model
    ):
        analysis = video_combined_analysis(model_path="fake/video.pt")
    
    return analysis, mock_visual_model, mock_audio_model


@pytest.mark.asyncio
async def test_analyse_combine_visual_and_audio(analysis_instance):
    analysis, mock_visual_model, mock_audio_model = analysis_instance

    video_tensor = torch.zeros((2, 3, 224, 224))
    audio_result = {
        "available": True,
        "prediction": "AI-generated",
        "ai_probability": 0.9,
        "authentic_probability": 0.1,
        "confidence": 0.9
    }

    frame_results = [
        {"sampled_frame": 0, "masked_probability": 0.5, "importance": 0.2},
        {"sampled_frame": 1, "masked_probability": 0.4, "importance": 0.4}
    ]

    mock_audio_model.predict.return_value = audio_result

    with patch(
        "app.training.video.analyser.read_video_frames",
        return_value=video_tensor
    ) as mock_read_frames, patch(
        "app.training.video.analyser.extract_audio_from_video",
        return_value="audio.wav"
    ) as mock_extract_audio, patch(
        "app.training.video.analyser.predict_probability",
        return_value=0.8
    ) as mock_predict, patch(
        "app.training.video.analyser.calculate_frame_importance",
        return_value=frame_results
    ), patch(
        "app.training.video.analyser.build_explanation",
        return_value="explanation text"
    ), patch(
        "pathlib.Path.unlink"
    ) as mock_unlink:
        result = await analysis.analyse("video.mp4", threshold=0.5)

    mock_read_frames.assert_called_once_with(Path("video.mp4"), num_frames=analysis.num_frames)
    mock_extract_audio.assert_called_once_with(Path("video.mp4"))
    mock_audio_model.predict.assert_called_once_with("audio.wav")
    mock_unlink.assert_called_once_with(missing_ok=True)

    mock_predict.assert_called_once()
    call_args = mock_predict.call_args
    assert call_args.args[0] is mock_visual_model
    assert torch.equal(call_args.args[1], video_tensor.unsqueeze(0))

    assert result["prediction"] == "AI-generated"
    assert result["ai_probability"] == pytest.approx(0.7 * 0.8 + 0.3 * 0.9)
    assert result["visual"]["prediction"] == "AI-generated"
    assert result["audio"] == audio_result
    assert result["fusion"] == {"visual_weight": 0.7, "audio_weight": 0.3}
    assert result["visual"]["most_influential_frame"] == frame_results[1]