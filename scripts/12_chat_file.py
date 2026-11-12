r"""把一个 Excel / CSV / SQLite 文件拖进来，直接开始问答。

用法：
    .venv\Scripts\python.exe scripts\12_chat_file.py "D:\某目录\销售表.xlsx"
    .venv\Scripts\python.exe scripts\12_chat_file.py --check      # 自检，不调模型

或者把文件直接拖到项目根目录的 ask_with_file.bat 上。
"""

import pathlib
import sqlite3
import sys
import importlib
import os
import tempfile

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
tools = importlib.import_module("07_tools")


def _ensure_api_key():
    """双击 bat 开的新进程读不到刚设的机器级变量，这里兜底去注册表捞一次。"""
    if os.getenv("DEEPSEEK_API_KEY"):
        return
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        ) as k:
            os.environ["DEEPSEEK_API_KEY"] = winreg.QueryValueEx(k, "DEEPSEEK_API_KEY")[0]
    except Exception:
        raise SystemExit(
            "没读到 DEEPSEEK_API_KEY。请设成环境变量：\n"
            '  setx DEEPSEEK_API_KEY "sk-xxx"'
        )


def _read_any(path: pathlib.Path) -> dict:
    """读成 {表名: DataFrame}。多 sheet 的 Excel，每张 sheet 一张表。"""
    suffix = path.suffix.lower()
    if suffix == ".xls":
        # 老格式要额外装 xlrd，不为它加依赖；让用户另存一次更省事
        raise SystemExit("暂不支持 .xls 老格式，请用 Excel 打开后「另存为 .xlsx」")
    if suffix == ".xlsx":
        return pd.read_excel(path, sheet_name=None)
    if suffix == ".csv":
        try:
            return {"data": pd.read_csv(path, encoding="utf-8")}
        except UnicodeDecodeError:  # 国内 Excel 导出的 CSV 常是 GBK
            return {"data": pd.read_csv(path, encoding="gbk")}
    if suffix == ".parquet":
        return {"data": pd.read_parquet(path)}
    raise SystemExit(f"不认识的文件类型：{suffix}（支持 .xlsx / .csv / .parquet / .db）")


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Excel 表头常有空列、重名、前后空格——不处理会让 to_sql 直接报错。"""
    df = df.loc[:, [not str(c).startswith("Unnamed:") for c in df.columns]]
    seen, cols = {}, []
    for i, c in enumerate(df.columns):
        name = str(c).strip() or f"col{i}"
        seen[name] = seen.get(name, 0) + 1
        cols.append(name if seen[name] == 1 else f"{name}_{seen[name]}")
    df.columns = cols
    return df


def load_any(path: str) -> sqlite3.Connection:
    """任意文件 → SQLite 连接。表名取自 sheet 名 / 固定 data。"""
    p = pathlib.Path(path)
    if not p.exists():
        raise SystemExit(f"文件不存在：{p}")
    if p.suffix.lower() in (".db", ".sqlite", ".sqlite3"):
        return sqlite3.connect(p)  # 已经是库，直接用

    sheets = _read_any(p)
    # ponytail: 整表进内存，几十万行内没问题；再大就要改成分块或落盘
    con = sqlite3.connect(":memory:")
    for i, (name, df) in enumerate(sheets.items()):
        table = str(name).strip() or f"sheet{i}"
        _clean_columns(df).to_sql(table, con, index=False)
    return con


def _check():
    """自检：空列丢弃、带空格列名保留、多 sheet 拆表、行数对。"""
    d = pathlib.Path(tempfile.mkdtemp())
    df = pd.DataFrame({"客户 编号": [1, 2], "金额": [10.5, 20.0], "Unnamed: 2": [None, None]})

    csv = d / "t.csv"
    df.to_csv(csv, index=False, encoding="utf-8")
    xlsx = d / "t.xlsx"
    with pd.ExcelWriter(xlsx) as w:
        df.to_excel(w, sheet_name="销售", index=False)
        df.to_excel(w, sheet_name="退货", index=False)

    c1 = load_any(str(csv))
    tables = [r[0] for r in c1.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    assert tables == ["data"], tables
    cols = [r[1] for r in c1.execute("PRAGMA table_info(data)")]
    assert cols == ["客户 编号", "金额"], cols          # Unnamed 被丢掉，空格列名保留
    assert c1.execute("SELECT COUNT(*) FROM data").fetchone()[0] == 2

    c2 = load_any(str(xlsx))
    tables = [r[0] for r in c2.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    assert tables == ["退货", "销售"], tables          # 两个 sheet 各自成表

    print("自检通过 ✓")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        raise SystemExit(__doc__)

    tools.con = load_any(args[0])  # 换掉 07_tools 的模块级 con，两个工具就都指向新库
    _ensure_api_key()
    agent = importlib.import_module("08_agent")

    print("已装载：\n" + tools.describe_database.invoke({}))
    print("-" * 60)
    while True:
        q = input("请输入您想查询的内容（输入 exit 退出）: ")
        if "exit" in q:
            break
        print(agent.ask(q))


if __name__ == "__main__":
    if "--check" in sys.argv:
        _check()
    else:
        main()
