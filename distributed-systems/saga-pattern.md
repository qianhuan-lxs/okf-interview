---
type: question
id: distributed-systems/saga-pattern
title: Saga 模式 (长事务 / 编排 vs 协同 / 补偿顺序 / 隔离性)
category: distributed-systems
subcategory: ""
difficulty: hard
tags: [saga, distributed-transaction, compensation, long-running, orchestration, choreography, eventual-consistency]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-07-05
---

# Saga 模式 (长事务 / 编排 vs 协同 / 补偿顺序 / 隔离性)

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

## 延伸

- 关联题：[[distributed-systems/distributed-txn-overview]]
- 关联题：[[distributed-systems/tcc-transaction]]
- 关联题：[[distributed-systems/eventual-consistency-patterns]]
- 关联题：[[distributed-systems/seata-framework]]
