---
type: question
id: backend/microservices/microservice-user-context-propagation
title: 微服务跨服务用户上下文传递 (设计题)
category: backend
subcategory: microservices
difficulty: hard
tags: [microservice, context-propagation, threadlocal, redis, design]
languages: []
role: [ai-app, sde, backend]
companies: [中泓一线]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 微服务跨服务用户上下文传递 (设计题)

## 问题描述
用户信息基础服务，多个业务服务需要获取用户信息，怎么设计使得带宽性能高、并发最高？不同微服务什么时候放到 ThreadLocal？怎么获取上下文信息？业务服务从哪里获取？在哪个阶段查 Redis？用户 ID 从哪里来？

## 思路

目标是**最小化重复查询、最小化跨服务带宽、最大化并发**。核心：**用户 ID 沿链路透传，用户详细信息本地缓存懒加载**。

## 解答

### 全链路设计

1. **入口（网关层）**
   - 网关解析 JWT/token → 拿到 `userId`、`tenantId`、`roles`。
   - 把 `userId` 等轻量身份信息塞进 HTTP 头 `X-User-Id` / `X-Tenant-Id` 透传下游。
   - **不在网关查用户详情**（避免网关成为瓶颈）。

2. **业务服务接收（Filter/Interceptor）**
   - 在 Servlet Filter / Spring Interceptor 拦截，从请求头读 `userId`。
   - 把 `userId` 放进当前线程 `ThreadLocal`（或 RequestScope Context）。
   - 此时 ThreadLocal 只放 **userId 等轻量字段**，不放整个 User 对象。

3. **懒加载用户详情 + 多级缓存**
   - 业务代码用 `UserContext.getUserId()` 拿到 id 后，需要详情时走：
     - **L1 进程内缓存（Caffeine）**：1~5s TTL，热点 user 命中率高、零网络。
     - **L2 Redis 缓存**：进程缓存未命中 → 查 Redis，缓存用户 JSON，5~30min TTL。
     - **L3 用户服务 + DB**：Redis 未命中 → 调用户基础服务（带本地缓存兜底）。
   - 用 **Cache-Aside**：读时回填，写时失效（用户信息变更发 MQ 广播失效）。

4. **查 Redis 的时机**
   - 不在 Filter 阶段全局查（每个请求都查会浪费，很多请求不需详情）。
   - 在 **业务代码第一次访问 UserContext.getUserDetail()** 时按需查缓存。可用 `Supplier.memoized` / `ThreadLocal` 存已加载的 User 对象，**同请求内只查一次**。

5. **跨线程透传**
   - 异步/线程池场景用 `TransmittableThreadLocal` 或 `TaskDecorator` 把 userId/userContext 透传到子线程，避免上下文丢失。

6. **RPC 透传**
   - OpenFeign/Dubbo 用 RequestInterceptor / Filter 把 `X-User-Id` 自动加到下游调用头。

### 性能要点
- **userId 走 Header，不查 DB**——零开销。
- **详情懒加载 + 进程缓存**——同一服务对同一 user 的 N 次访问只查一次外部。
- **Redis Pipeline / 本地缓存兜底**——高并发下 Redis 也不成瓶颈。
- **不要每个服务都全量查用户信息**——只取需要的字段，用 projection。

### 防雪崩
- 用户服务故障时本地缓存继续撑、Sentinel 降级返回最小信息（仅 userId + 默认权限）。

## 易错点
- 在 Filter 里无脑查用户详情 → 每个请求都查，浪费严重。
- ThreadLocal 不 remove → 线程池脏数据/泄漏（见 [[concurrency/threadlocal-threadpool-problems]]）。

## 延伸

## 延伸

- 关联题：[[concurrency/threadlocal-usage-pitfalls]]
- 关联题：[[concurrency/threadlocal-threadpool-problems]]
- 关联题：[[databases/redis-cache-avalanche]]
- 关联题：[[backend/microservices/spring-cloud-microservice-ecosystem]]
