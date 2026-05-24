"""Office document loader using MarkItDown.

This loader handles modern Office documents directly and can optionally
convert legacy ``.doc`` files through LibreOffice before parsing.
"""

from __future__ import annotations

import hashlib
import io
import logging
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from markitdown import MarkItDown

    MARKITDOWN_AVAILABLE = True
except ImportError:
    MARKITDOWN_AVAILABLE = False

from src.core.types import Document
from src.libs.loader.base_loader import BaseLoader
from src.libs.loader.image_filter import average_hash, is_decorative_image, is_near_duplicate

from PIL import Image

logger = logging.getLogger(__name__)


class OfficeLoader(BaseLoader):
    """Load Office documents and normalize them to Markdown text."""

    SUPPORTED_EXTENSIONS = {".docx", ".doc"}
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp"}

    def __init__(
        self,
        libreoffice_binary: str = "soffice",
        image_storage_dir: str | Path = "data/images",
        extract_images: bool = True,
    ):
        if not MARKITDOWN_AVAILABLE:
            raise ImportError(
                "MarkItDown is required for OfficeLoader. "
                "Install with: pip install 'markitdown[all]'"
            )

        self.libreoffice_binary = libreoffice_binary
        self.image_storage_dir = Path(image_storage_dir)
        self.extract_images = extract_images
        self._markitdown = MarkItDown()

    def load(self, file_path: str | Path) -> Document:
        """Load and parse a ``.docx`` or ``.doc`` file."""
        path = self._validate_file(file_path)
        suffix = path.suffix.lower()
        if suffix not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported Office file type: {path.suffix}")

        doc_hash = self._compute_file_hash(path)
        doc_id = f"doc_{doc_hash[:16]}"
        parse_path = path
        temp_dir: Optional[tempfile.TemporaryDirectory[str]] = None

        try:
            try:
                if suffix == ".doc":
                    temp_dir = tempfile.TemporaryDirectory()
                    parse_path = self._convert_doc_to_docx(path, Path(temp_dir.name))

                result = self._markitdown.convert(str(parse_path))
                text_content = (
                    result.text_content if hasattr(result, "text_content") else str(result)
                )
            except Exception as e:
                logger.error("Failed to parse Office document %s: %s", path, e)
                raise RuntimeError(f"Office document parsing failed: {e}") from e

            metadata: Dict[str, Any] = {
                "source_path": str(path),
                "doc_type": suffix.lstrip("."),
                "doc_hash": doc_hash,
            }

            title = self._extract_title(text_content)
            if title:
                metadata["title"] = title

            if self.extract_images and parse_path.suffix.lower() == ".docx":
                try:
                    text_content, images_metadata = self._extract_and_process_images(
                        parse_path, text_content, doc_hash
                    )
                    if images_metadata:
                        metadata["images"] = images_metadata
                except Exception as e:
                    logger.warning(
                        "Image extraction failed for Office document %s, "
                        "continuing with text-only: %s",
                        path,
                        e,
                    )

            return Document(id=doc_id, text=text_content, metadata=metadata)
        finally:
            if temp_dir is not None:
                temp_dir.cleanup()

    def _extract_and_process_images(
        self,
        docx_path: Path,
        text_content: str,
        doc_hash: str,
    ) -> tuple[str, List[Dict[str, Any]]]:
        """Extract embedded images from a DOCX zip package."""
        images_metadata: List[Dict[str, Any]] = []
        modified_text = text_content
        seen_image_hashes = set()
        seen_perceptual_hashes = []
        skipped_duplicates = 0
        skipped_decorative = 0
        image_dir = self.image_storage_dir / doc_hash
        image_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(docx_path) as archive:
            media_names = [
                name
                for name in archive.namelist()
                if name.startswith("word/media/")
                and Path(name).suffix.lower() in self.IMAGE_EXTENSIONS
            ]

            for sequence, media_name in enumerate(sorted(media_names), start=1):
                image_bytes = archive.read(media_name)
                image_ext = Path(media_name).suffix.lower().lstrip(".")
                image_content_hash = hashlib.sha256(image_bytes).hexdigest()
                image_perceptual_hash = average_hash(image_bytes)
                width, height = self._read_dimensions(image_bytes)

                if (
                    image_content_hash in seen_image_hashes
                    or is_near_duplicate(image_perceptual_hash, seen_perceptual_hashes)
                ):
                    skipped_duplicates += 1
                    continue
                if is_decorative_image(width, height):
                    skipped_decorative += 1
                    continue
                seen_image_hashes.add(image_content_hash)
                if image_perceptual_hash is not None:
                    seen_perceptual_hashes.append(image_perceptual_hash)

                image_id = self._generate_image_id(doc_hash, sequence)
                image_path = image_dir / f"{image_id}.{image_ext}"

                with open(image_path, "wb") as img_file:
                    img_file.write(image_bytes)

                placeholder = f"[IMAGE: {image_id}]"
                prefix = "\n" if modified_text else ""
                insert_position = len(modified_text) + len(prefix)
                modified_text += f"{prefix}{placeholder}\n"

                image_metadata = {
                    "id": image_id,
                    "path": self._display_path(image_path),
                    "page": 1,
                    "text_offset": insert_position,
                    "text_length": len(placeholder),
                    "position": {
                        "width": width,
                        "height": height,
                        "page": 1,
                        "index": sequence,
                        "source": media_name,
                    },
                }
                images_metadata.append(image_metadata)

        if images_metadata:
            logger.info(
                "Extracted %d images from %s (skipped duplicates=%d, decorative=%d)",
                len(images_metadata),
                docx_path,
                skipped_duplicates,
                skipped_decorative,
            )
        else:
            logger.debug(
                "No images kept from %s (skipped duplicates=%d, decorative=%d)",
                docx_path,
                skipped_duplicates,
                skipped_decorative,
            )

        return modified_text, images_metadata

    def _convert_doc_to_docx(self, path: Path, output_dir: Path) -> Path:
        """Convert a legacy ``.doc`` file to ``.docx`` with LibreOffice."""
        soffice = shutil.which(self.libreoffice_binary)
        if soffice is None:
            raise RuntimeError(
                "Legacy .doc support requires LibreOffice. Install LibreOffice "
                "or convert the file to .docx before ingestion."
            )

        cmd = [
            soffice,
            "--headless",
            "--convert-to",
            "docx",
            "--outdir",
            str(output_dir),
            str(path),
        ]
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            details = completed.stderr.strip() or completed.stdout.strip()
            raise RuntimeError(f"LibreOffice failed to convert .doc file: {details}")

        converted = output_dir / f"{path.stem}.docx"
        if not converted.exists():
            matches = list(output_dir.glob("*.docx"))
            if not matches:
                raise RuntimeError("LibreOffice conversion finished but produced no .docx file.")
            converted = matches[0]

        return converted

    def _compute_file_hash(self, file_path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _read_dimensions(self, image_bytes: bytes) -> tuple[int, int]:
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                return img.size
        except Exception:
            return 0, 0

    def _display_path(self, image_path: Path) -> str:
        try:
            return str(image_path.relative_to(Path.cwd()))
        except ValueError:
            return str(image_path.absolute())

    @staticmethod
    def _generate_image_id(doc_hash: str, sequence: int) -> str:
        return f"{doc_hash[:8]}_docx_{sequence}"

    def _extract_title(self, text: str) -> Optional[str]:
        lines = text.split("\n")
        for line in lines[:20]:
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()

        for line in lines[:10]:
            line = line.strip()
            if line:
                return line

        return None
