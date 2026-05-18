from __future__ import annotations

from typing import Protocol

from ai_search.config import SYSTEM_PROMPT


class FragmentLike(Protocol):
    text: str
    source_path: str
    title: str


def format_fragments_block(hits: list[FragmentLike], max_chars_per_hit: int = 1500) -> str:
    """将检索片段格式化为可嵌入 User Prompt 的文本块。"""
    blocks: list[str] = []
    for i, h in enumerate(hits, 1):
        body = h.text.strip()
        if len(body) > max_chars_per_hit:
            body = body[:max_chars_per_hit] + "…"
        blocks.append(
            f"[片段{i}] 标题：{h.title or '（无标题）'} | 来源：{h.source_path}\n{body}"
        )
    return "\n\n".join(blocks)


def build_user_prompt(query: str, hits: list[FragmentLike]) -> str:
    if not hits:
        return f"（未检索到相关文档）\n\n回答用户的问题：{query}"
    fragments = format_fragments_block(hits)
    return f"请严格基于以下文档内容：\n{fragments}\n\n回答用户的问题：{query}"


def system_prompt() -> str:
    return SYSTEM_PROMPT
