import pandas as pd
import sqlite3
import pathlib

file_dir = pathlib.Path(__file__).resolve().parents[1]
processed_dir = file_dir / "data" / "processed"


def get_schema(con):
    block = []
    tables = con.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    for table in tables:
        cols = con.execute(f"PRAGMA table_info({table[0]})").fetchall()
        n_rows = con.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
        samples = con.execute(f"SELECT * FROM {table[0]} LIMIT 3").fetchall()

        mess = []
        mess.append(f"表：{table[0]}（{n_rows} 行）")
        mess.append("字段：")
        for col in cols:
            names = col[1]
            types = col[2]
            mess.append(f" {names:<12}  {types}")
        mess.append("样本数据：")
        for sample in samples:
            sample = [str(i) for i in sample]
            mess.append(f" | ".join(sample))
        block.append("\n".join(mess))
    return "\n\n".join(block)





if __name__ == "__main__":
    con = sqlite3.connect(processed_dir/"datapilot.db")
    result = get_schema(con)
    print(result)
    con.close()




