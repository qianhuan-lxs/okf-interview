---
type: question
id: concurrency/locksupport-park-unpark
title: LockSupport.park / unpark 原理 (vs wait/notify)
category: concurrency
subcategory: concurrency
difficulty: medium
tags: [locksupport, park, unpark, concurrency, juc]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-05-26
---

# LockSupport.park / unpark 原理 (vs wait/notify)

## 问题描述

LockSupport.park/unpark 的原理？和 wait/notify 有什么区别？为什么 AQS 用它而不是 wait/notify？

## 解答

### LockSupport.park / unpark
- `park()`：阻塞当前线程，许可不可用则进入 WAITING/TIMED_WAITING。
- `unpark(Thread t)`：给线程 t 一个许可（permit），使其从 `park()` 返回。
- **许可最多一个**（不会累加）：连续 `unpark` 多次也只是 1 个许可，下一次 `park` 直接返回不阻塞。

### 关键区别：unpark 可先于 park
- **wait/notify**：`notify` 必须在 `wait` 之后调用——先 notify 后 wait 会丢信号（线程永远等）。
- **park/unpark**：`unpark` 可以在 `park` 之前调用——先 unpark 给了许可，之后 `park` 直接返回不阻塞。
- 这让 AQS 等无锁等待的实现更安全（不会因先唤醒后等待丢信号）。

### 实现（底层）
- 每个 Thread 有一个 `parkBlocker` 字段和许可（用 `Parker` 实现，C++ 层基于 `pthread_mutex` + `pthread_cond` 或 futex）。
- `park` 检查许可：有则消耗并返回，无则阻塞。
- `unpark` 设置许可（若线程在阻塞则唤醒）。
- 中断也会使 `park` 返回（需检查 `Thread.interrupted()`）。

### 对比表
| 维度 | wait/notify | park/unpark |
| --- | --- | --- |
| 所属 | Object 方法 | LockSupport 静态方法 |
| 前置条件 | 必须持有对象 monitor（synchronized 块内） | 无需任何锁 |
| 唤醒顺序 | notify 必须在 wait 后 | unpark 可在 park 前 |
| 许可累加 | 一次 notify 唤醒一个/全部 | 许可最多 1，不累加 |
| 阻塞对象 | 对象的 wait set | 线程本身 |
| 精准唤醒 | ❌（随机一个或全部） | ✅（指定线程） |

### AQS 为什么用 LockSupport
- AQS 的 Node 队列不依赖对象 monitor，park/unpark 无需持锁即可唤醒后继节点。
- `unparkSuccessor` 精准 `unpark` 后继线程，不唤醒无关线程。
- 避免 wait/notify 必须在 synchronized 块内的耦合（AQS 用 CAS + volatile 管队列，不用对象锁）。

### blocker 用法
- `park(blocker)` 传入对象，记录到 `parkBlocker` 字段，jstack 能看到"为什么阻塞"，便于诊断：
  `LockSupport.park(this)`。

## 易错点
- 连续 unpark 当多次许可 → 只 1 个，下次 park 仍阻塞。
- park 被中断后不检查 `interrupted()` → 中断信号丢失（AQS 在 `parkAndCheckInterrupt` 里检查并 selfInterrupt 补回）。
- 用 wait/notify 思路先 notify 后 wait → 永久阻塞。

## 延伸

## 延伸

- 关联题：[[concurrency/aqs-principle]]
- 关联题：[[concurrency/synchronized-vs-reentrantlock]]
