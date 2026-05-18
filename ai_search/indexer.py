from __future__ import annotations

import logging

import chromadb

from ai_search.chunker import iter_source_chunks
from ai_search.config import Settings
from ai_search.embedder import EmbeddingClient

logger = logging.getLogger(__name__)


def _get_collection(settings: Settings, *, recreate: bool) -> chromadb.Collection:
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(settings.chroma_dir))
    name = settings.chroma_collection
    if recreate:
        try:
            client.delete_collection(name)
            logger.info("已删除旧集合: %s", name)
        except Exception:
            pass
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def build_index(settings: Settings | None = None, *, force: bool = False) -> dict:
    settings = settings or Settings.load()
    settings.require_openai_key()

    chunks = iter_source_chunks(
        settings.psydrugs_source,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    if not chunks:
        raise RuntimeError(f"未在 {settings.psydrugs_source} 找到可索引的 .md 内容")

    logger.info("共 %d 个文本块，开始请求 Embedding API…", len(chunks))
    embedder = EmbeddingClient(settings)
    texts = [c.text for c in chunks]
    vectors = embedder.embed(texts)

    collection = _get_collection(settings, recreate=force)
    # Chroma 单次 add 有大小限制，分批写入
    batch = 128
    for i in range(0, len(chunks), batch):
        sl = chunks[i : i + batch]
        # upsert：重复执行 index 时覆盖同 id，避免 add 报 ID 已存在
        collection.upsert(
            ids=[c.chunk_id for c in sl],
            embeddings=vectors[i : i + batch],
            documents=[c.text for c in sl],
            metadatas=[
                {
                    "source_path": c.source_path,
                    "title": c.title,
                }
                for c in sl
            ],
        )
        logger.info("已写入 Chroma %d/%d", min(i + batch, len(chunks)), len(chunks))

    return {
        "chunks": len(chunks),
        "collection": settings.chroma_collection,
        "chroma_dir": str(settings.chroma_dir),
    }
