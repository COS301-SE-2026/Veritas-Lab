from __future__ import annotations
from pathlib import Path
from typing import Any
import numpy as np
import torch
from PIL import ExifTags, Image, ImageFilter
from torch import nn

class GradCAM:

    def _save_activations(self, module: nn.Module, input: tuple[torch.Tensor,...], output: torch.Tensor):
        self.activations = output.detach()
    
    def _save_gradients(self, module: nn.Module, grad_input: tuple[torch.Tensor,...], grad_output: tuple[torch.Tensor,...]):
        if grad_output and grad_output[0] is not None:
            self.gradients = grad_output[0].detach()

    def generate(self, image_tensor: torch.Tensor)->tuple[np.ndarray, float]:
        self.model.eval()
        self.model.zero_grad(set_to_none=True)
        
        logit = self.model(image_tensor)
        probability = torch.sigmoid(logit).item()

        logit.sum().backwards()

        if self.activations is None or self.gradients is None:
            raise RuntimeError("Grad-CAM could not capture activations or gradients.")
        
        weights = self.gradients.mean(dim=(2,3), keepdim=True)
        heatmap = (weights * self.activations).sum(dim=1)
        heatmap = torch.relu(heatmap)

        minimum = heatmap.min()
        maximum = heatmap.max()

        if maximum > minimum:
            heatmap = (heatmap - minimum) / (maximum - minimum)
        else:
            heatmap = torch.zeros_like(heatmap)

        return heatmap.squeeze().cpu().numpy(), probability
    
    def remove_hooks(self)->None:
        self.forward_handle.remove()
        self.backward_handle.remove()

    def __init__(self, model: nn.Module, target_layer: nn.Module)->None:
        self.model = model
        self.target_layer = target_layer
        self.activations: torch.Tensor | None=None
        self.gradients: torch.Tensor | None = None

        self.forward_handle = target_layer.register_forward_hook(self._save_activations)
        self.backward_handle = target_layer.register_full_backward_hook(self._save_gradients)

