---
type: question
id: concurrency/synchronized-vs-reentrantlock
title: synchronized vs ReentrantLock 区别 (含锁升级与选型)
category: concurrency
subcategory: concurrency
difficulty: hard
tags: [synchronized, reentrantlock, lock, aqs, juc, lock-escalation]
languages: [java]
role: [sde, backend]
companies: [恩士讯, 北京用友]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# synchronized vs ReentrantLock 区别 (含锁升级与选型)

## 问题描述

说一下 synchronized 和 ReentrantLock 的区别？你知道 AQS 原理吗？synchronized 的锁升级过程？

## 解答

| 维度 | synchronized | ReentrantLock |
| --- | --- | --- |
| 性质 | JVM 关键字（`monitorenter`/`monitorexit`） | JDK 类（`java.util.concurrent.locks`） |
| 实现 | 对象头 MarkWord + Monitor，重量级走 ObjectMonitor（C++ ObjectWaiter/ObjectMonitor） | AQS（CLH 变体 + volatile state + FIFO 队列） |
| 公平性 | 非公平（不可配） | 可配 `fair`/`nonfair` |
| 中断 | 不可中断 | `lockInterruptibly()` 可响应中断 |
| 超时 | 不支持 | `tryLock(timeout)` |
| 条件变量 | 单条件（`wait`/`notify`） | 多 `Condition`（独立等待队列） |
| 释放 | 自动（出块/异常，JVM 保证 monitorexit） | 必须 `finally { unlock() }`，否则死锁 |
| 锁状态查询 | 不可查 | `isLocked()` / `getHoldCount()` / `getQueueLength()` |
| 锁升级 | 偏向→轻量→重量（JVM 自动） | 无升级，直接 AQS 队列 |
| 性能 | JDK6+ 优化后接近 ReentrantLock | 高竞争下略优 |

### synchronized 锁升级（高频追问，详见 [锁升级专篇](concurrency/synchronized-lock-escalation)）
- **无锁→偏向锁→轻量锁→重量锁**，记录在对象头 MarkWord。
- 偏向锁：单线程访问，CAS 设线程 ID，无同步开销。竞争出现 → 升级。
- 轻量锁：竞争但不剧烈，CAS 自旋（自适应自旋）。自旋失败 → 升级。
- 重量锁：走 ObjectMonitor，OS mutex，线程 park。
- JDK 15+ 偏向锁默认禁用（标记位不再用），因收益递减。

### AQS 原理（追问要点，详见 [AQS 专篇](concurrency/aqs-principle)）
- `volatile int state` + CLH 变体双向队列。
- 独占：`tryAcquire` CAS 改 state，失败入队 park，前驱唤醒重试。
- 共享：`tryAcquireShared`，state 表示许可（Semaphore/CountDownLatch）。
- Condition 是独立单向队列，`await` 释放锁入队，`signal` 转移到主队列。

### 选型
- 简单同步、不需可中断/超时/多条件 → **synchronized**（语法糖，自动释放，JVM 优化足）。
- 需公平/中断/超时/多条件/可观测/与 AQS 生态配合 → **ReentrantLock**。
- 高并发读多写少 → **ReentrantReadWriteLock** 或 **StampedLock**。

## 易错点
- ReentrantLock 忘 `finally unlock` → 异常路径死锁。
- 以为 synchronized 一定慢 → JDK6 锁升级后差距很小，简单场景反而更优。
- `wait()/notify()` 在 ReentrantLock 上调 → 必须用 `Condition.await()/signal()`，否则 `IllegalMonitorStateException`。
- ReentrantLock 设 `fair=true` 但 `tryLock()` 无参仍插队 → `tryLock()` 不看队列公平性。

## 延伸

## 延伸

- 关联题：[[concurrency/aqs-principle]]
- 关联题：[[concurrency/cas-mechanism]]
- 关联题：[[concurrency/synchronized-lock-escalation]]
- 关联题：[[concurrency/readwritelock-stampedlock]]
