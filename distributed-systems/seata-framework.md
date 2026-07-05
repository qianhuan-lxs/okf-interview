---
type: question
id: distributed-systems/seata-framework
title: Seata 框架 (AT/TCC/SAGA/XA 四模式 / TC/TM/RM / AT 原理 / 生产坑)
category: distributed-systems
subcategory: ""
difficulty: hard
tags: [seata, at-mode, tcc, saga, xa, distributed-transaction, undo-log, global-lock, java, spring-cloud, dubbo]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-07-05
---

# Seata 框架 (AT/TCC/SAGA/XA 四模式 / TC/TM/RM / AT 原理 / 生产坑)

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

## 延伸

- 关联题：[[distributed-systems/distributed-txn-overview]]
- 关联题：[[distributed-systems/2pc-3pc-protocol]]
- 关联题：[[distributed-systems/tcc-transaction]]
- 关联题：[[distributed-systems/saga-pattern]]
- 关联题：[[distributed-systems/rpc-and-distributed-txn]]
