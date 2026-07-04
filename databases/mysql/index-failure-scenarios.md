---
type: question
id: databases/mysql/index-failure-scenarios
title: 索引失效场景
category: databases
subcategory: mysql
difficulty: easy
tags: [mysql, index, query-optimization, database]
languages: []
role: [ai-app, sde, backend]
companies: [海颐]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 索引失效场景

## 问题描述
说一下索引失效的场景。

## 解答

1. **对索引列做函数/运算**：`WHERE YEAR(create_time)=2026` → 失效。改 `WHERE create_time >= '2026-01-01' AND < '2027-01-01'`。
2. **隐式类型转换**：phone 是 varchar，`WHERE phone=13800000000`（数字）→ 全表。改 `'13800000000'`。
3. **最左前缀缺失**：联合索引 `(a,b,c)`，查询只有 `b,c` → 不走索引。
4. **范围后列失效**：`WHERE a=? AND b>? AND c=?` → c 不走索引（b 的范围阻断）。
5. **LIKE 以 % 开头**：`LIKE '%abc'` 失效；`LIKE 'abc%'` 走索引。
6. **OR 两边不全有索引**：`WHERE a=1 OR b=2`，若 b 无索引 → 全表。
7. **NOT IN / NOT EXISTS / != / <>**：通常不走索引（视优化器与数据分布）。
8. **IS NULL / IS NOT NULL**：通常不走索引（取决于 null 比例）。
9. **优化器认为全表更快**：表小、索引列区分度低（如性别）→ 主动放弃索引。
10. **字符集/排序规则不一致**（JOIN 两表 charset 不同）：失效。

### 排查
`EXPLAIN` 看 `type` / `key` / `rows` / `Extra`（`Using filesort` / `Using temporary` 是告警）。

## 延伸

## 延伸

- 关联题：[[databases/mysql/clustered-vs-secondary-index]]
- 关联题：[[databases/mysql/sql-tuning-deep-pagination]]
