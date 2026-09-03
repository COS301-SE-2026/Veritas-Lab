import importlib
import sys
import types
from unittest.mock import MagicMock, patch

import pytest
import torch

MODULE_PATH = "app.training.video.predict"

def load_predict_module():
    sys.modules.pop(MODULE_PATH, None)

    fake_model_module = types.ModuleType("app.training.video.model")
    fake_model_module.ai_video_classifier = MagicMock()

    with patch.dict(sys.modules, {"app.training.video.model": fake_model_module}):
        module = importlib.import_module(MODULE_PATH)

    return module

def test_predict_probability():
    module = load_predict_module()
    model = MagicMock()
    model.return_value = torch.tensor([0.0])
    video_batch = torch.zeros((1, 3, 8, 224, 224))
    probability = module.predict_probability(model, video_batch)

    assert probability == pytest.approx(0.5)
    model.assert_called_once_with(video_batch)

def test_extract_audio_success():
    module = load_predict_module()

    mock_temp_file = MagicMock()
    mock_temp_file.name = "/tmp/test_audio.wav"

    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch.object(
        module.tempfile,
        "NamedTemporaryFile",
        return_value=mock_temp_file
    ) as mock_temp, patch.object(
        module.subprocess,
        "run",
        return_value=mock_result
    ) as mock_run:

        result = module.extract_audio_from_video(
            "video.mp4"
        )

    mock_temp.assert_called_once_with(
        suffix=".wav",
        delete=False
    )

    mock_temp_file.close.assert_called_once()

    mock_run.assert_called_once()

    command = mock_run.call_args.args[0]

    assert command == [
        "ffmpeg",
        "-y",
        "-i",
        "video.mp4",
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "/tmp/test_audio.wav"
    ]

    assert result == "/tmp/test_audio.wav"

def test_extract_audio_failure():
    module = load_predict_module()

    mock_temp_file = MagicMock()
    mock_temp_file.name = "/tmp/test_audio.wav"

    mock_result = MagicMock()
    mock_result.returncode = 1

    with patch.object(
        module.tempfile,
        "NamedTemporaryFile",
        return_value=mock_temp_file
    ), patch.object(
        module.subprocess,
        "run",
        return_value=mock_result
    ), patch.object(
        module.Path,
        "unlink"
    ) as mock_unlink:
        result = module.extract_audio_from_video("bad_video.mp4")

    mock_unlink.assert_called_once_with(missing_ok=True)
    assert result is None

def test_mask_frame():
    module = load_predict_module()
    video = torch.ones((1, 3, 2, 2, 2))
    result = module.mask_frame(video, 1)

    assert torch.all(result[:, 1, :, :, :] == 0)
    assert torch.all(result[:, 0, :, :, :] == 1)
    assert torch.all(result[:, 2, :, :, :] == 1)
    assert torch.all(video == 1)

def test_calculate_decision_importance_ai():
    module = load_predict_module()
    result = module.calculate_decision_importance(original_probability=0.8, masked_probability=0.5, prediction="AI-generated")

    assert result == pytest.approx(0.3)

def test_calculate_decision_importance_authentic():
    module = load_predict_module()
    result = module.calculate_decision_importance(original_probability=0.3, masked_probability=0.5, prediction="Authentic")

    assert result == pytest.approx(0.2)

def test_calculate_frame_importance():
    module = load_predict_module()
    model = MagicMock()
    video = torch.ones((1, 3, 2, 2, 2))

    with patch.object(
        module,
        "predict_probability",
        side_effect=[0.6, 0.5, 0.4]
    ) as mock_predict:

        results = module.calculate_frame_importance(
            model=model,
            video=video,
            original_probability=0.8,
            prediction="AI-generated"
        )

    assert len(results) == 3

    assert results[0] == {
        "sampled_frame": 0,
        "masked_probability": 0.6,
        "importance": pytest.approx(0.2)
    }

    assert results[1] == {
        "sampled_frame": 1,
        "masked_probability": 0.5,
        "importance": pytest.approx(0.3)
    }

    assert results[2] == {
        "sampled_frame": 2,
        "masked_probability": 0.4,
        "importance": pytest.approx(0.4)
    }

    assert mock_predict.call_count == 3

def test_build_explanation_ai_generated():
    module = load_predict_module()

    frame_results = [
        {
            "sampled_frame": 0,
            "masked_probability": 0.7,
            "importance": 0.1
        },

        {
            "sampled_frame": 1,
            "masked_probability": 0.4,
            "importance": 0.4
        }
    ]

    result = module.build_explanation(
        prediction="AI-generated",
        probability=0.8,
        frame_results=frame_results
    )

    assert "AI-generated with 80.00% probability" in result
    assert "most influential sampled frame was frame 2" in result
    assert "40.00%" in result

def test_build_explanation_authentic():
    module = load_predict_module()

    frame_results = [
        {
            "sampled_frame": 0,
            "masked_probability": 0.4,
            "importance": 0.2
        }
    ]

    result = module.build_explanation(
        prediction="Authentic",
        probability=0.2,
        frame_results=frame_results
    )

    assert "authentic with 80.00% probability" in result

def test_build_explanation_no_positive_frame():
    module = load_predict_module()

    frame_results = [
        {
            "sampled_frame": 0,
            "masked_probability": 0.7,
            "importance": -0.1
        },

        {
            "sampled_frame": 1,
            "masked_probability": 0.6,
            "importance": 0.0
        }
    ]

    result = module.build_explanation(
        prediction="AI-generated",
        probability=0.7,
        frame_results=frame_results
    )

    assert "did not identify a sampled frame that positively supported" in result

def test_multimodal_summary_without_audio():
    module = load_predict_module()

    result = module.build_multimodal_summary(
        final_prediction="AI-generated",
        final_probability=0.8,
        visual_prediction="AI-generated",
        visual_probability=0.8,
        audio_result=None
    )

    assert "final multimodal classification is AI-generated" in result
    assert "80.00%" in result
    assert "No usable audio analysis was available" in result
    
def test_multimodal_summary_models_agree_ai():
    module = load_predict_module()

    audio_result = {
        "ai_probability": 0.9
    }

    result = module.build_multimodal_summary(
        final_prediction="AI-generated",
        final_probability=0.85,
        visual_prediction="AI-generated",
        visual_probability=0.8,
        audio_result=audio_result
    )

    assert "audio model predicted AI-generated" in result
    assert "visual and audio models agreed" in result

def test_multimodal_summary_models_agree_authentic():
    module = load_predict_module()

    audio_result = {
        "ai_probability": 0.2
    }

    result = module.build_multimodal_summary(
        final_prediction="Authentic",
        final_probability=0.3,
        visual_prediction="Authentic",
        visual_probability=0.25,
        audio_result=audio_result
    )

    assert "audio model predicted Authentic" in result
    assert "visual and audio models agreed" in result

def test_multimodal_summary_models_disagree():
    module = load_predict_module()

    audio_result = {
        "ai_probability": 0.8
    }

    result = module.build_multimodal_summary(
        final_prediction="AI-generated",
        final_probability=0.6,
        visual_prediction="Authentic",
        visual_probability=0.4,
        audio_result=audio_result
    )

    assert "audio model predicted AI-generated" in result
    assert "visual and audio models disagreed" in result
    assert "configured fusion weights were used" in result

def test_fusion_weights():
    module = load_predict_module()

    assert module.VISUAL_WEIGHT == 0.7
    assert module.AUDIO_WEIGHT == 0.3