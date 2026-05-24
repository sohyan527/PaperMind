from pathlib import Path

from PIL import Image

from src.core.settings import load_settings
from src.core.types import Document
from src.ingestion.chunking.document_chunker import DocumentChunker
from src.libs.loader.image_loader import ImageLoader


def test_image_loader_creates_document_with_image_metadata(tmp_path):
    source = tmp_path / "sample.png"
    Image.new("RGB", (32, 24), color="white").save(source)

    loader = ImageLoader(image_storage_dir=tmp_path / "images")
    doc = loader.load(source)

    assert isinstance(doc, Document)
    assert doc.id.startswith("doc_")
    assert doc.text.startswith("[IMAGE: ")
    assert doc.metadata["source_path"] == str(source.resolve())
    assert doc.metadata["doc_type"] == "image"
    assert doc.metadata["title"] == "sample"

    images = doc.metadata["images"]
    assert len(images) == 1
    image_meta = images[0]
    assert image_meta["id"] in doc.text
    assert image_meta["text_offset"] == 0
    assert image_meta["text_length"] == len(doc.text)
    assert image_meta["position"]["width"] == 32
    assert image_meta["position"]["height"] == 24
    assert Path(image_meta["path"]).exists()


def test_image_only_document_keeps_image_metadata_after_chunking(tmp_path):
    source = tmp_path / "photo.jpg"
    Image.new("RGB", (48, 36), color="white").save(source)

    loader = ImageLoader(image_storage_dir=tmp_path / "images")
    doc = loader.load(source)
    chunks = DocumentChunker(load_settings()).split_document(doc)

    assert len(chunks) == 1
    chunk = chunks[0]
    image_meta = doc.metadata["images"][0]
    assert f"[IMAGE: {image_meta['id']}]" in chunk.text
    assert chunk.metadata["image_refs"] == [image_meta["id"]]
    assert chunk.metadata["images"] == [image_meta]
    assert chunk.metadata["page_num"] == 1
