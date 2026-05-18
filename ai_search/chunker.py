from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai_search.text_utils import guess_title, markdown_to_plain


@dataclass
class Chunk:
    chunk_id: str
    text: str
    source_path: str
    title: str
    section: str


def _split_paragraphs(body: str) -> list[str]:
    parts = [p.strip() for p in body.split("\n\n") if p.strip()]
    if not parts:
        return [body] if body.strip() else []
    return parts


def chunk_text(
    body: str,
    *,
    source_path: str,
    title: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[Chunk]:
    paragraphs = _split_paragraphs(body)
    chunks: list[Chunk] = []
    buf: list[str] = []
    buf_len = 0
    idx = 0

    def flush() -> None:
        nonlocal idx, buf, buf_len
        if not buf:
            return
        text = "\n\n".join(buf).strip()
        if text:
            chunks.append(
                Chunk(
                    chunk_id=f"{source_path}#{idx}",
                    text=text,
                    source_path=source_path,
                    title=title,
                    section="",
                )
            )
            idx += 1
        buf = []
        buf_len = 0

    for para in paragraphs:
        plen = len(para)
        if plen > chunk_size:
            flush()
            start = 0
            while start < plen:
                end = min(start + chunk_size, plen)
                piece = para[start:end].strip()
                if piece:
                    chunks.append(
                        Chunk(
                            chunk_id=f"{source_path}#{idx}",
                            text=piece,
                            source_path=source_path,
                            title=title,
                            section="",
                        )
                    )
                    idx += 1
                if end >= plen:
                    break
                start = max(0, end - chunk_overlap)
            continue

        if buf_len + plen + 2 > chunk_size and buf:
            flush()
            if chunk_overlap > 0 and chunks:
                tail = chunks[-1].text[-chunk_overlap:]
                if tail.strip():
                    buf = [tail]
                    buf_len = len(tail)

        buf.append(para)
        buf_len += plen + 2

    flush()
    return chunks


def iter_source_chunks(
    source_root: Path,
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> list[Chunk]:
    if not source_root.is_dir():
        raise FileNotFoundError(f"psydrugs 源目录不存在: {source_root}")

    all_chunks: list[Chunk] = []
    for path in sorted(source_root.rglob("*.md")):
        rel = path.relative_to(source_root).as_posix()
        # 跳过数据/静态资源目录，只索引 wiki 正文
        skip_prefixes = ("_data/", "data/", "icons/", "others/")
        if rel.startswith(skip_prefixes):
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        plain = markdown_to_plain(raw)
        if len(plain) < 30:
            continue
        title = guess_title(raw, path)
        rel_full = f"psydrugs/source/{rel}"
        all_chunks.extend(
            chunk_text(
                plain,
                source_path=rel_full,
                title=title,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        )
    return all_chunks
