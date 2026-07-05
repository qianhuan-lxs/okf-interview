---
type: question
id: distributed-systems/tcc-transaction
title: TCC 事务 (Try-Confirm-Cancel / 业务侵入 / 三大坑: 空回滚/悬挂/幂等)
category: distributed-systems
subcategory: ""
difficulty: hard
tags: [tcc, distributed-transaction, eventual-consistency, compensation, idempotent, business-transaction]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-07-05
---

# TCC 事务 (Try-Confirm-Cancel / 业务侵入 / 三大坑: 空回滚/悬挂/幂等)

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

## 延伸

- 关联题：[[distributed-systems/distributed-txn-overview]]
- 关联题：[[distributed-systems/2pc-3pc-protocol]]
- 关联题：[[distributed-systems/saga-pattern]]
- 关联题：[[distributed-systems/seata-framework]]
