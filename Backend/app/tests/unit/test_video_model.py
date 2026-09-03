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

