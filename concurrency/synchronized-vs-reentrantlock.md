---
type: question
id: concurrency/synchronized-vs-reentrantlock
title: synchronized vs ReentrantLock 区别
category: concurrency
subcategory: concurrency
difficulty: medium
tags: [synchronized, reentrantlock, lock, aqs, juc]
languages: []
role: [ai-app, sde, backend]
companies: [恩士讯, 北京用友]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# synchronized vs ReentrantLock 区别

## 问题描述

说一下 synchronized 和 ReentrantLock 的区别？你知道 AQS 原理吗？

## 解答

| 维度 | synchronized | ReentrantLock |
| --- | --- | --- |
| 性质 | JVM 关键字（monitorenter/monitorexit） | JDK 类（java.util.concurrent.locks） |
| 实现 | 对象头 MarkWord + Monitor，重量级走 ObjectMonitor | AQS（CLH 变体 + state + FIFO 队列） |
| 公平性 | 非公平（不可配） | 可配 fair/non-fair |
| 中断 | 不可中断 | `lockInterruptibly()` 可响应中断 |
| 超时 | 不支持 | `tryLock(timeout)` |
| 条件变量 | 单条件（wait/notify） | 多 Condition |
| 释放 | 自动（出块/异常） | 必须 `finally { unlock() }`，否则死锁 |
| 锁状态 | 不可查询 | `isLocked() / getHoldCount()` |
| 性能 | JDK6+ 优化（偏向→轻量→重量）后接近 | 高竞争下略优 |

### 选型
- 简单同步、不需可中断/超时 → synchronized（语法糖，自动释放）
- 需公平/中断/超时/多条件/可观测 → ReentrantLock

### AQS 原理（追问）
- 核心是一个 `volatile int state` + 双向 FIFO 等待队列（CLH 变体）。
- 独占模式：`tryAcquire` CAS 改 state，失败则构造 Node 入队、park；前驱唤醒后 `tryAcquire` 重试。
- 共享模式：`tryAcquireShared`，state 表示许可数（Semaphore/CountDownLatch）。
- Condition 是独立等待队列，`await` 释放锁并入 cond 队列，`signal` 转移到主队列。

## 易错点
- ReentrantLock 忘 `finally unlock` —— 异常路径死锁。
- 以为 synchronized 一定慢 —— JDK6 之后锁升级优化下差距很小。

## 延伸

## 延伸

- 关联题：[[concurrency/aqs-principle]]
- 关联题：[[concurrency/cas-mechanism]]
- 关联题：[[concurrency/optimistic-vs-pessimistic-lock]]
