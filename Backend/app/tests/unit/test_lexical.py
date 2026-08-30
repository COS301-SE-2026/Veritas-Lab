import argparse
import numpy as np
import torch

from app.training.pdf.features import extract_pdf_features
from app.training.pdf.lexical import extract_pdf_text, lexical_ai_probability
import app.training.pdf.lexical as lexical
from app.training.pdf.model import PDFDetector
import pytest

@pytest.fixture(autouse=True)
def clear_model_caches():
    lexical.get_training_tokeniser.cache_clear()
    lexical.get_inference_model.cache_clear()
    lexical.get_inference_tokeniser.cache_clear()

    yield

    lexical.get_training_tokeniser.cache_clear()
    lexical.get_inference_model.cache_clear()
    lexical.get_inference_tokeniser.cache_clear()

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
