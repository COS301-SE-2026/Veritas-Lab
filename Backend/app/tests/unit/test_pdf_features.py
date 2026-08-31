import pytest
import app.training.pdf.features as features

@pytest.mark.parametrize(
    "obj, is_stream, expected",
    [
        ("/Type /Page", False, "PAGE"),
        ("/Type /Pages", False, "PAGES"),
        ("/Type /Catalog", False, "CATALOG"),
        ("/Type /FontDescriptor", False, "FONT_DESCRIPTOR"),
        ("/Type /Font", False, "FONT"),
        ("/Subtype /Type0", False, "FONT"),
        ("/Subtype /Type1", False, "FONT"),
        ("/Subtype /TrueType", False, "FONT"),
        ("/Subtype /Image", False, "IMAGE"),
        ("/Type /XObject", False, "XOBJECT"),
        ("/Type /XRef", False, "XREF_STREAM"),
        ("/Type /ObjStm", False, "OBJECT_STREAM"),
        ("/Type /FileSpec", False, "FILESPEC"),
        ("/Type /Filespec", False, "FILESPEC"),
        ("/Subtype /XML", False, "METADATA_OBJECT"),
        ("/Producer", False, "INFO"),
        ("/Creator", False, "INFO"),
        ("/CreationDate", False, "INFO"),
        ("something else", True, "STREAM"),
        ("something else", False, "OTHER"),
    ]
)
def test_classify_object(obj, is_stream, expected):
    assert features.classify_object(obj, is_stream) == expected

def test_classify_page_does_not_confuse_pages():
    assert features.classify_object("/Type /Pages", False) == "PAGES"

class FakeObjectDocument:
    def __init__(self):
        self.closed = False

    def xref_length(self):
        return 5

    def xref_object(self, xref, compressed=False):
        if xref == 1:
            return "/Type /Page"

        if xref == 2:
            return "/Type /Font"

        if xref == 3:
            raise RuntimeError("Unreadable object")

        return "unknown"

    def xref_is_stream(self, xref):
        return xref == 4

    def close(self):
        self.closed = True

def test_extract_object_sequence(monkeypatch):
    fake_doc = FakeObjectDocument()

    monkeypatch.setattr(
        features.pymupdf,
        "open",
        lambda path: fake_doc
    )

    result = features.extract_object_sequence("test.pdf")

    assert result == [
        "PAGE",
        "FONT",
        "UNREADABLE",
        "STREAM"
    ]

    assert fake_doc.closed is True

def test_extract_object_sequence_respects_max_objects(monkeypatch):
    class FakeDocument:
        def __init__(self):
            self.closed = False

        def xref_length(self):
            return 10

        def xref_object(self, xref, compressed=False):
            return "/Type /Page"

        def xref_is_stream(self, xref):
            return False

        def close(self):
            self.closed = True

    fake_doc = FakeDocument()

    monkeypatch.setattr(
        features.pymupdf,
        "open",
        lambda path: fake_doc
    )

    result = features.extract_object_sequence(
        "test.pdf",
        max_objects=2
    )

    assert result == [
        "PAGE",
        "PAGE"
    ]

    assert fake_doc.closed is True

def test_extract_line_features(tmp_path):
    pdf = tmp_path / "test.pdf"

    data = (
        b"%PDF-1.7\r\n"
        b"line one\r\n"
        b"line two\n"
        b"line three\r\n"
        b"xref\r\n"
        b"startxref\n"
        b"%%EOF"
    )

    pdf.write_bytes(data)

    result = features.extract_line_features(pdf)

    assert result["crlf_count"] == 4
    assert result["lf_count"] == 2
    assert result["cr_count"] == 0
    assert result["startxref_count"] == 1.0
    assert result["eof_count"] == 1.0
    assert result["classic_xref_count"] == 1.0

    assert result["lf_ratio"] == pytest.approx(2/6)
    assert result["crlf_ratio"] == pytest.approx(4/6)
    assert result["cr_ratio"] == 0

def test_extract_line_features_empty_file(tmp_path):
    pdf = tmp_path / "empty.pdf"
    pdf.write_bytes(b"")

    result = features.extract_line_features(pdf)

    assert result["lf_count"] == 0.0
    assert result["crlf_count"] == 0.0
    assert result["cr_count"] == 0.0

    assert result["lf_ratio"] == 0.0
    assert result["crlf_ratio"] == 0.0
    assert result["cr_ratio"] == 0.0

    assert result["line_endings_per_kb"] == 0.0

@pytest.mark.parametrize(
    "raw, expected",
    [
        (
            "ABCDEF+Helvetica",
            "Helvetica"
        ),

        (
            "Helvetica",
            "Helvetica"
        ),

        (
            "",
            ""
        ),

        (
            None,
            ""
        ),

        (
            "ABCDE+Helvetica",
            "ABCDE+Helvetica"
        )
    ]
)
def test_clean_font_name(raw, expected):
    assert features.clean_font_name(raw) == expected

class FakeFontPage:
    def get_fonts(self, full=True):
        return [
            (
                1,
                None,
                "Type1",
                "Helvetica"
            ),

            (
                2,
                None,
                "TrueType",
                "ABCDEF+CustomFont"
            ),

            (
                3,
                None,
                "Type0",
                "AnotherFont"
            ),

            (
                None,
                None,
                "Type1",
                ""
            )
        ]

class FakeFontDocument:
    def __init__(self):
        self.closed = False

    def __iter__(self):
        return iter([FakeFontPage()])

    def extract_font(self, xref):
        if xref == 1:
            return (
                None,
                None,
                None,
                b"font-data"
            )

        if xref == 2:
            return (
                None,
                None,
                None,
                b"font-data"
            )

        if xref == 3:
            return (
                None,
                None,
                None,
                b""
            )

        return None

    def close(self):
        self.closed = True

def test_extract_font_features(monkeypatch):
    fake_doc = FakeFontDocument()

    monkeypatch.setattr(
        features.pymupdf,
        "open",
        lambda path: fake_doc
    )

    font_tokens, numeric = features.extract_font_features("test.pdf")

    assert font_tokens == [
        "AnotherFont",
        "CustomFont",
        "Helvetica"
    ]

    assert numeric["font_reference_count"] == 3.0
    assert numeric["unique_font_count"] == 3.0
    assert numeric["embedded_font_count"] == 2.0
    assert numeric["subset_font_reference_count"] == 1.0
    assert numeric["base14_font_reference_count"] == 1.0
    assert numeric["non_base14_ratio"] == pytest.approx(2/3)
    assert numeric["type0_count"] == 1.0
    assert numeric["type1_count"] == 2.0
    assert numeric["truetype_count"] == 1.0
    assert fake_doc.closed is True

def test_extract_font_features_ignores_extract_font_error(monkeypatch):
    class Page:
        def get_fonts(self, full=True):
            return [
                (
                    5,
                    None,
                    "TrueType",
                    "ExampleFont"
                )
            ]

    class Document:
        def __iter__(self):
            return iter([Page()])

        def extract_font(self, xref):
            raise RuntimeError("bad font")

        def close(self):
            pass

    monkeypatch.setattr(
        features.pymupdf,
        "open",
        lambda path: Document()
    )

    tokens, numeric = features.extract_font_features("test.pdf")

    assert tokens == ["ExampleFont"]
    assert numeric["embedded_font_count"] == 0.0

def test_extract_font_features_with_no_fonts(monkeypatch):
    class Page:
        def get_fonts(self, full=True):
            return []

    class Document:
        def __iter__(self):
            return iter([Page()])

        def close(self):
            pass

    monkeypatch.setattr(
        features.pymupdf,
        "open",
        lambda path: Document()
    )

    tokens, numeric = features.extract_font_features("test.pdf")
    

    assert tokens == []
    assert numeric["font_reference_count"] == 0.0
    assert numeric["unique_font_count"] == 0.0
    assert numeric["non_base14_ratio"] == 0.0

def test_extract_object_features():
    sequence = [
        "PAGE",
        "PAGE",
        "FONT",
        "IMAGE",
        "STREAM",
        "UNREADABLE"
    ]

    result = features.extract_object_features(sequence)

    assert result["object_count_analyzed"] == 6.0
    assert result["page_object_ratio"] == pytest.approx(2/6)
    assert result["font_object_ratio"] == pytest.approx(1/6)
    assert result["image_object_ratio"] == pytest.approx(1/6)
    assert result["stream_object_ratio"] == pytest.approx(1/6)
    assert result["unreadable_object_ratio"] == pytest.approx(1/6)
    assert result["unique_object_type_count"] == 5.0

def test_extract_object_features_empty_sequence():
    result = features.extract_object_features([])

    assert result["object_count_analyzed"] == 0.0
    assert result["page_object_ratio"] == 0.0
    assert result["font_object_ratio"] == 0.0
    assert result["unique_object_type_count"] == 0.0

def test_extract_object_features_all_types():
    sequence = [
        "PAGE",
        "PAGES",
        "CATALOG",
        "FONT",
        "FONT_DESCRIPTOR",
        "IMAGE",
        "XOBJECT",
        "STREAM",
        "XREF_STREAM",
        "OBJECT_STREAM",
        "FILESPEC",
        "METADATA_OBJECT",
        "INFO",
        "OTHER",
        "UNREADABLE"
    ]

    result = features.extract_object_features(sequence)

    expected_ratio = 1 / len(sequence)

    ratio_keys = [
        "page_object_ratio",
        "pages_object_ratio",
        "catalog_object_ratio",
        "font_object_ratio",
        "font_descriptor_ratio",
        "image_object_ratio",
        "xobject_ratio",
        "stream_object_ratio",
        "xref_stream_ratio",
        "object_stream_ratio",
        "filespec_ratio",
        "metadata_object_ratio",
        "info_object_ratio",
        "other_object_ratio",
        "unreadable_object_ratio",
    ]

    for key in ratio_keys:
        assert result[key] == pytest.approx(expected_ratio)

def test_extract_pdf_features(monkeypatch, tmp_path):
    pdf = tmp_path / "document.pdf"

    pdf.write_bytes(
        b"%PDF-1.7\n"
        b"example\n"
    )

    class FakeDocument:
        def __len__(self):
            return 2

        def xref_length(self):
            return 11

        def close(self):
            pass

    monkeypatch.setattr(
        features.pymupdf,
        "open",
        lambda path: FakeDocument()
    )

    monkeypatch.setattr(
        features,
        "extract_object_sequence",
        lambda path: [
            "PAGE",
            "FONT"
        ]
    )

    monkeypatch.setattr(
        features,
        "extract_object_features",
        lambda sequence: {
            "object_count_analyzed": 2.0
        }
    )

    monkeypatch.setattr(
        features,
        "extract_font_features",
        lambda path: (
            [
                "Helvetica",
                "CustomFont"
            ],
            {
                "font_reference_count": 4.0,
                "unique_font_count": 2.0,
                "embedded_font_count": 1.0,
                "subset_font_reference_count": 2.0
            }
        )
    )

    monkeypatch.setattr(
        features,
        "extract_line_features",
        lambda path: {
            "lf_count": 2.0
        }
    )

    result = features.extract_pdf_features(pdf)

    assert result["path"] == str(pdf)
    assert result["page_count"] == 2.0
    assert result["xref_object_count"] == 10.0
    assert result["pdf_version"] == 1.7
    assert result["xref_objects_per_page"] == 5.0
    assert result["object_sequence"] == ["PAGE", "FONT"]
    assert result["object_features"] == {"object_count_analyzed": 2.0}
    assert result["font_tokens"] == [
        "Helvetica",
        "CustomFont"
    ]

    assert result["font_features"]["font_references_per_page"] == 2.0
    assert result["font_features"]["unique_fonts_per_page"] == 1.0
    assert result["font_features"]["embedded_font_ratio"] == 0.5
    assert result["font_features"]["subset_font_ratio"] == 0.5
    assert result["line_features"] == {"lf_count": 2.0}
    assert result["xref_objects_per_kb"] > 0

def test_extract_pdf_features_without_pdf_version(monkeypatch,tmp_path):
    pdf = tmp_path / "document.pdf"
    pdf.write_bytes(
        b"not-a-pdf-header"
    )

    class FakeDocument:
        def __len__(self):
            return 0

        def xref_length(self):
            return 0

        def close(self):
            pass

    monkeypatch.setattr(
        features.pymupdf,
        "open",
        lambda path: FakeDocument()
    )

    monkeypatch.setattr(
        features,
        "extract_object_sequence",
        lambda path: []
    )

    monkeypatch.setattr(
        features,
        "extract_object_features",
        lambda sequence: {}
    )

    monkeypatch.setattr(
        features,
        "extract_font_features",
        lambda path: (
            [],
            {
                "font_reference_count": 0.0,
                "unique_font_count": 0.0,
                "embedded_font_count": 0.0,
                "subset_font_reference_count": 0.0
            }
        )
    )

    monkeypatch.setattr(
        features,
        "extract_line_features",
        lambda path: {}
    )

    result = features.extract_pdf_features(pdf)

    assert result["pdf_version"] == 0.0
    assert result["page_count"] == 0.0
    assert result["xref_object_count"] == 0.0
    assert result["font_features"]["font_references_per_page"] == 0.0
    assert result["font_features"]["unique_fonts_per_page"] == 0.0
    assert result["font_features"]["embedded_font_ratio"] == 0.0
    assert result["font_features"]["subset_font_ratio"] == 0.0
    