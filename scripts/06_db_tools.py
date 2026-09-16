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


if __name__ == "__main__":
    con = sqlite3.connect(processed_dir/"datapilot.db")
    result = get_schema(con)
    print(result)
    con.close()
