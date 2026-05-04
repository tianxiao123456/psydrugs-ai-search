#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计「自动生成流水线」产出的对话条数，并写入可追加的历史记录 + 最新快照。

默认扫描本目录下文件名形如 YYYY-MM-DD_partNNN.jsonl 的产出文件（与 generate_dataset.py 一致）。
可选一并统计上级目录的 药理.jsonl 作为参考语料规模。

文件产物（均在脚本同目录）：
  - generation_history.jsonl   每条为一 JSON：时间戳、批次、本批写入条数、累计生成有效对话数等
  - generation_stats_snapshot.json   人类可读的汇总快照（覆盖写入）

用法：
  python dialogue_stats.py              # 打印汇总并刷新快照（不写 history）
  python dialogue_stats.py --append-history '{"note":"manual"}'   # 调试
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REF_JSONL = SCRIPT_DIR.parent / "药理.jsonl"
HISTORY_FILE = SCRIPT_DIR / "generation_history.jsonl"
SNAPSHOT_FILE = SCRIPT_DIR / "generation_stats_snapshot.json"


def count_valid_jsonl_lines(path: Path) -> tuple[int, int]:
    """返回 (合法对话行数, 损坏行数)。"""
    if not path.is_file():
        return 0, 0
    ok = bad = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                bad += 1
                continue
            if (
                isinstance(obj, dict)
                and set(obj.keys()) == {"instruction", "input", "output"}
                and all(isinstance(obj[k], str) for k in obj)
                and obj["instruction"].strip()
            ):
                ok += 1
            else:
                bad += 1
    return ok, bad


def scan_generated_parts(out_dir: Path) -> dict:
    files: dict[str, dict[str, int]] = {}
    total_ok = total_bad = 0
    for p in sorted(out_dir.glob("*_part*.jsonl")):
        v, inv = count_valid_jsonl_lines(p)
        files[p.name] = {"valid_dialogues": v, "invalid_lines": inv}
        total_ok += v
        total_bad += inv
    return {
        "generated_files": files,
        "generated_total_valid": total_ok,
        "generated_total_invalid_lines": total_bad,
        "generated_file_count": len(files),
    }


def scan_reference(ref_path: Path) -> dict[str, Any]:
    if not ref_path.is_file():
        return {"reference_path": None, "reference_valid": 0, "reference_invalid": 0}
    root = SCRIPT_DIR.parent.parent
    try:
        rp = str(ref_path.relative_to(root))
    except ValueError:
        rp = str(ref_path)
    v, inv = count_valid_jsonl_lines(ref_path)
    return {"reference_path": rp, "reference_valid": v, "reference_invalid": inv}


def build_snapshot(out_dir: Path, ref_path: Path | None = None) -> dict:
    snap = scan_generated_parts(out_dir)
    snap["updated_at"] = datetime.now().isoformat(timespec="seconds")
    if ref_path is None:
        ref_path = REF_JSONL
    snap["reference"] = scan_reference(ref_path)
    return snap


def write_snapshot(snap: dict) -> None:
    SNAPSHOT_FILE.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")


def append_history(event: dict) -> None:
    event = {**event, "logged_at": datetime.now().isoformat(timespec="seconds")}
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def record_batch(
    out_dir: Path,
    *,
    batch_index: int,
    kept_this_batch: int,
    mode: str,
    ref_path: Path | None = None,
) -> dict:
    """生成脚本在每个批次结束后调用：追加 history + 覆盖 snapshot。"""
    snap = build_snapshot(out_dir, ref_path or REF_JSONL)
    event = {
        "batch_index": batch_index,
        "kept_this_batch": kept_this_batch,
        "generated_total_valid_after": snap["generated_total_valid"],
        "mode": mode,
    }
    append_history(event)
    snap["last_batch_event"] = event
    write_snapshot(snap)
    return snap


def print_human_summary(snap: dict) -> None:
    print("—— 对话统计 ——", flush=True)
    print(f"更新时间: {snap.get('updated_at')}", flush=True)
    print(f"自动生成有效对话累计: {snap.get('generated_total_valid', 0)} 条", flush=True)
    print(f"自动生成损坏/不合规行: {snap.get('generated_total_invalid_lines', 0)} 行", flush=True)
    print(f"产出分卷文件数: {snap.get('generated_file_count', 0)}", flush=True)
    ref = snap.get("reference") or {}
    if ref.get("reference_valid") is not None:
        print(
            f"参考 药理.jsonl 有效条数: {ref.get('reference_valid')}（损坏行 {ref.get('reference_invalid')}）",
            flush=True,
        )
    files = snap.get("generated_files") or {}
    if files:
        print("分文件明细:", flush=True)
        for name, meta in files.items():
            print(f"  {name}: 有效 {meta.get('valid_dialogues')} / 异常 {meta.get('invalid_lines')}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--append-history", help="追加一行自定义 JSON（合并进事件）", default="")
    args = parser.parse_args()

    snap = build_snapshot(SCRIPT_DIR)
    print_human_summary(snap)
    write_snapshot(snap)

    if args.append_history.strip():
        try:
            extra = json.loads(args.append_history)
            if not isinstance(extra, dict):
                raise ValueError("必须是 JSON 对象")
        except Exception as e:
            print(f"[error] --append-history 解析失败: {e}", file=sys.stderr)
            return 1
        append_history({"manual": True, **extra})
        print("[info] 已追加一条自定义 history。", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
