---
type: question
id: distributed-systems/distributed-lock-redis-vs-zk
title: 分布式锁 (Redis vs ZK)
category: distributed-systems
subcategory: distributed-systems
difficulty: medium
tags: [distributed-lock, redis, zookeeper, redlock, consensus]
languages: []
role: [ai-app, sde, backend]
companies: [恩士讯]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 分布式锁 (Redis vs ZK)

## 问题描述
微服务多实例下 JVM 级别锁锁不住资源，有什么解决方案？Redis 和 ZK 实现分布式锁，各有什么优缺点？

## 解答

### 为什么 JVM 锁不够
JVM 锁（synchronized / ReentrantLock）只在单进程内有效。微服务多实例 = 多进程，各自 JVM 互不可见，锁失效。必须把锁放到**共享中间件**。

### Redis 分布式锁（SETNX + 过期）
```
SET lock:order:123 <requestId> NX PX 30000
```
- **加锁**：`SET key value NX PX ttl`，原子。
- **解锁**：Lua 脚本校验 value==requestId 再 DEL（避免误删别人锁）。
- **续期**：后台线程定时延长 TTL（Redisson 的 watchdog）。

**优点**：性能高（内存 + 简单命令）。
**缺点**：
- 主从异步复制，主挂从提升时锁可能丢（见 [[distributed-systems/redlock-redis-lock-loss]]）。
- 不是严格的 CP，极端情况锁不可靠。

### ZK 分布式锁（临时顺序节点 + Watch）
1. 在 `/lock` 下创建**临时顺序节点** `/lock/seq-001`。
2. 检查自己是不是最小序号 → 是则获锁。
3. 否则监听前一个节点删除事件，前驱释放时被唤醒。
4. 客户端断线 → 临时节点自动删，锁自动释放（避免死锁）。

**优点**：CP（ZAB 保证一致），锁可靠、不丢、客户端宕机自动释放。
**缺点**：性能低于 Redis（每次写要 quorum + 持久化）；写入频繁场景压力大。

### 选型
- 高性能、可容忍极端情况下锁失效 → Redis（Redisson）。
- 强一致、正确性优先（金融、库存）→ ZK / etcd。

## 延伸

## 延伸

- 关联题：[[distributed-systems/redlock-redis-lock-loss]]
- 关联题：[[concurrency/optimistic-vs-pessimistic-lock]]
- 关联题：[[distributed-systems/cap-theory]]
