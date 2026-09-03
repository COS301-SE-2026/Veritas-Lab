import sys
from unittest.mock import MagicMock, patch

import pytest
import torch
from app.training.video.train import calculate_accuracy, main, train_one_epoch, validate

class FakeDataset:
    def __init__(self, length):
        self._length = length

    def __len__(self):
        return self._length

def test_calculate_accuracy():
    logits = torch.tensor([2.0, -2.0, 0.6,-0.1])
    labels = torch.tensor([1.0, 0.0, 1.0, 0.0])

    assert calculate_accuracy(logits, labels) == pytest.approx(1.0)

def test_calculate_accuracy_with_mismatches():
    logits = torch.tensor([2.0, 2.0])
    labels = torch.tensor([1.0, 0.0])

    assert calculate_accuracy(logits, labels) == pytest.approx(0.5)

def test_train_one_epoch_runs_optimizer_and_returns_avaregas():
    model = MagicMock()
    model.return_value = torch.tensor([2.0, -2.0], requires_grad=True)

    criterion = MagicMock()
    loss = MagicMock()
    loss.item.return_value = 0.5
    criterion.return_value = loss

    optimizer = MagicMock()

    batch = {
        "video": torch.zeros((2, 1)),
        "label": torch.tensor([1.0, 0.0])
    }

    avg_loss, avg_accuracy = train_one_epoch(model, [batch, batch], criterion, optimizer, torch.device("cpu"))

    model.train.assert_called_once()
    assert optimizer.zero_grad.call_count == 2
    assert optimizer.step.call_count == 2
    assert avg_loss == pytest.approx(0.5)
    assert avg_accuracy == pytest.approx(0.5)