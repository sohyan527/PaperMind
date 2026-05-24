"""Qwen (DashScope) Vision LLM implementation (OpenAI-compatible)."""

from __future__ import annotations

import os
from typing import Any, Optional

from src.libs.llm.openai_vision_llm import OpenAIVisionLLM


class QwenVisionLLMError(RuntimeError):
    """Raised when Qwen Vision API call fails."""


class QwenVisionLLM(OpenAIVisionLLM):
    """Qwen Vision LLM provider — DashScope OpenAI-compatible endpoint."""

    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def __init__(
        self,
        settings: Any,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        max_image_size: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        vision_settings = getattr(settings, "vision_llm", None)
        resolved_base = (
            base_url
            or (getattr(vision_settings, "base_url", None) if vision_settings else None)
            or self.DEFAULT_BASE_URL
        )
        resolved_key = api_key
        if not resolved_key and vision_settings:
            resolved_key = getattr(vision_settings, "api_key", None)
        if not resolved_key:
            resolved_key = getattr(settings.llm, "api_key", None)
        if not resolved_key:
            resolved_key = os.environ.get("DASHSCOPE_API_KEY")
        if not resolved_key:
            raise ValueError(
                "Qwen API key not provided. Set in settings.yaml (vision_llm.api_key) "
                "or DASHSCOPE_API_KEY environment variable."
            )
        super().__init__(
            settings,
            api_key=resolved_key,
            base_url=resolved_base,
            max_image_size=max_image_size,
            **kwargs,
        )
