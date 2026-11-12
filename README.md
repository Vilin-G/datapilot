# DataPilot

用中文问一句"上个月哪个国家卖得最好"，系统自己去看数据库结构、自己写 SQL、自己算、自己给结论。

真正的难点不在查数据，**在让模型自己决定怎么查**——尤其在这个数据集上，"退货"到底指什么，模型和人的直觉都可能是错的。

**技术栈**：Python 3.12 · SQLite · DeepSeek `deepseek-chat`（OpenAI 兼容接口） · LangChain Tool
**数据集**：[UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii)，1,044,848 行 / 53,628 张发票 / 43 个国家 / 2009-12 ~ 2011-12（英国占 91.6%）

---

## 这是怎么跑起来的

```
你问一句中文
    │
    ▼
08_agent.py ── 手写的 function calling 循环，最多 8 步
               想 → 调工具 → 看结果 → 再想
    │
    │  模型自己决定：先看结构，还是直接查
    ├──▶ describe_database()   表结构 + 行数 + 3 行样本
    └──▶ query_database(sql)   只允许 SELECT，最多 100 行
             │
             ▼
         06_db_tools.py ── run_sql() / get_schema()
                           失败时把 SQLite 原始报错原样返回
             │
             ▼
         data/processed/datapilot.db  ·  orders 表
              1,044,848 行 · 8 字段
```

这三层是**能力递进**关系，顺序不能调：没有数据库，工具查什么？没有工具，模型调什么？

---

## 核心设计：报错回传不是"写出来的"

工具层做了一件事：**查询失败时，把 SQLite 的原始报错文本原样返回，不包装成"查询失败，请重试"。**

```python
except Exception as e:
    return {"ok": False, "error": str(e)}     # 原样，不美化
```

Agent 循环把这串文本不作处理地塞回对话：

```python
messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
```

就这两处，没有第三行专门处理错误的代码。**模型能自我修正，靠的是没人挡在它和报错之间。**

实测（故意把 `describe_database` 从工具列表里拿掉，逼它自己撞墙）：

```
[1] SELECT name FROM sqlite_master WHERE type='table'        ✅
[2] SELECT * FROM orders LIMIT 5                             ✅ 先偷看数据
[3] SELECT CustomerID, SUM(Quantity*UnitPrice) FROM orders
    → {"ok": false, "error": "no such column: CustomerID"}   ❌ 一次错两个词
[4] SELECT * FROM pragma_table_info('orders')                ← 自己去查真实列名
[5] SELECT "Customer ID", SUM(Quantity*Price) FROM orders    ← 改对了
[6] 答：客户 18102，570,380.61
```

这一步是后面所有评测数字能收回来的前提。

---

## 评测：10 道题，两个版本的数字都要看

题目按难度分四层，标准答案**全部由本机真库 SQL 跑出**，不用模型生成（否则测的是"两个模型答案一不一致"，不是"对不对"）。

| 轮次 | 步数预算 | 题干 | 脚本报 | 人工复核 |
| --- | --- | --- | --- | --- |
| 1 | 5 | 开放式 | 7/10 | 7/10 |
| 2 | 8 | 开放式 | 9/10 | 9/10 |
| 3 | 8 | 开放式 | 9/10 | **8/10** |
| 4 | 8 | 口径钉死 | **10/10** | **10/10** |
| 5 | 8 | 口径钉死 | **10/10** | **10/10** |

固定：DeepSeek `deepseek-chat`，单次运行，10 道题。

### 这组数字里最值钱的三件事

**① 7/10 那一轮，测的是预算不是能力。**
三道失败全是 `sys:到达最大步数限制`。手工把预算提到 8 重跑，三道全部答完且正确（分别用了 5 步、4 步、3 步）。**步数预算卡在边界上时，同一个问题会一次挂一次过。**

**② 第 3 轮的 9/10 是假的。**
模型在退货率那题上答错了，但它在解释里举了个反例："如果按另一种口径会变成 ≈7.2%"。判分脚本从文本里抠数字，**把反例当成了正答**。人工复核后真实成绩 8/10。

**③ 模型在正确答案旁边编数字。**
同一个退货率问题，它报过 `正向销售额 19,746,489 / 退货 -966,225 / 比例 -4.89%`。按它自己写的方法算应该是 3.65%；全库反查，**没有任何一条查询能跑出 19,746,489 或 966,225**。它编了两个精确到个位的假数，还配了四条"统计说明"。

更细的一处：同一模型有一次答对了 15.46% 的取消率，但顺手写"1,915,648 行中 19,165 行为取消"——真实总行数是 **1,044,848**。**结论对，中间数字是编的。**

### 10/10 是改题干换来的

开放式题干有两处没写清口径（"订单"算不算取消单、"退货"怎么定义），模型选了个也合理的读法被判错。把口径钉死进题目后稳定 10/10，跑两次都是。

**所以两个版本的数字都保留。** 只贴 10/10 是自欺；只贴 7/10 又答不出"那你改了吗"。

### 已知限制（没修，照实写）

- 判分是"从自然语言抠数字比对"，会把模型举的**反例**算作正答。本轮靠人工复核纠正。
- 10 道题、单模型、单次运行，不是学术评测，只能说明"在这个数据集上大概什么水平"。

---

## 一条取舍：为什么不用 LangChain Agent

`bind_tools()` + `create_react_agent()` 能把 `08_agent.py` 里 40 行循环压成 5 行。**没这么做，是刻意的。**

这个项目的重点是"模型怎么决定下一步"，那 40 行就是这个决定的全部现场：

```python
for step in range(MAX_STEPS):                       # 预算
    response = client.chat.completions.create(..., tools=tools, tool_choice="auto")
    messages.append(response.choices[0].message)    # 请求必须回填，否则下一轮模型不知道自己要过工具
    if response.choices[0].finish_reason == "stop": # 说完了
        return response.choices[0].message.content
    for tc in response.choices[0].message.tool_calls:
        ...
        messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
else:
    return "sys:到达最大步数限制"                    # 只在没被 break 时执行 = 撞上限
```

几个只有手写过才知道的点：

- **`for...else` 天然对上"防死循环"**：`else` 只在循环没被 `break` 时执行，正好是"撞上限没停"，不需要额外计数器。这就是 `AgentExecutor.max_iterations` 的等价物。
- **模型答完时 `message.tool_calls` 是 `None`**，不先判断 `finish_reason` 直接迭代会 `TypeError`。
- **`tc.function.arguments` 是字符串**（`'{"sql": "..."}'`），得自己 `json.loads`；换成框架版后 `tc["args"]` 已经是 dict。
- **两个循环不能合并**：外层是用户对话（输 `exit` 退出），内层是模型步进（`finish_reason == "stop"` 退出）。两个 `break` 位置错一个行为就变。

框架版留作重构对照，不替换主线。

---

## 目录

```
scripts/
  01_to_csv.py           xlsx → CSV（双 sheet 拆分）
  02_check_overlap.py    检查 2009-2010 与 2010-2011 是否有重叠
  03_merge_clean.py      合并 + 清洗
  04_inspect_data.py     数据体检（空值 / 异常 / 分布）
  05_build_db.py         建 SQLite
  06_db_tools.py         get_schema(con) / run_sql(con, sql)   ← 数据层
  07_tools.py            @tool 包成 LangChain Tool             ← 工具层
  08_agent.py            function calling 循环 + ask(question)  ← Agent
  09_run_eval_sqls.py    评测题 SQL 批量试跑（一次性筛选工具）
  10_verify_eval_set.py  10 道题标准答案对账，assert 全过才算
  11_eval_agent.py       评测脚本：跑 10 道题，输出完成率
docs/
  项目地图.md            四层结构、为什么是这个顺序
  评测集.md              10 道题 + 标准答案 + 五轮实跑结果
  复盘手册.md            18 条踩坑记录（撞过的墙都在这里）
  进度看板.md            唯一事实来源
```

## 跑起来

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# 1. 建库：放好 data/raw/online_retail_II.xlsx 后按顺序跑（每步都有 assert 对账）
python scripts/01_to_csv.py             # xlsx → 两个年度 CSV（约 40 秒）
python scripts/02_check_overlap.py      # 诊断两段数据重叠区间
python scripts/03_merge_clean.py        # 合并 + 剔除重叠 → orders_all.csv
python scripts/04_inspect_data.py       # 数据体检
python scripts/05_build_db.py           # → data/processed/datapilot.db

# 2. 对账：标准答案必须 10/10，不动过就算环境没问题
python scripts/10_verify_eval_set.py

# 3. 交互式提问
set DEEPSEEK_API_KEY=sk-xxx
python scripts/08_agent.py

# 4. 跑评测（会调 10 道题的 API，1~5 分钟）
python scripts/11_eval_agent.py
```

`.env.example` 只是配置留档，**代码不读 `.env`**——`08_agent.py` 第 11 行直接 `os.getenv("DEEPSEEK_API_KEY")`，所以必须真的设成环境变量。
