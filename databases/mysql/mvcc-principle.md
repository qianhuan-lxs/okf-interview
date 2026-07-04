---
type: question
id: databases/mysql/mvcc-principle
title: MVCC 原理
category: databases
subcategory: mysql
difficulty: hard
tags: [mysql, mvcc, transaction, isolation, database]
languages: []
role: [ai-app, sde, backend]
companies: [恩士讯]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# MVCC 原理

## 问题描述
说一下 MVCC 原理。

## 解答

**MVCC (Multi-Version Concurrency Control)**：通过维护数据多版本，让**读不阻塞写、写不阻塞读**，提升并发。InnoDB 在 RC/RR 隔离级别下用 MVCC。

### 三个组件

1. **隐藏列**：每行有 `DB_TRX_ID`（最近修改的事务 id）、`DB_ROLL_PTR`（回滚指针指向 undo log）。
2. **Undo Log**：每次修改前旧版本写入 undo log，形成版本链（旧 → 更旧）。
3. **Read View（读视图）**：事务在某次快照读时生成的"可见性判断快照"：
   - `m_ids`：生成时活跃未提交的事务 id 列表。
   - `min_trx_id` / `max_trx_id`：活跃事务最小/下一个分配 id。
   - `creator_trx_id`：当前事务 id。

### 可见性判断规则
对当前行的 `DB_TRX_ID`：
- `< min_trx_id` → 已提交，可见。
- `>= max_trx_id` → 未来事务，不可见。
- 在 `m_ids` 中 → 还活跃，不可见，沿 undo 链找下一版本再判。
- 不在 `m_ids` 中且在区间内 → 已提交，可见。

### RC vs RR 区别
- **RC (Read Committed)**：每次 SELECT 都生成新 Read View → 能看到新提交。
- **RR (Repeatable Read)**：事务内**只在第一次 SELECT 时生成一次** Read View → 后续都用同一份，可重复读。
- InnoDB 的 RR + MVCC 在大部分场景下已防幻读；严格防幻读用 `SELECT ... FOR UPDATE` 加间隙锁。

### 当前读 vs 快照读
- 快照读（普通 SELECT）走 MVCC。
- 当前读（`FOR UPDATE / LOCK IN SHARE MODE / UPDATE / DELETE`）读最新版本 + 加锁。

## 延伸

## 延伸

- 关联题：[[databases/mysql/transaction-annotation-failure]]
- 关联题：[[databases/mysql/mysql-transaction-usage]]
