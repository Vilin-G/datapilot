import pathlib
import sqlite3
import importlib
import sys
from langchain_core.tools import tool
import json

project_root = pathlib.Path(__file__).resolve().parents[1]
processed_dir = project_root / "data" / "processed"

sys.path.insert(0, str(project_root / "scripts"))
db_tools = importlib.import_module("06_db_tools")

con = sqlite3.connect(processed_dir / "datapilot.db")

@tool
def describe_database() -> str:
    """List the tables in the database, with column names, types and sample rows.
        Call this first when you do not know the schema."""
    return db_tools.get_schema(con)

@tool
def query_database(sql: str) -> str:
    """Run a read-only SQL query. Only SELECT is allowed.
        Returns at most 100 rows. Column names with spaces need double quotes,
        for example "Customer ID"."""
    result = db_tools.run_sql(con, sql)  # TODO 2：con 是从哪来的？
    # if result["ok"]:
    #     return json.dumps(result, ensure_ascii=False)
    # else:
    #     return str(result) # 模型会拿到两种语言：成功：{"ok": true...以及 失败：{'ok': False, 'error':
    return json.dumps(result, ensure_ascii=False)


if __name__ == "__main__":
    print("工具 1:", describe_database.name)
    print("  描述:", describe_database.description)
    print("  参数:", describe_database.args)
    print()
    print("工具 2:", query_database.name)
    print("  描述:", query_database.description)
    print("  参数:", query_database.args)

    con.close()