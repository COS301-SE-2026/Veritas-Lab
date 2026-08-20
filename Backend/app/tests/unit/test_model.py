import torch
from torch import nn
from Backend.app.training.image.model import AIImageDetector
from pathlib import Path

def test_model_is_torch_module() -> None:
    model = AIImageDetector(use_pretrained_weights=False)
    assert isinstance(model,nn.Module)

def test_model_uses_efficientnet_features() -> None:
    model = AIImageDetector(use_pretrained_weights=False)

    assert hasattr(model.network, "features")
    assert isinstance(model.network.features, nn.Sequential)

def test_classifier_structure() -> None:
    model = AIImageDetector(use_pretrained_weights=False)
    classifier = model.network.classifier

    assert isinstance(classifier, nn.Sequential)
    assert len(classifier) == 2
    assert isinstance(classifier[0], nn.Dropout)
    assert classifier[0].p == 0.3
    assert isinstance(classifier[1], nn.Linear)
    assert classifier[1].out_features == 1

def test_features_are_frozen_by_default() -> None:
    model = AIImageDetector(use_pretrained_weights=False)

    featured_parameters = list(model.network.features.parameters())

    assert len(featured_parameters) > 0
    assert all(
        parameter.requires_grad is False
        for parameter in featured_parameters
    )

def test_features_can_start_unfrozen() -> None:
    model = AIImageDetector(use_pretrained_weights=False, freeze_features=False)

    feature_parameters = list(model.network.features.parameters())
    assert all(
        parameter.requires_grad is True
        for parameter in feature_parameters
    )

def test_classifier_parameters_remain_trainable_when_features_frozen() -> None:
    model = AIImageDetector(use_pretrained_weights=False, freeze_features=True)

    classifier_parameters = list(model.network.classifier.parameters())

    assert len(classifier_parameters) > 0

    assert all(
        parameter.requires_grad is True
        for parameter in classifier_parameters
    )

def test_unfreeze_features() -> None:
    model = AIImageDetector(use_pretrained_weights=False, freeze_features=True)

    assert all(
        parameter.requires_grad is False
        for parameter in model.network.features.parameters()
    )

    model.unfreeze_features()

    assert all(
        parameter.requires_grad is True
        for parameter in model.network.features.parameters()
    )

def test_forward_returns_one_logit_per_image() -> None:
    model = AIImageDetector(use_pretrained_weights=False)

    model.eval()
    images = torch.rand(2,3,224,224)

    with torch.no_grad():
        output = model(images)

    assert isinstance(output, torch.Tensor)
    assert output.shape == (2,1)

def test_forward_supports_single_image() -> None:
    model = AIImageDetector(use_pretrained_weights=False)

    model.eval()

    image = torch.rand(1,3,224,224)

    with torch.no_grad():
        output = model(image)
    
    assert output.shape == (1,1)

def test_forward_output_contains_finite_values() -> None:
    model = AIImageDetector(use_pretrained_weights=False)

    model.eval()

    image = torch.rand(2,3,224,224)

    with torch.no_grad():
        output = model(image)

    assert torch.isfinite(output).all()

def test_logits_can_be_converted_to_probabilities() -> None:
    model = AIImageDetector(use_pretrained_weights=False)

    model.eval()

    image = torch.rand(2,3,224,224)

    with torch.no_grad():
        logits = model(image)
        probabilities = torch.sigmoid(logits)
    
    assert probabilities.shape == (2,1)
    assert torch.all(probabilities >= 0.0)
    assert torch.all(probabilities <=1.0)

def test_model_works_with_binary_cross_entropy_loss() -> None:
    model = AIImageDetector(use_pretrained_weights=False)

    images = torch.rand(2,3,224,224)

    labels = torch.tensor(
        [
            [0.0],
            [1.0]
        ]
    )

    logits = model(images)

    loss_function = nn.BCEWithLogitsLoss()
    loss = loss_function(logits, labels)

    assert loss.ndim == 0
    assert torch.isfinite(loss)
    assert loss.item() >= 0.0

def test_backward_creates_classifier_gradients() -> None:
    model = AIImageDetector(freeze_features=True, use_pretrained_weights=False)

    images = torch.rand(2,3,224,224)
    labels = torch.tensor(
        [
            [0.0],
            [1.0]
        ]
    )

    logits = model(images)

    loss = nn.BCEWithLogitsLoss()(
        logits,
        labels
    )

    loss.backward()

    classifier_gradients = [
        parameter.grad
        for parameter in model.network.classifier.parameters()
    ]

    assert all(
        gradient is not None
        for gradient in classifier_gradients
    )

def test_frozen_features_do_not_receive_gradients() -> None:
    model = AIImageDetector(freeze_features=True, use_pretrained_weights=False)

    images = torch.rand(2,3,224,224)

    labels = torch.tensor(
        [
            [0.0],
            [1.0]
        ]
    )

    logits = model(images)
    loss = nn.BCEWithLogitsLoss()(logits, labels)

    loss.backward()

    assert all(
        parameter.grad is None
        for parameter in model.network.features.parameters()
    )

def test_unfrozen_features_receive_gradients() -> None:
    model = AIImageDetector(freeze_features=False, use_pretrained_weights=False)

    images = torch.rand(2,3,224,224)

    labels = torch.tensor(
        [
            [0.0],
            [1.0]
        ]
    )

    logits = model(images)
    loss = nn.BCEWithLogitsLoss()(logits, labels)

    loss.backward()

    feature_gradients = [
        parameter.grad
        for parameter in model.network.features.parameters()
        if parameter.requires_grad
    ]

    assert any(
        gradient is not None
        for gradient in feature_gradients
    )

def test_state_dict_can_be_saved_and_loaded(tmp_path: Path) -> None:
    original_model = AIImageDetector(use_pretrained_weights=False)

    model_path = tmp_path / "model.pth"

    torch.save(
        original_model.state_dict(),
        model_path
    )

    loaded_model = AIImageDetector(use_pretrained_weights=False)

    state_dict = torch.load(
        model_path,
        map_location="cpu",
        weights_only=True
    )

    loaded_model.load_state_dict(state_dict)

    original_state = original_model.state_dict()
    loaded_state = loaded_model.state_dict()

    assert original_state.keys() == loaded_state.keys()

    for parameter_name in original_state:
        assert torch.equal(
            original_state[parameter_name],
            loaded_state[parameter_name]
        )
    

