from __future__ import annotations

import logging
from typing import Sequence

from openai import APIConnectionError, APITimeoutError, OpenAI

from ai_search.config import Settings
from ai_search.openai_client import build_openai_client

logger = logging.getLogger(__name__)
BATCH_SIZE = 64


class EmbeddingClient:
    def __init__(self, settings: Settings | None = None, client: OpenAI | None = None) -> None:
        self._settings = settings or Settings.load()
        self._client = client or build_openai_client(self._settings)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        out: list[list[float]] = []
        model = self._settings.embedding_model
        try:
            for i in range(0, len(texts), BATCH_SIZE):
                batch = list(texts[i : i + BATCH_SIZE])
                resp = self._client.embeddings.create(model=model, input=batch)
                ordered = sorted(resp.data, key=lambda x: x.index)
                out.extend([row.embedding for row in ordered])
                logger.info("已向量化 %d/%d", min(i + BATCH_SIZE, len(texts)), len(texts))
        except APITimeoutError as e:
            raise RuntimeError("Embedding API 请求超时，请稍后重试。") from e
        except APIConnectionError as e:
            raise RuntimeError("无法连接 Embedding API，请检查网络与 OPENAI_BASE_URL。") from e
        except Exception as e:
            raise RuntimeError(f"Embedding API 调用失败: {e}") from e
        return out
