import numpy as np
import torch
from types import SimpleNamespace
import app.training.pdf.lexical as lexical
import pytest

def clear_cache(function):
    cache_clear = getattr(
        function,
        "cache_clear",
        None
    )

    if cache_clear:
        cache_clear()

@pytest.fixture(autouse=True)
def clear_model_caches():
    clear_cache(lexical.get_training_tokeniser)
    clear_cache(lexical.get_inference_model)
    clear_cache(lexical.get_inference_tokeniser)

    yield

    clear_cache(lexical.get_training_tokeniser)
    clear_cache(lexical.get_inference_model)
    clear_cache(lexical.get_inference_tokeniser)

def test_get_training_tokeniser_loads_and_caches(monkeypatch):
    fake_tokeniser = object()
    calls = []

    def fake_from_pretrained(name):
        calls.append(name)
        return fake_tokeniser

    monkeypatch.setattr(
        lexical.AutoTokenizer,
        "from_pretrained",
        fake_from_pretrained
    )

    first = lexical.get_training_tokeniser()
    second = lexical.get_training_tokeniser()

    assert first is fake_tokeniser
    assert second is fake_tokeniser
    assert calls == [lexical.TOKENIZER_NAME]

def test_get_inference_model_missing(monkeypatch, tmp_path):
    missing_path = tmp_path / "missing_model"

    monkeypatch.setattr(
        lexical,
        "MODEL_OUTPUT_PATH",
        missing_path
    )

    lexical.get_inference_model.cache_clear()

    with pytest.raises(
        FileNotFoundError,
        match="Lexical model has not been trained yet"
    ):
        lexical.get_inference_model()

def test_get_inference_model_loads_and_caches(monkeypatch, tmp_path):
    model_path = tmp_path / "model"
    model_path.mkdir()

    class FakeModel:
        def __init__(self):
            self.eval_called = False

        def eval(self):
            self.eval_called = True
            return self

    fake_model = FakeModel()
    calls = []

    def fake_from_pretrained(path):
        calls.append(path)
        return fake_model

    monkeypatch.setattr(
        lexical,
        "MODEL_OUTPUT_PATH",
        model_path
    )

    monkeypatch.setattr(
        lexical.AutoModelForSequenceClassification,
        "from_pretrained",
        fake_from_pretrained
    )

    lexical.get_inference_model.cache_clear()
    first = lexical.get_inference_model()
    second = lexical.get_inference_model()

    assert first is fake_model
    assert second is fake_model
    assert fake_model.eval_called is True
    assert calls == [model_path]

def test_get_inference_tokeniser_missing(monkeypatch, tmp_path):
    missing_path = tmp_path / "missing_model"
    monkeypatch.setattr(
        lexical,
        "MODEL_OUTPUT_PATH",
        missing_path
    )

    lexical.get_inference_tokeniser.cache_clear()

    with pytest.raises(
        FileNotFoundError,
        match="Lexical model has not been trained yet"
    ):
        lexical.get_inference_tokeniser()

def test_get_inference_tokeniser_loads(monkeypatch, tmp_path):
    model_path = tmp_path / "model"
    model_path.mkdir()

    fake_tokeniser = object()

    monkeypatch.setattr(
        lexical,
        "MODEL_OUTPUT_PATH",
        model_path
    )

    monkeypatch.setattr(
        lexical.AutoTokenizer,
        "from_pretrained",
        lambda path: fake_tokeniser
    )

    lexical.get_inference_tokeniser.cache_clear()

    assert lexical.get_inference_tokeniser() is fake_tokeniser

def test_create_model(monkeypatch):
    captured = {}
    fake_model = object()

    def fake_from_pretrained(name, **kwargs):
        captured["name"] = name
        captured["kwargs"] = kwargs
        return fake_model

    monkeypatch.setattr(
        lexical.AutoModelForSequenceClassification,
        "from_pretrained",
        fake_from_pretrained
    )

    result = lexical.create_model()
    assert result is fake_model
    assert captured["name"] == "distilroberta-base"
    assert captured["kwargs"]["num_labels"] == 2

    assert captured["kwargs"]["id2label"] == {
        0: "0_authentic",
        1: "1_ai"
    }

    assert captured["kwargs"]["label2id"] == {
        "0_authentic": 0,
        "1_ai": 1
    }

class FakeRect:
    def __init__(self, width, height):
        self.width = width
        self.height = height

class FakeOCRPage:
    def __init__(self, width=1000, height=1000, images=None):
        self.rect = FakeRect(width, height)
        self.images = images or []

    def get_image_info(self):
        return self.images

def test_page_has_ocr_candidate_zero_page_area():
    page = FakeOCRPage(width=0, height=1000)

    assert lexical.page_has_ocr_candidate(page) is False

def test_page_has_ocr_candidate_rejects_small_image():
    page = FakeOCRPage(
        images=[
            {
                "width": 50,
                "height": 50,
                "bbox": (0, 0, 900, 900)
            }
        ]
    )

    assert lexical.page_has_ocr_candidate(page) is False

def test_page_has_ocr_candidate_rejects_missing_bbox():
    page = FakeOCRPage(
        images=[
            {
                "width": 500,
                "height": 500,
                "bbox": None
            }
        ]
    )

    assert lexical.page_has_ocr_candidate(page) is False

def test_extract_pdf_text_falls_back_when_ocr_returns_empty(monkeypatch, tmp_path):
    class Page:
        number = 0

        def get_text(self, *args, **kwargs):
            if "textpage" in kwargs:
                return ""

            return "Fallback"

        def get_textpage_ocr(self, **kwargs):
            return object()

    monkeypatch.setattr(
        lexical.pymupdf,
        "open",
        lambda path: FakeDocument([Page()])
    )

    monkeypatch.setattr(
        lexical,
        "page_has_ocr_candidate",
        lambda page: True
    )

    result = lexical.extract_pdf_text(tmp_path / "document.pdf")
    assert result == "Fallback"


def test_page_has_ocr_candidate_rejects_low_coverage():
    page = FakeOCRPage(
        images=[
            {
                "width": 200,
                "height": 200,
                "bbox": (0, 0, 200, 200)
            }
        ]
    )

    assert lexical.page_has_ocr_candidate(page) is False

def test_page_has_ocr_candidate_accepts_large_image():
    page = FakeOCRPage(
        images=[
            {
                "width": 600,
                "height": 600,
                "bbox": (0, 0, 600, 600)
            }
        ]
    )

    assert lexical.page_has_ocr_candidate(page) is True

class FakeDocument:
    def __init__(self, pages):
        self.pages = pages

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def __iter__(self):
        return iter(self.pages)

def test_extract_pdf_text_uses_native_text(monkeypatch, tmp_path):
    expected = "This is sufficiently long embedded PDF text."

    class Page:
        def get_text(self, *args, **kwargs):
            return expected

    monkeypatch.setattr(
        lexical.pymupdf,
        "open",
        lambda path: FakeDocument([Page()])
    )

    result = lexical.extract_pdf_text(tmp_path / "document.pdf")
    assert result == expected

def test_extract_pdf_text_keeps_short_text_without_ocr(monkeypatch, tmp_path):
    class Page:
        def get_text(self, *args, **kwargs):
            return "Short text"

    monkeypatch.setattr(
        lexical.pymupdf,
        "open",
        lambda path: FakeDocument([Page()])
    )

    monkeypatch.setattr(
        lexical,
        "page_has_ocr_candidate",
        lambda page: False
    )

    result = lexical.extract_pdf_text(tmp_path / "document.pdf")
    assert result == "Short text"

def test_extract_pdf_text_uses_ocr(monkeypatch, tmp_path):
    class Page:
        number = 0

        def get_text(self, *args, **kwargs):
            if "textpage" in kwargs:
                return "Text extracted successfully using OCR."
        
            return ""

        def get_textpage_ocr(self, **kwargs):
            assert kwargs["language"] == "eng"
            assert kwargs["dpi"] == 300
            assert kwargs["full"] is True
            
            return object()

    monkeypatch.setattr(
        lexical.pymupdf,
        "open",
        lambda path: FakeDocument([Page()])
    )

    monkeypatch.setattr(
        lexical,
        "page_has_ocr_candidate",
        lambda page: True
    )

    result = lexical.extract_pdf_text(tmp_path / "document.pdf")
    assert result == "Text extracted successfully using OCR."

def test_extract_pdf_text_falls_back_when_ocr_fails(monkeypatch, tmp_path, capsys):
    class Page:
        number = 0
    
        def get_text(self, *args, **kwargs):
            return "Fallback"
    
        def get_textpage_ocr(self, **kwargs):
            raise RuntimeError("OCR error")

    monkeypatch.setattr(
        lexical.pymupdf,
        "open",
        lambda path: FakeDocument([Page()])
    )

    monkeypatch.setattr(
        lexical,
        "page_has_ocr_candidate",
        lambda page: True
    )

    result = lexical.extract_pdf_text(tmp_path / "document.pdf")

    output = capsys.readouterr().out
    assert result == "Fallback"
    assert "OCR failed" in output

def test_load_split(monkeypatch, tmp_path):
    authentic = tmp_path / "0_authentic"
    ai = tmp_path / "1_ai"
    authentic.mkdir()
    ai.mkdir()

    (authentic / "authentic.pdf").touch()
    (authentic / "empty.pdf").touch()
    (ai / "ai.pdf").touch()

    def fake_extract(path):
        if path.name == "empty.pdf":
            return ""
    
        return f"text from {path.name}"

    monkeypatch.setattr(
        lexical,
        "extract_pdf_text",
        fake_extract
    )

    dataset = lexical.load_split(tmp_path)
    
    assert len(dataset) == 2
    assert sorted(dataset["label"]) == [0, 1]
    
    assert "text from authentic.pdf" in dataset["text"]
    assert "text from ai.pdf" in dataset["text"]

def test_pdf_ai_probability_returns_neutral_when_no_text(monkeypatch):
    monkeypatch.setattr(
        lexical,
        "extract_pdf_text",
        lambda path: ""
    )

    assert lexical.pdf_ai_probability("test.pdf") == 0.5

def test_pdf_ai_probability_calls_lexical_model(monkeypatch):
    monkeypatch.setattr(
        lexical,
        "extract_pdf_text",
        lambda path: "Some extracted text"
    )

    captured = {}

    def fake_probability(text, max_chunks=None):
        captured["text"] = text
        captured["max_chunks"] = max_chunks
        return 0.83

    monkeypatch.setattr(
        lexical,
        "lexical_ai_probability",
        fake_probability
    )

    result = lexical.pdf_ai_probability(
        "test.pdf",
        max_chunks=4
    )

    assert result == 0.83
    assert captured["text"] == "Some extracted text"
    assert captured["max_chunks"] == 4

def test_prepare_dataset_limits_chunks(monkeypatch):
    class FakeTokeniser:
        def __call__(self, text, **kwargs):
            return {
                "input_ids": [
                    [1,2],
                    [3,4],
                    [5,6]
                ],

                "attention_mask": [
                    [1,1],
                    [1,1],
                    [1,1]
                ]
            }

    monkeypatch.setattr(
        lexical,
        "get_training_tokeniser",
        lambda: FakeTokeniser()
    )

    monkeypatch.setattr(
        lexical,
        "MAX_TRAINING_CHUNKS_PER_PDF",
        2
    )

    raw_dataset = [
        {
            "text": "example text",
            "label": 1,
            "pdf_id": "example.pdf"
        }
    ]

    prepared, pdf_ids = lexical.prepare_dataset(raw_dataset)

    assert len(prepared) == 2
    assert prepared["label"] == [1, 1]
    
    assert pdf_ids == [
        "example.pdf",
        "example.pdf"
    ]

def test_create_pdf_metrics_returns_correct_metrics():
    pdf_ids = [
        "ai.pdf",
        "ai.pdf",
        "authentic.pdf"
    ]

    compute_metrics = lexical.create_pdf_metrics(pdf_ids)

    logits = np.array(
        [
            [0.0, 3.0],
            [0.0, 2.0],
            [3.0, 0.0]
        ]
    )

    labels = np.array(
        [
            1,
            1,
            0
        ]
    )

    result = compute_metrics((logits, labels))

    assert result["accuracy"] == 1.0
    assert result["precision"] == 1.0
    assert result["recall"] == 1.0
    assert result["f1"] == 1.0

def test_lexical_ai_probability_empty_text():
    assert lexical.lexical_ai_probability("") == 0.5
    assert lexical.lexical_ai_probability(None) == 0.5

def test_lexical_ai_probability_runs_in_batches(monkeypatch):
    class FakeTokeniser:
        def __call__(self, text, **kwargs):
            return {
                "input_ids": torch.ones(
                    (5,4),
                    dtype=torch.long
                ),
                "attention_mask": torch.ones(
                    (5,4),
                    dtype=torch.long
                )
            }

    class FakeModel:
        def __init__(self):
            self.calls = 0

        def __call__(self, input_ids, attention_mask):
            self.calls += 1
            
            batch_size = input_ids.shape[0]
            
            logits = torch.tensor(
                [[0.0, 2.0]] * batch_size,
                dtype=torch.float32
            )
            
            return SimpleNamespace(logits=logits)

    fake_model = FakeModel()

    monkeypatch.setattr(
        lexical,
        "get_inference_model",
        lambda: fake_model
    )

    monkeypatch.setattr(
        lexical,
        "get_inference_tokeniser",
        lambda: FakeTokeniser()
    )

    monkeypatch.setattr(
        lexical,
        "INFERENCE_BATCH_SIZE",
        2
    )

    probability = lexical.lexical_ai_probability(
        "Some document text",
        max_chunks=3
    )

    expected = torch.softmax(
        torch.tensor([0.0, 2.0]),
        dim=-1
    )[1].item()

    assert probability == pytest.approx(
        expected,
        rel=1e-5
    )

    assert fake_model.calls == 2

def test_lexical_ai_probability_no_chunks(monkeypatch):
    class FakeTokeniser:
        def __call__(self, text, **kwargs):
            return {
                "input_ids": torch.empty(
                    (0,4),
                    dtype=torch.long
                ),

                "attention_mask": torch.empty(
                    (0,4),
                    dtype=torch.long
                )
            }

    monkeypatch.setattr(
        lexical,
        "get_inference_model",
        lambda: object()
    )

    monkeypatch.setattr(
        lexical,
        "get_inference_tokeniser",
        lambda: FakeTokeniser()
    )

    result = lexical.lexical_ai_probability(
        "Some text"
    )

    assert result == 0.5

def test_test_model_pdf_level(monkeypatch, tmp_path):
    authentic = tmp_path / "0_authentic"
    ai = tmp_path / "1_ai"

    authentic.mkdir()
    ai.mkdir()

    (authentic / "authentic.pdf").touch()
    (ai / "ai.pdf").touch()

    monkeypatch.setattr(
        lexical,
        "TEST_PATH",
        tmp_path
    )

    def fake_probability(path, max_chunks=None):
        if path.name == "ai.pdf":
            return 0.90

        return 0.10  

    monkeypatch.setattr(
        lexical,
        "pdf_ai_probability",
        fake_probability
    )

    results = lexical.test_model_pdf_level()

    assert results["accuracy"] == 1.0
    assert results["precision"] == 1.0
    assert results["recall"] == 1.0
    assert results["f1"] == 1.0

def test_test_model_pdf_level_raises_when_no_pdfs(monkeypatch, tmp_path):
    (tmp_path / "0_authentic").mkdir()
    (tmp_path / "1_ai").mkdir()

    monkeypatch.setattr(
        lexical,
        "TEST_PATH",
        tmp_path
    )

    with pytest.raises(
        ValueError,
        match="No test PDFs with extractable text were found"
    ):
        lexical.test_model_pdf_level()

def test_train_model_raises_when_training_set_empty(monkeypatch):
    def fake_load_split(path):
        if path == lexical.TRAIN_PATH:
            return []

        return [1]

    monkeypatch.setattr(
        lexical,
        "load_split",
        fake_load_split
    )

    with pytest.raises(
        ValueError,
        match="No training PDFs"
    ):
        lexical.train_model()

def test_train_model_raises_when_validation_set_empty(monkeypatch):
    def fake_load_split(path):
        if path == lexical.TRAIN_PATH:
            return [1]

        return []

    monkeypatch.setattr(
        lexical,
        "load_split",
        fake_load_split
    )

    with pytest.raises(
        ValueError,
        match="No validation PDFs"
    ):
        lexical.train_model()

def test_train_model_success(monkeypatch):
    train_raw = [{"text": "train"}]
    validation_raw = [{"text": "validation"}]

    def fake_load_split(path):
        if path == lexical.TRAIN_PATH:
            return train_raw

        return validation_raw

    monkeypatch.setattr(
        lexical,
        "load_split",
        fake_load_split
    )

    def fake_prepare_dataset(dataset):
        if dataset is train_raw:
            return "train_dataset", []

        return (
            "validation_dataset",
            ["validation.pdf"]
        )

    monkeypatch.setattr(
        lexical,
        "prepare_dataset",
        fake_prepare_dataset
    )

    fake_model = object()

    monkeypatch.setattr(
        lexical,
        "create_model",
        lambda: fake_model
    )

    monkeypatch.setattr(
        lexical,
        "TrainingArguments",
        lambda **kwargs: kwargs
    )

    class FakeTrainer:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.train_called = False
            self.saved_path = None

        def train(self):
            self.train_called = True

        def save_model(self, path):
            self.saved_path = path

    monkeypatch.setattr(
        lexical,
        "Trainer",
        FakeTrainer
    )

    class FakeTrainingTokeniser:
        def __init__(self):
            self.saved_path = None

        def save_pretrained(self, path):
            self.saved_path = path

    fake_tokeniser = FakeTrainingTokeniser()

    monkeypatch.setattr(
        lexical,
        "get_training_tokeniser",
        lambda: fake_tokeniser
    )

    trainer = lexical.train_model()

    assert trainer.train_called is True
    assert trainer.saved_path == (lexical.MODEL_OUTPUT_PATH)
    assert fake_tokeniser.saved_path == (lexical.MODEL_OUTPUT_PATH)
    assert trainer.kwargs["model"] is fake_model
    assert trainer.kwargs["train_dataset"] == "train_dataset"
    assert trainer.kwargs["eval_dataset"] == "validation_dataset"