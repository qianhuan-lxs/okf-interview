---
type: question
id: distributed-systems/eventual-consistency-patterns
title: 最终一致性方案 (本地消息表 / 事务消息 / Outbox+CDC / 最大努力通知 / 对账)
category: distributed-systems
subcategory: ""
difficulty: hard
tags: [eventual-consistency, local-message-table, transaction-message, outbox, cdc, rocketmq, debezium, best-effort, reconciliation]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-07-05
---

# 最终一致性方案 (本地消息表 / 事务消息 / Outbox+CDC / 最大努力通知 / 对账)

## 问题描述

最终一致性有哪些方案？本地消息表怎么实现？RocketMQ 事务消息原理？Outbox + CDC 是什么？最大努力通知和对账怎么配合？

## 解答

## 一、为什么需要这些方案

"DB 写成功 + 发 MQ" 这个看似简单的需求无法用本地事务保证——MQ 发送是网络操作不在 DB 事务内。两种失败：
- DB 提交了，MQ 没发 → 业务丢了下游通知。
- MQ 发了，DB 回滚了 → 下游收到不该有的消息。

最终一致性方案核心：**把"发消息"和"业务写"绑成一个原子动作，再异步发到 MQ**。

## 二、本地消息表

### 思路
- 在业务 DB 加一张 `local_message` 表。
- 业务写 + 写消息表**同一个本地事务**（保证原子）。
- 后台扫描消息表，把 `pending` 状态的消息发到 MQ，发成功标记 `sent`。
- 消费方消费后回调（或基于幂等 + 状态机）通知服务可清理。

### 流程
```
BEGIN;
INSERT INTO orders ...;
INSERT INTO local_message (id, topic, payload, status) VALUES (...,'pending');
COMMIT;
-- 后台任务扫描 pending，发 MQ，发成功改 sent
```

### 优点
- 简单可靠，任意 MQ 都能做。
- 不依赖 MQ 协议特性。

### 缺点
- 业务表与消息表耦合（同库）。
- 后台扫描频率决定延迟（通常秒级）。
- 高并发下消息表压力大，需分表/索引优化。

## 三、RocketMQ 事务消息（半消息 + 回查）

### 思路
MQ 内建两阶段：先发"半消息"（消费者不可见），执行本地事务，根据本地事务结果 commit/rollback 半消息；如果 MQ 收不到结果，主动回查本地事务状态。

### 流程
1. 生产者发 **half message** 到 MQ（半消息，消费者不可见）。
2. MQ 收到半消息回 ACK，生产者执行**本地事务**。
3. 本地事务成功 → 生产者发 `commit` 给 MQ → 半消息变可消费。
   本地事务失败 → 发 `rollback` → 半消息删除。
4. **若 MQ 收不到 commit/rollback**（生产者宕机/网络问题）→ MQ 主动**回查**生产者 `checkLocalTransaction` 接口，由生产者告知本地事务最终状态。
5. 回查多次仍无结果 → 按超时策略（默认回滚半消息）。

### 关键
- 生产者必须实现 `checkLocalTransaction`（幂等的本地事务状态查询）。
- 本地事务必须幂等（半消息可能因回查被多次评估）。

### 优点
- 与 MQ 深度集成，生产端不需要单独消息表。
- RocketMQ 保证半消息最终一致。

### 缺点
- **仅 RocketMQ 原生支持**（Kafka 需要自己模拟，复杂）。
- 业务侧需实现回查接口。

## 四、Outbox 模式 + CDC

### 思路
- 业务写 + 写 `outbox` 表**同事务**（类似本地消息表）。
- 用 **CDC（Change Data Capture，如 Debezium）** 监听 outbox 表的 binlog，把变更作为事件投递到 MQ。
- 业务侧不需要后台扫描线程，由 CDC 实时投递。

### 流程
```
BEGIN;
INSERT INTO orders ...;
INSERT INTO outbox (id, aggregate_type, event_type, payload) VALUES (...);
COMMIT;
-- Debezium 监听 binlog，把 outbox insert 转成 MQ 消息
```

### 优点
- 与 MQ 解耦（任意 MQ：Kafka/Pulsar/RocketMQ）。
- 实时（binlog 秒级内投递，不像本地消息表扫描延迟）。
- 业务无后台扫描负担。

### 缺点
- CDC 部署复杂（Debezium + Kafka Connect）。
- 顺序保证需按 aggregate_id 分区。
- outbox 表会增长，需定期归档。

### Outbox vs 本地消息表
| 维度 | 本地消息表 | Outbox + CDC |
| --- | --- | --- |
| 投递机制 | 后台扫描 | binlog CDC |
| 延迟 | 秒级（扫描频率） | 毫秒级 |
| MQ 依赖 | 任意 MQ | 任意 MQ（通过 CDC） |
| 复杂度 | 低 | 中（CDC 部署） |
| 适合 | 简单业务、低延迟要求不高 | 中大型、实时事件驱动 |

## 五、最大努力通知

### 思路
- 服务做完业务后**主动通知下游**，按 N 次重试 + 指数退避。
- 不保证一定送达，下游也可主动查询对账。
- 适合"通知类"业务：支付结果通知商户、营销通知用户。

### 流程
```
支付成功 → 通知服务发 HTTP → 失败重试 (1s, 5s, 30s, 5min, 30min...) 共 N 次
                                → 仍失败则记录待对账
```

### 特点
- 极简，业务无侵入。
- **不保证可靠送达**，必须配**对账兜底**。
- 通知接口要幂等。

### 与本地消息表区别
最大努力通知**不与业务写原子绑定**（业务已成功，通知可能丢）；本地消息表/事务消息保证业务+消息原子。所以最大努力通知用于"业务已成功、通知可丢"的场景。

## 六、对账兜底（所有最终一致方案的最终防线）

- 定时（T+1 / 小时级）比对两边数据，发现差异修复。
- 资金类：每日对账总额、明细。
- 订单状态：定时扫描超时未完成的 Saga/事务，主动补偿或标记异常。
- 工具：自研对账系统 / Spark 批处理 / SQL diff。

## 七、幂等是所有方案的前提

最终一致方案都依赖重试，下游必须幂等：
- **唯一键去重**：`UNIQUE KEY` 约束 / `INSERT IGNORE` / `ON DUPLICATE KEY UPDATE`。
- **状态机**：状态流转单向，重复消息不改变已流转的状态。
- **去重表**：`processed_message (msg_id PK)`，处理前 insert，冲突即跳过。
- **Redis SETNX** 短期去重（结合 DB 持久化）。

## 易错点
- 业务 + MQ 不绑原子 → DB 成功 MQ 没发或反之。
- 用 Kafka 当事务消息 → Kafka 无原生事务消息，要自己模拟（事务 KIP-117 不等同 RocketMQ 事务消息）。
- CDC 当实时可靠 → binlog 顺序、Debezium 重启、幂等都要处理。
- 最大努力通知当可靠 → 必须配对账。
- 不做幂等 → 重试导致重复扣款/超卖。
- 本地消息表后台扫描无锁 → 多实例并发重复发消息（要用 `SELECT FOR UPDATE` 或分布式锁）。

## 延伸

## 延伸

- 关联题：[[distributed-systems/distributed-txn-overview]]
- 关联题：[[distributed-systems/saga-pattern]]
- 关联题：[[distributed-systems/tcc-transaction]]
- 关联题：[[distributed-systems/kafka-duplicate-consumption-message-loss.md]]
- 关联题：[[distributed-systems/redis-mq-vs-kafka-rocketmq.md]]
