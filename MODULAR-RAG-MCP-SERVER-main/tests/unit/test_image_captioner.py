from pathlib import Path

from src.core.settings import load_settings
from src.core.types import Chunk
from src.ingestion.transform.image_captioner import ImageCaptioner
from src.libs.llm.base_llm import ChatResponse


class FakeVisionLLM:
    def __init__(self):
        self.calls = []

    def chat_with_image(self, text, image, messages=None, trace=None, **kwargs):
        self.calls.append(image.path)
        return ChatResponse(content=f"caption for {Path(image.path).name}", model="fake")


def test_image_captioner_filters_small_images_when_document_has_many_images(tmp_path):
    fake_llm = FakeVisionLLM()
    captioner = ImageCaptioner(load_settings(), llm=fake_llm)

    images = []
    placeholders = []
    for idx in range(90):
        image_id = f"small_{idx}"
        image_path = tmp_path / f"{image_id}.png"
        image_path.write_bytes(b"fake")
        placeholders.append(f"[IMAGE: {image_id}]")
        images.append(
            {
                "id": image_id,
                "path": str(image_path),
                "position": {"width": 16, "height": 16},
            }
        )

    for idx in range(2):
        image_id = f"large_{idx}"
        image_path = tmp_path / f"{image_id}.png"
        image_path.write_bytes(b"fake")
        placeholders.append(f"[IMAGE: {image_id}]")
        images.append(
            {
                "id": image_id,
                "path": str(image_path),
                "position": {"width": 800, "height": 600},
            }
        )

    chunk = Chunk(
        id="chunk_1",
        text="\n".join(placeholders),
        metadata={"source_path": "doc.docx", "images": images},
    )

    [processed] = captioner.transform([chunk])

    assert len(fake_llm.calls) == 2
    assert "large_0" in processed.text
    assert "large_1" in processed.text
    assert processed.text.count("(Description:") == 2
    assert len(processed.metadata["image_captions"]) == 2
