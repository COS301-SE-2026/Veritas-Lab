import sys
from types import SimpleNamespace

import numpy as np
import pytest
import torch

import app.training.pdf.explain as explain

def clear_cache(function):
    cache_clear = getattr(function, "cache_clear", None)

    if cache_clear:
        cache_clear()

@pytest.fixture(autouse=True)
def clear_detector_cache():
    clear_cache(explain.load_detector)
    yield
    clear_cache(explain.load_detector)

def make_checkpoint():
    return {
        "object_vocab": {
            "<PAD>": 0,
            "<UNK>": 1,
            "PAGE": 2,
            "FONT": 3
        },

        "font_vocab": {
            "<PAD>": 0,
            "<UNK>": 1,
            "Arial": 2
        },

        "max_objects": 4,
        "max_fonts": 3,

        "basic_keys": [
            "page_count",
            "file_size_kb"
        ],

        "line_keys": [
            "lf_ratio"
        ],

        "object_keys": [
            "page_object_ratio",
            "font_object_ratio"
        ],

        "font_keys": [
            "font_reference_count",
            "embedded_font_ratio"
        ],

        "line_mean": [
            1.0,
            10.0,
            0.5
        ],

        "line_std": [
            1.0,
            2.0,
            0.5
        ],

        "object_mean": [
            0.2,
            0.3
        ],

        "object_std": [
            0.1,
            0.2
        ],

        "font_mean": [
            2.0,
            0.5
        ],

        "font_std": [
            1.0,
            0.25
        ],

        "model_state": {}
    }

def make_tensors():
    return {
        "lexical": torch.tensor(
            [[0.8]],
            dtype=torch.float32
        ),

        "object_ids": torch.tensor(
            [[2, 3, 0, 0]],
            dtype=torch.long
        ),

        "object_numeric": torch.tensor(
            [[1.0, 2.0]],
            dtype=torch.float32
        ),

        "line_basic": torch.tensor(
            [[1.0, 2.0, 3.0]],
            dtype=torch.float32
        ),

        "font_ids": torch.tensor(
            [[2, 0, 0]],
            dtype=torch.long
        ),

        "font_numeric": torch.tensor(
            [[1.0, 2.0]],
            dtype=torch.float32
        )
    }

def test_encode_sequence_uses_vocab_and_padding():
    vocab = {
        "<PAD>": 0,
        "<UNK>": 1,
        "PAGE": 2
    }

    result = explain.encode_sequence(
        ["PAGE", "UNKNOWN"],
        vocab,
        4
    )

    assert result == [2, 1, 0, 0]

def test_encode_sequence_truncates():
    vocab = {
        "<PAD>": 0,
        "<UNK>": 1,
        "A": 2,
        "B": 3,
        "C": 4
    }

    result = explain.encode_sequence(
        ["A", "B", "C"],
        vocab,
        2
    )

    assert result == [2, 3]

def test_load_detector_builds_model(monkeypatch, tmp_path):
    checkpoint = make_checkpoint()

    monkeypatch.setattr(
        explain.torch,
        "load",
        lambda *args, **kwargs: checkpoint
    )

    class FakeModel:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.state = None
            self.eval_called = False

        def load_state_dict(self, state):
            self.state = state

        def eval(self):
            self.eval_called = True

    monkeypatch.setattr(
        explain,
        "PDFDetector",
        FakeModel
    )

    explain.load_detector.cache_clear()

    model, loaded_checkpoint = explain.load_detector(str(tmp_path / "model.pt"))

    assert loaded_checkpoint is checkpoint
    assert model.kwargs["object_vocab_size"] == len(checkpoint["object_vocab"])
    assert model.kwargs["font_vocab_size"] == len(checkpoint["font_vocab"])
    assert model.kwargs["line_basic_dim"] == 3
    assert model.kwargs["font_numeric_dim"] == 2
    assert model.kwargs["object_numeric_dim"] == 2
    assert model.state == checkpoint["model_state"]
    assert model.eval_called is True

def test_load_detector_is_cached(monkeypatch, tmp_path):
    checkpoint = make_checkpoint()
    calls = []

    def fake_load(*args, **kwargs):
        calls.append(1)
        return checkpoint

    monkeypatch.setattr(
        explain.torch,
        "load",
        fake_load
    )

    class FakeModel:
        def __init__(self, **kwargs):
            pass

        def load_state_dict(self, state):
            pass

        def eval(self):
            pass

    monkeypatch.setattr(
        explain,
        "PDFDetector",
        FakeModel
    )

    explain.load_detector.cache_clear()
    path = str(tmp_path / "model.pt")
    first = explain.load_detector(path)
    second = explain.load_detector(path)

    assert first is second
    assert len(calls) == 1

def test_prepare_inputs(monkeypatch):
    checkpoint = make_checkpoint()

    features = {
        "page_count": 3,
        "file_size_kb": 14,

        "object_sequence": [
            "PAGE",
            "FONT"
        ],

        "font_tokens": [
            "Arial"
        ],

        "line_features": {
            "lf_ratio": 1.0
        },

        "object_features": {
            "page_object_ratio": 0.4,
            "font_object_ratio": 0.7
        },

        "font_features": {
            "font_reference_count": 4,
            "embedded_font_ratio": 1.0
        }
    }

    monkeypatch.setattr(
        explain,
        "extract_pdf_features",
        lambda path: features
    )

    monkeypatch.setattr(
        explain,
        "extract_pdf_text",
        lambda path: "example text"
    )

    monkeypatch.setattr(
        explain,
        "lexical_ai_probability",
        lambda text: 0.75
    )

    returned_features, lexical_score, tensors = (
        explain.prepare_inputs(
            "test.pdf",
            checkpoint
        )
    )

    assert returned_features is features
    assert lexical_score == 0.75

    assert tensors["lexical"].shape == (1, 1)
    assert tensors["object_ids"].tolist() == [[2, 3, 0, 0]]
    assert tensors["font_ids"].tolist() == [[2, 0, 0]]

    expected_line = np.array(
        [
            (3 - 1.0) / 1.0,
            (14 - 10.0) / 2.0,
            (1.0 - 0.5) / 0.5
        ]
    )

    assert np.allclose(tensors["line_basic"].numpy()[0], expected_line) 

def test_predict_probability():
    class FakeModel:
        def __call__(
            self,
            lexical,
            object_ids,
            object_numeric,
            line_basic,
            font_ids,
            font_numeric
        ):
            return torch.tensor([2.0])

    probability = explain.predict_probability(
        FakeModel(),
        make_tensors()
    )

    expected = torch.sigmoid(torch.tensor(2.0)).item()
    assert probability == pytest.approx(expected)

@pytest.mark.parametrize(
    "branch",
    [
        "lexical",
        "object_sequence",
        "object_numeric",
        "line_basic",
        "fonts"
    ]
)
def test_neutralise_branch(branch):
    checkpoint = make_checkpoint()
    tensors = make_tensors()

    modified = explain.neutralise_branch(
        tensors,
        branch,
        checkpoint
    )

    if branch == "lexical":
        assert modified["lexical"].item() == 0.5

    elif branch == "object_sequence":
        assert modified["object_ids"].tolist() == [[1, 0, 0, 0]]

    elif branch == "object_numeric":
        assert torch.all(modified["object_numeric"] == 0)

    elif branch == "line_basic":
        assert torch.all(modified["line_basic"] == 0)

    elif branch == "fonts":
        assert torch.all(modified["font_ids"] == 0)
        assert torch.all(modified["font_numeric"] == 0)

def test_calculate_branch_contributions(monkeypatch):
    tensors = make_tensors()
    checkpoint = make_checkpoint()

    probabilities = iter(
        [
            0.6,
            0.55,
            0.7,
            0.65,
            0.75
        ]
    )

    monkeypatch.setattr(
        explain,
        "predict_probability",
        lambda model, modified: next(
            probabilities
        )
    )

    contributions = (
        explain.calculate_branch_contributions(
            model=object(),
            tensors=tensors,
            checkpoint=checkpoint,
            full_probability=0.80
        )
    )

    assert contributions["lexical"] == pytest.approx(0.20)
    assert contributions["object_sequence"] == pytest.approx(0.25)
    assert contributions["object_numeric"] == pytest.approx(0.10)
    assert contributions["line_basic"] == pytest.approx(0.15)
    assert contributions["fonts"] == pytest.approx(0.05)

@pytest.mark.parametrize(
    "value, expected",
    [
        (0.20, "high"),
        (-0.15, "high"),
        (0.10, "medium"),
        (-0.05, "medium"),
        (0.01, "low"),
        (0.0, "low")
    ]
)
def test_contribution_strength(value, expected):
    assert explain.contribution_strength(value) == expected

@pytest.mark.parametrize(
    "value, expected",
    [
        (
            0.1,
            "AI-generated content"
        ),

        (
            -0.1,
            "authentic content"
        ),

        (
            0.0,
            "neither classification"
        )
    ]
)
def test_contribution_direction(value, expected):
    assert explain.contribution_direction(value) == expected

@pytest.mark.parametrize(
    "branch, expected",
    [
        (
            "lexical",
            "lexical analysis"
        ),

        (
            "object_sequence",
            "PDF object sequence"
        ),

        (
            "object_numeric",
            "PDF object structure"
        ),

        (
            "line_basic",
            "line-ending and basic PDF structure"
        ),

        (
            "fonts",
            "font analysis"
        ),

        (
            "unknown",
            "unknown"
        )
    ]
)
def test_branch_display_name(branch, expected):
    assert explain.branch_display_name(branch) == expected
    
def test_contribution_sentence_positive():
    result = explain.contribution_sentence("lexical", 0.20)
    assert "high evidence" in result
    assert "AI-generated content" in result

def test_contribution_sentence_zero():
    result = explain.contribution_sentence("fonts", 0.0)
    assert "does not clearly favour" in result