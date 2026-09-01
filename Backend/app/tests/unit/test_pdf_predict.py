import sys
import numpy as np
import pytest
import torch
import app.training.pdf.predict as predict

def test_enc_uses_vocab_and_padding():
    vocab = {
        "<PAD>": 0,
        "<UNK>": 1,
        "PAGE": 2,
        "FONT": 3
    }

    result = predict.enc(
        ["PAGE", "FONT"],
        vocab,
        max_length=4
    )

    assert result == [2, 3, 0, 0]

def test_enc_uses_unknown_token():
    vocab = {
        "<PAD>": 0,
        "<UNK>": 1,
        "PAGE": 2
    }

    result = predict.enc(
        ["PAGE", "UNKNOWN_TOKEN"],
        vocab,
        max_length=3
    )

    assert result == [2, 1, 0]

def test_enc_truncates_sequence():
    vocab = {
        "<PAD>": 0,
        "<UNK>": 1,
        "PAGE": 2,
        "FONT": 3,
        "IMAGE": 4
    }

    result = predict.enc(
        ["PAGE", "FONT", "IMAGE"],
        vocab,
        max_length=2
    )

    assert result == [2, 3]

class FakeModel:
    last_instance = None

    def __init__(
        self,
        object_vocab_size,
        object_pad_id,
        font_vocab_size,
        font_pad_id,
        line_basic_dim,
        font_numeric_dim,
        object_numeric_dim
    ):
        self.object_vocab_size = object_vocab_size
        self.object_pad_id = object_pad_id
        self.font_vocab_size = font_vocab_size
        self.font_pad_id = font_pad_id
        self.line_basic_dim = line_basic_dim
        self.font_numeric_dim = font_numeric_dim
        self.object_numeric_dim = object_numeric_dim

        self.loaded_state = None
        self.eval_called = False
        self.received_inputs = None

        FakeModel.last_instance = self

    def load_state_dict(self, state):
        self.loaded_state = state

    def eval(self):
        self.eval_called = True

    def __call__(
        self,
        lexical,
        object_ids,
        object_numeric,
        line_basic,
        font_ids,
        font_numeric
    ):
        self.received_inputs = {
            "lexical": lexical,
            "object_ids": object_ids,
            "object_numeric": object_numeric,
            "line_basic": line_basic,
            "font_ids": font_ids,
            "font_numeric": font_numeric
        }

        return torch.tensor([0.0], dtype=torch.float32)

@pytest.fixture
def checkpoint():
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
            "Helvetica": 2
        },

        "max_objects": 4,
        "max_fonts": 3,

        "basic_keys": [
            "page_count",
            "xref_object_count"
        ],

        "line_keys": [
            "lf_count",
            "crlf_count"
        ],

        "object_keys": [
            "page_object_ratio",
            "font_object_ratio"
        ],

        "font_keys": [
            "font_reference_count",
            "unique_font_count"
        ],

        "line_mean": [
            1.0,
            2.0,
            3.0,
            4.0
        ],

        "line_std": [
            1.0,
            2.0,
            1.0,
            2.0
        ],

        "object_mean": [
            0.1,
            0.2
        ],

        "object_std": [
            0.1,
            0.2
        ],

        "font_mean": [
            1.0,
            1.0
        ],

        "font_std": [
            1.0,
            2.0
        ],

        "model_state": {
            "fake": "state"
        }
    }

@pytest.fixture
def extracted_features():
    return {
        "page_count": 3.0,
        "xref_object_count": 10.0,

        "object_sequence": [
            "PAGE",
            "FONT"
        ],

        "font_tokens": [
            "Helvetica"
        ],

        "line_features": {
            "lf_count": 5.0,
            "crlf_count": 8.0
        },

        "object_features": {
            "page_object_ratio": 0.5,
            "font_object_ratio": 0.4
        },

        "font_features": {
            "font_reference_count": 3.0,
            "unique_font_count": 2.0
        }
    }

def setup_main_mocks(monkeypatch, checkpoint, extracted_features, lexical_score=0.8):
    monkeypatch.setattr(
        predict.torch,
        "load",
        lambda *args, **kwargs: checkpoint
    )

    monkeypatch.setattr(
        predict,
        "extract_pdf_features",
        lambda path: extracted_features
    )

    monkeypatch.setattr(
        predict,
        "extract_pdf_text",
        lambda path: "example PDF text"
    )

    monkeypatch.setattr(
        predict,
        "lexical_ai_probability",
        lambda text: lexical_score
    )

    monkeypatch.setattr(
        predict,
        "PDFDetector",
        FakeModel
    )

def test_main_with_lexical_analysis(monkeypatch, checkpoint, extracted_features, capsys):
    setup_main_mocks(
        monkeypatch,
        checkpoint,
        extracted_features,
        lexical_score=0.8
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "predict.py",
            "example.pdf",
            "--model",
            "model.pt"
        ]
    )

    predict.main()
    output = capsys.readouterr().out

    assert "Lexical AI score: 0.8000" in output
    assert "Final AI probability: 0.5000" in output
    assert "Prediction: AI-generated" in output

    model = FakeModel.last_instance

    assert model.loaded_state == {"fake": "state"}
    assert model.eval_called is True
    assert model.object_vocab_size == 4
    assert model.object_pad_id == 0
    assert model.font_vocab_size == 3
    assert model.font_pad_id == 0
    assert model.line_basic_dim == 4
    assert model.object_numeric_dim == 2
    assert model.font_numeric_dim == 2

def test_main_skip_lexical(monkeypatch, checkpoint, extracted_features, capsys):
    setup_main_mocks(
        monkeypatch,
        checkpoint,
        extracted_features
    )

    def fail_if_called(path):
        raise AssertionError("extract_pdf_text should not be called")

    monkeypatch.setattr(
        predict,
        "extract_pdf_text",
        fail_if_called
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "predict.py",
            "example.pdf",
            "--skip-lexical"
        ]
    )

    predict.main()
    output = capsys.readouterr().out

    assert "Lexical AI score: 0.5000" in output
    assert "Prediction: AI-generated" in output

def test_main_creates_expected_tensors(monkeypatch, checkpoint, extracted_features):
    setup_main_mocks(
        monkeypatch,
        checkpoint,
        extracted_features,
        lexical_score=0.75
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "predict.py",
            "example.pdf"
        ]
    )

    predict.main()
    inputs = FakeModel.last_instance.received_inputs

    assert inputs["lexical"].shape == (1, 1)
    assert inputs["object_ids"].shape == (1, 4)
    assert inputs["object_numeric"].shape == (1, 2)
    assert inputs["line_basic"].shape == (1, 4)
    assert inputs["font_ids"].shape == (1, 3)
    assert inputs["font_numeric"].shape == (1, 2)
    assert inputs["lexical"].dtype == torch.float32
    assert inputs["object_ids"].dtype == torch.long
    assert inputs["object_numeric"].dtype == torch.float32
    assert inputs["line_basic"].dtype == torch.float32
    assert inputs["font_ids"].dtype == torch.long
    assert inputs["font_numeric"].dtype == torch.float32

def test_main_encodes_object_and_font_tokens(monkeypatch, checkpoint, extracted_features):
    setup_main_mocks(
        monkeypatch,
        checkpoint,
        extracted_features
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "predict.py",
            "example.pdf"
        ]
    )

    predict.main()
    inputs = FakeModel.last_instance.received_inputs

    assert inputs["object_ids"].tolist() == [
        [2, 3, 0, 0]
    ]

    assert inputs["font_ids"].tolist() == [
        [2, 0, 0]
    ]

def test_main_standardises_numeric_features(monkeypatch, checkpoint, extracted_features):
    setup_main_mocks(
        monkeypatch,
        checkpoint,
        extracted_features
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "predict.py",
            "example.pdf"
        ]
    )

    predict.main()
    inputs = FakeModel.last_instance.received_inputs

    expected_line = np.array(
        [
            (3.0 - 1.0) / 1.0,
            (10.0 - 2.0) / 2.0,
            (5.0 - 3.0) / 1.0,
            (8.0 - 4.0) / 2.0
        ],
        dtype=np.float32
    )

    expected_object = np.array(
        [
            (0.5 - 0.1) / 0.1,
            (0.4 - 0.2) / 0.2
        ],
        dtype=np.float32
    )

    expected_font = np.array(
        [
            (3.0 - 1.0) / 1.0,
            (2.0 - 1.0) / 2.0
        ],
        dtype=np.float32
    )

    np.testing.assert_allclose(inputs["line_basic"].numpy()[0], expected_line)
    np.testing.assert_allclose(inputs["object_numeric"].numpy()[0], expected_object)
    np.testing.assert_allclose(inputs["font_numeric"].numpy()[0], expected_font)

def test_main_uses_zero_for_missing_features(monkeypatch, checkpoint, extracted_features):
    incomplete_features = {
        **extracted_features,
        "page_count": 3.0,

        "line_features": {
            "lf_count": 5.0
        },

        "object_features": {
            "page_object_ratio": 0.5
        },

        "font_features": {
            "font_reference_count": 3.0
        }
    }

    incomplete_features.pop(
        "xref_object_count",
        None
    )

    setup_main_mocks(
        monkeypatch,
        checkpoint,
        incomplete_features
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "predict.py",
            "example.pdf"
        ]
    )

    predict.main()

    inputs = FakeModel.last_instance.received_inputs

    expected_line = np.array(
        [
            (3.0 - 1.0) / 1.0,
            (0.0 - 2.0) / 2.0,
            (5.0 - 3.0) / 1.0,
            (0.0 - 4.0) / 2.0
        ],
        dtype=np.float32
    )

    np.testing.assert_allclose(
        inputs["line_basic"].numpy()[0],
        expected_line
    )

def test_main_predicts_authentic(monkeypatch, checkpoint, extracted_features, capsys):
    class AuthenticModel(FakeModel):
        def __call__(
            self,
            lexical,
            object_ids,
            object_numeric,
            line_basic,
            font_ids,
            font_numeric
        ):
            return torch.tensor(
                [-2.0],
                dtype=torch.float32
            )

    setup_main_mocks(
        monkeypatch,
        checkpoint,
        extracted_features
    )

    monkeypatch.setattr(
        predict,
        "PDFDetector",
        AuthenticModel
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "predict.py",
            "example.pdf"
        ]
    )

    predict.main()
    output = capsys.readouterr().out
    assert "Prediction: Authentic" in output