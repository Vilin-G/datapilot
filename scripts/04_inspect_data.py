r"""数据体检：查看 orders_all.csv 的规模、类型、缺失值和日期范围。

用法：& .venv\Scripts\python.exe scripts\04_inspect_data.py
"""

import pathlib

import pandas as pd

project_root = pathlib.Path(__file__).resolve().parents[1]
data_path = project_root / "data" / "processed" / "orders_all.csv"

# parse_dates：CSV 不保存类型信息，日期列必须显式解析，否则读回来是字符串
df = pd.read_csv(data_path, parse_dates=["InvoiceDate"])

print("文件：", data_path.name)
print("形状：", df.shape)

print("\n每列类型：")
print(df.dtypes)

print("\n缺失值：")
print(df.isnull().sum())

print("\n日期范围：", df["InvoiceDate"].min(), "→", df["InvoiceDate"].max())

print("\n前 5 行：")
print(df.head().to_string())
