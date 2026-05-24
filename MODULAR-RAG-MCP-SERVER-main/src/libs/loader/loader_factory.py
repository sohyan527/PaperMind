"""Factory for selecting document loaders by file extension."""

from __future__ import annotations

from pathlib import Path

from src.libs.loader.base_loader import BaseLoader
from src.libs.loader.image_loader import ImageLoader
from src.libs.loader.office_loader import OfficeLoader
from src.libs.loader.pdf_loader import PdfLoader


class LoaderFactory:
    """Create a loader that matches the input file type."""

    PDF_EXTENSIONS = {".pdf"}
    OFFICE_EXTENSIONS = {".doc", ".docx"}
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}

    def __init__(
        self,
        extract_images: bool = True,
        image_storage_dir: str | Path = "data/images",
        libreoffice_binary: str = "soffice",
    ):
        self.extract_images = extract_images
        self.image_storage_dir = Path(image_storage_dir)
        self.libreoffice_binary = libreoffice_binary

    @property
    def supported_extensions(self) -> set[str]:
        return self.PDF_EXTENSIONS | self.OFFICE_EXTENSIONS | self.IMAGE_EXTENSIONS

    def create(self, file_path: str | Path) -> BaseLoader:
        suffix = Path(file_path).suffix.lower()

        if suffix in self.PDF_EXTENSIONS:
            return PdfLoader(
                extract_images=self.extract_images,
                image_storage_dir=self.image_storage_dir,
            )

        if suffix in self.OFFICE_EXTENSIONS:
            return OfficeLoader(
                libreoffice_binary=self.libreoffice_binary,
                image_storage_dir=self.image_storage_dir,
                extract_images=self.extract_images,
            )

        if suffix in self.IMAGE_EXTENSIONS:
            return ImageLoader(image_storage_dir=self.image_storage_dir)

        supported = ", ".join(sorted(self.supported_extensions))
        raise ValueError(f"Unsupported file type '{suffix}'. Supported types: {supported}")
