import re
import sys, importlib

sys.path.insert(0, "scripts")
agent = importlib.import_module("08_agent")


QUESTIONS = [
    ("我们这份销售明细一共有多少条记录？", 1044848),
    ("这家零售商一共有多少个不同的客户？", 5942),
    ("2011 年 11 月这个月，我们一共做了多少张订单？", 3462),
    ("除了英国，把所有发票都算作订单（取消单也算），哪个国家的订单数量最多？有多少张？", ["Germany", 1095]),
    ("2010 年全年，英国本土做了多少张订单？", 25301),
    ("不算退货和取消单的话，哪个月份的销售额最高？销售额是多少？", ["2011-11", 1509496.33]),
    ("请只用发票号前缀区分：把发票号以 C 开头的记录的销售额总额（取绝对值）当作退货金额，把所有发票号不以 C 开头的记录的销售额总额当作正向销售额。退货金额占正向销售额的百分之多少？", 7.19),
    ("不算退货和取消单，销售额最高的五种商品是哪几个？各自的销售额是多少？", ["22423", 331084.27]),
    ("历史上被取消的订单，大概占全部订单的百分之多少？", 15.46),
    ("我想了解一下客户主要集中在哪个年龄段，能统计出各年龄段的客户人数吗？", None),
]

def nums(answer: str):
    """从文本里抠出所有数字，返回 float 列表。"""
    return [float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*\.?\d*", answer)]

def score(answer: str, expect):
    if answer.startswith("sys:"):  # 没答完，不算
        return False
    if expect is None:  # 无解题
        return any(k in answer for k in ("没有", "无法", "不存在"))
    if isinstance(expect, (list, tuple)):  # 多个都要对
        return all(score(answer, e) for e in expect)
    if isinstance(expect, str):  # 文字
        return expect.lower() in answer.lower()
    # 0.02 是绝对下限，够 Q7(7.19)/Q9(15.46) 两位小数舍入；将来若有 <1 的百分比题要调
    tol = 0.0 if isinstance(expect, int) else max(0.05, abs(expect) * 1e-7)
    return any(abs(v - expect) <= tol for v in nums(answer))


passed = 0
for q, expect in QUESTIONS:
    answer = agent.ask(q)
    print("=" * 60)
    print("问题:", q)
    print("答案:", answer)
    ok = score(answer, expect)
    passed += ok
    print(" ✅ " if ok else " ❌")

print("-" * 60)
print(f"完成率：{passed}/{len(QUESTIONS)}")











