---
type: question
id: databases/mysql/sql-tuning-deep-pagination
title: SQL 调优 / 深分页优化
category: databases
subcategory: mysql
difficulty: medium
tags: [mysql, sql-tuning, deep-pagination, database, optimization]
languages: []
role: [ai-app, sde, backend]
companies: [恩士讯, 海颐]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# SQL 调优 / 深分页优化

## 问题描述
具体怎么从十多秒优化到 2 秒的？数据量大分页越深越慢，有什么解决方案？

## 解答

### 深分页为什么慢
`SELECT * FROM t ORDER BY id LIMIT 1000000, 10`：
- MySQL 需要先扫前 100 万行 → 每行回表取 `*` → 丢掉 → 再取 10 行。
- 偏移越大，丢弃越多，IO 与 CPU 浪费越多。

### 优化方案

1. **延迟关联（Deferred Join）** —— 最常用
```sql
SELECT * FROM t
INNER JOIN (SELECT id FROM t ORDER BY id LIMIT 1000000, 10) x ON t.id = x.id;
```
子查询只走索引覆盖（`id` 是主键，索引覆盖），不用回表，扫完 100 万拿到 10 个 id 后才回表 10 次。

2. **游标 / Keyset 分页**（推荐）
```sql
SELECT * FROM t WHERE id > <last_id> ORDER BY id LIMIT 10;
```
不丢数据，每次只扫 10 行。要求按主键或唯一索引排序，且页面用"上一页最后 id"翻页（不能跳页）。

3. **覆盖索引 + 子查询**：同 1 思路。

4. **缓存热门页**：前几页缓存 Redis，深页才走 DB。

5. **产品层妥协**：限制最大翻页深度（如最多 100 页），或改无限滚动（游标分页）。

### 其他调优手段
- 加合适索引（覆盖索引避免回表）。
- 大表历史归档 / 冷热分离。
- `SELECT *` 改具体列。
- JOIN 用小表驱动大表、JOIN 字段建索引且同类型。

## 延伸

## 延伸

- 关联题：[[databases/mysql/index-failure-scenarios]]
- 关联题：[[databases/mysql/clustered-vs-secondary-index]]
