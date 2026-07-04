---
type: question
id: concurrency/optimistic-vs-pessimistic-lock
title: 乐观锁 vs 悲观锁
category: concurrency
subcategory: concurrency
difficulty: easy
tags: [optimistic-lock, pessimistic-lock, cas, version]
languages: []
role: [ai-app, sde, backend]
companies: [海颐]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 乐观锁 vs 悲观锁

## 问题描述
说一下乐观锁跟悲观锁。

## 解答

| 维度 | 悲观锁 | 乐观锁 |
| --- | --- | --- |
| 假设 | 假设冲突高，先锁再操作 | 假设冲突少，先操作提交时校验 |
| 实现 | `SELECT ... FOR UPDATE`、synchronized | CAS / version 字段 |
| 并发 | 串行化，吞吐低 | 不阻塞，吞吐高 |
| 适用 | 写多读少、强一致 | 读多写少、冲突少 |

### 乐观锁典型实现（version）
```sql
UPDATE t SET stock = stock - 1, version = version + 1
WHERE id = ? AND version = ?;
-- 影响行数=0 说明被别人改过，重试或失败
```

### 取舍
- 冲突率高 → 悲观锁（避免乐观锁大量重试）。
- 冲突率低 → 乐观锁（无阻塞）。
- 极端高并发抢购 → 都不理想，用 Redis 预扣 + 异步落库 / 分布式锁。

## 延伸

## 延伸

- 关联题：[[concurrency/cas-mechanism]]
- 关联题：[[distributed-systems/distributed-lock-redis-vs-zk]]
