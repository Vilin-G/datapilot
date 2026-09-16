import pathlib
import sqlite3
import pandas as pd


project_root = pathlib.Path(__file__).resolve().parents[1]
processed_dir = project_root / "data" / "processed"

df = pd.read_csv(processed_dir/"orders_all.csv",
                 parse_dates=["InvoiceDate"])

con = sqlite3.connect(processed_dir/"datapilot.db")

df.to_sql(
    "orders",
    con=con,
    if_exists="replace",
    index=False,
)

cur = con.cursor()
cur.execute("SELECT COUNT(*) FROM orders")
count = cur.fetchone()[0]
print(f"数据行数：{count}")

assert count == 1044848, f"数据行数不对，实际 {count} 请检查！"
con.close()
