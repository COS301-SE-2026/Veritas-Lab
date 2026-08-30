import json
import sys
from pathlib import Path

import app.training.pdf.build_dataset as build_dataset

def test_pdfs_finds_recursive_pdfs_sorted(tmp_path):
    nested = tmp_path / "nested"
    nested.mkdir()

    pdf_b = tmp_path / "b.pdf"
    pdf_a = nested / "a.pdf"
    not_pdf = tmp_path / "notes.txt"

    pdf_b.touch()
    pdf_a.touch()
    not_pdf.touch()

    result = build_dataset.pdfs(tmp_path)

    assert result == sorted(
        [
            pdf_a,
            pdf_b
        ]
    )

def test_main_with_lexical_analysis(monkeypatch, tmp_path):
    ai_dir = tmp_path / "ai"
    authentic_dir = tmp_path / "authentic"
    output = tmp_path / "features.jsonl"

    ai_dir.mkdir()
    authentic_dir.mkdir()

    ai_pdf = ai_dir / "ai.pdf"
    authentic_pdf = authentic_dir / "authentic.pdf"

    ai_pdf.touch()
    authentic_pdf.touch()

    def fake_extract_pdf_features(path):
        return {
            "path": str(path),
            "page_count": 1
        }

    def fake_extract_pdf_text(path):
        return f"text from {path.name}"

    def fake_lexical_ai_probability(text):
        if "ai.pdf" in text:
            return 0.9

        return 0.1

    monkeypatch.setattr(
        build_dataset,
        "extract_pdf_features",
        fake_extract_pdf_features
    )

    monkeypatch.setattr(
        build_dataset,
        "extract_pdf_text",
        fake_extract_pdf_text
    )

    monkeypatch.setattr(
        build_dataset,
        "lexical_ai_probability",
        fake_lexical_ai_probability
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_dataset.py",
            "--ai-dir",
            str(ai_dir),
            "--authentic-dir",
            str(authentic_dir),
            "--output",
            str(output) 
        ]
    )

    build_dataset.main()

    lines = output.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2

    rows = [
        json.loads(line)
        for line in lines
    ]

    ai_row = next(
        row
        for row in rows
        if row["label"] == 1
    )

    authentic_row = next(
        row
        for row in rows
        if row["label"] == 0
    )

    assert ai_row["lexical_ai_probability"] == 0.9
    assert authentic_row["lexical_ai_probability"] == 0.1

    assert ai_row["page_count"] == 1
    assert authentic_row["page_count"] == 1

def test_main_skip_lexical(monkeypatch, tmp_path):
    ai_dir = tmp_path / "ai"
    authentic_dir = tmp_path / "authentic"
    output = tmp_path / "features.jsonl"

    ai_dir.mkdir()
    authentic_dir.mkdir()

    ai_pdf = ai_dir / "ai.pdf"
    ai_pdf.touch()

    monkeypatch.setattr(
        build_dataset,
        "extract_pdf_features",
        lambda path: {
            "path": str(path)
        }
    )

    def fail_if_called(path):
        raise AssertionError("extract_pdf_text should not be called")

    monkeypatch.setattr(
        build_dataset,
        "extract_pdf_text",
        fail_if_called
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_dataset.py",
            "--ai-dir",
            str(ai_dir),
            "--authentic-dir",
            str(authentic_dir),
            "--output",
            str(output),
            "--skip-lexical"
        ]
    )

    build_dataset.main()

    lines = output.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    row = json.loads(lines[0])

    assert row["label"] == 1
    assert row["lexical_ai_probability"] == 0.5

def test_main_continues_when_pdf_fails(monkeypatch, tmp_path, capsys):
    ai_dir = tmp_path / "ai"
    authentic_dir = tmp_path / "authentic"
    output = tmp_path / "features.jsonl"

    ai_dir.mkdir()
    authentic_dir.mkdir()

    good_pdf = ai_dir / "good.pdf"
    bad_pdf = ai_dir / "bad.pdf"

    good_pdf.touch()
    bad_pdf.touch()

    def fake_extract_pdf_features(path):
        if path.name == "bad.pdf":
            raise RuntimeError("broken PDF")

        return {
            "path": str(path)
        }

    monkeypatch.setattr(
        build_dataset,
        "extract_pdf_features",
        fake_extract_pdf_features
    )

    monkeypatch.setattr(
        build_dataset,
        "extract_pdf_text",
        lambda path: "some text"
    )

    monkeypatch.setattr(
        build_dataset,
        "lexical_ai_probability",
        lambda text: 0.8
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_dataset.py",
            "--ai-dir",
            str(ai_dir),
            "--authentic-dir",
            str(authentic_dir),
            "--output",
            str(output)
        ]
    )

    build_dataset.main()

    captured = capsys.readouterr()

    assert "FAILED:" in captured.out
    assert "bad.pdf" in captured.out
    assert "broken PDF" in captured.out

    lines = output.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 1

    row = json.loads(lines[0])

    assert row["label"] == 1
    assert row["lexical_ai_probability"] == 0.8

def test_main_prints_total_pdf_count(monkeypatch, tmp_path, capsys):
    ai_dir = tmp_path / "ai"
    authentic_dir = tmp_path / "authentic"
    output = tmp_path / "features.jsonl"

    ai_dir.mkdir()
    authentic_dir.mkdir()

    (ai_dir / "one.pdf").touch()
    (authentic_dir / "two.pdf").touch()

    monkeypatch.setattr(
        build_dataset,
        "extract_pdf_features",
        lambda path: {}
    )

    monkeypatch.setattr(
        build_dataset,
        "extract_pdf_text",
        lambda path: ""
    )

    monkeypatch.setattr(
        build_dataset,
        "lexical_ai_probability",
        lambda text: 0.5
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_dataset.py",
            "--ai-dir",
            str(ai_dir),
            "--authentic-dir",
            str(authentic_dir),
            "--output",
            str(output)
        ]
    )

    build_dataset.main()

    captured = capsys.readouterr()

    assert "Total PDFs: 2" in captured.out
