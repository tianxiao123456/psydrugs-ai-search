from __future__ import annotations

import argparse
import json
import logging
import sys

from ai_search.indexer import build_index
from ai_search.search_service import RagSearchService


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Psydrugs RAG（FastAPI + Chroma + OpenAI SDK）")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_index = sub.add_parser("index", help="扫描 psydrugs/source 并写入 Chroma")
    p_index.add_argument("--force", action="store_true", help="重建集合")

    p_search = sub.add_parser("search", help="完整 RAG（同 POST /api/search）")
    p_search.add_argument("query")
    p_search.add_argument("-k", type=int, default=5)

    p_retrieve = sub.add_parser("retrieve", help="仅向量检索")
    p_retrieve.add_argument("query")
    p_retrieve.add_argument("-k", type=int, default=5)

    p_serve = sub.add_parser("serve", help="启动 FastAPI")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if args.cmd == "index":
        print(json.dumps(build_index(force=args.force), ensure_ascii=False, indent=2))
        return 0

    svc = RagSearchService()

    if args.cmd == "search":
        out = svc.rag_search(args.query, top_k=args.k)
        print(out.get("answer", ""))
        if not out.get("success"):
            return 1
        return 0

    if args.cmd == "retrieve":
        hits = svc.retrieve(args.query, top_k=args.k)
        for i, h in enumerate(hits, 1):
            print(f"\n--- [{i}] {h.title} ({h.source_path}) dist={h.distance}")
            print(h.text[:500])
        return 0

    if args.cmd == "serve":
        import uvicorn

        uvicorn.run("ai_search.api:app", host=args.host, port=args.port, reload=False)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
