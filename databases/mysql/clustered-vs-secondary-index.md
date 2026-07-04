---
type: question
id: databases/mysql/clustered-vs-secondary-index
title: 聚簇索引 vs 二级索引
category: databases
subcategory: mysql
difficulty: medium
tags: [mysql, clustered-index, secondary-index, covering-index, database]
languages: []
role: [ai-app, sde, backend]
companies: [北京用友]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 聚簇索引 vs 二级索引

## 问题描述
什么是聚簇索引？什么是二级索引？

## 解答

### 聚簇索引 (Clustered Index)
- 索引与数据**一起存储**：B+ 树叶子节点 = 完整行数据。
- 一张表**只有一个**聚簇索引（InnoDB 默认主键）。
- 没有显式主键时：选第一个 NOT NULL 唯一索引；都没有则 InnoDB 隐式生成 6 字节 ROWID。
- 数据物理上按聚簇索引键顺序存（所以主键最好自增、单调，避免页分裂）。

### 二级索引 (Secondary / Non-clustered Index)
- 叶子节点存的是**主键值**（不是行指针），不是完整行。
- 查询走二级索引 → 拿到主键 → **回表**到聚簇索引取完整行（除非**覆盖索引**）。
- 一张表可有多个。

### 覆盖索引 (Covering Index)
- 查询列全部被索引覆盖 → 不需要回表，直接从索引返回。
- 优化技巧：把 `SELECT *` 改为只查索引列，或建联合索引覆盖热点查询。

### 回表代价
- 每次回表 = 多一次随机 IO。
- 高频查询应尽量覆盖索引，避免回表。

### 联合索引与最左前缀
- `(a, b, c)` 联合索引：能用于 `a` / `a,b` / `a,b,c`，不能跳过 `a` 直接用 `b,c`。
- 范围查询（> / BETWEEN / LIKE 'x%'）之后的列不再走索引。

## 延伸

## 延伸

- 关联题：[[databases/mysql/mysql-btree-index]]
- 关联题：[[databases/mysql/index-failure-scenarios]]
- 关联题：[[databases/mysql/sql-tuning-deep-pagination]]
