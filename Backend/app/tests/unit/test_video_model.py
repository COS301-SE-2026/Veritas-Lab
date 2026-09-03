from unittest.mock import MagicMock, patch

import pytest
import torch

from app.training.video.model import ai_video_classifier, detail_temporal_block

def make_fake_encoder(hidden_size=8, grid_size=2):
    encoder = MagicMock()
    encoder.config.hidden_size = hidden_size

    params = [torch.nn.Parameter(torch.zeros(1))]
    encoder.parameters.side_effect = lambda: iter(params)

    def forward(pixel_values):
        batch = pixel_values.shape[0]
        num_patches = grid_size * grid_size + 1
        output = MagicMock()
        output.last_hidden_state = torch.zeros((batch, num_patches, hidden_size))
        return output

    encoder.side_effect = forward
    return encoder, params

def test_serpentine_scan_flips_odd_rows():
    zone = torch.tensor(
        [[[[[1.0, 2.0],[3.0, 4.0]]]]]
    )

    result = detail_temporal_block.serpentine_scan(zone)

    assert result.shape == (1, 4, 1)
    assert result.squeeze().tolist() == [1.0, 2.0, 4.0, 3.0]

def test_temporal_block_raises_when_zones_exceed_feature_map():
    block = detail_temporal_block(
        d_model=4,
        zones_per_dim=4,
        hidden_dim=2
    )
    features = torch.zeros((1, 2, 4, 2, 2))

    with pytest.raises(
        ValueError,
        match="zones_per_dim is larger than the CLIP feature map"
    ):
        block(features)

def test_temporal_block_forward_returns_one_feature_per_zone():
    block = detail_temporal_block(
        d_model=4,
        zones_per_dim=2,
        hidden_dim=3
    )
    features = torch.zeros((1, 2, 4, 2, 4))

    local_features = block(features)

    assert len(local_features) == 4
    for feature in local_features:
        assert feature.shape == (1, 3)

@patch("app.training.video.model.CLIPVisionModel")
def test_classifier_initialises_and_freezes_encoder(mock_clip_class):
    encoder, params = make_fake_encoder(hidden_size=8)
    mock_clip_class.from_pretrained.return_value = encoder

    classifier = ai_video_classifier(
        num_frames=2,
        zones_per_dim=2,
        freeze_encoder=True,
        temporal_hidden_dim=4,
        classifier_hidden_dim=4
    )

    mock_clip_class.from_pretrained.assert_called_once_with("openai/clip-vit-base-patch32")
    assert classifier.feature_dim == 8
    assert params[0].requires_grad is False


@patch("app.training.video.model.CLIPVisionModel")
def test_classifier_does_not_freeze_encoder_when_disabled(mock_clip_class):
    encoder, params = make_fake_encoder(hidden_size=8)
    mock_clip_class.from_pretrained.return_value = encoder

    classifier = ai_video_classifier(
        num_frames=2,
        zones_per_dim=2,
        freeze_encoder=False,
        temporal_hidden_dim=4,
        classifier_hidden_dim=4
    )

    assert params[0].requires_grad is True

@patch("app.training.video.model.CLIPVisionModel")
def test_classifier_forward_returns_expected_shape(mock_clip_class):
    encoder, _ = make_fake_encoder(hidden_size=8, grid_size=2)
    mock_clip_class.from_pretrained.return_value = encoder

    classifier = ai_video_classifier(
        num_frames=2,
        zones_per_dim=2,
        freeze_encoder=False,
        temporal_hidden_dim=4,
        classifier_hidden_dim=4
    )

    video = torch.zeros((1, 2, 3, 4, 4))

    logits = classifier(video)
    assert logits.shape == (1,)

@patch("app.training.video.model.CLIPVisionModel")
def test_classifier_forward_rejects_wrong_frame_count(mock_clip_class):
    encoder, _ = make_fake_encoder()
    mock_clip_class.from_pretrained.return_value = encoder

    classifier = ai_video_classifier(
        num_frames=2,
        zones_per_dim=1,
        temporal_hidden_dim=4,
        classifier_hidden_dim=4
    )

    with pytest.raises(
        ValueError,
        match="Expected 2 frames"
    ):
        video = torch.zeros((1, 3, 3, 4, 4))
        classifier(video)