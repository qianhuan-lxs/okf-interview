---
type: question
id: distributed-systems/2pc-3pc-protocol
title: 2PC / 3PC / XA 协议 (协调者 / prepare / 阻塞问题 / 3PC 解决了什么)
category: distributed-systems
subcategory: ""
difficulty: hard
tags: [2pc, 3pc, xa, distributed-transaction, strong-consistency, coordinator, blocking, mysql]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-07-05
---

# 2PC / 3PC / XA 协议 (协调者 / prepare / 阻塞问题 / 3PC 解决了什么)

## 问题描述

2PC 怎么工作？为什么有阻塞问题？3PC 解决了什么？为什么仍少用？XA 是什么？MySQL XA 怎么用？

## 解答

## 一、2PC（两阶段提交）

**角色**：协调者（Coordinator，TM）+ 多个参与者（Participant，RM）。

### 阶段一：Prepare（投票阶段）
1. 协调者发 `prepare` 给所有参与者。
2. 参与者执行事务到**未提交**状态，写 undo/redo，**锁资源**。
3. 参与者回 `yes`（可提交）或 `no`（失败）。

### 阶段二：Commit / Abort
- 全部 `yes` → 协调者发 `commit`，参与者提交并释放锁，回 `ack`。
- 任一 `no` 或超时 → 协调者发 `abort`，参与者回滚释放锁。

### 关键性质
- **同步阻塞**：阶段一后参与者持有锁等阶段二决定，期间所有访问这些资源的请求阻塞。
- **协调者单点**：协调者宕机，参与者一直持锁等指令。
- **数据不一致可能**：阶段二只发到部分参与者时协调者宕机 → 已 commit 的和未收到的参与者不一致。

## 二、2PC 三大问题

1. **同步阻塞**：全程锁资源，性能差，不适合高并发。
2. **协调者单点**：宕机后参与者阻塞（尤其是阶段一后宕机）。
3. **网络分区下不一致**：阶段二部分消息丢失 → 部分提交部分未提交，需人工介入。

## 三、3PC（三阶段提交）解决什么

3PC 在 2PC 前加 **CanCommit**（询问阶段，不锁资源），并在参与者引入**超时**。

### 三阶段
1. **CanCommit**：协调者问"能否提交？"，参与者只评估不锁资源，回 yes/no。
2. **PreCommit**：yes 则发 prepare，参与者执行事务+锁+回 ack；no 或超时则 abort。
3. **DoCommit**：收到全部 ack 发 commit；参与者**超时未收到也自动提交**（关键变化）。

### 3PC 的"改进"
- 参与者超时机制：协调者宕机时参与者**等超时后自行决定**（默认提交，假设大概率成功）。
- CanCommit 提前探测，减少 PreCommit 阶段失败率。

### 3PC 仍存在的问题
- **网络分区下脑裂**：分区让部分参与者收不到 DoCommit 但超时自动提交，另一部分被协调者 abort → 不一致。
- **不解决性能问题**：反而多一轮通信，更慢。
- 实际工程**几乎不用 3PC**。

## 四、XA 规范

**XA** 是 X/Open 制定的**分布式事务规范**——2PC 的工业标准实现接口。
- 定义 TM（事务管理器）和 RM（资源管理器，如 DB）之间的接口。
- Java 对应 **JTA**（`javax.transaction`）+ **JTS**。
- MySQL 支持 XA：`XA START`、`XA END`、`XA PREPARE`、`XA COMMIT`、`XA ROLLBACK`。

### MySQL XA 示例
```sql
XA START 'xid_db1';
INSERT INTO orders ...;
XA END 'xid_db1';
XA PREPARE 'xid_db1';   -- 阶段一
-- 协调者收集所有 RM prepare 成功后
XA COMMIT 'xid_db1';    -- 阶段二
```
- prepare 后事务**保持 prepared 状态**，锁不释放，直到 commit/rollback。
- MySQL XA 5.7+ 修复了诸多 bug，但**性能仍远低于普通事务**。

## 五、XA/2PC 实际用在哪

- **传统金融核心**：银行跨账户转账、证券清算，要求实时强一致，能接受性能损失。
- **同构多 DB**：MySQL 多库 XA，配合 Seata XA 模式 / Atomikos / Narayana 等 TM。
- **少用场景**：互联网高并发交易——锁等待和协调者开销拖死吞吐。

## 六、为什么不流行了
- 性能差（同步阻塞、协调者通信开销）。
- 协调者单点 + 宕机数据不一致难解。
- 最终一致方案（TCC/Saga/消息）成熟后吞吐高一个数量级。
- 跨异构数据源（DB+MQ+缓存）难做 XA。

## 易错点
- 把 2PC 当无阻塞 → 全程锁资源。
- 以为 3PC 完美解决 → 网络分区仍不一致，且更慢。
- XA 当万能 → 跨异构资源（DB+MQ）难做。
- 用 MySQL XA 做高并发业务 → 锁等待拖死。
- 忘了 prepare 后 XA 事务持锁到 commit → 长时间持锁阻塞其他事务。

## 延伸

## 延伸

- 关联题：[[distributed-systems/distributed-txn-overview]]
- 关联题：[[distributed-systems/tcc-transaction]]
- 关联题：[[distributed-systems/seata-framework]]
- 关联题：[[databases/mysql/clustered-vs-secondary-index.md]]
