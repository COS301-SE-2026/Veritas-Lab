import sys
import numpy as np
import pytest
import torch
import app.training.pdf.train as train

def test_load_rows_reads_jsonl_and_ignores_blank_lines(tmp_path):
    file = tmp_path / "data.jsonl"

    file.write_text(
        '{"label": 0}\n'
        '\n'
        '{"label": 1}\n',
        encoding="utf-8"
    )

    result = train.load_rows(file)

    assert result == [
        {"label": 0},
        {"label": 1}
    ]

def test_build_vocab_contains_pad_and_unk():
    vocab = train.build_vocab(
        [
            ["PAGE", "FONT"],
            ["PAGE", "IMAGE"]
        ]
    )

    assert vocab[train.PAD] == 0
    assert vocab[train.UNK] == 1

    assert "PAGE" in vocab
    assert "FONT" in vocab
    assert "IMAGE" in vocab

def test_build_vocab_orders_by_frequency():
    vocab = train.build_vocab(
        [
            ["PAGE", "PAGE", "FONT"],
            ["PAGE", "IMAGE"]
        ]
    )

    assert vocab["PAGE"] == 2

def test_build_vocab_empty_sequences():
    vocab = train.build_vocab([])

    assert vocab == {
        train.PAD: 0,
        train.UNK: 1
    }

def test_encode_sequence_pads():
    vocab = {
        train.PAD: 0,
        train.UNK: 1,
        "PAGE": 2,
        "FONT": 3
    }

    result = train.encode_sequence(
        ["PAGE", "FONT"],
        vocab,
        max_length=4
    )

    assert result == [2, 3, 0, 0]

def test_encode_sequence_uses_unknown():
    vocab = {
        train.PAD: 0,
        train.UNK: 1,
        "PAGE": 2
    }

    result = train.encode_sequence(
        ["PAGE", "SOMETHING_UNKNOWN"],
        vocab,
        max_length=3
    )

    assert result == [2, 1, 0]

def test_encode_sequence_truncates():
    vocab = {
        train.PAD: 0,
        train.UNK: 1,
        "A": 2,
        "B": 3,
        "C": 4
    }

    result = train.encode_sequence(
        ["A", "B", "C"],
        vocab,
        max_length=2
    )

    assert result == [2, 3]

def test_calculate_stats_top_level():
    rows = [
        {
            "a": 1.0,
            "b": 2.0
        },
        {
            "a": 3.0,
            "b": 4.0
        }
    ]

    mean, std = train.calculate_stats(
        rows,
        ["a", "b"]
    )

    np.testing.assert_allclose(
        mean,
        [2.0, 3.0]
    )

    np.testing.assert_allclose(
        std,
        [1.0, 1.0]
    )

def test_calculate_stats_nested():
    rows = [
        {
            "features": {
                "a": 2.0,
                "b": 4.0
            }
        },
        {
            "features": {
                "a": 4.0,
                "b": 8.0
            }
        }
    ]

    mean, std = train.calculate_stats(
        rows,
        ["a", "b"],
        nested="features"
    )

    np.testing.assert_allclose(
        mean,
        [3.0, 6.0]
    )

    np.testing.assert_allclose(
        std,
        [1.0, 2.0]
    )

def test_calculate_stats_missing_values_become_zero():
    rows = [
        {"a": 2},
        {}
    ]

    mean, std = train.calculate_stats(
        rows,
        ["a"]
    )

    np.testing.assert_allclose(
        mean,
        [1.0]
    )

    np.testing.assert_allclose(
        std,
        [1.0]
    )

def test_calculate_stats_replaces_zero_std():
    rows = [
        {"a": 5.0},
        {"a": 5.0}
    ]

    mean, std = train.calculate_stats(
        rows,
        ["a"]
    )

    assert mean[0] == pytest.approx(5.0)
    assert std[0] == pytest.approx(1.0)

@pytest.fixture
def dataset_row():
    return {
        "label": 1,
        "lexical_ai_probability": 0.8,

        "page_count": 2.0,
        "xref_object_count": 10.0,
        "pdf_version": 1.7,
        "file_size_kb": 5.0,
        "xref_objects_per_page": 5.0,
        "xref_objects_per_kb": 2.0,

        "object_sequence": [
            "PAGE",
            "FONT"
        ],

        "font_tokens": [
            "Helvetica"
        ],

        "line_features": {
            key: float(index + 1)
            for index, key
            in enumerate(train.LINE)
        },

        "object_features": {
            key: float(index + 1)
            for index, key
            in enumerate(train.OBJECT)
        },

        "font_features": {
            key: float(index + 1)
            for index, key
            in enumerate(train.FONT)
        }
    }

@pytest.fixture
def dataset(dataset_row):
    object_vocab = {
        train.PAD: 0,
        train.UNK: 1,
        "PAGE": 2,
        "FONT": 3
    }

    font_vocab = {
        train.PAD: 0,
        train.UNK: 1,
        "Helvetica": 2
    }

    line_dim = len(train.BASIC) + len(train.LINE)
    object_dim = len(train.OBJECT)
    font_dim = len(train.FONT)

    return train.PDFDataset(
        rows=[dataset_row],
        object_vocab=object_vocab,
        font_vocab=font_vocab,
        max_objects=4,
        max_fonts=3,

        line_mean=np.zeros(
            line_dim,
            dtype=np.float32
        ),

        line_std=np.ones(
            line_dim,
            dtype=np.float32
        ),

        object_mean=np.zeros(
            object_dim,
            dtype=np.float32
        ),

        object_std=np.ones(
            object_dim,
            dtype=np.float32
        ),

        font_mean=np.zeros(
            font_dim,
            dtype=np.float32
        ),

        font_std=np.ones(
            font_dim,
            dtype=np.float32
        )
    )

def test_pdf_dataset_length(dataset):
    assert len(dataset) == 1

def test_pdf_dataset_returns_expected_keys(dataset):
    item = dataset[0]

    assert set(item.keys()) == {
        "lex",
        "obj",
        "objnum",
        "line",
        "fonts",
        "fontnum",
        "y"
    }

def test_pdf_dataset_tensor_shapes(dataset):
    item = dataset[0]

    assert item["lex"].shape == (1,)
    assert item["obj"].shape == (4,)
    assert item["objnum"].shape == (len(train.OBJECT),)
    assert item["line"].shape == (len(train.BASIC) + len(train.LINE),)
    assert item["fonts"].shape == (3,)
    assert item["fontnum"].shape == (len(train.FONT),)
    assert item["y"].shape == ()

def test_pdf_dataset_tensor_types(dataset):
    item = dataset[0]

    assert item["lex"].dtype == torch.float32
    assert item["obj"].dtype == torch.long
    assert item["objnum"].dtype == torch.float32
    assert item["line"].dtype == torch.float32
    assert item["fonts"].dtype == torch.long
    assert item["fontnum"].dtype == torch.float32
    assert item["y"].dtype == torch.float32

def test_pdf_dataset_encodes_sequences(dataset):
    item = dataset[0]

    assert item["obj"].tolist() == [2, 3, 0, 0]
    assert item["fonts"].tolist() == [2, 0, 0]

def test_pdf_dataset_label_and_lexical(dataset):
    item = dataset[0]

    assert item["lex"].item() == pytest.approx(0.8)
    assert item["y"].item() == pytest.approx(1.0)

class FakeEvaluationModel:
    def __init__(self):
        self.eval_called = False

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
        return torch.tensor(
            [-2.0, 2.0],
            dtype=torch.float32
        )

def test_evaluate_model():
    model = FakeEvaluationModel()

    loader = [
        {
            "lex": torch.zeros((2, 1)),
            "obj": torch.zeros(
                (2, 2),
                dtype=torch.long
            ),
            "objnum": torch.zeros((2, 1)),
            "line": torch.zeros((2, 1)),
            "fonts": torch.zeros(
                (2, 2),
                dtype=torch.long
            ),
            "fontnum": torch.zeros((2, 1)),
            "y": torch.tensor(
                [0.0, 1.0]
            )
        }
    ]

    true_labels, predictions, probabilities = (
        train.evaluate_model(
            model,
            loader,
            torch.device("cpu")
        )
    )

    assert model.eval_called is True

    assert true_labels == [
        0.0,
        1.0
    ]

    assert predictions == [
        0,
        1
    ]

    assert probabilities[0] < 0.5
    assert probabilities[1] >= 0.5

class FakeTrainingModel:
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
        self.weight = torch.nn.Parameter(
            torch.tensor([0.0])
        )

        self.train_called = False
        self.eval_called = False
        self.loaded_state = None

        FakeTrainingModel.last_instance = self

    def to(self, device):
        return self

    def parameters(self):
        return [self.weight]

    def train(self):
        self.train_called = True
        return self

    def eval(self):
        self.eval_called = True
        return self

    def __call__(
        self,
        lexical,
        object_ids,
        object_numeric,
        line_basic,
        font_ids,
        font_numeric
    ):
        batch_size = lexical.shape[0]

        return self.weight.expand(
            batch_size
        )

    def state_dict(self):
        return {
            "weight": self.weight.detach().clone()
        }

    def load_state_dict(self, state):
        self.loaded_state = state

def make_training_row(label):
    return {
        "label": label,
        "lexical_ai_probability": (
            0.8 if label == 1 else 0.2
        ),

        "page_count": 2.0,
        "xref_object_count": 5.0,
        "pdf_version": 1.7,
        "file_size_kb": 10.0,
        "xref_objects_per_page": 2.5,
        "xref_objects_per_kb": 0.5,

        "object_sequence": [
            "PAGE",
            "FONT"
        ],

        "font_tokens": [
            "Helvetica"
        ],

        "line_features": {
            key: 1.0
            for key in train.LINE
        },

        "object_features": {
            key: 1.0
            for key in train.OBJECT
        },

        "font_features": {
            key: 1.0
            for key in train.FONT
        }
    }

def test_main_training_flow(monkeypatch, tmp_path, capsys):
    train_rows = [
        make_training_row(0),
        make_training_row(1)
    ]

    validation_rows = [
        make_training_row(0),
        make_training_row(1)
    ]

    def fake_load_rows(path):
        if "train" in str(path):
            return train_rows

        return validation_rows

    monkeypatch.setattr(
        train,
        "load_rows",
        fake_load_rows
    )

    monkeypatch.setattr(
        train,
        "PDFDetector",
        FakeTrainingModel
    )

    monkeypatch.setattr(
        train.torch.cuda,
        "is_available",
        lambda: False
    )

    saved = {}

    def fake_save(checkpoint, output):
        saved["checkpoint"] = checkpoint
        saved["output"] = output

    monkeypatch.setattr(
        train.torch,
        "save",
        fake_save
    )

    monkeypatch.setattr(
        train,
        "confusion_matrix",
        lambda y_true, y_pred: [
            [1, 0],
            [0, 1]
        ]
    )

    monkeypatch.setattr(
        train,
        "classification_report",
        lambda *args, **kwargs: "report"
    )

    output_path = tmp_path / "model.pt"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "train.py",

            "--train-features",
            "train.jsonl",

            "--validation-features",
            "validation.jsonl",

            "--output",
            str(output_path),

            "--epochs",
            "1",

            "--batch-size",
            "2",

            "--lr",
            "0.001",

            "--max-objects",
            "4",

            "--max-fonts",
            "3",

            "--seed",
            "42"
        ]
    )

    train.main()

    output = capsys.readouterr().out

    assert "Training PDFs: 2" in output
    assert "Validation PDFs: 2" in output
    assert "Device: cpu" in output
    assert "Epoch 01" in output
    assert "Saved:" in output

    model = FakeTrainingModel.last_instance

    assert model.train_called is True
    assert model.eval_called is True
    assert model.loaded_state is not None

    assert saved["output"] == str(output_path)

    checkpoint = saved["checkpoint"]

    assert "model_state" in checkpoint
    assert "object_vocab" in checkpoint
    assert "font_vocab" in checkpoint

    assert checkpoint["max_objects"] == 4
    assert checkpoint["max_fonts"] == 3

    assert checkpoint["basic_keys"] == train.BASIC
    assert checkpoint["line_keys"] == train.LINE
    assert checkpoint["object_keys"] == train.OBJECT
    assert checkpoint["font_keys"] == train.FONT

    assert "line_mean" in checkpoint
    assert "line_std" in checkpoint
    assert "object_mean" in checkpoint
    assert "object_std" in checkpoint
    assert "font_mean" in checkpoint
    assert "font_std" in checkpoint
    assert checkpoint["best_validation_accuracy"] >= 0.0
    
    
