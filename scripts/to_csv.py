"""
该程序是将xlsx文件转换为csv文件，方便后续数据处理和分析
"""

import pandas as pd
import pathlib
xlsx_path = r"D:/LLM_TEST/Own_project_NO2_v1/data/raw/online_retail_II.xlsx"

sheets = pd.read_excel(
    xlsx_path,
    sheet_name=None,
    engine="openpyxl",
)

for sheet_name, df in sheets.items():
    df.to_csv(pathlib.Path("D:/LLM_TEST/Own_project_NO2_v1/data/processed", f"{sheet_name}.csv"),
              index=False)
