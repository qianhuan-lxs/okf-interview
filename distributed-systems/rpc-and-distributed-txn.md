---
type: question
id: distributed-systems/rpc-and-distributed-txn
title: RPC 调用与分布式事务 (超时/重试/幂等 / XID 透传 / 大事务 / 降级)
category: distributed-systems
subcategory: ""
difficulty: hard
tags: [rpc, dubbo, grpc, feign, distributed-transaction, xid, timeout, retry, idempotent, circuit-breaker, java]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-07-05
---

# RPC 调用与分布式事务 (超时/重试/幂等 / XID 透传 / 大事务 / 降级)

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

## 延伸

- 关联题：[[distributed-systems/distributed-txn-overview]]
- 关联题：[[distributed-systems/seata-framework]]
- 关联题：[[distributed-systems/tcc-transaction]]
- 关联题：[[distributed-systems/saga-pattern]]
- 关联题：[[distributed-systems/eventual-consistency-patterns]]
- 关联题：[[concurrency/threadlocal-usage-pitfalls]]
- 关联题：[[concurrency/threadpool-parameter-tuning]]
