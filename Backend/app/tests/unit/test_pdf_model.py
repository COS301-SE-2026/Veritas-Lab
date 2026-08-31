import pytest
import torch
from app.training.pdf.model import ObjectSequenceBranch, FontBranch, PDFDetector

def test_object_sequence_branch_output_shape():
    model = ObjectSequenceBranch(vocab_size=10, pad_id=0, dim=64)
    model.eval()

    ids = torch.tensor(
        [
            [1, 2, 3, 0],
            [4, 5, 0, 0]
        ],
        dtype=torch.long
    )

    with torch.no_grad():
        output = model(ids)

    assert output.shape == (2, 64)

def test_object_sequence_branch_handles_padding():
    model = ObjectSequenceBranch(vocab_size=10, pad_id=0, dim=64)
    model.eval()

    ids = torch.tensor(
        [
            [1, 2, 0, 0]
        ],
        dtype=torch.long
    )

    with torch.no_grad():
        output = model(ids)

    assert output.shape == (1, 64)
    assert torch.isfinite(output).all()

def test_object_sequence_branch_stores_pad_id():
    model = ObjectSequenceBranch(vocab_size=10, pad_id=3)

    assert model.pad_id == 3
    assert model.embedding.padding_idx == 3

def test_font_branch_output_shape():
    model = FontBranch(vocab_size=10, pad_id=0, numeric_dim=4)
    model.eval()

    ids = torch.tensor(
        [
            [1, 2, 0],
            [3, 0, 0]
        ],
        dtype=torch.long
    )

    numeric = torch.tensor(
        [
            [1.0, 2.0, 3.0, 4.0],
            [4.0, 3.0, 2.0, 1.0]
        ],
        dtype=torch.float32
    )

    with torch.no_grad():
        output = model(ids, numeric)

    assert output.shape == (2, 48)
    assert torch.isfinite(output).all()

def test_font_branch_handles_all_padding():
    model = FontBranch(vocab_size=10, pad_id=0, numeric_dim=3)
    model.eval()

    ids = torch.tensor(
        [
            [0, 0, 0]
        ],
        dtype=torch.long
    )

    numeric = torch.tensor(
        [
            [1.0, 2.0, 3.0]
        ],
        dtype=torch.float32
    )

    with torch.no_grad():
        output = model(ids, numeric)

    assert output.shape == (1, 48)
    assert torch.isfinite(output).all()

def test_font_branch_stores_pad_id():
    model = FontBranch(vocab_size=8,pad_id=2,numeric_dim=3)

    assert model.pad_id == 2
    assert model.embedding.padding_idx == 2

@pytest.fixture
def detector():
    model = PDFDetector(
        object_vocab_size=10,
        object_pad_id=0,
        font_vocab_size=8,
        font_pad_id=0,
        line_basic_dim=6,
        font_numeric_dim=4,
        object_numeric_dim=5
    )
    model.eval()
    return model

def test_pdf_detector_output_shape(detector):
    lexical = torch.tensor(
        [
            [0.8],
            [0.2]
        ],
        dtype=torch.float32
    )

    object_ids = torch.tensor(
        [
            [1, 2, 3, 0],
            [4, 5, 0, 0]
        ],
        dtype=torch.long
    )

    object_numeric = torch.tensor(
        [
            [1, 2, 3, 4, 5],
            [5, 4, 3, 2, 1]
        ],
        dtype=torch.float32
    )

    line_basic = torch.tensor(
        [
            [1, 2, 3, 4, 5, 6],
            [6, 5, 4, 3, 2, 1]
        ],
        dtype=torch.float32
    )

    font_ids = torch.tensor(
        [
            [1, 2, 0],
            [3, 0, 0]
        ],
        dtype=torch.long
    )

    font_numeric = torch.tensor(
        [
            [1, 2, 3, 4],
            [4, 3, 2, 1]
        ],
        dtype=torch.float32
    )

    with torch.no_grad():
        output = detector(
            lexical,
            object_ids,
            object_numeric,
            line_basic,
            font_ids,
            font_numeric
        )

    assert output.shape == (2,)
    assert torch.isfinite(output).all()

def test_pdf_detector_single_item(detector):
    lexical = torch.tensor([[0.7]], dtype=torch.float32)

    object_ids = torch.tensor(
        [[1, 2, 0, 0]],
        dtype=torch.long
    )

    object_numeric = torch.tensor(
        [[1, 2, 3, 4, 5]],
        dtype=torch.float32
    )

    line_basic = torch.tensor(
        [[1, 2, 3, 4, 5, 6]],
        dtype=torch.float32
    )

    font_ids = torch.tensor(
        [[1, 0, 0]],
        dtype=torch.long
    )

    font_numeric = torch.tensor(
        [[1, 2, 3, 4]],
        dtype=torch.float32
    )

    with torch.no_grad():
        output = detector(
            lexical,
            object_ids,
            object_numeric,
            line_basic,
            font_ids,
            font_numeric
        )
    
    assert output.shape == (1,)

def test_pdf_detector_returns_logits(detector):
    lexical = torch.tensor([[0.5]], dtype=torch.float32)

    object_ids = torch.tensor(
        [[1, 0, 0, 0]],
        dtype=torch.long
    )

    object_numeric = torch.zeros((1, 5), dtype=torch.float32)
    line_basic = torch.zeros((1, 6), dtype=torch.float32)

    font_ids = torch.tensor(
        [[1, 0, 0]],
        dtype=torch.long
    )

    font_numeric = torch.zeros((1, 4), dtype=torch.float32)

    with torch.no_grad():
        output = detector(
            lexical,
            object_ids,
            object_numeric,
            line_basic,
            font_ids,
            font_numeric
        )

    assert output.ndim == 1

    probability = torch.sigmoid(output)

    assert torch.all(probability >= 0)
    assert torch.all(probability <= 1)

def test_pdf_detector_supports_batch_size_three(detector):
    batch_size = 3
    lexical = torch.rand(batch_size, 1)

    object_ids = torch.tensor(
        [
            [1, 2, 0, 0],
            [3, 4, 5, 0],
            [6, 0, 0, 0]
        ],
        dtype=torch.long
    )

    object_numeric = torch.rand(batch_size, 5)
    line_basic = torch.rand(batch_size, 6)

    font_ids = torch.tensor(
        [
            [1, 2, 0],
            [3, 0, 0],
            [4, 5, 6]
        ],
        dtype=torch.long
    )

    font_numeric = torch.rand(batch_size, 4)

    with torch.no_grad():
        output = detector(
            lexical,
            object_ids,
            object_numeric,
            line_basic,
            font_ids,
            font_numeric
        )

    assert output.shape == (batch_size,)

def test_pdf_detector_components_have_expected_sizes(detector):
    assert detector.lexical[0].in_features == 1
    assert detector.lexical[0].out_features == 16
    assert detector.object_numeric[0].in_features== 5
    assert detector.object_numeric[0].out_features == 32
    assert detector.lines[0].in_features == 6
    assert detector.fonts.numeric[0].in_features == 4
    assert detector.classifier[-1].out_features == 1

def test_pdf_detector_eval_mode_disables_dropout(detector):
    detector.eval()
    assert detector.training is False

    for module in detector.modules():
        if isinstance(module, torch.nn.Dropout):
            assert module.training is False