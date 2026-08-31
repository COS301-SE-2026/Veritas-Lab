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


