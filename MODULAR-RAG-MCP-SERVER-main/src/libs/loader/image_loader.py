"""Image file loader for multimodal ingestion.

Image files are represented as a tiny document containing a single
``[IMAGE: id]`` placeholder so the existing ImageCaptioner can enrich it.
"""

from __future__ import annotations

import hashlib
import logging
import shutil
from pathlib import Path
from typing import Any, Dict

from PIL import Image

from src.core.types import Document
from src.libs.loader.base_loader import BaseLoader

logger = logging.getLogger(__name__)


class ImageLoader(BaseLoader):
    """Load standalone image files into the RAG document contract."""

    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg"}

    def __init__(self, image_storage_dir: str | Path = "data/images"):
        self.image_storage_dir = Path(image_storage_dir)

    def load(self, file_path: str | Path) -> Document:
        path = self._validate_file(file_path)
        suffix = path.suffix.lower()
        if suffix not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported image file type: {path.suffix}")

        doc_hash = self._compute_file_hash(path)
        doc_id = f"doc_{doc_hash[:16]}"
        image_id = f"{doc_hash[:8]}_1_1"
        image_dir = self.image_storage_dir / doc_hash
        image_dir.mkdir(parents=True, exist_ok=True)

        stored_path = image_dir / f"{image_id}{suffix}"
        if path.resolve() != stored_path.resolve():
            shutil.copy2(path, stored_path)

        width, height = self._read_dimensions(stored_path)
        placeholder = f"[IMAGE: {image_id}]"

        image_path = self._display_path(stored_path)
        image_metadata: Dict[str, Any] = {
            "id": image_id,
            "path": image_path,
            "page": 1,
            "text_offset": 0,
            "text_length": len(placeholder),
            "position": {
                "width": width,
                "height": height,
                "page": 1,
                "index": 1,
            },
        }

        metadata: Dict[str, Any] = {
            "source_path": str(path),
            "doc_type": "image",
            "doc_hash": doc_hash,
            "title": path.stem,
            "images": [image_metadata],
        }

        return Document(id=doc_id, text=placeholder, metadata=metadata)

    def _compute_file_hash(self, file_path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _read_dimensions(self, image_path: Path) -> tuple[int, int]:
        try:
            with Image.open(image_path) as img:
                return img.size
        except Exception as e:
            logger.warning("Failed to read image dimensions for %s: %s", image_path, e)
            return 0, 0

    def _display_path(self, image_path: Path) -> str:
        try:
            return str(image_path.relative_to(Path.cwd()))
        except ValueError:
            return str(image_path.absolute())
