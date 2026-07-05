---
type: question
id: concurrency/aqs-principle
title: AQS 原理 (从直觉到源码)
category: concurrency
subcategory: concurrency
difficulty: hard
tags: [aqs, clh-queue, juc, condition, concurrency]
languages: [java]
role: [sde, backend]
companies: [北京用友]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-07-05
---

# AQS 原理 (从直觉到源码)

## 问题描述

AQS 是什么？为什么 JUC 的锁都基于它？独占和共享怎么实现？Condition 怎么工作？

## 一、先建直觉：AQS 在解决什么问题

想象银行大厅：你抢不到柜员（资源）就得**排队等**，柜员空了**叫下一个**。AQS 就是干这个的——它给"抢不到资源就排队、资源空了唤醒队首"提供了一个通用骨架。

没有 AQS 之前，每个锁自己写一套等待队列 + park/unpark 逻辑，重复且容易错。AQS 把这套排队逻辑抽成框架，子类只管"什么算抢到、什么算释放"。

> **一句话**：AQS = 一个 `state` 变量 + 一个等待队列 + park/unpark 调度。子类实现"怎么改 state 算成功"，AQS 管"失败了怎么排队、成功了怎么唤醒"。

## 二、核心三件套

### 1. `volatile int state`——资源的"状态"
- 一个 int，语义由子类定义：
  - `ReentrantLock`：0=没人拿，>0=拿了几个（重入次数）。
  - `Semaphore`：还剩几个许可。
  - `CountDownLatch`：还差几个计数。
  - `ReentrantReadWriteLock`：**高 16 位=读者数，低 16 位=写者重入数**（一个 int 装两个数）。
- `volatile` 保证多线程可见，修改用 CAS 保证原子。

### 2. 等待队列——CLH 变体双向链表
- 抢不到的线程被包成 `Node` 挂到队尾，线程自己 `park`（挂起）。
- 队首线程被唤醒后重新尝试抢。
- **为什么叫"CLH 变体"**：原版 CLH 是单向、自旋（不 park，死循环检查前驱）。AQS 改成**双向 + park/unpark**——能 park 省 CPU，双向是为了取消节点时能找到前驱。所以是"借鉴 CLH 思想的变体"，不是原版 CLH。

### 3. `Node.waitStatus`——节点状态
| 值 | 名 | 含义 |
| --- | --- | --- |
| 0 | 初始 | 刚入队 |
| -1 | SIGNAL | "我后面有人，我释放时要唤醒后继"——**最关键** |
| -2 | CONDITION | 在 Condition 等待队列里 |
| -3 | PROPAGATE | 共享模式传播唤醒 |
| 1 | CANCELLED | 取消了，可剔除 |

> 新手记住 SIGNAL 就够：**每个节点要把前驱设成 SIGNAL 才能 park**，意思是"前驱你走的时候记得叫我"。

## 三、独占模式获取流程（用 ReentrantLock 讲）

### 白话版
1. 我要锁 → 看 `state` 是 0 吗？是 0 就 CAS 抢（设成 1，记自己为 owner）。
2. 不是 0 但 owner 是我自己 → 重入，`state++`。
3. 都不是 → 我抢不到，**入队排队**，把自己 park 挂起。
4. 前面的人用完释放 → 把 `state` 改回 0 → 唤醒队首（我）→ 我醒来重试第 1 步。

### 源码版（`acquire` 主干）
```java
public final void acquire(int arg) {
    if (!tryAcquire(arg) &&                              // 子类实现：尝试抢
        acquireQueued(addWaiter(Node.EXCLUSIVE), arg))   // 抢失败：入队 + 自旋park
        selfInterrupt();                                  // 补中断标志
}
```
- `tryAcquire`：子类实现（ReentrantLock 的非公平版上来 CAS 抢 state）。
- `addWaiter`：把当前线程包成 Node，CAS 挂到队尾。
- `acquireQueued`：自旋——**只有前驱是 head 且 tryAcquire 成功**才出队当 head；否则把前驱 waitStatus 设成 SIGNAL，然后 `park`。
- `selfInterrupt`：park 期间若被中断，AQS 不立即响应，但补回中断标志（`Thread.currentThread().interrupt()`），让上层感知。

### 公平 vs 非公平（新手易混）
- **非公平**（默认）：`tryAcquire` 上来就 CAS 抢，**不管队列有没有人在等** → 新来的能"插队" → 吞吐高（少一次 park/unpark）。
- **公平**：`tryAcquire` 先 `hasQueuedPredecessors()` 查队列有没有前驱，有就去排队 → 严格 FIFO、不饿死队尾但慢。
- 为什么默认非公平？线程 park/unpark 一次开销大，让刚释放的线程或新来的直接抢，能减少切换。

## 四、释放流程

```java
public final boolean release(int arg) {
    if (tryRelease(arg)) {              // 子类：state-- 到 0
        Node h = head;
        if (h != null && h.waitStatus != 0)
            unparkSuccessor(h);          // 唤醒后继
        return true;
    }
    return false;
}
```
- `tryRelease`：`state--`，到 0 清 owner。
- `unparkSuccessor`：从**队尾向前**找第一个未 CANCELLED 的后继，`LockSupport.unpark` 它。（从尾向前是因为中间节点可能已取消，正向 next 链可能断。）

## 五、共享模式（Semaphore / CountDownLatch）

- `tryAcquireShared` 返回值：
  - `>0`：成功，且**继续唤醒后继**（还有许可，传播）。
  - `=0`：成功，但不再传播（许可刚好用完）。
  - `<0`：失败，入队。
- `CountDownLatch` 的 `tryAcquireShared` 返回 `state==0 ? 1 : -1`——**只有计数归零才放行所有等待者**。
- 共享模式有 PROPAGATE 状态：确保多个许可被连续获取，不会"唤醒一个就停"。

## 六、Condition（条件变量，重点追问）

### 直觉
synchronized 只有一个等待室（`wait/notify`）。ReentrantLock 可以有**多个独立等待室**（Condition）——比如"满了的等待室"和"空了的等待室"，生产者等"非满"、消费者等"非空"，互不干扰。

### 实现
- 每个 `Condition` 是 AQS 内的**独立单向链表**（firstWaiter/lastWaiter），与主队列分离。
- `await()`：
  1. **释放全部锁**（`fullyRelease`，否则别的线程进不来）。
  2. 把当前线程包成 CONDITION 节点挂到 Condition 队列。
  3. `park`。
  4. 被 `signal` 唤醒后，节点从 Condition 队列**转移到主队列**（状态改 SIGNAL），重新排队抢锁；抢到后恢复重入数。
- `signal()`：取 Condition 队首节点，CAS 转移到主队列。
- **坑**：`await` 必须在 `lock.lock()` 之后调（持有锁才能释放锁），否则 `IllegalMonitorStateException`。

## 七、面试高频追问速答

| 问题 | 答 |
| --- | --- |
| AQS 队列是普通 FIFO 吗？ | 是 FIFO，但带 waitStatus 的 CLH 变体，SIGNAL 决定该不该 park。 |
| 为什么用双向链表？ | 取消节点时要找前驱改 next；共享模式传播也要看前驱。 |
| 公平锁一定更好吗？ | 不，吞吐更低，只在需要防饿死时用。 |
| Condition 和 wait/notify 区别？ | Condition 支持多等待队列、可超时、可响应中断；必须在 lock 内用。 |
| AQS 为什么用 LockSupport 而不是 wait/notify？ | park/unpark 无需持锁、可先 unpark 后 park（不丢信号）、精准唤醒指定线程。 |

## 易错点
- `await()` 没 lock 就调 → `IllegalMonitorStateException`。
- 以为公平锁更快 → 严格 FIFO 牺牲吞吐。
- 以为 Condition 是同步队列一部分 → 它是独立队列，signal 时才转移到主队列。
- 以为队列是原版 CLH → 是 park 版变体，原版 CLH 是自旋不 park。

## 延伸

## 延伸

- 关联题：[[concurrency/synchronized-vs-reentrantlock]]
- 关联题：[[concurrency/cas-mechanism]]
- 关联题：[[concurrency/thread-pool-principles]]
- 关联题：[[concurrency/locksupport-park-unpark]]
- 关联题：[[concurrency/readwritelock-stampedlock]]
