import re
from pathlib import Path
from collections import Counter
import pymupdf

BASE_14 = {
    "Courier","Courier-Bold","Courier-Oblique","Courier-BoldOblique",
    "Helvetica","Helvetica-Bold","Helvetica-Oblique","Helvetica-BoldOblique",
    "Times-Roman","Times-Bold","Times-Italic","Times-BoldItalic", "Symbol","ZapfDingbats",
}

OBJECT_TYPES = {
    "/Type /Pages": "PAGES",
    "/Type /Catalog": "CATALOG",
    "/Type /FontDescriptor": "FONT_DESCRIPTOR",
    "/Type /Font": "FONT",
    "/Subtype /Type0": "FONT",
    "/Subtype /Type1": "FONT",
    "/Subtype /TrueType": "FONT",
    "/Subtype /Image": "IMAGE",
    "/Type /XObject": "XOBJECT",
    "/Type /XRef": "XREF_STREAM",
    "/Type /ObjStm": "OBJECT_STREAM",
    "/Type /FileSpec": "FILESPEC",
    "/Type /Filespec": "FILESPEC",
    "/Subtype /XML": "METADATA_OBJECT",
    "/Producer": "INFO",
    "/Creator": "INFO",
    "/CreationDate": "INFO",
}

def classify_object(obj, is_stream):
    if "/Type /Page" in obj and "/Type /Pages" not in obj:
        return "PAGE"

    for pattern, object_type in OBJECT_TYPES.items():
        if pattern in obj:
            return object_type

    return "STREAM" if is_stream else "OTHER"

def extract_object_sequence(pdf_path, max_objects=512):
    doc = pymupdf.open(str(pdf_path))

    try:
        seq = []
        for xref in range(1, min(doc.xref_length(), max_objects + 1)):
            try:
                obj = doc.xref_object(xref, compressed=False)
                seq.append(classify_object(obj, doc.xref_is_stream(xref)))
            except Exception:
                seq.append("UNREADABLE")
        return seq
    finally:
        doc.close()

def extract_line_features(pdf_path):
    data = Path(pdf_path).read_bytes()
    crlf = data.count(b"\r\n")
    lf = max(0, data.count(b"\n") - crlf)
    cr = max(0, data.count(b"\r") - crlf)
    total = lf + crlf + cr
    size = max(len(data), 1)

    return {
        "lf_count": float(lf),
        "crlf_count": float(crlf),
        "cr_count": float(cr),
        "lf_ratio": lf / max(total, 1),
        "crlf_ratio": crlf / max(total, 1),
        "cr_ratio": cr / max(total, 1),
        "line_endings_per_kb": total / max(size / 1024.0, 1e-6),
        "classic_xref_count": float(len(re.findall(rb"(?m)^xref\s*$", data))),
        "startxref_count": float(data.count(b"startxref")),
        "eof_count": float(data.count(b"%%EOF")),
    }

def clean_font_name(name):
    return re.sub(r"^[A-Z]{6}\+", "", name or "")

def extract_embedded_font(doc, xref, embedded):
    if xref <= 0:
        return

    try:
        info = doc.extract_font(xref)

        if info and len(info) >= 4 and info[3]:
            embedded.add(xref)

    except (RuntimeError, ValueError):
        pass

def process_font_item(doc, item, fonts, embedded, subtypes):
    xref = int(item[0]) if item and item[0] is not None else 0
    subtype = str(item[2]) if len(item) > 2 else "UNKNOWN"
    raw_name = str(item[3]) if len(item) > 3 else ""
    name = clean_font_name(raw_name)

    base14_count = 0
    subset_count = 0

    if name:
        fonts.append(name)

        if name in BASE_14:
            base14_count = 1

    if re.match(r"^[A-Z]{6}\+", raw_name):
        subset_count = 1

    subtypes[subtype] += 1

    extract_embedded_font(
        doc,
        xref,
        embedded
    )

    return base14_count, subset_count

def build_font_numeric(
    fonts,
    embedded,
    subtypes,
    subset_count,
    base14_count
):
    denom = max(len(fonts), 1)

    return {
        "font_reference_count": float(len(fonts)),
        "unique_font_count": float(len(set(fonts))),
        "embedded_font_count": float(len(embedded)),
        "subset_font_reference_count": float(subset_count),
        "base14_font_reference_count": float(base14_count),
        "non_base14_ratio": (len(fonts) - base14_count) / denom,
        "type0_count": float(subtypes.get("Type0", 0)),
        "type1_count": float(subtypes.get("Type1", 0)),
        "truetype_count": float(subtypes.get("TrueType", 0))
    }

def extract_font_features(pdf_path):
    doc = pymupdf.open(str(pdf_path))

    fonts = []
    embedded = set()
    subtypes = Counter()

    subset_count = 0
    base14_count = 0

    try:
        for page in doc:
            for item in page.get_fonts(full=True):
                base14, subset = process_font_item(
                    doc,
                    item,
                    fonts,
                    embedded,
                    subtypes
                )

                base14_count += base14
                subset_count += subset

        numeric = build_font_numeric(
            fonts,
            embedded,
            subtypes,
            subset_count,
            base14_count
        )

        return sorted(set(fonts)), numeric

    finally:
        doc.close()

def extract_pdf_features(pdf_path):
    path = Path(pdf_path)
    doc = pymupdf.open(str(path))

    try:
        page_count = len(doc)
        xref_count = max(doc.xref_length()-1, 0)
    finally:
        doc.close()

    file_size = max(path.stat().st_size, 1)
    file_size_kb = file_size / 1024.0

    m = re.search(rb"%PDF-(\d+\.\d+)", path.read_bytes()[:16])
    object_sequence = extract_object_sequence(path)
    object_features = extract_object_features(object_sequence)

    version = float(m.group(1)) if m else 0.0
    font_tokens, font_numeric = extract_font_features(path)

    font_numeric["font_references_per_page"] = (font_numeric["font_reference_count"] / max(page_count, 1))
    font_numeric["unique_fonts_per_page"] = (font_numeric["unique_font_count"] / max(page_count, 1))
    font_numeric["embedded_font_ratio"] = (font_numeric["embedded_font_count"] / max(font_numeric["unique_font_count"], 1))
    font_numeric["subset_font_ratio"] = (font_numeric["subset_font_reference_count"] / max(font_numeric["font_reference_count"], 1))

    return {
        "path": str(path),

        "page_count": float(page_count),
        "xref_object_count": float(xref_count),
        "pdf_version": version,
        "file_size_kb": file_size_kb,

        "xref_objects_per_page": xref_count / max(page_count, 1),
        "xref_objects_per_kb": xref_count / max(file_size_kb, 1e-6),

        "object_sequence": object_sequence,
        "object_features": object_features,

        "line_features": extract_line_features(path),

        "font_tokens": font_tokens,
        "font_features": font_numeric,
    }

def extract_object_features(sequence):
    counts = Counter(sequence)
    total = max(len(sequence), 1)

    return {
        "object_count_analyzed": float(len(sequence)),
        "page_object_ratio": counts["PAGE"] / total,
        "pages_object_ratio": counts["PAGES"] / total,
        "catalog_object_ratio": counts["CATALOG"] / total,
        "font_object_ratio": counts["FONT"] / total,
        "font_descriptor_ratio": counts["FONT_DESCRIPTOR"] / total,
        "image_object_ratio": counts["IMAGE"] / total,
        "xobject_ratio": counts["XOBJECT"] / total,
        "stream_object_ratio": counts["STREAM"] / total,
        "xref_stream_ratio": counts["XREF_STREAM"] / total,
        "object_stream_ratio": counts["OBJECT_STREAM"] / total,
        "filespec_ratio": counts["FILESPEC"] / total,
        "metadata_object_ratio": counts["METADATA_OBJECT"] / total,
        "info_object_ratio": counts["INFO"] / total,
        "other_object_ratio": counts["OTHER"] / total,
        "unreadable_object_ratio": counts["UNREADABLE"] / total,
        "unique_object_type_count": float(len(counts)),
    }