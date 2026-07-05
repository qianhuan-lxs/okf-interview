---
type: question
id: concurrency/deadlock-detection-prevention
title: 死锁四条件 + 排查 + 避免
category: concurrency
subcategory: concurrency
difficulty: medium
tags: [deadlock, jstack, lock-ordering, concurrency]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-05-26
---

# 死锁四条件 + 排查 + 避免

## 问题描述

死锁的四个必要条件？怎么排查？怎么避免？

## 解答

### 四个必要条件（Coffman）
1. **互斥**：资源同一时刻只能一个进程/线程用。
2. **持有并等待**：持着资源 A 又请求资源 B。
3. **不可剥夺**：资源不能强行抢，只能自愿释放。
4. **循环等待**：存在线程链 T1 等 T2 持的资源、T2 等 T3……Tn 等 T1。

破坏任一条件即可避免死锁。

### 经典场景
```java
// 线程1
synchronized(A) { synchronized(B) { ... } }
// 线程2
synchronized(B) { synchronized(A) { ... } }
```
循环等待：T1 持 A 等 B，T2 持 B 等 A。

### 排查
- **`jstack <pid>`**：直接看 "Found one Java-level deadlock" 段，列出死锁链和持有/等待的锁。
- **`jconsole` / `VisualVM`**：图形界面看线程标签页的 deadlock 检测。
- **`ThreadMXBean.findDeadlockedThreads()`**：代码内检测，可埋点告警。
- 日志特征：线程长期 BLOCKED，且 `waiting to lock <0x...addr>` 与 `locked <0x...addr>` 形成环。

### 避免策略
1. **锁顺序**：全系统约定按固定顺序获取锁（如按锁对象 hash 排序）→ 破坏循环等待。最实用。
2. **锁超时**：`tryLock(timeout)` 拿不到就回退或释放已有锁重试 → 破坏不可剥夺。
3. **一次性获取所有锁**：用 `tryLock` 同时锁多把，失败全部释放重试（带随机退避防活锁）。
4. **粗粒度锁 / 单锁**：用一个锁代替多把 → 破坏持有并等待（牺牲并发度）。
5. **无锁数据结构**：CAS / `Atomic*` / `ConcurrentHashMap` → 破坏互斥。
6. **更高层抽象**：用 `Semaphore`/`CompletableFuture` 编排，避免手动多锁嵌套。

### 活锁与饥饿
- **活锁**：线程不阻塞但一直重试失败（互相让步退避相同）→ 加随机退避。
- **饥饿**：优先级/公平性问题导致某线程长期拿不到锁 → 用公平锁或限流队列。

## 易错点
- 锁顺序按 hash 排序但两对象 hash 相同（碰撞）→ 用 `System.identityHashCode` 仍可能同；终极方案：再加一把 tie-break 锁。
- `tryLock` 拿到后忘 `unlock` → 锁泄漏。
- 死锁不抛异常、不报错，进程"卡住"——靠监控 + jstack 才发现。

## 延伸

## 延伸

- 关联题：[[concurrency/synchronized-vs-reentrantlock]]
- 关联题：[[concurrency/aqs-principle]]
- 关联题：[[concurrency/thread-pool-principles]]
