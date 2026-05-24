import io
from types import SimpleNamespace
import zipfile

from PIL import Image

from src.core.types import Document
from src.libs.loader.office_loader import OfficeLoader


def test_office_loader_docx_uses_markitdown_result(tmp_path):
    source = tmp_path / "report.docx"
    source.write_bytes(b"fake docx content")

    loader = OfficeLoader(extract_images=False)
    loader._markitdown = SimpleNamespace(
        convert=lambda _: SimpleNamespace(text_content="# Quarterly Report\n\nRevenue is up.")
    )

    doc = loader.load(source)

    assert isinstance(doc, Document)
    assert doc.id.startswith("doc_")
    assert doc.text == "# Quarterly Report\n\nRevenue is up."
    assert doc.metadata["source_path"] == str(source.resolve())
    assert doc.metadata["doc_type"] == "docx"
    assert doc.metadata["title"] == "Quarterly Report"
    assert "doc_hash" in doc.metadata


def test_office_loader_extracts_docx_embedded_images(tmp_path):
    source = tmp_path / "with-image.docx"
    image_bytes = io.BytesIO()
    Image.new("RGB", (400, 300), color="white").save(image_bytes, format="PNG")

    with zipfile.ZipFile(source, "w") as docx:
        docx.writestr("[Content_Types].xml", "")
        docx.writestr("word/document.xml", "<w:document />")
        docx.writestr("word/media/image1.png", image_bytes.getvalue())

    loader = OfficeLoader(image_storage_dir=tmp_path / "images")
    loader._markitdown = SimpleNamespace(
        convert=lambda _: SimpleNamespace(text_content="# Image Report\n\nSee the chart.")
    )

    doc = loader.load(source)

    assert doc.metadata["doc_type"] == "docx"
    assert "images" in doc.metadata
    assert len(doc.metadata["images"]) == 1

    image_meta = doc.metadata["images"][0]
    assert image_meta["id"] in doc.text
    assert f"[IMAGE: {image_meta['id']}]" in doc.text
    assert image_meta["position"]["width"] == 400
    assert image_meta["position"]["height"] == 300
    assert image_meta["position"]["source"] == "word/media/image1.png"
    assert image_meta["text_offset"] == doc.text.index(f"[IMAGE: {image_meta['id']}]")
    assert image_meta["text_length"] == len(f"[IMAGE: {image_meta['id']}]")


def test_office_loader_skips_duplicate_and_decorative_images(tmp_path):
    source = tmp_path / "filtered-images.docx"

    large = io.BytesIO()
    Image.new("RGB", (500, 320), color="white").save(large, format="PNG")
    large_bytes = large.getvalue()

    small = io.BytesIO()
    Image.new("RGB", (24, 24), color="white").save(small, format="PNG")

    with zipfile.ZipFile(source, "w") as docx:
        docx.writestr("[Content_Types].xml", "")
        docx.writestr("word/document.xml", "<w:document />")
        docx.writestr("word/media/useful.png", large_bytes)
        docx.writestr("word/media/logo-repeat.png", large_bytes)
        docx.writestr("word/media/decorative.png", small.getvalue())

    loader = OfficeLoader(image_storage_dir=tmp_path / "images")
    loader._markitdown = SimpleNamespace(
        convert=lambda _: SimpleNamespace(text_content="# Image Report")
    )

    doc = loader.load(source)

    assert len(doc.metadata["images"]) == 1
    assert doc.text.count("[IMAGE:") == 1
    kept = doc.metadata["images"][0]
    assert kept["position"]["source"] in {
        "word/media/useful.png",
        "word/media/logo-repeat.png",
    }
