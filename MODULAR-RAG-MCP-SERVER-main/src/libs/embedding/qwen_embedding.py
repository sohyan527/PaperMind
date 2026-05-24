"""Qwen (DashScope) Embedding implementation (OpenAI-compatible)."""

from __future__ import annotations

import os
from typing import Any, Optional

from src.libs.embedding.openai_embedding import OpenAIEmbedding


class QwenEmbeddingError(RuntimeError):
    """Raised when Qwen Embedding API call fails."""


class QwenEmbedding(OpenAIEmbedding):
    """Qwen Embedding provider — DashScope OpenAI-compatible endpoint."""

    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def __init__(
        self,
        settings: Any,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        resolved_base = (
            base_url
            or getattr(settings.embedding, "base_url", None)
            or self.DEFAULT_BASE_URL
        )
        resolved_key = (
            api_key
            or getattr(settings.embedding, "api_key", None)
            or os.environ.get("DASHSCOPE_API_KEY")
        )
        if not resolved_key:
            raise ValueError(
                "Qwen API key not provided. Set in settings.yaml (embedding.api_key) "
                "or DASHSCOPE_API_KEY environment variable."
            )
        super().__init__(settings, api_key=resolved_key, base_url=resolved_base, **kwargs)
