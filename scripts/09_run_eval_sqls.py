r"""一次性脚本：把评测题文件里的所有 SQL 跑一遍，输出筛选表。跑完可删。

用法：python scripts\09_run_eval_sqls.py "路径\xxx_50道.md"
"""
import sqlite3
import sys
import re
import pathlib

md_path = pathlib.Path(sys.argv[1])
db = pathlib.Path(__file__).resolve().parents[1] / "data" / "processed" / "datapilot.db"

text = md_path.read_text(encoding="utf-8")
# 按 "## 题号 标题" 切块
blocks = re.split(r"^## ", text, flags=re.M)[1:]
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=10)

rows = []
for blk in blocks:
    title = blk.splitlines()[0].strip()
    sqls = re.findall(r"```\s*sql\s*\n(.*?)```", blk, flags=re.S)
    if not sqls:
        rows.append((title, "-", 0, "无 SQL（L4 预期）", ""))
        continue
    for i, sql in enumerate(sqls):
        tag = title if len(sqls) == 1 else f"{title} #{i+1}"
        try:
            cur = con.execute(sql.strip())
            data = cur.fetchall()
            ncol = len(cur.description) if cur.description else 0
            preview = ""
            if data:
                first = data[0]
                preview = str(first)[:70]
                if ncol > 4:
                    preview = f"[{ncol} 列] " + preview
            rows.append((tag, len(data), ncol, "OK", preview))
        except Exception as e:
            rows.append((tag, 0, 0, f"报错: {str(e)[:60]}", ""))
con.close()

print(f"共 {len(rows)} 条 SQL\n")
print(f"{'题号':<34} {'行数':>5} {'列':>3}  状态 / 首行预览")
print("-" * 110)
for tag, n, ncol, status, prev in rows:
    print(f"{tag[:34]:<34} {n:>5} {ncol:>3}  {status}  {prev}")

# 分类汇总
ok = [r for r in rows if r[3] == "OK"]
err = [r for r in rows if r[3].startswith("报错")]
empty = [r for r in rows if r[3] == "OK" and r[1] == 0]
wide = [r for r in rows if r[3] == "OK" and r[1] > 100]
print(f"\n汇总：成功 {len(ok)} / 报错 {len(err)} / 空结果 {len(empty)} / 超 100 行 {len(wide)}")
if err:
    print("\n【报错的行】")
    for r in err:
        print("  ", r[0], "→", r[3])
if empty:
    print("\n【空结果的行】")
    for r in empty:
        print("  ", r[0])
if wide:
    print("\n【超过 100 行（可能是忘了聚合）】")
    for r in wide:
        print("  ", r[0], "→", r[1], "行")
