from __future__ import annotations
from dataclasses import dataclass
import torch
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score
)

from torch import nn
from torch.utils.data import DataLoader

@dataclass
class EvaluationResult:
    loss: float
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float | None
    confusion_matrix: list[list[int]]
    classification_report: str

def evaluate_model(
    model: nn.Module,
    data_loader: DataLoader,
    loss_function: nn.Module,
    device: torch.device,
    threshold: float = 0.5
) -> EvaluationResult:
    model.eval()

    total_loss = 0.0
    probabilities: list[float] = []
    targets: list[int] = []

    with torch.no_grad():
        for images, labels in data_loader:
            images = images.to(device)
            float_labels = labels.float().unsqueeze(1).to(device)
            logits = model(images)
            loss = loss_function(logits, float_labels)
            total_loss += loss.item()

            batch_probabilities = torch.sigmoid(logits).squeeze(1)
            probabilities.extend(batch_probabilities.cpu().tolist())
            targets.extend(labels.cpu().tolist())
    
    predictions = [
        1 if probability >= threshold else 0
        for probability in probabilities
    ]

    try:
        roc_auc = float(roc_auc_score(targets, probabilities))
    except ValueError:
        roc_auc = None

    return EvaluationResult(
        loss=total_loss / max(len(data_loader), 1),
        f1=float(f1_score(targets, predictions, zero_division=0)),
        accuracy=float(accuracy_score(targets, predictions)),
        precision=float(precision_score(targets, predictions, zero_division=0)),
        recall=float(recall_score(targets, predictions, zero_division=0)),
        roc_auc=roc_auc,
        confusion_matrix=confusion_matrix(targets, predictions, labels=[0,1]).tolist(),
        classification_report=classification_report(targets, predictions, labels=[0,1], target_names=["authentic", "ai"], zero_division=0)
    )
