r"""把原始 xlsx 按 sheet 转成 CSV（一次性格式转换）。

用法：& .venv\Scripts\python.exe scripts\01_to_csv.py
输入：data/raw/online_retail_II.xlsx
输出：data/processed/Year 2009-2010.csv、data/processed/Year 2010-2011.csv
"""

import pathlib

import pandas as pd

project_root = pathlib.Path(__file__).resolve().parents[1]
xlsx_path = project_root / "data" / "raw" / "online_retail_II.xlsx"
processed_dir = project_root / "data" / "processed"

print("读取 xlsx（约 40 秒，慢是因为 xlsx 要先解压再解析）……")
sheets = pd.read_excel(xlsx_path, sheet_name=None, engine="openpyxl")

for sheet_name, df in sheets.items():
    out_path = processed_dir / f"{sheet_name}.csv"
    print("写出：", out_path)
    df.to_csv(out_path, index=False)

print("完成。")
