from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAIError
from pydantic import BaseModel, Field

from ai_search.search_service import RagSearchService

logger = logging.getLogger(__name__)
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="Psydrugs RAG Search API",
    version="1.0.0",
    description="FastAPI + ChromaDB + OpenAI SDK 检索增强生成服务",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_service: RagSearchService | None = None


def get_service() -> RagSearchService:
    global _service
    if _service is None:
        _service = RagSearchService()
    return _service


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, examples=["查一下关于文拉法辛的报告"])
    top_k: int = Field(default=5, ge=3, le=5, description="检索片段数量（3–5）")


class SearchResponse(BaseModel):
    success: bool
    query: str
    answer: str
    sources: list[dict] = Field(default_factory=list)
    top_k: int = 5
    model: str | None = None


@app.get("/")
def index_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/search", response_model=SearchResponse)
def api_search(req: SearchRequest) -> SearchResponse:
    """
    RAG 主接口（按需求顺序）：
    1. 解析 query
    2. Embedding API 向量化
    3. ChromaDB 检索 3–5 段文档
    4. 拼接 System / User Prompt
    5. OpenAI SDK 调用 LLM
    6. 返回 JSON（含 answer）
    """
    try:
        result = get_service().rag_search(req.query, top_k=req.top_k)
        return SearchResponse(**result)
    except RuntimeError as e:
        logger.warning("业务错误: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except OpenAIError as e:
        logger.exception("OpenAI SDK 错误")
        raise HTTPException(status_code=502, detail=f"模型服务错误: {e}") from e
    except Exception as e:
        logger.exception("未处理异常")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {e}") from e


@app.post("/api/retrieve")
def api_retrieve(req: SearchRequest) -> dict:
    """仅向量检索，不调用大模型（调试用）。"""
    try:
        hits = get_service().retrieve(req.query, top_k=req.top_k)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {
        "query": req.query,
        "results": [
            {
                "index": i,
                "title": h.title,
                "source_path": h.source_path,
                "text": h.text,
                "distance": h.distance,
            }
            for i, h in enumerate(hits, 1)
        ],
    }


# 兼容旧前端路径
@app.post("/api/ask")
def api_ask(req: SearchRequest) -> SearchResponse:
    return api_search(req)


if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
