"""Configuration loading and fail-fast validation.

DEV_SPEC A3 requirements:
1) Load `config/settings.yaml` and parse it into structured Settings objects.
2) Validate that critical fields exist; missing fields raise a readable error
   that includes the config field path (e.g., "embedding.provider").
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    model: str
    # provider-specific fields (kept optional in A3)
    api_key: Optional[str] = None
    azure_endpoint: Optional[str] = None
    deployment_name: Optional[str] = None
    base_url: Optional[str] = None


@dataclass(frozen=True)
class EmbeddingSettings:
    provider: str
    model: str
    api_key: Optional[str] = None
    azure_endpoint: Optional[str] = None


@dataclass(frozen=True)
class VectorStoreSettings:
    backend: str
    persist_path: Optional[str] = None


@dataclass(frozen=True)
class RetrievalSettings:
    sparse_backend: str
    fusion_algorithm: str
    top_k_dense: int = 20
    top_k_sparse: int = 20
    top_k_final: int = 10


@dataclass(frozen=True)
class RerankSettings:
    backend: str
    model: Optional[str] = None
    top_m: Optional[int] = None


@dataclass(frozen=True)
class EvaluationSettings:
    backends: List[str]
    golden_test_set: Optional[str] = None


@dataclass(frozen=True)
class ObservabilitySettings:
    enabled: bool = True
    log_file: Optional[str] = None
    detail_level: str = "standard"


@dataclass(frozen=True)
class Settings:
    project: Dict[str, Any]
    llm: LLMSettings
    embedding: EmbeddingSettings
    vector_store: VectorStoreSettings
    retrieval: RetrievalSettings
    rerank: RerankSettings
    evaluation: EvaluationSettings
    observability: ObservabilitySettings


def _require_path(data: Dict[str, Any], dotted_path: str) -> Any:
    """Require a field to exist inside nested dict.

    Args:
        data: parsed YAML dict.
        dotted_path: e.g. "embedding.provider"

    Returns:
        The value at that path.

    Raises:
        ValueError: if the field is missing.
    """

    parts = dotted_path.split(".")
    cur: Any = data
    for part in parts:
        if not isinstance(cur, dict) or part not in cur:
            raise ValueError(f"Missing required config field: {dotted_path}")
        cur = cur[part]
    return cur


def _expand_env_vars(value: Any) -> Any:
    """Expand ${VAR} style environment variables in string values (deep).

    A3 only needs basic support so users can write `${OPENAI_API_KEY}` etc.
    """

    if isinstance(value, str):
        # Basic ${VAR} expansion; keep other patterns untouched.
        return os.path.expandvars(value)
    if isinstance(value, dict):
        return {k: _expand_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env_vars(v) for v in value]
    return value


def validate_settings(settings: Settings) -> None:
    """Validate required Settings constraints.

    This is a second-layer validation after parsing required fields.
    """

    if not settings.llm.provider:
        raise ValueError("Missing required config field: llm.provider")
    if not settings.llm.model:
        raise ValueError("Missing required config field: llm.model")

    if not settings.embedding.provider:
        raise ValueError("Missing required config field: embedding.provider")
    if not settings.embedding.model:
        raise ValueError("Missing required config field: embedding.model")

    if not settings.vector_store.backend:
        raise ValueError("Missing required config field: vector_store.backend")

    if not settings.retrieval.sparse_backend:
        raise ValueError("Missing required config field: retrieval.sparse_backend")
    if not settings.retrieval.fusion_algorithm:
        raise ValueError("Missing required config field: retrieval.fusion_algorithm")

    if not settings.rerank.backend:
        raise ValueError("Missing required config field: rerank.backend")

    if settings.observability.enabled and not settings.observability.log_file:
        raise ValueError("Missing required config field: observability.log_file")

    if not settings.evaluation.backends:
        raise ValueError("Missing required config field: evaluation.backends")


def load_settings(path: str) -> Settings:
    """Load YAML config and parse into Settings with fail-fast validation."""

    cfg_path = Path(path)
    if not cfg_path.exists():
        raise FileNotFoundError(f"Settings file not found: {cfg_path}")

    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Settings YAML must parse to a mapping/dict at top-level.")

    # Expand env placeholders in-place for top-level string leaves.
    # (Keep this shallow for A3; deep expansion can be added later.)
    raw = _expand_env_vars(raw)

    # Critical field checks (A3 acceptance criteria).
    _require_path(raw, "project.name")
    _require_path(raw, "llm.provider")
    _require_path(raw, "llm.model")
    _require_path(raw, "embedding.provider")
    _require_path(raw, "embedding.model")
    _require_path(raw, "vector_store.backend")
    _require_path(raw, "retrieval.sparse_backend")
    _require_path(raw, "retrieval.fusion_algorithm")
    _require_path(raw, "rerank.backend")
    _require_path(raw, "evaluation.backends")
    _require_path(raw, "observability.enabled")

    project = raw.get("project", {})
    llm_data = raw.get("llm", {})
    embedding_data = raw.get("embedding", {})
    vector_store_data = raw.get("vector_store", {})
    retrieval_data = raw.get("retrieval", {})
    rerank_data = raw.get("rerank", {})
    evaluation_data = raw.get("evaluation", {})
    observability_data = raw.get("observability", {})

    llm = LLMSettings(
        provider=str(llm_data["provider"]),
        model=str(llm_data["model"]),
        api_key=llm_data.get("api_key"),
        azure_endpoint=llm_data.get("azure_endpoint"),
        deployment_name=llm_data.get("deployment_name"),
        base_url=llm_data.get("base_url"),
    )

    embedding = EmbeddingSettings(
        provider=str(embedding_data["provider"]),
        model=str(embedding_data["model"]),
        api_key=embedding_data.get("api_key"),
        azure_endpoint=embedding_data.get("azure_endpoint"),
    )

    vector_store = VectorStoreSettings(
        backend=str(vector_store_data["backend"]),
        persist_path=vector_store_data.get("persist_path"),
    )

    retrieval = RetrievalSettings(
        sparse_backend=str(retrieval_data["sparse_backend"]),
        fusion_algorithm=str(retrieval_data["fusion_algorithm"]),
        top_k_dense=int(retrieval_data.get("top_k_dense", 20)),
        top_k_sparse=int(retrieval_data.get("top_k_sparse", 20)),
        top_k_final=int(retrieval_data.get("top_k_final", 10)),
    )

    rerank = RerankSettings(
        backend=str(rerank_data["backend"]),
        model=rerank_data.get("model"),
        top_m=rerank_data.get("top_m"),
    )

    evaluation = EvaluationSettings(
        backends=list(evaluation_data["backends"]),
        golden_test_set=evaluation_data.get("golden_test_set"),
    )

    observability = ObservabilitySettings(
        enabled=bool(observability_data["enabled"]),
        log_file=observability_data.get("log_file"),
        detail_level=str(observability_data.get("detail_level", "standard")),
    )

    settings = Settings(
        project=project,
        llm=llm,
        embedding=embedding,
        vector_store=vector_store,
        retrieval=retrieval,
        rerank=rerank,
        evaluation=evaluation,
        observability=observability,
    )

    validate_settings(settings)
    return settings
