from pathlib import Path

import pytest

from src.libs.loader.image_loader import ImageLoader
from src.libs.loader.loader_factory import LoaderFactory
from src.libs.loader.office_loader import OfficeLoader
from src.libs.loader.pdf_loader import PdfLoader


def test_loader_factory_selects_pdf_loader(tmp_path):
    factory = LoaderFactory(image_storage_dir=tmp_path)

    loader = factory.create("example.pdf")

    assert isinstance(loader, PdfLoader)
    assert loader.image_storage_dir == tmp_path


def test_loader_factory_selects_office_loader():
    factory = LoaderFactory()

    assert isinstance(factory.create("example.docx"), OfficeLoader)
    assert isinstance(factory.create("example.doc"), OfficeLoader)


def test_loader_factory_selects_image_loader(tmp_path):
    factory = LoaderFactory(image_storage_dir=tmp_path)

    loader = factory.create(Path("example.JPG"))

    assert isinstance(loader, ImageLoader)
    assert loader.image_storage_dir == tmp_path


def test_loader_factory_rejects_unsupported_extension():
    factory = LoaderFactory()

    with pytest.raises(ValueError, match="Unsupported file type"):
        factory.create("example.txt")
