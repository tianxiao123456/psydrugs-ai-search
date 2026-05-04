#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
药理风格 JSONL 自动生成流水线（Cursor Cloud Agent / 可插拔 Shell）。

结束方式（仅由你主动停）：
  1) 在本脚本同目录创建空文件 STOP（默认文件名 STOP，可用环境变量 STOP_FILE 改名）
  2) Ctrl+C

可选：
  --max-batches N   跑 N 个生成批次后正常退出（便于试跑；默认 0 表示不设上限，只靠 STOP）

三种调用后端（按优先级）：
  A) DRY_RUN=1  — 不写 API，生成占位 JSON 测轮转/校验逻辑
  B) CURSOR_PROMPT_SHELL — 每条调用是你自定义的命令，prompt 走 stdin，stdout 须为模型原始回复
  C) CURSOR_API_KEY + CURSOR_CLOUD_REPO_URL — Cursor Cloud Agents API（新建 agent → SSE → 删 agent）

Cloud 模式还需：
  CURSOR_CLOUD_REPO_URL   例如 https://github.com/you/psydrugs-ai-search
  CURSOR_CLOUD_REF        分支/tag，默认 main

质检模型：
  CURSOR_LOGIC_MODEL      默认 gpt-5.5-medium（若 /v1/models 无则退回列表第一个）
  CURSOR_QC_MODELS        逗号分隔；默认从 API 列表里随机抽 2 个（与逻辑模型去重）

输出：
  本目录下 YYYY-MM-DD_part001.jsonl，每满 30 行新建 part002…

参考格式文件：
  上级目录 ../药理.jsonl（截取示例塞进 prompt）

统计日志（同目录 dialogue_stats.py）：
  每个批次结束后写入 generation_history.jsonl + generation_stats_snapshot.json
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import random
import re
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent.parent
DEFAULT_REF = SCRIPT_DIR.parent / "药理.jsonl"
STOP_NAME = os.environ.get("STOP_FILE", "STOP")
STOP_PATH = SCRIPT_DIR / STOP_NAME
LINES_PER_ROTATE = int(os.environ.get("JSONL_LINES_PER_FILE", "30"))
BATCH_SIZE = int(os.environ.get("GENERATE_BATCH_SIZE", "4"))
API_BASE = os.environ.get("CURSOR_API_BASE", "https://api.cursor.com")


def log_generation_batch(
    *,
    batch_no: int,
    kept: int,
    mode: str,
    ref_path: Path,
) -> None:
    try:
        from dialogue_stats import record_batch

        record_batch(SCRIPT_DIR, batch_index=batch_no, kept_this_batch=kept, mode=mode, ref_path=ref_path)
    except Exception as e:
        print(f"[warn] 统计日志写入失败: {e}", flush=True)


def basic_auth_header(api_key: str) -> dict[str, str]:
    token = base64.b64encode(f"{api_key}:".encode()).decode()
    return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}


def http_request(
    method: str,
    path: str,
    api_key: str,
    body: dict[str, Any] | None = None,
    timeout: int | None = 120,
) -> tuple[int, Any]:
    url = f"{API_BASE}{path}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers=basic_auth_header(api_key))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} {path}: {err_body}") from e


def stream_sse_text(api_key: str, agent_id: str, run_id: str, timeout: int = 900) -> str:
    """读取 assistant 事件的 text 增量拼接。"""
    url = f"{API_BASE}/v1/agents/{agent_id}/runs/{run_id}/stream"
    req = urllib.request.Request(
        url,
        headers={
            **basic_auth_header(api_key),
            "Accept": "text/event-stream",
        },
        method="GET",
    )
    parts: list[str] = []
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        while True:
            line = resp.readline()
            if not line:
                break
            s = line.decode("utf-8", errors="replace").rstrip("\r\n")
            if not s.startswith("data:"):
                continue
            payload = s[5:].strip()
            if not payload or payload == "{}":
                continue
            try:
                obj = json.loads(payload)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and "text" in obj and isinstance(obj["text"], str):
                parts.append(obj["text"])
    return "".join(parts)


def delete_agent(api_key: str, agent_id: str) -> None:
    try:
        http_request("DELETE", f"/v1/agents/{agent_id}", api_key, None, timeout=60)
    except Exception:
        pass


def list_models(api_key: str) -> list[str]:
    _, data = http_request("GET", "/v1/models", api_key, None, timeout=60)
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        return [str(x) for x in data["items"]]
    return []


def cloud_agent_prompt(
    api_key: str,
    repo_url: str,
    ref: str,
    prompt_text: str,
    model_id: str | None,
) -> str:
    """单次问答：新建 agent → 等 stream → 删除 agent。"""
    body: dict[str, Any] = {
        "prompt": {"text": prompt_text},
        "repos": [{"url": repo_url, "startingRef": ref}],
        "autoCreatePR": False,
        "skipReviewerRequest": True,
    }
    if model_id:
        body["model"] = {"id": model_id}
    _, created = http_request("POST", "/v1/agents", api_key, body, timeout=120)
    assert isinstance(created, dict)
    agent = created["agent"]
    run = created["run"]
    agent_id = agent["id"]
    run_id = run["id"]
    try:
        # 偶发：run 尚未就绪，短暂等待
        for _ in range(30):
            try:
                return stream_sse_text(api_key, agent_id, run_id)
            except urllib.error.HTTPError:
                time.sleep(1.0)
        return stream_sse_text(api_key, agent_id, run_id)
    finally:
        delete_agent(api_key, agent_id)


def shell_prompt(prompt_text: str) -> str:
    cmd = os.environ["CURSOR_PROMPT_SHELL"]
    proc = subprocess.run(
        cmd,
        shell=True,
        input=prompt_text,
        capture_output=True,
        text=True,
        timeout=int(os.environ.get("CURSOR_PROMPT_TIMEOUT", "900")),
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[:2000] or "shell hook failed")
    return proc.stdout


def dry_run_response(kind: str) -> str:
    if kind == "generate":
        batch = []
        for i in range(BATCH_SIZE):
            batch.append(
                {
                    "instruction": f"[DRY_RUN 示例问句 {i}]",
                    "input": "",
                    "output": "*正在为您检索...*\n\n（占位）\n\n还要我告诉你更多吗？",
                }
            )
        return json.dumps(batch, ensure_ascii=False)
    if kind.startswith("qc") or kind == "logic":
        return json.dumps({"pass": True}, ensure_ascii=False)
    raise ValueError(kind)


def call_llm(prompt_text: str, model_id: str | None, kind: str) -> str:
    if os.environ.get("DRY_RUN") == "1":
        return dry_run_response(kind)
    if os.environ.get("CURSOR_PROMPT_SHELL"):
        return shell_prompt(prompt_text)
    api_key = os.environ.get("CURSOR_API_KEY", "").strip()
    repo = os.environ.get("CURSOR_CLOUD_REPO_URL", "").strip()
    ref = os.environ.get("CURSOR_CLOUD_REF", "main").strip()
    if not api_key or not repo:
        raise RuntimeError("请设置 CURSOR_API_KEY + CURSOR_CLOUD_REPO_URL，或 CURSOR_PROMPT_SHELL，或 DRY_RUN=1")
    return cloud_agent_prompt(api_key, repo, ref, prompt_text, model_id)


def load_reference_snippet(path: Path, max_lines: int = 5, max_chars: int = 3500) -> str:
    if not path.is_file():
        return ""
    lines = []
    with open(path, encoding="utf-8") as f:
        for i, ln in enumerate(f):
            if i >= max_lines:
                break
            lines.append(ln.rstrip("\n"))
    text = "\n".join(lines)
    return text[:max_chars]


def extract_json_array(text: str) -> list[Any]:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.I)
    if fence:
        text = fence.group(1).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("响应中未找到 JSON 数组")
    return json.loads(text[start : end + 1])


def extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.I)
    if fence:
        text = fence.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("响应中未找到 JSON 对象")
    return json.loads(text[start : end + 1])


def validate_record_local(obj: Any) -> bool:
    if not isinstance(obj, dict):
        return False
    if set(obj.keys()) != {"instruction", "input", "output"}:
        return False
    for k in ("instruction", "input", "output"):
        if not isinstance(obj[k], str):
            return False
    if not obj["instruction"].strip():
        return False
    return True


def qc_prompt(record_json: str, focus: str) -> str:
    return f"""你是药物滥用减害 wiki 对话数据的质检员。请只输出一行 JSON 对象，不要 Markdown，不要解释。
字段要求严格为：{{"pass": true}} 或 {{"pass": false, "reason": "简短中文"}}

检查对象（单行 JSONL 语义）：
{record_json}

检查重点：{focus}

pass=false 的情况包括但不限于：JSON 结构错了、instruction/output 空白、含有明显违法教唆制毒、或与常识严重冲突且未声明为虚构。"""


def logic_prompt(record_json: str) -> str:
    return f"""你是逻辑审计员。只输出一行 JSON：{{"pass": true}} 或 {{"pass": false, "reason": "..."}}
不要 Markdown。

记录：
{record_json}

重点：自相矛盾、夸大疗效、暗含「安全用量」暗示、或与前文声明冲突。"""


def generate_batch_prompt(ref_snippet: str) -> str:
    return f"""你是数据标注助手。请只输出一个 JSON 数组（不要 Markdown 围栏），数组元素为对象，且每个对象必须恰好包含三个字符串字段：
"instruction"、"input"、"output"。

风格综合要求：
- 中文；语气接近药理问答：常以「*正在为您检索...*」开头；可用 ## 与小列表；适度 Markdown。
- 话题围绕精神药物、滥用联用风险、仓库缺失药物（开头明确写本站无该药专页）、或模糊检索；链接尽量使用 psydrugs.org/source/... 
- input 多数为空字符串。
- 禁止输出违法教唆；医学表述允许多写「遵医嘱」「急诊」。

生成 {BATCH_SIZE} 条，彼此主题不要重复。

下面是参考格式（节选真实样本，勿照抄）：
{ref_snippet}
"""


@dataclass
class RotatingWriter:
    out_dir: Path
    date_str: str
    part: int = 1
    lines_in_part: int = 0
    fp: Any = None

    def __post_init__(self) -> None:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self._open_part()

    def _open_part(self) -> None:
        name = f"{self.date_str}_part{self.part:03d}.jsonl"
        path = self.out_dir / name
        self.fp = open(path, "a", encoding="utf-8")

    def write(self, obj: dict[str, Any]) -> None:
        assert self.fp
        self.fp.write(json.dumps(obj, ensure_ascii=False) + "\n")
        self.fp.flush()
        self.lines_in_part += 1
        if self.lines_in_part >= LINES_PER_ROTATE:
            self.fp.close()
            self.part += 1
            self.lines_in_part = 0
            self._open_part()

    def close(self) -> None:
        if self.fp:
            self.fp.close()
            self.fp = None


interrupted = False


def _sigint(_sig, _frm):
    global interrupted
    interrupted = True


def pick_qc_models(api_key: str, logic_model: str) -> tuple[str, str]:
    env = os.environ.get("CURSOR_QC_MODELS", "").strip()
    if env:
        xs = [x.strip() for x in env.split(",") if x.strip()]
        if len(xs) >= 2:
            return xs[0], xs[1]
    pool = list_models(api_key)
    pool = [m for m in pool if m != logic_model]
    if len(pool) < 2:
        raise RuntimeError("/v1/models 可用模型不足 2 个，请设置 CURSOR_QC_MODELS")
    return tuple(random.sample(pool, 2))  # type: ignore


def resolve_logic_model(api_key: str) -> str:
    want = os.environ.get("CURSOR_LOGIC_MODEL", "gpt-5.5-medium").strip()
    pool = list_models(api_key)
    if want in pool:
        return want
    if pool:
        return pool[0]
    return want


def main() -> int:
    signal.signal(signal.SIGINT, _sigint)
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-batches", type=int, default=0, help=">0 时跑若干批次后退出（默认 0=只靠 STOP）")
    parser.add_argument("--ref", type=Path, default=DEFAULT_REF, help="格式参考 JSONL")
    args = parser.parse_args()

    ref_snippet = load_reference_snippet(args.ref)

    api_key = os.environ.get("CURSOR_API_KEY", "").strip()
    use_shell = bool(os.environ.get("CURSOR_PROMPT_SHELL"))
    dry = os.environ.get("DRY_RUN") == "1"
    qc_a = qc_b = ""
    logic_m = ""
    if api_key and not dry and not use_shell:
        logic_m = resolve_logic_model(api_key)
        qc_a, qc_b = pick_qc_models(api_key, logic_m)
        print(f"[info] logic_model={logic_m} qc_models={qc_a}, {qc_b}", flush=True)
    elif dry or use_shell:
        logic_m = os.environ.get("CURSOR_LOGIC_MODEL", "").strip() or None  # type: ignore
        print("[info] DRY_RUN / CURSOR_PROMPT_SHELL：质检将调用同一后端两次（model 省略）。", flush=True)

    writer = RotatingWriter(SCRIPT_DIR, datetime.now().strftime("%Y-%m-%d"))
    batches = 0
    mode_tag = "dry_run" if dry else ("shell" if use_shell else "cloud")

    try:
        while not interrupted:
            if STOP_PATH.is_file():
                print("[stop] 检测到 STOP 文件，退出。", flush=True)
                break
            batches += 1
            print(f"[batch] 生成批次 {batches} …", flush=True)
            raw = call_llm(generate_batch_prompt(ref_snippet), None, "generate")
            try:
                arr = extract_json_array(raw)
            except Exception as e:
                print(f"[warn] 解析生成结果失败，跳过本批次：{e}", flush=True)
                log_generation_batch(batch_no=batches, kept=0, mode=mode_tag, ref_path=args.ref)
                if args.max_batches and batches >= args.max_batches:
                    break
                time.sleep(float(os.environ.get("SLEEP_SEC", "3")))
                continue

            if not isinstance(arr, list):
                print("[warn] 生成结果不是数组，跳过。", flush=True)
                log_generation_batch(batch_no=batches, kept=0, mode=mode_tag, ref_path=args.ref)
                if args.max_batches and batches >= args.max_batches:
                    break
                continue

            kept = 0
            for obj in arr:
                if STOP_PATH.is_file() or interrupted:
                    break
                if not validate_record_local(obj):
                    continue
                line = json.dumps(obj, ensure_ascii=False)
                ok = True
                if qc_a and qc_b:
                    qc_rounds = [(qc_a, "qc-a"), (qc_b, "qc-b")]
                else:
                    qc_rounds = [(None, "qc-1"), (None, "qc-2")]
                for mid, tag in qc_rounds:
                    try:
                        ans = call_llm(qc_prompt(line, "语法与严重事实错误"), mid, tag)
                        verdict = extract_json_object(ans)
                        if not verdict.get("pass"):
                            ok = False
                            print(f"[drop-{tag}] {verdict}", flush=True)
                            break
                    except Exception as e:
                        ok = False
                        print(f"[drop-{tag}] {e}", flush=True)
                        break
                if not ok:
                    continue
                try:
                    lm = logic_m.strip() if isinstance(logic_m, str) and logic_m.strip() else None
                    ans = call_llm(logic_prompt(line), lm, "logic")
                    verdict = extract_json_object(ans)
                    if not verdict.get("pass"):
                        print(f"[drop-logic] {verdict}", flush=True)
                        continue
                except Exception as e:
                    print(f"[drop-logic] {e}", flush=True)
                    continue

                writer.write(obj)
                kept += 1

            print(f"[batch] 本批写入 {kept} 条。", flush=True)
            log_generation_batch(batch_no=batches, kept=kept, mode=mode_tag, ref_path=args.ref)
            if args.max_batches and batches >= args.max_batches:
                print("[stop] 已达 --max-batches。", flush=True)
                break
            time.sleep(float(os.environ.get("SLEEP_SEC", "3")))
    finally:
        writer.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
