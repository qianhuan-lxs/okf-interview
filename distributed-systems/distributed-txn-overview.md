---
type: question
id: distributed-systems/distributed-txn-overview
title: 分布式事务全景 (方案分类 / 强一致 vs 最终一致 / 选型决策树)
category: distributed-systems
subcategory: ""
difficulty: hard
tags: [distributed-transaction, 2pc, tcc, saga, xa, eventual-consistency, seata, base, cap, consistency]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-07-05
---

# 分布式事务全景 (方案分类 / 强一致 vs 最终一致 / 选型决策树)

## 问题描述

为什么需要分布式事务？有哪些方案？强一致和最终一致怎么选？2PC/TCC/Saga/事务消息/本地消息表/Seata 各是什么关系？怎么选型？

## 解答

## 一、为什么需要分布式事务

单机事务靠 DB 的 ACID（redo/undo/MVCC）保证。一旦跨进程/跨数据源：
- **跨库**：一个业务要写多个 DB（分库分表、多业务库）。
- **跨服务**：微服务架构下订单服务写订单、库存服务减库存、账户服务扣钱——各自 DB，本地事务管不到对方。
- **跨消息**：DB 写成功 + MQ 发送要原子（否则丢消息或重复发）。

→ 需要**分布式事务**保证跨这些边界的"要么都成功、要么都回滚"语义。

## 二、CAP/BASE 取舍决定方案选型

- **CAP**（详见 [CAP 理论](distributed-systems/cap-theory)）：分区时 C 与 A 二选一。
- **BASE**：Basically Available + Soft state + Eventually consistent——多数互联网系统选 AP + 最终一致。
- 分布式事务方案本质是在 **C 强度 vs 性能/可用性/侵入性** 之间取舍：

| 一致性强度 | 方案 | 性能 | 侵入性 | 场景 |
| --- | --- | --- | --- | --- |
| **强一致**（实时） | 2PC / XA / Seata XA | 低（锁等待） | 低 | 资金核心、传统金融 |
| **最终一致**（业务可见延迟） | TCC / Saga / Seata AT / 事务消息 / 本地消息表 | 高 | 中~高 | 互联网交易、库存、营销 |
| **弱一致**（尽力通知） | 最大努力通知 | 极高 | 低 | 对账、通知、日志 |

## 三、方案分类总览（必背）

| 方案 | 一致性 | 协议/角色 | 关键机制 | 优点 | 缺点 |
| --- | --- | --- | --- | --- | --- |
| **2PC / XA** | 强一致 | 协调者 + 参与者 | prepare + commit/abort | 业务无侵入、标准 | 阻塞、协调者单点、性能差 |
| **3PC** | 强一致 | 2PC + CanCommit | 超时容错 | 减少阻塞 | 仍可能不一致、网络分区内乱序 |
| **TCC** | 最终一致 | Try-Confirm-Cancel | 业务三段式 | 性能好、可控 | 业务侵入大、要写三个接口 |
| **Saga** | 最终一致 | 正向 + 补偿 | 长事务拆步骤+补偿 | 适合长流程 | 无隔离、补偿复杂 |
| **本地消息表** | 最终一致 | DB + MQ | 业务 + 消息同库写入，异步发 MQ | 简单可靠 | 与 MQ 耦合、要保证幂等 |
| **事务消息**（RocketMQ） | 最终一致 | half msg + 回查 | MQ 内建两阶段 | 与 MQ 深度集成 | 仅 RocketMQ 支持 |
| **Outbox + CDC** | 最终一致 | outbox 表 + Debezium | 同库写 outbox，CDC 投 MQ | 解耦、不依赖 MQ 协议 | CDC 部署复杂 |
| **最大努力通知** | 弱一致 | 重试 + 对账 | 服务做完主动通知，失败重试 N 次 | 极简 | 不保证一定送达 |
| **Seata AT** | 最终一致 | 全局锁 + undo_log | 一阶段执行+记 undo，二阶段 commit/rollback | 业务无侵入、自动补偿 | 全局锁、不适合高并发 |
| **Seata TCC/SAGA/XA** | 见上 | Seata 框架封装 | 同名方案 | 框架统一 | 框架依赖 |

## 四、各方案详解索引

- 强一致协议：[2PC/3PC 协议](distributed-systems/2pc-3pc-protocol)
- 业务补偿型：[TCC 事务](distributed-systems/tcc-transaction)、[Saga 模式](distributed-systems/saga-pattern)
- 最终一致性方案：[最终一致性方案集](distributed-systems/eventual-consistency-patterns)
- 框架：[Seata 框架](distributed-systems/seata-framework)
- RPC 集成：[RPC 调用与事务边界](distributed-systems/rpc-and-distributed-txn)

## 五、选型决策树

```
业务能接受最终一致？
├─ 否（资金核心、要实时强一致）
│   └─ 2PC / XA / Seata XA（接受性能损失）
└─ 是
    ├─ 业务能改三段式（Try/Confirm/Cancel）？
    │   ├─ 是，且并发高、要可控 → TCC / Seata TCC
    │   └─ 否 → 走补偿路线 ↓
    ├─ 长流程多步骤？
    │   └─ Saga / Seata SAGA（编排或协同）
    ├─ 只是 "DB + MQ" 原子？
    │   ├─ RocketMQ → 事务消息
    │   ├─ 任意 MQ + 想解耦 → 本地消息表 / Outbox + CDC
    │   └─ 通用、不要求强实时 → Seata AT（自动补偿，业务零侵入）
    └─ 只需通知、不要求一定送达？
        └─ 最大努力通知 + 对账
```

## 六、几个工程必知

### 1. 幂等是最终一致性的前提
所有最终一致方案（TCC Confirm/Cancel、Saga 补偿、消息消费）都可能**重试**——下游必须幂等：唯一键去重、状态机、`select for update` 锁、`Redis SETNX` 去重。

### 2. 业务与消息原子是核心难点
"DB 写成功 + MQ 发送" 不能跨 DB+MQ 做事务 → 用本地消息表/Outbox/事务消息把消息和业务数据**写同一个 DB 事务**，再异步发 MQ。

### 3. 补偿必须可重入且幂等
补偿动作可能被多次触发（网络重试），必须幂等且能在正向未完成时处理（空补偿）。

### 4. 隔离性差是最终一致方案的通病
TCC/Saga 中间态对外可见，并发问题靠业务层锁/版本号/状态机解决（不像 DB 事务的 RR/Serializable）。

## 易错点
- 以为分布式事务能像本地事务一样"实时强一致且高性能" → 强一致必损性能。
- 用 2PC 做互联网高并发交易 → 锁等待拖死。
- 用最终一致方案但不做幂等 → 重试导致数据错乱。
- 业务 + MQ 不做原子 → DB 成功 MQ 没发 / 反之。
- 用 Seata AT 跑超高并发 → 全局锁成瓶颈。
- 把"最大努力通知"当可靠 → 它就是不可靠，要配对账兜底。

## 延伸

## 延伸

- 关联题：[[distributed-systems/cap-theory]]
- 关联题：[[distributed-systems/2pc-3pc-protocol]]
- 关联题：[[distributed-systems/tcc-transaction]]
- 关联题：[[distributed-systems/saga-pattern]]
- 关联题：[[distributed-systems/eventual-consistency-patterns]]
- 关联题：[[distributed-systems/seata-framework]]
- 关联题：[[distributed-systems/rpc-and-distributed-txn]]
