from __future__ import annotations

import logging
from dataclasses import dataclass

import chromadb
from openai import APIConnectionError, APITimeoutError, OpenAI

from ai_search.config import Settings
from ai_search.embedder import EmbeddingClient
from ai_search.openai_client import build_openai_client
from ai_search.rag import build_user_prompt, system_prompt

logger = logging.getLogger(__name__)


@dataclass
class SearchHit:
    text: str
    source_path: str
    title: str
    distance: float | None


class RagSearchService:
    """RAG 检索增强生成：Chroma 向量检索 + OpenAI SDK 对话。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.load()
        self.settings.require_openai_key()
        self.settings.chroma_dir.mkdir(parents=True, exist_ok=True)

        self._client = build_openai_client(self.settings)
        self._embedder = EmbeddingClient(self.settings, self._client)
        self._chroma = chromadb.PersistentClient(path=str(self.settings.chroma_dir))
        self._collection = self._load_collection()

    def _load_collection(self) -> chromadb.Collection:
        try:
            col = self._chroma.get_collection(self.settings.chroma_collection)
        except Exception as e:
            raise RuntimeError(
                f"Chroma 集合「{self.settings.chroma_collection}」不存在。"
                "请先执行: python -m ai_search index --force"
            ) from e
        if col.count() == 0:
            raise RuntimeError("向量库为空，请先执行: python -m ai_search index --force")
        return col

    def retrieve(self, query: str, top_k: int | None = None) -> list[SearchHit]:
        k = top_k or self.settings.search_top_k
        k = max(3, min(5, k))  # 需求：3–5 段

        qvec = self._embedder.embed([query])[0]
        try:
            res = self._collection.query(
                query_embeddings=[qvec],
                n_results=k,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            raise RuntimeError(f"Chroma 检索失败: {e}") from e

        hits: list[SearchHit] = []
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        for doc, meta, dist in zip(docs, metas, dists):
            meta = meta or {}
            hits.append(
                SearchHit(
                    text=doc or "",
                    source_path=str(meta.get("source_path", "")),
                    title=str(meta.get("title", "")),
                    distance=float(dist) if dist is not None else None,
                )
            )
        return hits

    def rag_search(self, query: str, top_k: int | None = None) -> dict:
        """
        完整 RAG 流程（对应 POST /api/search）：
        1. query 向量化
        2. Chroma 检索 3–5 段
        3. 拼接 Prompt
        4. OpenAI SDK 调用 LLM
        5. 返回 JSON 结构结果
        """
        k = top_k or self.settings.search_top_k
        k = max(3, min(5, k))

        hits = self.retrieve(query, top_k=k)
        sources = [
            {
                "index": i,
                "title": h.title,
                "source_path": h.source_path,
                "snippet": h.text[:400],
                "distance": h.distance,
            }
            for i, h in enumerate(hits, 1)
        ]

        if not hits:
            return {
                "success": False,
                "query": query,
                "answer": "未在本地知识库中检索到相关文档片段，请尝试更换关键词。",
                "sources": [],
                "top_k": k,
            }

        user_content = build_user_prompt(query, hits)

        try:
            completion = self._client.chat.completions.create(
                model=self.settings.chat_model,
                messages=[
                    {"role": "system", "content": system_prompt()},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.2,
            )
        except APITimeoutError as e:
            raise RuntimeError("大模型 API 请求超时，请稍后重试。") from e
        except APIConnectionError as e:
            raise RuntimeError("无法连接大模型 API，请检查 OPENAI_BASE_URL 与网络。") from e
        except Exception as e:
            raise RuntimeError(f"大模型 API 调用失败: {e}") from e

        answer = (completion.choices[0].message.content or "").strip()
        if not answer:
            return {
                "success": False,
                "query": query,
                "answer": "大模型返回内容为空，请稍后重试。",
                "sources": sources,
                "top_k": k,
                "model": self.settings.chat_model,
            }

        return {
            "success": True,
            "query": query,
            "answer": answer,
            "sources": sources,
            "top_k": k,
            "model": self.settings.chat_model,
        }


# 兼容旧代码引用
SearchService = RagSearchService
