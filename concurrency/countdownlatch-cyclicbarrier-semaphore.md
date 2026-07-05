---
type: question
id: concurrency/countdownlatch-cyclicbarrier-semaphore
title: CountDownLatch / CyclicBarrier / Semaphore 区别
category: concurrency
subcategory: concurrency
difficulty: medium
tags: [countdownlatch, cyclicbarrier, semaphore, juc, concurrency]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-05-26
---

# CountDownLatch / CyclicBarrier / Semaphore 区别

## 问题描述

CountDownLatch、CyclicBarrier、Semaphore 三个同步器区别？各自适用场景？

## 解答

| 维度 | CountDownLatch | CyclicBarrier | Semaphore |
| --- | --- | --- | --- |
| 基于 | AQS 共享 | AQS 共享 + ReentrantLock Condition | AQS 共享 |
| 计数 | 不可重置（一次性） | 可重置（cyclic） | 许可数，可增减 |
| 动作 | 一个线程等多 N 个完成 | N 个线程互相等到达屏障点 | 控制并发访问数 |
| 释放 | 计数归零自动放行 | 全到后全部放行 + 可执行 barrier action | acquire 拿许可，release 还 |
| 不可重用 | ✅ 一次性 | ❌ 可循环 | — |

### CountDownLatch
- `countDown()` 每次使 state -1；`await()` 阻塞到 state==0。
- **不可重置**——countDown 完就废。要循环用得新建。
- 场景：主线程等 N 个子任务完成（如多服务并行加载后汇总）；启动时等多个依赖就绪。
- 基于 AQS 共享：`tryAcquireShared` 返回 `state==0 ? 1 : -1`。

### CyclicBarrier
- `await()` 到达屏障点阻塞，等 parties 个线程都到 → 全部释放；**自动重置**计数，可再次 await（cyclic）。
- 可指定 `barrierAction`：所有线程到齐后、释放前执行一个动作（最后一个到的线程执行）。
- `BrokenBarrierException`：任一等待线程被中断或超时 → 屏障 broken，所有等待者抛异常。
- 场景：多线程分阶段计算，每阶段全员到齐再进下一阶段（如多阶段批处理、并行算法的同步步）。
- 实现是 `ReentrantLock` + `Condition` + `Generation`（每次重置换 generation）。

### Semaphore
- `acquire()` 拿许可（state -1），不够则阻塞；`release()` 还许可（state +1）。
- **可公平可非公平**（`new Semaphore(permits, fair)`）。
- 场景：限流（接口并发数上限）、资源池（连接池大小）、限制并发访问。
- 注意：`release()` 可以不配对 acquire（释放多于获取）→ 实际增加许可数，慎用。

### 选型
- 等 N 个完成 → CountDownLatch。
- N 个互等到齐再继续 → CyclicBarrier。
- 限并发数 → Semaphore。

## 易错点
- 想循环等待却用 CountDownLatch → 不可重置，得重建。
- Semaphore release 多于 acquire → 许可数越界增多。
- CyclicBarrier 一个线程被中断 → 整个屏障 broken，全抛异常。

## 延伸

## 延伸

- 关联题：[[concurrency/aqs-principle]]
- 关联题：[[concurrency/completablefuture-async-orchestration]]
- 关联题：[[concurrency/thread-pool-principles]]
