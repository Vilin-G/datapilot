import pandas as pd
import pathlib

csv_path = pathlib.Path("D:/LLM_TEST/Own_project_NO2_v1/data/processed")
for csv_file in csv_path.glob("*.csv"):
    print(csv_file.name)
    df = pd.read_csv(csv_file)
    print(df.shape)