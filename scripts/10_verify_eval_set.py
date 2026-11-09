"""对账：把 docs\评测集.md 里的对账 SQL 全部跑一遍，断言答案与文档一致。"""
import re
import pathlib
import sqlite3

root = pathlib.Path(__file__).resolve().parents[1]
doc = (root / "docs" / "评测集.md").read_text(encoding="utf-8")
db = root / "data" / "processed" / "datapilot.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)

# 只取「五、定稿 10 道题」那一节
body = doc.split("# 五、定稿 10 道题")[1].split("## 六、")[0]
questions = re.split(r"^### ", body, flags=re.M)[1:]

EXPECT = {
    "Q1": lambda r: r[0][0] == 1044848,
    "Q2": lambda r: r[0][0] == 5942,
    "Q3": lambda r: r[0][0] == 3462,
    "Q4": lambda r: r[0] == ("Germany", 1095),
    "Q5": lambda r: r[0][0] == 25301,
    "Q6": lambda r: r[0] == ("2011-11", 1509496.33) and len(r) == 3,
    "Q7": lambda r: abs(r[0][0] - 7.19) < 1e-9,
    "Q8": lambda r: len(r) == 5 and r[0][2] == 331084.27 and r[4][2] == 148395.98,
    "Q9": lambda r: abs(r[0][0] - 15.46) < 1e-9,
    "Q10": lambda r: r is None,  # L4 无 SQL
}

ok = 0
for blk in questions:
    qid = blk.split()[0]
    sqls = re.findall(r"```sql\n(.*?)```", blk, flags=re.S)
    if qid == "Q10":
        assert not sqls, "Q10 不该有 SQL"
        print(f"{qid}: L4 无 SQL ✅")
        ok += 1
        continue
    assert len(sqls) == 1, f"{qid} 应恰好 1 条 SQL，实际 {len(sqls)}"
    rows = con.execute(sqls[0].strip()).fetchall()
    good = EXPECT[qid](rows)
    print(f"{qid}: {'✅' if good else '❌'} {rows[:2]}{' ...' if len(rows) > 2 else ''}")
    ok += good

con.close()
print(f"\n{ok}/10 通过")
assert ok == 10, "有题答案对不上，别提交"
