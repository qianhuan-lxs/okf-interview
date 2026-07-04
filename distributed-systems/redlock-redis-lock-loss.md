---
type: question
id: distributed-systems/redlock-redis-lock-loss
title: Redlock / Redis 主从切换丢锁
category: distributed-systems
subcategory: distributed-systems
difficulty: hard
tags: [redlock, redis, distributed-lock, consensus, failover]
languages: []
role: [ai-app, sde, backend]
companies: [恩士讯]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# Redlock / Redis 主从切换丢锁

## 问题描述
Redis 加锁后主节点挂了，从节点被提升为主，锁没同步导致丢失，怎么解决？

## 解答

### 问题根因
Redis 主从**异步复制**：客户端在主加锁成功返回，但还未同步到从；此时主挂、从提升为新主，新主没有这把锁 → 另一个客户端也能加锁成功 → **双持锁**。

### 方案一：Redlock（Antirez 提出）
- 用 **N（通常 5）个独立 Redis 实例**（不是主从，是独立部署）。
- 客户端向所有 N 个实例依次 `SET NX PX`，加锁成功率 = 在 **多数派 (N/2+1)** 实例上成功 + 总耗时 < TTL。
- 解锁：向所有实例发 DEL。
- 思路：多数派独立实例同时故障的概率远低于单主从切换。

### Redlock 争议
- Martin Kleppmann 批评：依赖时钟同步，GC 暂停/进程暂停会导致客户端持锁过期仍以为自己有锁。
- 实践中：对正确性要求极高的场景推荐 ZK/etcd（CP）而非 Redlock。

### 方案二：用 fencing token
- 每次加锁返回**单调递增 token**，下游服务（DB/存储）只接受更高 token 的写。
- 即便双持锁，旧 token 的写会被下游拒绝。这是更鲁棒的正确性保证，但要求下游支持 token 校验。

### 方案三：Redisson
- 单 Redis 主从场景下用 Redisson 的 watchdog 续期，降低 TTL 过期误判。
- 但仍不能解决主从切换丢锁的根本问题，需配合 Redlock 或换 ZK。

### 工程结论
- 业务能容忍偶发双持（幂等保护兜底）→ Redisson 单实例足够。
- 强一致 → ZK/etcd 临时顺序节点锁 + fencing token。

## 延伸

## 延伸

- 关联题：[[distributed-systems/distributed-lock-redis-vs-zk]]
- 关联题：[[distributed-systems/cap-theory]]
