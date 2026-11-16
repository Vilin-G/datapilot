"""DataPilot MCP Server — 把 get_schema / run_sql 暴露为标准 MCP tool。

传输：stdio（由 MCP host 作为子进程启动）
用法：
    1. 本地调试：mcp dev scripts/mcp_server.py
    2. 接入宿主：在 MCP host 配置里指向本文件
"""
import json
import pathlib
import sqlite3
import sys
import importlib

from mcp.server.mcpserver import MCPServer

project_root = pathlib.Path(__file__).resolve().parents[1]
processed_dir = project_root / "data" / "processed"
db_path = processed_dir / "datapilot.db"

# 复用第一站写的底层函数，不重写逻辑
sys.path.insert(0, str(project_root / "scripts"))
db_tools = importlib.import_module("06_db_tools")

server = MCPServer(
    name="datapilot",
    version="0.1.0",
    instructions="零售数据分析助手。先用 describe_database 了解表结构，再用 query_database 查数。",
)


def _connect():
    return sqlite3.connect(db_path)


@server.tool(
    name="describe_database",
    description=(
        "列出数据库中的表、字段名、字段类型、行数和样例数据。"
        "在不知道表结构时先调用这个工具。"
    ),
)
def describe_database() -> str:
    con = _connect()
    try:
        return db_tools.get_schema(con)
    finally:
        con.close()


@server.tool(
    name="query_database",
    description=(
        "执行只读 SQL 查询，仅允许 SELECT 语句，最多返回 100 行。"
        "含空格的列名需要双引号，例如 \"Customer ID\"。"
        "查询报错时会把错误信息原样返回，可据此修正 SQL 后重试。"
    ),
)
def query_database(sql: str) -> str:
    con = _connect()
    try:
        result = db_tools.run_sql(con, sql)
        return json.dumps(result, ensure_ascii=False)
    finally:
        con.close()


if __name__ == "__main__":
    server.run()
