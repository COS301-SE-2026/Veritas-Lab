import importlib
import sys
from unittest.mock import MagicMock, patch
import pytest
import torch

MODULE_PATH = "app.training.audio.train"

def load_train_module():
    sys.modules.pop(MODULE_PATH, None)

    mock_model = MagicMock()
    mock_feature_extractor = MagicMock()
    mock_device = torch.device("cpu")

    mock_train_dataset = MagicMock()
    mock_validation_dataset = MagicMock()

    with patch(
        "app.training.audio.model.model",
        mock_model
    ), patch(
        "app.training.audio.model.feature_extractor",
        mock_feature_extractor
    ), patch(
        "app.training.audio.model.device",
        mock_device
    ), patch(
        "app.training.audio.dataset.audio_dataset",
        side_effect=[
            mock_train_dataset,
            mock_validation_dataset
        ]
    ), patch(
        "torch.utils.data.DataLoader"
    ) as mock_dataloader, patch(
        "torch.optim.AdamW"
    ) as mock_adamw:

        mock_train_loader = MagicMock()
        mock_validation_loader = MagicMock()

        mock_dataloader.side_effect = [mock_train_loader, mock_validation_loader]

        mock_optimizer = MagicMock()
        mock_adamw.return_value = mock_optimizer

        module = importlib.import_module(MODULE_PATH)

    return (
        module,
        mock_model,
        mock_feature_extractor,
        mock_train_loader,
        mock_validation_loader,
        mock_optimizer
    )

def test_validate_returns_correct_accuracy():
    module, mock_model, _, _, _, _ = load_train_module()

    batch1 = {
        "input_values": torch.tensor([[1.0], [2.0]]),
        "labels": torch.tensor([0, 1])
    }

    batch2 = {
        "input_values": torch.tensor([[3.0], [4.0]]),
        "labels": torch.tensor([1, 1])
    }

    module.validation_loader = [batch1, batch2]

    output1 = MagicMock()
    output1.logits = torch.tensor(
        [
            [2.0, 1.0],
            [1.0, 2.0]
        ]
    )

    output2 = MagicMock()
    output2.logits = torch.tensor(
        [
            [2.0, 1.0],
            [1.0, 2.0]
        ]
    )

    mock_model.side_effect = [output1, output2]

    accuracy = module.validate()

    assert accuracy == 0.75
    mock_model.eval.assert_called_once()

def test_validate_raises_error_for_empty_validation_loader():
    module, mock_model, _, _, _, _= load_train_module()

    module.validation_loader = []

    with pytest.raises(
        ValueError,
        match="Validation dataset is empty"
    ):
        module.validate()

    mock_model.eval.assert_called_once()

def test_train_raises_error_for_empty_training_loader():
    module, _, _, _, _, _ = load_train_module()
    module.train_loader = []

    with pytest.raises(
        ValueError,
        match="Training dataset is empty"
    ):
        module.train()

def test_train_runs_training_loop():
    module, mock_model, mock_feature_extractor, _, _, mock_optimizer = load_train_module()

    input_values = torch.tensor(
        [
            [0.1, 0.2]
        ]
    )

    labels = torch.tensor([0])

    batch = {
        "input_values": input_values,
        "labels": labels
    }

    module.train_loader = [batch]

    loss = MagicMock()
    loss.item.return_value = 0.5

    outputs = MagicMock()
    outputs.loss = loss

    mock_model.return_value = outputs

    module.EPOCHS = 1

    with patch.object(module, "validate", return_value=0.8) as mock_validate:
        module.train()

    mock_model.train.assert_called_once()
    mock_optimizer.zero_grad.assert_called_once()
    mock_model.assert_called_once_with(input_values=input_values, labels=labels)
    loss.backward.assert_called_once()
    mock_optimizer.step.assert_called_once()
    mock_validate.assert_called_once()
    mock_model.save_pretrained.assert_called_once_with(module.OUTPUT_DIR)

    mock_feature_extractor.save_pretrained.assert_called_once_with(module.OUTPUT_DIR)

def test_train_does_not_save_when_accuracy_does_not_improve():
    module, mock_model, mock_feature_extractor, _, _, mock_optimizer = load_train_module()

    batch = {
        "input_values": torch.tensor([[0.1, 0.2]]),
        "labels": torch.tensor([0])
    }

    module.train_loader = [batch]

    loss = MagicMock()
    loss.item.return_value = 0.5

    outputs = MagicMock()
    outputs.loss = loss

    mock_model.return_value = outputs

    module.EPOCHS = 1

    with patch.object(module,"validate", return_value=0.0):
        module.train()

    mock_model.save_pretrained.assert_not_called()
    mock_feature_extractor.save_pretrained.assert_not_called()

    mock_optimizer.zero_grad.assert_called_once()
    mock_optimizer.step.assert_called_once()

def test_train_runs_multiple_epochs():
    module, mock_model, mock_feature_extractor, _, _, mock_optimizer = load_train_module()

    batch = {
        "input_values": torch.tensor([[0.1, 0.2]]),
        "labels": torch.tensor([1])
    }

    module.train_loader = [batch]

    loss = MagicMock()
    loss.item.return_value = 0.25

    outputs = MagicMock()
    outputs.loss = loss

    mock_model.return_value = outputs

    module.EPOCHS = 2

    with patch.object(module, "validate", side_effect=[0.6, 0.7]):
        module.train()

    assert mock_model.train.call_count == 2
    assert mock_optimizer.zero_grad.call_count == 2
    assert mock_optimizer.step.call_count == 2
    assert loss.backward.call_count == 2
    assert mock_model.save_pretrained.call_count == 2
    assert mock_feature_extractor.save_pretrained.call_count == 2

def test_train_only_saves_best_accuracy():
    module, mock_model, mock_feature_extractor, _, _, _= load_train_module()

    batch = {
        "input_values": torch.tensor([[0.1]]),
        "labels": torch.tensor([0])
    }

    module.train_loader = [batch]

    loss = MagicMock()
    loss.item.return_value = 0.3

    outputs = MagicMock()
    outputs.loss = loss

    mock_model.return_value = outputs

    module.EPOCHS = 3

    with patch.object(
        module,
        "validate",
        side_effect=[0.8, 0.7, 0.9]
    ):
        module.train()

    assert mock_model.save_pretrained.call_count == 2
    assert mock_feature_extractor.save_pretrained.call_count == 2