from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

SYSTEM_PROMPT = "你是一个严谨的医药搜索助手。"


@dataclass(frozen=True)
class Settings:
    psydrugs_source: Path
    chroma_dir: Path
    chroma_collection: str
    chunk_size: int
    chunk_overlap: int
    search_top_k: int
    openai_api_key: str
    openai_base_url: str
    embedding_model: str
    chat_model: str
    api_timeout_seconds: float
    api_max_retries: int

    @staticmethod
    def load() -> Settings:
        def _path(name: str, default: str) -> Path:
            raw = os.environ.get(name, default).strip()
            p = Path(raw)
            return p if p.is_absolute() else (REPO_ROOT / p).resolve()

        api_key = (
            os.environ.get("OPENAI_API_KEY", "").strip()
            or os.environ.get("EMBEDDING_API_KEY", "").strip()
            or os.environ.get("CHAT_API_KEY", "").strip()
        )
        base_url = (
            os.environ.get("OPENAI_BASE_URL", "").strip()
            or os.environ.get("OPENAI_API_BASE", "").strip()
            or os.environ.get("CHAT_API_BASE", "").strip()
            or os.environ.get("EMBEDDING_API_BASE", "").strip()
        ).rstrip("/")

        chunk_size = int(os.environ.get("CHUNK_SIZE", "1000"))
        chunk_overlap = int(os.environ.get("CHUNK_OVERLAP", "200"))
        if chunk_overlap >= chunk_size:
            raise ValueError("CHUNK_OVERLAP 必须小于 CHUNK_SIZE")

        return Settings(
            psydrugs_source=_path("PSYDRUGS_SOURCE_DIR", "psydrugs/source"),
            chroma_dir=_path("CHROMA_PERSIST_DIR", "data/chroma"),
            chroma_collection=os.environ.get("CHROMA_COLLECTION", "psydrugs_wiki").strip(),
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            search_top_k=int(os.environ.get("SEARCH_TOP_K", "5")),
            openai_api_key=api_key,
            openai_base_url=base_url,
            embedding_model=os.environ.get(
                "EMBEDDING_MODEL", os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
            ).strip(),
            chat_model=os.environ.get(
                "CHAT_MODEL", os.environ.get("OPENAI_CHAT_MODEL", "deepseek-chat")
            ).strip(),
            api_timeout_seconds=float(os.environ.get("API_TIMEOUT_SECONDS", "120")),
            api_max_retries=int(os.environ.get("API_MAX_RETRIES", "2")),
        )

    def require_openai_key(self) -> None:
        if not self.openai_api_key:
            raise RuntimeError(
                "未设置 OPENAI_API_KEY。请复制 .env.example 为 .env 并填写 API Key。"
            )
