r"""把两张年度表合并成一张订单明细表，并剔除已确认重复的 2010-12-01 ~ 2010-12-09 区间。

用法：& .venv\Scripts\python.exe scripts\merge_clean.py
输出：data/processed/orders_all.csv
"""

import pandas as pd
import pathlib

# 从本脚本位置往上找两级 = 项目根目录（换台机器也能跑，不写死绝对路径）
project_root = pathlib.Path(__file__).resolve().parents[1]
processed_dir = project_root / "data" / "processed"

# 1. 读入两张表（读的时候就把日期解析好）
df1 = pd.read_csv(processed_dir / "Year 2009-2010.csv", parse_dates=["InvoiceDate"])
df2 = pd.read_csv(processed_dir / "Year 2010-2011.csv", parse_dates=["InvoiceDate"])
print("表1 行数 =", len(df1))
print("表2 行数 =", len(df2))

# 2. 定点删除表2 中与表1 重复的 9 天（已诊断：该区间两表内容完全一致）
start, end = "2010-12-01", "2010-12-09 23:59:59"
mask = (df2["InvoiceDate"] >= start) & (df2["InvoiceDate"] <= end)
print("从表2 删除的重叠行数 =", int(mask.sum()))
df2_clean = df2[~mask].copy()

# 3. 合并两张表：这是"追加"（同一张表的两段时间），不是"连接"
orders = pd.concat([df1, df2_clean], ignore_index=True)

# 4. 对账：数字不对就直接炸，别让错误数据往下走
print("合并后总行数 =", len(orders))
assert len(orders) == 1_044_848, f"对账失败！期望 1044848，实际 {len(orders)}"
print("对账通过 ✓")

# 5. 落地
out_path = processed_dir / "orders_all.csv"
orders.to_csv(out_path, index=False)
print("已写出：", out_path)
