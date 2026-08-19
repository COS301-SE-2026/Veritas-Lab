import pytest
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
#this may need to be revised upon
from app.training.metrics import evaluate_model

class FixedOutputModel(nn.Module):
    def __init__(self, logits: list[float]):
        super().__init__()
        self.logits = torch.tensor(logits, dtype=torch.float32).unsqueeze(1)
    
    def forward(self, images: torch.Tensor) -> torch.Tensor:
        batch_size = images.shape[0]
        return self.logits[:batch_size]
    
def create_loader(labels: list[int]) -> DataLoader:
    images = torch.zeros((len(labels), 3, 32, 32))
    label_tensor = torch.tensor(labels, dtype=torch.long)
    dataset = TensorDataset(images, label_tensor)

    return DataLoader(
        dataset,
        batch_size=len(labels),
        shuffle=False
    )

def test_evaluate_model_perfect_predictions():
    model = FixedOutputModel(logits=[-5.0, -5.0, 5.0, 5.0])

    loader = create_loader([0, 0, 1, 1])

    result = evaluate_model(
        model=model,
        data_loader=loader,
        loss_function=nn.BCEWithLogitsLoss(),
        device=torch.device("cpu")
    )

    assert result.accuracy == pytest.approx(1.0)
    assert result.precision == pytest.approx(1.0)
    assert result.recall == pytest.approx(1.0)
    assert result.f1 == pytest.approx(1.0)
    assert result.roc_auc == pytest.approx(1.0)
    assert result.confusion_matrix == [[2, 0], [0, 2]]
    assert "authentic" in result.classification_report
    assert "ai" in result.classification_report

def test_evaluate_model_uses_custom_threshold():
    model = FixedOutputModel(logits=[0.4, 1.0])
    loader = create_loader([0,1])

    result = evaluate_model(
        model=model,
        data_loader=loader,
        loss_function=nn.BCEWithLogitsLoss(),
        device=torch.device("cpu"),
        threshold=0.7
    )

    assert result.accuracy == pytest.approx(1.0)
    assert result.confusion_matrix == [[1, 0], [0, 1]]

def test_evaluate_model_returns_none_for_single_class_roc_auc():
    model = FixedOutputModel(logits=[-5.0, -4.0, -3.0])
    loader = create_loader([0,0,0])
    result = evaluate_model(
        model=model,
        data_loader=loader,
        loss_function=nn.BCEWithLogitsLoss(),
        device=torch.device("cpu")
    )

    assert result.roc_auc is None
    assert result.accuracy == pytest.approx(1.0)
    assert result.confusion_matrix == [[3, 0], [0, 0]]