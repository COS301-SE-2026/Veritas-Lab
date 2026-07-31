from __future__ import annotations
import torch
from torch import nn
from torch.utils.data import DataLoader

def train_one_epoch(
    model: nn.Module,
    data_loader: DataLoader,
    loss_function: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device
) ->float:
    model.train()
    total_loss = 0.0

    for images, labels in data_loader:
        images = images.to(device)
        labels=labels.float().unsqueeze(1).to(device)

        optimizer.zero_grad(set_to_none=True)

        logits = model(images)
        loss = loss_function(logits, labels)

        loss.backward()
        optimizer.step()

        total_loss += loss.item()
    
    return total_loss/max(len(data_loader), 1)