from __future__ import annotations
import torch
from torch import nn
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0

class AIImageDetector(nn.Module):

    def __init__(self, freeze_features: bool = True, use_pretrained_weights: bool = True) -> None:
        super().__init__()

        weights = (EfficientNet_B0_Weights.DEFAULT if use_pretrained_weights else None)

        self.network = efficientnet_b0(weights=weights)
        if freeze_features:
            for parameter in self.network.features.parameters():
                parameter.requires_grad = False
        
        input_features = self.network.classifier[1].in_features
        self.network.classifier = nn.Sequential(nn.Dropout(p=0.3), nn.Linear(input_features, 1))
    
    def forward(self, images: torch.Tensor) -> torch.Tensor:
        return self.network(images)
    
    def unfreeze_features(self) -> None:
        for parameter in self.network.features.parameters():
            parameter.requires_grad = True