# DataPilot SQL 热身练习

> **用法**：每次开工前 5 分钟，从项目数据里做 1-2 道小题。做完当场对答案、讲口径。
> **格式**：题目 / 我的写法 / 正确写法 / 踩到的坑
> **库**：`data\processed\datapilot.db`，表 `orders`（1,044,848 行）
> **命令行**：`sqlite3 D:\LLM_TEST\Own_project_NO2_v1\data\processed\datapilot.db`

---

## 2026-10-26 · 热身（第 2 层复习 + 第 3 层入门）

### 练习 A · 复习 GROUP BY + 去重计数

**题目**：2011 年每个月分别有多少张订单？

**练的关键词**：`GROUP BY` + `COUNT(DISTINCT ...)` + 日期过滤
**提示**：`InvoiceDate` 是 TEXT，格式 `2009-12-01 07:45:00`，所以"2011 年"可以用 `LIKE '2011%'` 或 `strftime('%Y', "InvoiceDate")`

**我的写法**：

**正确写法**：

**踩到的坑**：

---

### 练习 B · 新关键词 HAVING

**题目**：哪些月份的销售额超过 1,000,000？（只算 2011 年）

**练的关键词**：`HAVING`（分组之后的过滤）
**提示**：销售额 = `SUM(Quantity * Price)`，没有现成的销售额列；`WHERE` 是分组前的过滤，过滤"组"要用 `HAVING`

**我的写法**：

**正确写法**：

**踩到的坑**：
