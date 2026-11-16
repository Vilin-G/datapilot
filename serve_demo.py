"""DataPilot 本地演示服务器（演示壳，不是正式服务层）。

设计约束：
- 不修改项目里任何既有文件，只调用 scripts/08_agent.py 里的 ask(question) -> str
- 不新增任何依赖，只用标准库（跑得起来比用框架更重要）
- 现状边界：ask() 只返回最终文字答案；中途调了哪个工具、写了什么 SQL，
  当前拿不到，所以 /ask 也不返回假轨迹

用法（在项目根目录，用项目自己的 .venv）：
    python serve_demo.py
然后打开 http://127.0.0.1:8000
"""
from __future__ import annotations

import importlib
import json
import os
import sqlite3
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPTS = PROJECT_ROOT / "scripts"
DB_PATH = PROJECT_ROOT / "data" / "processed" / "datapilot.db"
INDEX = PROJECT_ROOT / "static" / "index.html"

SOFT_TIMEOUT = float(os.getenv("DATAPILOT_TIMEOUT", "120"))
STEP_LIMIT_MARK = "sys:到达最大步数限制"

# .env 必须在导入 agent 之前加载：08_agent.py 在模块顶层读 DEEPSEEK_API_KEY
try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except Exception:  # dotenv 缺失时也不拦着启动，只是可能没有 key
    pass

os.chdir(PROJECT_ROOT)  # 08_agent.py 内部用相对路径 "scripts"
sys.path.insert(0, str(SCRIPTS))

agent = importlib.import_module("08_agent")
MAX_STEPS = getattr(agent, "MAX_STEPS", 8)


def db_rows() -> int | None:
    try:
        con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        try:
            return con.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        finally:
            con.close()
    except Exception:
        return None


def run_question(question: str) -> dict:
    t0 = time.perf_counter()
    try:
        answer = agent.ask(question)
    except Exception as exc:  # 报错原样返回，和项目里 run_sql 的做法一致
        return {
            "ok": False,
            "kind": "error",
            "elapsed": round(time.perf_counter() - t0, 1),
            "message": f"{type(exc).__name__}: {exc}",
        }

    elapsed = round(time.perf_counter() - t0, 1)

    if answer is None or not str(answer).strip():
        return {
            "ok": False,
            "kind": "empty_answer",
            "elapsed": elapsed,
            "message": "模型这一轮没有返回文字内容，换个问法再试一次。",
        }

    text = str(answer)
    if text.startswith("sys:"):
        return {
            "ok": False,
            "kind": "step_limit",
            "elapsed": elapsed,
            "answer": text,
            "message": f"到达 {MAX_STEPS} 步上限，这一问没答完。这是当前 Agent 的真实行为（评测里也出现过）。",
        }

    return {"ok": True, "kind": "answer", "elapsed": elapsed, "answer": text}


class Handler(BaseHTTPRequestHandler):
    server_version = "DataPilotDemo/0.1"

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _json(self, code: int, payload: dict) -> None:
        self._send(code, json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        if self.path in ("/", "/index.html"):
            if not INDEX.exists():
                self._json(500, {"ok": False, "message": f"缺少前端文件：{INDEX}"})
                return
            self._send(200, INDEX.read_bytes(), "text/html; charset=utf-8")
            return
        if self.path == "/health":
            rows = db_rows()
            self._json(200, {
                "ok": rows is not None,
                "rows": rows,
                "table": "orders",
                "model": "deepseek-chat",
                "max_steps": MAX_STEPS,
                "soft_timeout": SOFT_TIMEOUT,
                "api_key_loaded": bool(os.getenv("DEEPSEEK_API_KEY")),
            })
            return
        self._json(404, {"ok": False, "message": "没有这个路径"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/ask":
            self._json(404, {"ok": False, "message": "没有这个路径"})
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length) or b"{}")
        except Exception as exc:
            self._json(400, {"ok": False, "kind": "bad_request", "message": str(exc)})
            return

        question = str(payload.get("question") or "").strip()
        if not question:
            self._json(400, {"ok": False, "kind": "empty_question",
                             "message": "问题为空，先写一句想问的。"})
            return

        self._json(200, run_question(question))

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("[demo] %s\n" % (fmt % args))


def main() -> None:
    port = int(os.getenv("DATAPILOT_PORT", "8000"))
    rows = db_rows()
    print(f"DataPilot demo → http://127.0.0.1:{port}")
    print(f"  数据库: {DB_PATH.name} · orders 表 {rows if rows is not None else '读取失败'} 行")
    print(f"  模型: deepseek-chat · 最多 {MAX_STEPS} 步 · 软超时 {SOFT_TIMEOUT:.0f}s")
    print("  Ctrl+C 停止")
    # 单线程是必须的：07_tools.py 里的 sqlite 连接建在模块导入时（主线程），
    # sqlite3 默认不允许跨线程复用同一条连接，ThreadingHTTPServer 会直接报
    # "SQLite objects created in a thread can only be used in that same thread"。
    # 副作用是一次只能问一个问题 —— 这跟当前 agent 的能力一致。
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
