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

def test_train_one_epoch_runs_optimizer_and_returns_avareges():
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
    assert loss.backward.call_count == 2
    assert avg_loss == pytest.approx(0.5)
    assert avg_accuracy == pytest.approx(1.0)

def test_validate_runs_without_gradients_and_returns_avareges():
    model = MagicMock()
    model.return_value = torch.tensor([2.0, -2.0])

    criterion = MagicMock()
    loss = MagicMock()
    loss.item.return_value = 0.3
    criterion.return_value = loss

    batch = {
        "video": torch.zeros((2, 1)),
        "label": torch.tensor([1.0, 0.0])
    }

    avg_loss, avg_accuracy = validate(model, [batch], criterion, torch.device("cpu"))

    model.eval.assert_called_once()
    assert avg_loss == pytest.approx(0.3)
    assert avg_accuracy == pytest.approx(1.0)

@patch("app.training.video.train.torch.load")
@patch("app.training.video.train.torch.save")
@patch("app.training.video.train.ai_video_classifier")
@patch("app.training.video.train.DataLoader")
@patch("app.training.video.train.video_binary_dataset")
def test_main_trains_and_saves_best_checkpoint(
    mock_video_binary_dataset,
    mock_dataloader,
    mock_video_classifier_class,
    mock_torch_save,
    mock_torch_load,
    monkeypatch
):
    mock_video_binary_dataset.side_effect = [FakeDataset(2), FakeDataset(1), FakeDataset(1)]

    batch = {
        "video": torch.zeros((1, 1)),
        "label": torch.tensor([1.0])
    }

    mock_dataloader.side_effect = [[batch], [batch], [batch]]

    mock_model = MagicMock()
    mock_model.to.return_value = mock_model
    mock_model.return_value = torch.tensor([2.0], requires_grad=True)
    mock_model.parameters.return_value = [torch.nn.Parameter(torch.zeros(1))]
    mock_video_classifier_class.return_value = mock_model

    mock_torch_load.return_value = {"model_state_dict": "state"}

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "train.py",
            "--epochs", "1",
            "--data-root", "dataset/video",
            "--checkpoint", "test_checkpoint.pt"
        ]
    )

    main()

    mock_video_classifier_class.assert_called_once_with(
        num_frames=8,
        zones_per_dim=2,
        freeze_encoder=True,
        temporal_hidden_dim=256,
        classifier_hidden_dim=256
    )

    assert mock_dataloader.call_count == 3
    mock_torch_save.assert_called_once()
    mock_torch_load.assert_called_once_with(
        "test_checkpoint.pt",
        map_location=torch.device("cpu"),
        weights_only=True
    )
    mock_model.load_state_dict.assert_called_once_with("state")