r"""一次性诊断：检查两张年度表在 2010-12-01 ~ 2010-12-09 是否存在重复数据。

用法：& .venv\Scripts\python.exe scripts\02_check_overlap.py
已跑结论（2026-09-14）：两表在该区间各 22523 行、各 1088 张发票，逐行内容完全相同 → 完全重复。
处理方式见 03_merge_clean.py。
"""

import pathlib

import pandas as pd

project_root = pathlib.Path(__file__).resolve().parents[1]
processed_dir = project_root / "data" / "processed"

# 注意用 Year*.csv 而不是 *.csv：processed 目录里还有合并后的 orders_all.csv，不要读进来
frames = {}
for csv_file in sorted(processed_dir.glob("Year*.csv")):
    print("读取：", csv_file.name)
    frames[csv_file.name] = pd.read_csv(csv_file, parse_dates=["InvoiceDate"])

df1 = frames["Year 2009-2010.csv"]
df2 = frames["Year 2010-2011.csv"]

start, end = "2010-12-01", "2010-12-09 23:59:59"
sub1 = df1[(df1["InvoiceDate"] >= start) & (df1["InvoiceDate"] <= end)]
sub2 = df2[(df2["InvoiceDate"] >= start) & (df2["InvoiceDate"] <= end)]
print("重叠期行数： 表1 =", sub1.shape[0], " 表2 =", sub2.shape[0])

inv1 = set(sub1["Invoice"])
inv2 = set(sub2["Invoice"])
common = inv1 & inv2
print("不同发票数： 表1 =", len(inv1), " 表2 =", len(inv2), " 共同 =", len(common))

if common:
    cols = ["Invoice", "StockCode", "Quantity", "Price"]
    a = sub1[sub1["Invoice"].isin(common)].sort_values(cols).reset_index(drop=True)
    b = sub2[sub2["Invoice"].isin(common)].sort_values(cols).reset_index(drop=True)
    print("共同发票行数： 表1 =", len(a), " 表2 =", len(b))
    print("两边内容完全相同？", a.equals(b))
else:
    print("没有交集 —— 这 9 天在两表里不重复")
