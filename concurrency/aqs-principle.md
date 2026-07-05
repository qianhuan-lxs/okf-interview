---
type: question
id: concurrency/aqs-principle
title: AQS 原理 (CLH 变体 / state / Condition / 独占共享)
category: concurrency
subcategory: concurrency
difficulty: hard
tags: [aqs, clh-queue, juc, condition, concurrency]
languages: [java]
role: [sde, backend]
companies: [北京用友]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# AQS 原理 (CLH 变体 / state / Condition / 独占共享)

## 问题描述

AQS 原理知道吗？为什么它是 JUC 锁的基础框架？独占和共享怎么实现？Condition 是怎么工作的？

## 解答

**AQS (AbstractQueuedSynchronizer)** 是 JUC 锁与同步器的基础框架。`ReentrantLock / Semaphore / CountDownLatch / ReentrantReadWriteLock / CyclicBarrier` 底层都基于它。核心思想：**模板方法模式**——AQS 管队列与 park/unpark，子类只实现 `tryAcquire/tryRelease/tryAcquireShared/tryReleaseShared`。

### 核心结构
- `volatile int state`：同步状态，语义由子类定义。
  - `ReentrantLock`：0=未持有；>0=重入次数（owner 线程独占）。
  - `Semaphore`：剩余许可数。
  - `CountDownLatch`：剩余计数。
  - `ReentrantReadWriteLock`：高 16 位=共享读数，低 16 位=独占写重入数。
- **CLH 变体双向队列**：head / tail 指向哨兵 `Node`。注意 **AQS 的队列不是原版 CLH**——原版 CLH 是单向、自旋、无 park；AQS 改成**双向 + park/unpark + 检查前驱状态**，因此叫 "CLH variant"。
- `Node` 字段：`waitStatus`（CANCELLED=1 / SIGNAL=-1 / CONDITION=-2 / PROPAGATE=-3 / 0 初始）、`prev`、`next`、`thread`、`nextWaiter`（Condition 队列用单向链）。

### 独占获取流程（ReentrantLock 非公平 `nonfairTryAcquire`）
1. `state==0` → CAS 改 1，设 owner=当前线程，返回 true。
2. `owner==当前线程` → `state++`（重入），返回 true。
3. 否则返回 false，进入 `acquireQueued`：
   - `addWaiter(Node.EXCLUSIVE)`：CAS 入队尾，初始化时若 head 为空先 CAS 建哨兵。
   - 自旋 `acquireQueued`：**只有前驱是 head 且 `tryAcquire` 成功**才出队（setHead）；否则 `shouldParkAfterFailedAcquire` 把前驱 waitStatus 设为 SIGNAL，再 `parkAndCheckInterrupt`。
   - 被唤醒后继续自旋尝试。若 park 期间被中断，记录 interrupted，**最后 `selfInterrupt()` 补上中断标志**（AQS 不响应中断但保留标志）。

### 释放（独占）
- `tryRelease`：`state--`，到 0 则清 owner、返回 true。
- `unparkSuccessor`：把 head.waitStatus 清 0，从尾向前找第一个未 CANCELLED 的后继，`LockSupport.unpark`。

### 公平 vs 非公平
- **非公平** `nonfairTryAcquire`：上来就 CAS 抢，允许插队 → 吞吐高（默认）。
- **公平** `fairTryAcquire`：先 `hasQueuedPredecessors()` 检查队列有无前驱，有则排队 → 严格 FIFO、防饿死但慢。
- **为什么默认非公平**：线程切换成本高，非公平让刚释放锁的线程或新来的线程直接抢，减少 park/unpark 开销；代价是队尾线程可能延迟。

### 共享模式（Semaphore / CountDownLatch）
- `tryAcquireShared` 返回 `>=0` 表示成功且可传播；`<0` 表示失败需排队。
- 释放 `doReleaseShared`：**PROPAGATE 机制**——唤醒后继后，若 head 状态变化继续传播，确保多个共享许可被连续获取。
- `CountDownLatch` 的 `tryAcquireShared` 返回 `state==0 ? 1 : -1`——只有计数归零才放行所有等待者。

### ConditionObject（条件变量，重点）
- 每个 `Condition` 是 AQS 内的**独立单向等待队列**（firstWaiter/lastWaiter），与主同步队列分离。
- `await()`：**先释放全部锁（fullyRelease）**→ 把当前线程封装成 CONDITION 节点入 Condition 队列 → `park`。被 `signal` 唤醒后，节点从 Condition 队列**转移到主队列**（`transferForSignal`，状态改 SIGNAL），重新参与抢锁；抢到后恢复原重入数。
- `signal()`：移 firstWaiter，CAS 状态转主队列。
- 这就是 ReentrantLock 能有**多个 Condition** 的原理：一个锁多个等待队列，而 synchronized 的 wait/notify 只有一个。
- **坑**：`await` 必须先 `lock.lock()` 拿到锁（在 lock 块内调），否则 `IllegalMonitorStateException`。

### AQS 不保证可见性的细节
- `state` 是 volatile，子类修改 state 用 CAS 或 volatile 写；节点入队用 CAS tail；这些保证队列操作的可见性与有序性。

## 易错点
- 以为 AQS 队列是普通 FIFO 链表——是带 waitStatus 的 CLH 变体，SIGNAL 决定是否该 park。
- `await()` 没 lock 就调 → `IllegalMonitorStateException`。
- 以为公平锁一定更好——吞吐更低，只在需要防饿死时用。
- 以为 Condition 是同步队列的一部分——它是独立单向队列，signal 时才转移到主队列。

## 延伸

## 延伸

- 关联题：[[concurrency/synchronized-vs-reentrantlock]]
- 关联题：[[concurrency/cas-mechanism]]
- 关联题：[[concurrency/thread-pool-principles]]
- 关联题：[[concurrency/locksupport-park-unpark]]
- 关联题：[[concurrency/readwritelock-stampedlock]]
