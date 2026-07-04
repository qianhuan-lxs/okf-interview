---
type: question
id: concurrency/aqs-principle
title: AQS 原理
category: concurrency
subcategory: concurrency
difficulty: hard
tags: [aqs, clh-queue, juc, concurrency]
languages: []
role: [ai-app, sde, backend]
companies: [北京用友]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# AQS 原理

## 问题描述
AQS 原理知道吗？

## 解答
**AQS (AbstractQueuedSynchronizer)** 是 JUC 锁与同步器的基础框架。ReentrantLock / Semaphore / CountDownLatch / ReentrantReadWriteLock 都基于它。

### 核心结构
- `volatile int state`：同步状态，语义由子类定义（ReentrantLock 表示锁是否被持有/重入次数；Semaphore 表示剩余许可）。
- **CLH 变体双向队列**：获取失败的线程封装为 `Node` 入队、`LockSupport.park`。
- `Node` 有 CANCELLED/SIGNAL/CONDITION/PROPAGATE 等等待状态。

### 独占获取流程（以 ReentrantLock 非公平为例）
1. `tryAcquire`：CAS 把 state 从 0 改为 1，成功则设当前线程为 owner。
2. 若 state != 0 但 owner==当前线程 → state++（重入）。
3. 否则构造 Node 入队，`acquireQueued` 自旋：前驱是 head 且 `tryAcquire` 成功则出队；否则 `shouldParkAfterFailedAcquire` 把前驱设为 SIGNAL 后 park。
4. head 节点释放时 `unparkSuccessor` 唤醒后继。

### 公平 vs 非公平
- 非公平：`tryAcquire` 上来就 CAS 抢，允许插队（吞吐高）。
- 公平：先检查队列是否有前驱 `hasQueuedPredecessors`，有则排队。

### 共享模式
- `tryAcquireShared` 返回 >=0 表示成功；释放时 `doReleaseShared` 传播唤醒。

## 易错点
- 以为 AQS 队列是普通 FIFO 链表 —— 是带等待状态的 CLH 变体，SIGNAL 标志决定是否该 park。

## 延伸

## 延伸

- 关联题：[[concurrency/synchronized-vs-reentrantlock]]
- 关联题：[[concurrency/cas-mechanism]]
- 关联题：[[concurrency/thread-pool-principles]]
