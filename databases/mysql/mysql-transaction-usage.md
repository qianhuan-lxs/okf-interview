---
type: question
id: databases/mysql/mysql-transaction-usage
title: MySQL 事务使用方式 / 注解事务
category: databases
subcategory: mysql
difficulty: medium
tags: [mysql, transaction, spring, isolation, database]
languages: []
role: [ai-app, sde, backend]
companies: [恩士讯]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# MySQL 事务使用方式 / 注解事务

## 问题描述
MySQL 事务了解吗？代码上怎么使用事务？注解方式使用事务有哪些注意点？

## 解答

### MySQL 事务
- ACID：原子/一致/隔离/持久。
- 隔离级别：READ UNCOMMITTED → READ COMMITTED → REPEATABLE READ（InnoDB 默认）→ SERIALIZABLE。
- InnoDB 通过 redo log（持久性）+ undo log（原子性/回滚）+ MVCC（隔离性）+ 锁实现。

### 代码使用（Spring `@Transactional`）
```java
@Transactional(rollbackFor = Exception.class, isolation = Isolation.REPEATABLE_READ, propagation = Propagation.REQUIRED)
public void createOrder(...) { ... }
```

### 注意点
1. **rollbackFor**：默认只回滚 `RuntimeException` 和 `Error`；checked 异常不回滚。建议显式 `rollbackFor = Exception.class`。
2. **propagation（传播）**：REQUIRED / REQUIRES_NEW / NESTED / SUPPORTS / MANDATORY / NOT_SUPPORTED / NEVER。
3. **隔离级别**：根据场景选，默认 RR 在高并发写场景可能死锁/间隙锁，可降 RC。
4. **超时**：`timeout` 防止长事务占锁。
5. **只读**：`readOnly = true` 让优化器做读优化。

### @Transactional 失效场景（高频追问）
1. **方法非 public**：Spring AOP 默认只代理 public 方法。
2. **同类内部调用**：`this.method()` 不走代理 → 注解失效。解法：注入自身代理 `AopContext.currentProxy()` 或拆到另一个 Bean。
3. **rollbackFor 没配**：checked 异常不回滚。
4. **异常被 catch 吞掉**：事务感知不到异常，不回滚。
5. **传播行为不当**：内部方法 `REQUIRES_NEW` 但同类内部调用仍走原事务。
6. **数据库引擎不支持事务**：MyISAM 无事务。
7. **Bean 没被 Spring 管理**（new 出来的对象）。
8. **多线程跨连接**：事务绑定线程，跨线程不在同一事务。

## 延伸

## 延伸

- 关联题：[[databases/mysql/mvcc-principle]]
- 关联题：[[databases/mysql/transaction-annotation-failure]]
