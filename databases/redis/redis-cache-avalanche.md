---
type: question
id: databases/redis/redis-cache-avalanche
title: 缓存雪崩 / 穿透 / 击穿
category: databases
subcategory: redis
difficulty: medium
tags: [redis, cache-avalanche, cache-breakdown, cache-penetration, cache]
languages: []
role: [ai-app, sde, backend]
companies: [海颐]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 缓存雪崩 / 穿透 / 击穿

## 问题描述
你说一下缓存雪崩的理解。

## 解答

三种经典缓存故障，区分清楚是高频考点。

| 故障 | 现象 | 原因 | 解法 |
| --- | --- | --- | --- |
| **雪崩** | 大量 key 同时失效 / Redis 宕机，请求全打 DB | TTL 集中、Redis 挂 | TTL 加随机抖动；多级缓存；熔断限流；Redis 集群高可用 |
| **穿透** | 查不存在的 key，每次都打到 DB | 恶意攻击 / 业务 bug | 布隆过滤器拦截；缓存空值（短 TTL）；参数校验 |
| **击穿** | 单个热 key 过期瞬间，海量并发同时查 DB | 热 key 失效 | 互斥锁（SETNX）只让一个线程回源；热 key 永不过期 + 后台异步刷新 |

### 雪崩专项
- TTL 加 `random(60s)` 抖动避免同时过期。
- Redis 集群 + 哨兵/Cluster 高可用，避免整体宕机。
- 应用层 Hystrix/Sentinel 熔断限流，DB 不被压垮。
- 多级缓存：Caffeine 本地 + Redis + DB。

### 穿透专项
- 布隆过滤器前置：启动时把所有合法 id 加进 BF，请求先过 BF，不存在直接拒绝。
- 缓存空对象 `null` 短 TTL（30s），防同 key 反复打 DB。

### 击穿专项
- 互斥锁重建缓存：
```java
if (redis.get(key) == null) {
  if (setnx(lock, 1, 10s)) {
    val = db.query(); redis.set(key, val, ttl); del(lock);
  } else { sleep+retry; }
}
```
- 热 key 逻辑过期（不设 TTL，存过期时间戳，发现过期后异步刷新，期间返回旧值）。

## 延伸

## 延伸

- 关联题：[[databases/redis/redis-data-types]]
- 关联题：[[distributed-systems/distributed-lock-redis-vs-zk]]
- 关联题：[[backend/microservices/microservice-user-context-propagation]]
