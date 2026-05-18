from __future__ import annotations

import re
from pathlib import Path

_FRONTMATTER = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)
_MD_LINK = re.compile(r"\[([^\]]*)\]\([^)]+\)")
_MD_IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]+\)")
_HTML_TAG = re.compile(r"<[^>]+>")
_MULTI_NL = re.compile(r"\n{3,}")


def strip_frontmatter(text: str) -> str:
    return _FRONTMATTER.sub("", text, count=1)


def markdown_to_plain(text: str) -> str:
    text = strip_frontmatter(text)
    text = _MD_IMAGE.sub(r"\1", text)
    text = _MD_LINK.sub(r"\1", text)
    text = _HTML_TAG.sub("", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\^+\[\[?[^\]]*\]?\]?", "", text)
    text = _MULTI_NL.sub("\n\n", text)
    return text.strip()


def guess_title(text: str, path: Path) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem
