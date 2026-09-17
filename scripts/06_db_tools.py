import sqlite3
import pathlib
import pandas as pd


project_root = pathlib.Path(__file__).resolve().parents[1]
processed_dir = project_root / "data" / "processed"


def get_schema(con):
    message = []
    tables = con.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    for table in tables:
        cols = con.execute(f"PRAGMA table_info({table[0]});").fetchall()
        n_rows = con.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
        sample = con.execute(f"SELECT * FROM {table[0]} LIMIT 3").fetchall()

        mess = []
        mess.append(f"表：{table[0]}（{n_rows} 行）")
        mess.append("字段：")
        for col in cols:
            name = col[1]
            types = col[2]
            mess.append(f" {name:<12}  {types}")
        mess.append("样本数据：")
        for row in sample:
            row = [str(i) for i in row]
            mess.append(f"{' | '.join(row)}")
        message.append("\n".join(mess))
    return "\n\n".join(message)


def run_sql(con, sql):
    max_rows = 100
    cursor = con.cursor()
    try:
        if type(sql) is not str:
            return {"ok": False, "error": "Input must be a string.输入必须是字符串。"}

        if not sql.strip().upper().startswith("SELECT"):
            return {"ok": False, "error": "Not a SELECT statement, 系统拒绝了此命令。"}

        if "LIMIT" not in sql.strip().upper():
            sql = sql.strip() + f" LIMIT {max_rows};"

        first_back = cursor.execute(sql).fetchall()
        total = len(first_back)
        second_back = first_back[:max_rows]
        return {"ok": True,
                "rows": second_back,
                "truncated": total > max_rows,
                "total": total}

    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    con = sqlite3.connect(processed_dir/"datapilot.db")
    result = get_schema(con)
    run = run_sql(con, "SELECT Country FROM orders LIMIT 3")
    run2 = run_sql(con, "CREATE TABLE tmp_test (a TEXT)")
    run3 = run_sql(con, "SELECT * FROM orders; DROP TABLE orders")
    run4 = run_sql(con, "SELECT * FROM orders LIMIT 1000")
    run5 = run_sql(con, "SELECT DISTINCT Country FROM orders")
    print(run, "\n", run2, "\n", run3)
    print(len(run4["rows"]), run4["truncated"], run4["total"])
    print(len(run5["rows"]), run5["truncated"], run5["total"])
    print(result)
    con.close()
