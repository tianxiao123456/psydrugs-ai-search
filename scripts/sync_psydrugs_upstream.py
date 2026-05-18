#!/usr/bin/env python3
"""
定时/单次从上游 wiki 仓库同步内容到本地 psydrugs/ 目录。

上游默认: https://github.com/KrvyFT/psydrugs.org.git
本地目标: <仓库根>/psydrugs/

用法:
  python scripts/sync_psydrugs_upstream.py              # 同步一次
  python scripts/sync_psydrugs_upstream.py --interval 6 # 每 6 小时循环
  python scripts/sync_psydrugs_upstream.py --dry-run    # 只拉取不写入

环境变量:
  PSYDRUGS_UPSTREAM_URL   上游 git URL
  PSYDRUGS_UPSTREAM_BRANCH  分支，默认 main
  PSYDRUGS_SYNC_TARGET    目标目录绝对或相对路径
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_UPSTREAM = "https://github.com/KrvyFT/psydrugs.org.git"
DEFAULT_BRANCH = "main"
DEFAULT_TARGET = REPO_ROOT / "psydrugs"
DEFAULT_CACHE = REPO_ROOT / ".cache" / "psydrugs.org-upstream"
STATE_FILE = REPO_ROOT / ".cache" / "psydrugs-sync-state.json"

# 从上游复制到 psydrugs 的顶层项（与 KrvyFT/psydrugs.org 仓库结构一致）
SYNC_TOP_LEVEL = (
    "source",
    "tools",
    "themes",
    "scaffolds",
    "backups",
    "_config.yml",
    "_config.stellar.yml",
    "package.json",
    "package-lock.json",
    "LICENSE",
    "LICENSE-CONTENT",
    "README.md",
    ".gitignore",
)

# 复制目录时跳过的子目录名
SKIP_DIR_NAMES = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def run_git(args: list[str], cwd: Path) -> str:
    logging.debug("git %s (cwd=%s)", " ".join(args), cwd)
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed ({proc.returncode}):\n"
            f"{proc.stderr.strip() or proc.stdout.strip()}"
        )
    return proc.stdout.strip()


def ensure_upstream_checkout(cache: Path, url: str, branch: str) -> str:
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not (cache / ".git").is_dir():
        logging.info("首次克隆上游 %s (branch=%s) -> %s", url, branch, cache)
        run_git(
            ["clone", "--branch", branch, "--single-branch", "--depth", "1", url, str(cache)],
            cwd=cache.parent,
        )
    else:
        logging.info("拉取上游更新: %s", cache)
        run_git(["fetch", "origin", branch, "--depth", "1"], cwd=cache)
        run_git(["reset", "--hard", f"origin/{branch}"], cwd=cache)
    commit = run_git(["rev-parse", "HEAD"], cwd=cache)
    short = run_git(["rev-parse", "--short", "HEAD"], cwd=cache)
    logging.info("上游当前提交: %s (%s)", short, commit)
    return commit


def _ignore_copy(dir_path: str, names: list[str]) -> set[str]:
    return {n for n in names if n in SKIP_DIR_NAMES}


def copy_path(src: Path, dst: Path) -> None:
    if not src.exists():
        logging.warning("上游缺少路径，跳过: %s", src)
        return
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        logging.debug("文件: %s", dst.relative_to(REPO_ROOT))
        return
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=_ignore_copy, dirs_exist_ok=False)
    logging.info("目录: %s", dst.relative_to(REPO_ROOT))


def sync_tree(upstream_root: Path, target_root: Path, dry_run: bool) -> list[str]:
    updated: list[str] = []
    for name in SYNC_TOP_LEVEL:
        src = upstream_root / name
        dst = target_root / name
        if not src.exists():
            logging.warning("上游无 %s，跳过", name)
            continue
        updated.append(name)
        if dry_run:
            logging.info("[dry-run] 将同步 %s -> %s", src, dst)
            continue
        copy_path(src, dst)
    return updated


def write_state(commit: str, updated: list[str]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "last_sync_utc": _utc_now_iso(),
        "upstream_commit": commit,
        "updated_paths": updated,
        "upstream_url": os.environ.get("PSYDRUGS_UPSTREAM_URL", DEFAULT_UPSTREAM),
        "branch": os.environ.get("PSYDRUGS_UPSTREAM_BRANCH", DEFAULT_BRANCH),
    }
    STATE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logging.info("状态已写入 %s", STATE_FILE.relative_to(REPO_ROOT))


def sync_once(
    url: str,
    branch: str,
    cache: Path,
    target: Path,
    dry_run: bool,
) -> None:
    target.mkdir(parents=True, exist_ok=True)
    commit = ensure_upstream_checkout(cache, url, branch)
    updated = sync_tree(cache, target, dry_run)
    if not dry_run:
        write_state(commit, updated)
    logging.info(
        "同步完成%s: %d 项 -> %s",
        " (dry-run)" if dry_run else "",
        len(updated),
        target.relative_to(REPO_ROOT),
    )


def parse_interval_hours(s: str) -> float:
    try:
        h = float(s)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"无效间隔: {s}") from e
    if h <= 0:
        raise argparse.ArgumentTypeError("间隔必须 > 0")
    return h


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="从 psydrugs.org 上游同步 wiki 到本地 psydrugs/")
    parser.add_argument(
        "--url",
        default=os.environ.get("PSYDRUGS_UPSTREAM_URL", DEFAULT_UPSTREAM),
        help=f"上游仓库 URL (默认 {DEFAULT_UPSTREAM})",
    )
    parser.add_argument(
        "--branch",
        default=os.environ.get("PSYDRUGS_UPSTREAM_BRANCH", DEFAULT_BRANCH),
        help="分支名 (默认 main)",
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path(os.environ.get("PSYDRUGS_SYNC_CACHE", str(DEFAULT_CACHE))),
        help="上游 git 缓存目录",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=Path(os.environ.get("PSYDRUGS_SYNC_TARGET", str(DEFAULT_TARGET))),
        help="本地 psydrugs 目录",
    )
    parser.add_argument(
        "--interval",
        type=parse_interval_hours,
        default=None,
        metavar="HOURS",
        help="若指定则循环运行，间隔小时数（如 6 表示每 6 小时）",
    )
    parser.add_argument("--dry-run", action="store_true", help="只拉取上游，不写入 psydrugs/")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    setup_logging(args.verbose)
    cache = args.cache.resolve()
    target = args.target.resolve()

    def run() -> None:
        sync_once(args.url, args.branch, cache, target, args.dry_run)

    if args.interval is None:
        try:
            run()
        except Exception:
            logging.exception("同步失败")
            return 1
        return 0

    seconds = args.interval * 3600
    logging.info("定时模式: 每 %.2f 小时同步一次 (Ctrl+C 停止)", args.interval)
    while True:
        try:
            run()
        except Exception:
            logging.exception("本轮同步失败，将在下一周期重试")
        logging.info("下次同步: %.0f 秒后", seconds)
        try:
            time.sleep(seconds)
        except KeyboardInterrupt:
            logging.info("已停止定时同步")
            return 0


if __name__ == "__main__":
    sys.exit(main())
