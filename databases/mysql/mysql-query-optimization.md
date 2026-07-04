---
type: question
id: databases/mysql/mysql-query-optimization
title: MySQL 查询优化经验
category: databases
subcategory: mysql
difficulty: medium
tags: [mysql, query-optimization, explain, database]
languages: []
role: [ai-app, sde, backend]
companies: [拼多多, 北京用友]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# MySQL 查询优化经验

## 问题描述
有一些查询优化经验吗？你说的游标跟跳跃具体是指什么？MySQL 优化？

## 解答

### 通用优化流程
1. **EXPLAIN** 看 `type`（const > eq_ref > ref > range > index > ALL）、`key`（实际用的索引）、`rows`（估算扫描行）、`Extra`（Using index = 覆盖索引好；Using filesort/Using temporary = 告警）。
2. 避免全表扫描：建合适索引、避免索引失效写法。
3. 减少回表：覆盖索引、避免 `SELECT *`。
4. 大结果集分页：游标/延迟关联（见 [[databases/mysql/sql-tuning-deep-pagination]]）。
5. 小表驱动大表：JOIN 时小结果集做驱动表。
6. 子查询改 JOIN（早期 MySQL 子查询优化差，新版改善）。

### "游标 vs 跳跃"澄清
- **游标分页（Keyset / Seek）**：`WHERE id > last_id LIMIT n`，每次定位到上次最大 id 之后，O(n) 不浪费。
- **跳跃分页（OFFSET）**：`LIMIT offset, n`，offset 即"跳跃"过的行数；深翻页时跳过大量行，越深越慢。
- 拼多多追问的"游标 vs 跳跃"指这两种分页策略的对比。

### 索引设计
- 高频查询列建索引，区分度低的（性别/状态）不单独建。
- 联合索引按"等值在前、范围在后、排序字段再后"排列。
- 别滥用索引：写多读少场景索引会拖慢写入。

### 监控
- 慢查询日志 `slow_query_log` + `pt-query-digest` 分析 TopN。
- `SHOW PROCESSLIST` / `sys.schema_index_statistics`。

## 延伸

## 延伸

- 关联题：[[databases/mysql/index-failure-scenarios]]
- 关联题：[[databases/mysql/sql-tuning-deep-pagination]]
