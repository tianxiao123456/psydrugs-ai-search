from __future__ import annotations

from openai import OpenAI

from ai_search.config import Settings


def build_openai_client(settings: Settings) -> OpenAI:
    """创建 OpenAI 官方 SDK 客户端（兼容 OpenAI / DeepSeek / Qwen 等 Base URL）。"""
    settings.require_openai_key()
    kwargs: dict = {
        "api_key": settings.openai_api_key,
        "timeout": settings.api_timeout_seconds,
        "max_retries": settings.api_max_retries,
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return OpenAI(**kwargs)
