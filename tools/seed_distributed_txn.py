#!/usr/bin/env python3
"""Distributed transaction docs: overview, 2PC/3PC, TCC, Saga,
eventual consistency patterns, Seata framework, RPC + txn boundary."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from ikf_writer import q

DATE = "2026-07-05"

# =========================================================================== #
# 1. 全景
# =========================================================================== #
q("distributed-systems/distributed-txn-overview.md",
  "分布式事务全景 (方案分类 / 强一致 vs 最终一致 / 选型决策树)",
  "distributed-systems", "", "hard",
  ["distributed-transaction", "2pc", "tcc", "saga", "xa", "eventual-consistency",
   "seata", "base", "cap", "consistency"],
  [],
  """# 分布式事务全景 (方案分类 / 强一致 vs 最终一致 / 选型决策树)

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
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["distributed-systems/cap-theory",
         "distributed-systems/2pc-3pc-protocol",
         "distributed-systems/tcc-transaction",
         "distributed-systems/saga-pattern",
         "distributed-systems/eventual-consistency-patterns",
         "distributed-systems/seata-framework",
         "distributed-systems/rpc-and-distributed-txn"])

# =========================================================================== #
# 2. 2PC / 3PC
# =========================================================================== #
q("distributed-systems/2pc-3pc-protocol.md",
  "2PC / 3PC / XA 协议 (协调者 / prepare / 阻塞问题 / 3PC 解决了什么)",
  "distributed-systems", "", "hard",
  ["2pc", "3pc", "xa", "distributed-transaction", "strong-consistency",
   "coordinator", "blocking", "mysql"],
  [],
  """# 2PC / 3PC / XA 协议 (协调者 / prepare / 阻塞问题 / 3PC 解决了什么)

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
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["distributed-systems/distributed-txn-overview",
         "distributed-systems/tcc-transaction",
         "distributed-systems/seata-framework",
         "databases/mysql/clustered-vs-secondary-index.md"])

# =========================================================================== #
# 3. TCC
# =========================================================================== #
q("distributed-systems/tcc-transaction.md",
  "TCC 事务 (Try-Confirm-Cancel / 业务侵入 / 三大坑: 空回滚/悬挂/幂等)",
  "distributed-systems", "", "hard",
  ["tcc", "distributed-transaction", "eventual-consistency",
   "compensation", "idempotent", "business-transaction"],
  [],
  """# TCC 事务 (Try-Confirm-Cancel / 业务侵入 / 三大坑: 空回滚/悬挂/幂等)

## 问题描述

TCC 是什么？和 2PC 什么区别？Try/Confirm/Cancel 各做什么？为什么有"空回滚、悬挂、幂等"三大坑？什么时候用 TCC？

## 解答

## 一、TCC 是什么

**TCC = Try-Confirm-Cancel**，业务层面的两阶段提交。把每个业务操作拆成三个接口：
- **Try**：资源预留（不真正执行业务，先冻结资源）。
- **Confirm**：真正执行业务（用 Try 预留的资源）。
- **Cancel**：释放 Try 预留的资源。

由**全局事务协调者**（TM）统一调度：所有 Try 成功 → 调所有 Confirm；任一 Try 失败 → 调所有 Cancel。

## 二、典型例子：转账

扣钱方 A、加钱方 B，各暴露 Try/Confirm/Cancel：

| 阶段 | A（扣钱） | B（加钱） |
| --- | --- | --- |
| Try | `frozen += 100; balance -= 100`（冻结 100，余额先扣） | `frozen += 100`（预留 100 待加，先不动 balance） |
| Confirm | `frozen -= 100`（冻结转正） | `balance += 100; frozen -= 100` |
| Cancel | `balance += 100; frozen -= 100`（解冻退回） | `frozen -= 100`（预留取消） |

关键：**Try 阶段已经把"扣钱"做到了"冻结"，业务对外还看不到完成**；Confirm/Cancel 只是状态切换，幂等可重试。

## 三、TCC vs 2PC

| 维度 | 2PC/XA | TCC |
| --- | --- | --- |
| 层次 | 数据库层（RM 锁） | 业务层（业务字段冻结） |
| 锁 | DB 行锁，全程持锁 | 业务字段标记，无 DB 长锁 |
| 性能 | 低（锁等待） | 高 |
| 一致性 | 强一致 | 最终一致（中间态可见但短暂） |
| 业务侵入 | 无 | 大（要写三接口） |
| 隔离性 | DB 隔离级别保证 | 业务层自己保证（冻结字段） |
| 适用 | 资金核心强一致 | 互联网高并发交易 |

## 四、TCC 三大坑（必背）

### 1. 空回滚（Empty Rollback）
**现象**：Try 还没执行（或失败了），但因网络问题 TM 收不到 Try 响应 → 触发 Cancel。Cancel 来了但 Try 没做。
**危害**：Cancel 直接执行会按"假设 Try 成功"去释放资源，但 Try 没冻结过任何资源，导致数据错乱（如把没冻结的钱退回 balance，凭空多钱）。
**解法**：Cancel 前**检查 Try 是否执行过**——
- 引入"事务活动表"（`tx_activity`）记录每个分支事务的 Try 状态。
- Try 进来先插一条 `trying`；Cancel 时查不到 `trying` → 插 `cancelled` 直接返回（空回滚）。

### 2. 悬挂（Suspend）
**现象**：Cancel 比 Try 先到（TM 超时发 Cancel，但 Try 网络延迟后才到）。Cancel 做了空回滚，之后 Try 才到 → Try 冻结了资源，但 Confirm 永远不会来了（TM 已认为事务结束）→ 资源永久悬挂。
**危害**：资源被冻结后再也释放不了。
**解法**：Try 进来先查 `tx_activity`，**若已有 `cancelled` 记录则直接跳过 Try**（已被回滚过，再 Try 没意义）。

### 3. 幂等（Idempotent）
**现象**：TM 重试 Confirm/Cancel（网络抖动、超时），同一个 Confirm/Cancel 被调多次。
**危害**：Confirm 多次 → 钱加多次；Cancel 多次 → 钱退多次。
**解法**：每次操作前查 `tx_activity` 状态：
- 已 `confirmed` 的 Confirm 再调直接返回；
- 已 `cancelled` 的 Cancel 再调直接返回。
- 状态机 + 唯一事务 ID 保证只执行一次。

## 五、TCC 隔离性

TCC 中间态对外可见（Try 后 A 余额已扣但 B 还没加），并发问题靠业务层：
- **预留字段隔离**：A 扣的是 `balance`，预留 `frozen`；其他事务看 `available = balance - frozen`。
- **业务版本号 / 状态机**：库存类用 `version` 字段或状态机避免超卖。
- **资源总额校验**：Try 时校验 `balance >= 预留量`，不足拒绝。

不像 DB 事务的 RR/Serializable 由锁/MVCC 保证，TCC 隔离**靠业务设计**。

## 六、TCC 适合什么场景

- **高并发资金/库存**：电商扣库存、积分、优惠券、账户转账。
- **业务能改三接口**：愿意为性能付出业务侵入代价。
- **需要较强隔离**：通过预留字段实现业务隔离。

不适合：
- 业务无法拆 Try/Confirm/Cancel（如调第三方 API，不能"预留"）。
- 短期内频繁变更的业务（三接口维护成本高）。

## 七、TCC 框架
- **Seata TCC**：Seata 框架的 TCC 模式，TM/TC/RM 角色清晰。
- **Hmily**：国产 TCC 框架，支持 Spring Cloud/Dubbo。
- **ByteTCC**、**EasyTransaction**：早期开源 TCC。

## 易错点
- TCC 当 2PC → 是业务层两阶段，不是 DB 层。
- 不做幂等 → Confirm/Cancel 重试导致数据错乱。
- 不防空回滚 → Try 没执行 Cancel 来了乱释放。
- 不防悬挂 → Cancel 先到 Try 后到，资源永久冻结。
- Try 真做业务（不是预留）→ 失去 TCC 隔离优势，退化成普通调用。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["distributed-systems/distributed-txn-overview",
         "distributed-systems/2pc-3pc-protocol",
         "distributed-systems/saga-pattern",
         "distributed-systems/seata-framework"])

# =========================================================================== #
# 4. Saga
# =========================================================================== #
q("distributed-systems/saga-pattern.md",
  "Saga 模式 (长事务 / 编排 vs 协同 / 补偿顺序 / 隔离性)",
  "distributed-systems", "", "hard",
  ["saga", "distributed-transaction", "compensation", "long-running",
   "orchestration", "choreography", "eventual-consistency"],
  [],
  """# Saga 模式 (长事务 / 编排 vs 协同 / 补偿顺序 / 隔离性)

## 问题描述

Saga 是什么？和 TCC 区别？编排和协同两种实现？补偿怎么设计？为什么说 Saga 没有隔离性？

## 解答

## 一、Saga 是什么

**Saga = 把一个长分布式事务拆成一串本地事务，每个本地事务有对应的补偿事务**。任何一步失败，**按反向顺序执行已成功步骤的补偿**，最终达到"业务回滚"。

特征：
- **最终一致**（不是强一致）。
- **适合长流程**（旅游预订：订机票→订酒店→租车→支付，跨多个服务，总时长几十秒~几分钟）。
- **没有全局锁**，中间态可见。
- **补偿是业务级**（不是 DB undo）。

## 二、Saga vs TCC

| 维度 | TCC | Saga |
| --- | --- | --- |
| 阶段 | 三阶段（Try/Confirm/Cancel） | 一串本地事务 + 反向补偿 |
| 资源占用 | Try 阶段预留资源（贯穿全程） | 每步做完即提交，不留预留 |
| 失败回滚 | Cancel 释放预留 | 反向执行补偿 |
| 隔离 | 预留字段隔离 | **无隔离**（中间态对外可见） |
| 适合 | 短事务、需强隔离 | **长事务**、能接受中间态可见 |

→ **Saga 不预留资源**，每步立即提交，失败靠补偿回滚。这让它适合长流程（资源不用长时间锁定），代价是无隔离。

## 三、两种实现方式

### 1. 编排式（Orchestration）—— 中心协调者
- 有一个 **Saga 协调者**（Orchestrator）按顺序调用各服务，跟踪状态，失败时反向调补偿。
- 协调者维护状态机：`{step1: done, step2: done, step3: failed}` → 反向调 `compensate2, compensate1`。
- 优点：流程清晰、易监控、易扩展。
- 缺点：协调者中心化（单点风险，需做高可用 + 状态持久化）。
- 框架：**Seata SAGA**、**Camunda**、**Temporal**、**AWS Step Functions**。

### 2. 协同式（Choreography）—— 事件驱动无中心
- 每个服务监听事件，做完自己的事 + 发下一个事件；失败发补偿事件。
- 例：订单服务发 `OrderCreated` → 库存服务扣库存发 `InventoryDeducted` → 支付服务扣钱发 `PaymentCompleted` → 订单服务更新订单为完成。
- 失败：支付失败发 `PaymentFailed` → 库存服务监听到回滚库存 → 订单服务监听到取消订单。
- 优点：去中心化、无单点。
- 缺点：流程隐式难追踪，环路/重复事件难管理，扩展时易出错。
- 适合：步骤少、稳定的流程。

## 四、补偿设计要点

### 1. 补偿必须可重入且幂等
网络重试可能让补偿被多次调用——必须幂等（状态机 / 唯一键 / 版本号）。

### 2. 补偿顺序严格反向
T1 → T2 → T3 → T3 失败 → C2 → C1（**不调 C3**，T3 失败了本身就没成功）。

### 3. 补偿可能不完美
- 已发出去的邮件/短信：补偿是"发更正邮件"，不是"撤回邮件"（做不到）。
- 已对外可见的状态：补偿是"标记取消"，不能假装没发生过。
- 资金类：补偿必须精确（金额对账）。

### 4. 补偿失败怎么办
- 重试 N 次 → 仍失败 → 告警 + 人工介入 + 持久化失败状态待对账。
- 框架（Seata SAGA/Temporal）会持续重试，状态机持久化。

### 5. 超时处理
- 每步设超时 + 重试策略。
- 整个 Saga 设总超时，超时未完成进异常状态。

## 五、隔离性问题（Saga 最大短板）

- Saga 中间态**对外可见**：订机票成功但酒店还没订，外部查询能看到机票已订。
- 并发问题典型：**脏读 + 不可重复读 + 幻读**业务级发生。
- 解法：
  - **业务层锁**：状态机 + 版本号（如订单状态机 `pending` → `confirmed`）。
  - **语义锁**：每步开始把业务对象标记为 `processing`，外部查询时按业务规则决定能否读。
  - **可交换的步骤**：把可乱序执行的步骤用 commutative 设计（如累加可用任意顺序）。
  - **读补救**：外部读时考虑中间态（显示"订单处理中"而不是"已预订"）。

## 六、Saga 适用场景

- **长流程跨服务**：旅游预订、订单履约、贷款审批、报销流程。
- **能接受中间态可见**：业务允许"处理中"状态对外。
- **补偿可实现**：每步都能设计合理补偿（资金、库存可行；邮件/通知只能"补发更正"）。

不适合：
- 短事务高并发（用 TCC）。
- 不能接受中间态可见的强一致场景（用 2PC/XA）。
- 补偿不可能的操作（如已发货不可"取消发货"）。

## 七、框架

- **Seata SAGA**：状态机驱动编排式，JSON 定义流程。
- **Temporal**：通用工作流引擎，支持 Saga 模式，强类型 + 持久化。
- **Camunda BPMN**：业务流程引擎， BPMN 建模 Saga。
- **AWS Step Functions**：云上编排式 Saga。

## 易错点
- Saga 当强一致 → 是最终一致，中间态可见。
- 不做补偿幂等 → 重试乱回滚。
- 补偿当"撤销" → 已对外可见的动作只能"补偿"，不能假装没发生。
- 协同式不画流程图 → 步骤一多就乱。
- 忽略隔离性 → 并发导致业务脏读/超卖。
- 用 Saga 做短高并发交易 → 应该用 TCC，Saga 是为长流程而生。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["distributed-systems/distributed-txn-overview",
         "distributed-systems/tcc-transaction",
         "distributed-systems/eventual-consistency-patterns",
         "distributed-systems/seata-framework"])

# =========================================================================== #
# 5. 最终一致性方案集
# =========================================================================== #
q("distributed-systems/eventual-consistency-patterns.md",
  "最终一致性方案 (本地消息表 / 事务消息 / Outbox+CDC / 最大努力通知 / 对账)",
  "distributed-systems", "", "hard",
  ["eventual-consistency", "local-message-table", "transaction-message",
   "outbox", "cdc", "rocketmq", "debezium", "best-effort", "reconciliation"],
  [],
  """# 最终一致性方案 (本地消息表 / 事务消息 / Outbox+CDC / 最大努力通知 / 对账)

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
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["distributed-systems/distributed-txn-overview",
         "distributed-systems/saga-pattern",
         "distributed-systems/tcc-transaction",
         "distributed-systems/kafka-duplicate-consumption-message-loss.md",
         "distributed-systems/redis-mq-vs-kafka-rocketmq.md"])

# =========================================================================== #
# 6. Seata
# =========================================================================== #
q("distributed-systems/seata-framework.md",
  "Seata 框架 (AT/TCC/SAGA/XA 四模式 / TC/TM/RM / AT 原理 / 生产坑)",
  "distributed-systems", "", "hard",
  ["seata", "at-mode", "tcc", "saga", "xa", "distributed-transaction",
   "undo-log", "global-lock", "java", "spring-cloud", "dubbo"],
  [],
  """# Seata 框架 (AT/TCC/SAGA/XA 四模式 / TC/TM/RM / AT 原理 / 生产坑)

## 问题描述

Seata 是什么？四种模式区别？AT 模式怎么自动补偿？TC/TM/RM 各干什么？生产怎么用？有什么坑？

## 解答

## 一、Seata 是什么

阿里开源的**分布式事务框架**，提供统一的 API + 四种事务模式，适配 Spring Cloud / Dubbo / gRPC。原名 Fescar，2019 改名 Seata。

### 三个核心角色
| 角色 | 全称 | 职责 |
| --- | --- | --- |
| **TC** | Transaction Coordinator | 协调者，独立部署的服务（`seata-server`），维护全局事务状态，决定 commit/rollback |
| **TM** | Transaction Manager | 全局事务发起方（标注 `@GlobalTransactional` 的方法所在服务），向 TC 开启/提交/回滚全局事务 |
| **RM** | Resource Manager | 资源管理器，每个微服务里的分支事务，向 TC 注册分支、上报状态 |

### 全局事务流程
1. TM 调 `TC.begin()` 开全局事务，拿 `XID`。
2. XID 通过 RPC 头（Dubbo/SpringCloud filter）传到下游服务。
3. 下游 RM 拿到 XID，向 TC 注册分支事务，执行业务，上报状态。
4. TM 调 `TC.commit()` 或 `TC.rollback()`。
5. TC 通知所有 RM commit 或 rollback。

## 二、四种模式对比

| 模式 | 一致性 | 业务侵入 | 性能 | 适合 |
| --- | --- | --- | --- | --- |
| **AT** | 最终一致 | **零**（自动生成 undo） | 中（全局锁） | 大多数业务、CRUD 场景 |
| **TCC** | 最终一致 | 大（三接口） | 高 | 高并发交易、需强隔离 |
| **SAGA** | 最终一致 | 中（写补偿） | 高 | 长流程业务 |
| **XA** | 强一致 | 零 | 低（锁等待） | 资金核心、传统 DB |

## 三、AT 模式原理（重点）

AT = Auto Transaction，**业务零侵入**，框架自动生成 undo_log 反向补偿。

### 一阶段：业务执行 + 记录 undo
1. RM 拦截业务 SQL（基于 MyBatis/JDBC 代理）。
2. **解析 SQL**，查 `before image`（执行前的数据快照）。
3. 执行业务 SQL。
4. 查 `after image`（执行后快照）。
5. 把 before/after image 存到 `undo_log` 表（**与业务 SQL 同一本地事务**）。
6. **向 TC 注册分支 + 申请全局锁**（锁住业务操作的行，防止其他全局事务修改）。
7. 本地事务提交（业务 + undo_log 一起提交）。

### 二阶段 commit
1. TC 通知 RM commit。
2. RM **异步删 undo_log**（一阶段已提交，无需做别的）。

### 二阶段 rollback
1. TC 通知 RM rollback。
2. RM 查 undo_log 拿 after image。
3. **校验当前数据是否等于 after image**（防脏写）：
   - 相等 → 用 before image 反向恢复数据。
   - 不等 → 被别的事务改过，告警人工介入。
4. 删 undo_log。

### AT 的全局锁
- AT 用全局锁保证分支事务的"写隔离"：分支一阶段提交本地事务后，行被"全局锁"标记，其他全局事务要改这些行得等锁。
- **读隔离默认读已提交**；要可重复读需 `@GlobalLock` + `SELECT FOR UPDATE`。

### AT 优缺点
- 优点：**业务零侵入**，加 `@GlobalTransactional` 就能用。
- 缺点：
  - 全局锁影响并发性能。
  - 不支持复杂 SQL（如多表 join 后改、存储过程）。
  - 全局锁争用是高并发瓶颈。
  - 需要每张业务表对应 `undo_log` 表。

## 四、TCC 模式（Seata 封装）
- 业务实现 `BusinessAction` 接口的 `prepare / commit / rollback` 三方法，标 `@TwoPhaseBusinessAction`。
- Seata 自动管理状态、重试、超时。
- 框架帮解决"空回滚/悬挂/幂等"中的部分（通过 `TCC fence` 表，1.5.0+ 引入）。

## 五、SAGA 模式（Seata 封装）
- 用 JSON 状态机定义流程（每步的 service + 补偿 service）。
- 适合长流程，无全局锁。
- 状态机引擎持久化状态，失败自动反向执行补偿。

## 六、XA 模式
- Seata 1.2+ 支持标准 XA，依赖 DB 的 XA 协议。
- 强一致，性能低，跨异构 DB（MySQL/Oracle）可行。
- 业务零侵入（同 AT），但底层是 XA 协议（持锁到 commit）。

## 七、生产部署

### TC 集群
- `seata-server` 多实例 + 注册中心（Nacos/Eureka）+ 配置中心。
- 状态存储：DB（MySQL）/ Redis（高可用）。
- 高可用：TC 无状态，状态持久化即可水平扩。

### 集成
- Spring Boot：`seata-spring-boot-starter`。
- Spring Cloud：`spring-cloud-starter-alibaba-seata`，自动加 RPC filter 透传 XID。
- Dubbo：`seata-dubbo` filter 透传 XID。
- 数据源代理：`DataSourceProxy` 拦截 SQL（AT 用）。

### 必做
- 每个业务库加 `undo_log` 表（AT 必需）。
- `branch_table` / `global_table` / `lock_table`（TC 端）。
- XID 透传：自定义 RPC（gRPC/REST）要手动在 header 传 `TX_XID`。

## 八、生产坑

### 1. 全局锁成瓶颈
AT 模式高并发热点行 → 全局锁排队，吞吐骤降。解法：拆表/分桶/换 TCC。

### 2. undo_log 脏写校验失败
after image 与当前数据不一致（被其他**非全局事务**改过）→ rollback 失败需人工介入。要保证所有改这表的入口都走 Seata。

### 3. 跨服务调用 XID 丢失
- 自定义 RPC（Feign filter 漏配 / gRPC interceptor 没加）→ XID 不传，下游不加入全局事务。
- 异步线程（`@Async` / 线程池）默认不传 XID → 用 `RootContext.bind` 手动传或用 Seata 的 `ThreadLocal` 上下文传播工具。

### 4. 全局事务超时
- 默认 60s，长事务超过 → TC 强制 rollback。长流程该用 SAGA 或调大超时。

### 5. 死锁
- 多个全局事务交叉锁不同表的相同行 → 全局锁死锁。监控 `lock_table` + 优化加锁顺序。

### 6. RPC 重试导致分支重复执行
- Dubbo/Spring Cloud 重试会让一个分支被调多次 → 业务接口必须幂等。

### 7. 不支持嵌套全局事务
- Seata 不支持嵌套（一个 `@GlobalTransactional` 内开另一个会失败或并入父事务）。

### 8. AT 不支持的 SQL
- 复杂 join、存储过程、DDL → AT 拦截不了，要么改 TCC，要么避开。

## 易错点
- AT 当万能 → 复杂 SQL / 高并发热点不行。
- 忘 `undo_log` 表 → AT 一阶段就报错。
- XID 不透传 → 跨服务事务不生效。
- 异步线程不传 XID → 分支事务丢失。
- 全局事务超时默认 60s 不调 → 长业务被强制 rollback。
- AT 和非 AT 入口混用 → 脏写校验失败。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["distributed-systems/distributed-txn-overview",
         "distributed-systems/2pc-3pc-protocol",
         "distributed-systems/tcc-transaction",
         "distributed-systems/saga-pattern",
         "distributed-systems/rpc-and-distributed-txn"])

# =========================================================================== #
# 7. RPC + 分布式事务
# =========================================================================== #
q("distributed-systems/rpc-and-distributed-txn.md",
  "RPC 调用与分布式事务 (超时/重试/幂等 / XID 透传 / 大事务 / 降级)",
  "distributed-systems", "", "hard",
  ["rpc", "dubbo", "grpc", "feign", "distributed-transaction",
   "xid", "timeout", "retry", "idempotent", "circuit-breaker", "java"],
  [],
  """# RPC 调用与分布式事务 (超时/重试/幂等 / XID 透传 / 大事务 / 降级)

## 问题描述

RPC 调用在分布式事务里有哪些坑？超时重试和事务边界怎么处理？XID 怎么跨服务传？异步线程怎么办？降级时事务怎么处理？大事务怎么拆？

## 解答

## 一、RPC 调用的核心不确定性

分布式事务里的 RPC 调用比同步本地调用多三类问题：
1. **超时不确定**：调用超时，但对方可能已执行/未执行/执行了一半。
2. **重试导致重复**：重试让同一调用被多次执行。
3. **链路状态丢失**：跨服务后本地事务上下文（XID、TraceId、ThreadLocal）丢失。

## 二、超时处理

### 三个超时层次
| 超时 | 含义 | 配置 |
| --- | --- | --- |
| RPC 调用超时 | 等对方响应的最大时间 | Dubbo `timeout` / Feign `connectTimeout`+`readTimeout` |
| 全局事务超时 | 整个全局事务允许的最长时间 | Seata `service.default.grouplist.timeout` / `@GlobalTransactional(timeout=...)` |
| 业务超时 | 业务级等待（如锁等待、外部 API） | 业务自己控制 |

### 超时配置原则
- **RPC 超时 < 全局事务超时**：避免 RPC 还没回，全局事务已被 TC 强制 rollback。
- **下游 RPC 超时 < 上游 RPC 超时**：链路上越往下游超时越短，让上游能在自己超时前拿到下游失败。
- 默认值参考：RPC 1~3s，全局事务 60s（长流程调大或用 SAGA）。

### 超时后的处理
- 超时**不能假设对方没执行**——可能已执行成功但响应未回。
- 重试必须**幂等**，避免重复执行副作用。
- 超时后可主动查询对方状态（如果对方提供查询接口）。

## 三、重试与幂等

### 重试策略
- Dubbo：`retries=2`（默认重试 2 次，共 3 次调用），**仅对幂等接口重试**。
- Feign：`Retryer.Default` 可配。
- 重试 + 指数退避（避免雪崩）：1s → 2s → 4s。

### 必须幂等
- **写接口绝不能盲目重试**：扣款接口重试 2 次 = 扣 3 次。
- 幂等实现：
  - **唯一请求 ID**：每次调用带 `requestId`，下游用 `UNIQUE KEY` 去重。
  - **业务键去重**：订单号 + 操作类型作为幂等键。
  - **状态机**：状态流转单向，重复调用不改变已流转的状态。
  - **去重表**：`processed_request (request_id PK)`，处理前 insert，冲突即跳过。

### Dubbo/Feign 重试注意事项
- Dubbo 默认重试 2 次 → **写接口必须显式 `retries=0`** 或保证幂等。
- Feign 默认不重试（`Retryer.NEVER_RETRY`）。
- 重试期间若发生超时，要小心总耗时超过全局事务超时。

## 四、XID 跨服务透传（核心机制）

### Seata XID 透传
- TM 开全局事务后生成 `XID`（`IP:PORT:transactionId`）。
- XID 通过 **RPC 上下文**透传到下游，下游 RM 拿到 XID 注册分支事务。

### 各 RPC 框架集成
| 框架 | 集成方式 |
| --- | --- |
| **Dubbo** | `seata-dubbo` filter 自动透传 XID |
| **Spring Cloud OpenFeign** | `spring-cloud-starter-alibaba-seata` 自动加 RequestInterceptor |
| **gRPC** | 自己写 Interceptor，在 metadata 里塞 `TX_XID` |
| **RestTemplate** | `ClientHttpRequestInterceptor` 加 header |
| **自定义 HTTP** | 在 header 传 `TX_XID`，下游解出来 `RootContext.bind` |

### 漏配的常见症状
- 下游事务不加入全局事务，独立提交 → 数据不一致。
- `RootContext.getXID()` 在下游为 null。

## 五、异步线程与上下文传播

### 问题
- `@Async` / `ThreadPoolExecutor` / `CompletableFuture` 默认**不传 ThreadLocal**，XID 丢失 → 分支事务脱离全局事务。

### 解法
1. **Seata 的 `RootContext.bind` / `unbind`**：手动传 XID。
2. **TTL（TransmittableThreadLocal）**：阿里的 TTL 框架能跨线程池传 ThreadLocal，Seata 1.5+ 集成支持。
3. **TaskDecorator**（Spring）：给 `TaskExecutor` 加装饰器传上下文。
4. **显式传递**：提交任务时把 XID 作为参数传，任务里 `RootContext.bind(xid)` 开始时、`unbind` 结束时。

```java
String xid = RootContext.getXID();
executor.submit(() -> {
    RootContext.bind(xid);
    try { businessLogic(); }
    finally { RootContext.unbind(); }
});
```

## 六、大事务拆分

### 问题
- 一个全局事务包太多 RPC 调用 → 耗时长 → 全局锁长时间持有 → 性能差 + 超时风险。
- 长事务占用 TC 资源、增加 rollback 范围。

### 拆分原则
- **核心强相关**放一个全局事务：如"扣库存 + 创建订单"。
- **可异步的副作用**拆出去：如"下单成功后发短信、加积分、通知物流"用消息驱动最终一致（本地消息表/事务消息）。
- **长流程**用 Saga 而非 AT/TCC：每步独立提交，不长时间持锁。

### 经典模式：核心事务 + 消息后置
```
@GlobalTransactional  // 只包核心写
public void placeOrder() {
    orderService.create();        // 同事务
    inventoryService.deduct();    // 同事务
    accountService.charge();      // 同事务
    // 不在这里发短信/加积分
}

// 用本地消息表/事务消息异步触发后续：
// 发短信、加积分、通知物流 → 各自幂等消费
```

## 七、降级与熔断时的事务处理

### 熔断（Sentinel/Resilience4j）触发
- 下游服务熔断 → 上游 RPC 失败 → 全局事务 rollback。
- **降级返回默认值要谨慎**：在事务中降级会让"部分成功部分降级"破坏一致性。
- 解法：
  - 事务中的关键步骤**不降级**，失败即 rollback。
  - 降级只能放在事务外（事务结束后做"尽力而为"的副作用）。

### 服务不可用
- 全局事务中某分支服务挂了 → 整个事务 rollback，等待人工或重试。
- 长期不可用 → 用 Saga 让流程可以暂停 + 后续重试。

### 限流
- 事务中调下游被限流 → 等同于失败 → rollback。
- 限流配置要与事务超时协调：限流等待时间 < RPC 超时 < 全局事务超时。

## 八、调用链监控

- TraceId（SkyWalking/Skywalking/Zipkin）必须透传，便于跨服务排查事务失败点。
- Seata 的 XID 也建议加入 Trace 上下文，监控事务链路。
- 关键指标：全局事务成功率、分支事务失败率、超时率、rollback 原因分布。

## 九、典型陷阱速查

| 陷阱 | 表现 | 解法 |
| --- | --- | --- |
| RPC 重试非幂等 | 扣款被扣多次 | 写接口 `retries=0` 或加幂等键 |
| XID 丢失 | 下游不加入事务 | 检查 filter / interceptor / header |
| 异步线程丢 XID | 异步分支脱离事务 | TTL / 手动 bind-unbind |
| RPC 超时 > 全局超时 | 全局事务先 rollback，RPC 后回成功 | 调小 RPC 超时 / 调大全局超时 |
| 大事务包太多 | 全局锁长时间持有 | 拆分 + 消息后置 |
| 事务中降级 | 部分成功部分默认值 | 降级放事务外 |
| 超时假设没执行 | 重试导致重复 | 幂等 + 主动查状态 |

## 易错点
- RPC 重试非幂等写接口 → 重复扣款/超卖。
- XID 没透传到自定义 RPC → 跨服务事务不生效。
- 异步线程不传 XID → 分支丢失。
- RPC 超时 > 全局事务超时 → 全局先 rollback，RPC 后回成功，数据不一致。
- 事务里降级 → 破坏一致性。
- 大事务不拆 → 全局锁瓶颈 + 超时。
- 超时当"没执行" → 实际可能已执行，重试幂等关键。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["distributed-systems/distributed-txn-overview",
         "distributed-systems/seata-framework",
         "distributed-systems/tcc-transaction",
         "distributed-systems/saga-pattern",
         "distributed-systems/eventual-consistency-patterns",
         "concurrency/threadlocal-usage-pitfalls",
         "concurrency/threadpool-parameter-tuning"])

print("\nDone: 7 distributed transaction docs")
