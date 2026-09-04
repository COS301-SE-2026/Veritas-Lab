import math
import torch
import torch.nn as nn
from transformers import CLIPVisionModel

class detail_temporal_block(nn.Module):
    def __init__(
        self,
        d_model: int,
        zones_per_dim: int = 2,
        hidden_dim: int = 256,
    ):
        super().__init__()

        self.d_model = d_model
        self.zones_per_dim = zones_per_dim
        self.hidden_dim = hidden_dim

        self.norm = nn.LayerNorm(d_model)

        self.gru = nn.GRU(
            input_size=d_model,
            hidden_size=hidden_dim,
            num_layers=1,
            batch_first=True,
            bidirectional=False,
        )

    @staticmethod
    def serpentine_scan(zone: torch.Tensor) -> torch.Tensor:
        B, T, C, H, W = zone.shape
        rows = []

        for r in range(H):
            row = zone[:, :, :, r, :]

            if r % 2 == 1:
                row = torch.flip(row,dims=[-1],)

            row = row.permute(0, 1, 3, 2)
            rows.append(row)

        sequence = torch.cat(rows, dim=2)
        sequence = sequence.reshape(B, T * H * W, C)
        return sequence

    def forward(self, features: torch.Tensor):
        if self.zones_per_dim > features.shape[3] or self.zones_per_dim > features.shape[4]:
            raise ValueError("zones_per_dim is larger than the CLIP feature map.")

        s = self.zones_per_dim
        row_zones = torch.tensor_split(features, s, dim=3)
        local_features = []

        for row_zone in row_zones:
            column_zones = torch.tensor_split(row_zone, s, dim=4)

            for zone in column_zones:
                sequence = self.serpentine_scan(zone)
                sequence = self.norm(sequence)

                output, _ = self.gru(sequence)

                local_feature = output.mean(dim=1)
                local_features.append(local_feature)

        return local_features

class ai_video_classifier(nn.Module):
    def __init__(
        self,
        clip_name: str = "openai/clip-vit-base-patch32",
        num_frames: int = 8,
        zones_per_dim: int = 2,
        freeze_encoder: bool = True,
        temporal_hidden_dim: int = 256,
        classifier_hidden_dim: int = 256,
        dropout: float = 0.3,
    ):
        super().__init__()

        self.num_frames = num_frames
        self.zones_per_dim = zones_per_dim

        self.encoder = CLIPVisionModel.from_pretrained(clip_name)

        self.feature_dim = self.encoder.config.hidden_size

        if freeze_encoder:
            for parameter in self.encoder.parameters():
                parameter.requires_grad = False

        self.temporal_block = detail_temporal_block(
            d_model=self.feature_dim,
            zones_per_dim=zones_per_dim,
            hidden_dim=temporal_hidden_dim
        )

        number_of_zones = zones_per_dim * zones_per_dim

        classifier_input_size = self.feature_dim + (number_of_zones * temporal_hidden_dim)
    
        self.classifier = nn.Sequential(
            nn.Linear(classifier_input_size, classifier_hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(classifier_hidden_dim, 1)
        )

    def _encode_frames(self, video: torch.Tensor) -> torch.Tensor:
        B, T, C, H, W = video.shape

        x = video.reshape(B * T, C, H, W)

        encoder_frozen = all(
            not parameter.requires_grad
            for parameter
            in self.encoder.parameters()
        )

        if encoder_frozen:
            with torch.no_grad():
                output = self.encoder(pixel_values=x)

        else:
            output = self.encoder(pixel_values=x)

        patch_tokens = output.last_hidden_state[:, 1:, :]

        number_of_patches = patch_tokens.shape[1]

        grid_size = int(math.sqrt(number_of_patches))

        if grid_size * grid_size != number_of_patches:
            raise ValueError(f"CLIP produced a non-square patch grid with {number_of_patches} patches.")

        features = patch_tokens.reshape(
            B,
            T,
            grid_size,
            grid_size,
            self.feature_dim,
        )

        features = features.permute(0, 1, 4, 2, 3).contiguous()
        return features

    def forward(self, video: torch.Tensor) -> torch.Tensor:
        if video.ndim != 5:
            raise ValueError(f"Expected video tensor with 5 dimensions [B,T,C,H,W], but got shape {tuple(video.shape)}")

        if video.shape[2] != 3:
            raise ValueError(f"Expected 3 RGB channels, but received {video.shape[2]}")

        if video.shape[1] != self.num_frames:
            raise ValueError(f"Expected {self.num_frames} frames, but received {video.shape[1]}")

        features = self._encode_frames(video)
        global_feature = features.mean(dim=(1, 3, 4))
        local_features = self.temporal_block(features)

        fused_features = torch.cat(
            [
                global_feature,
                *local_features,
            ],
            dim=-1,
        )

        logits = self.classifier(fused_features)
        logits = logits.squeeze(-1)

        return logits

    def train(self, mode: bool = True):
        super().train(mode)

        encoder_frozen = all(
            not parameter.requires_grad
            for parameter in self.encoder.parameters()
        )

        if encoder_frozen:
            self.encoder.eval()

        return self