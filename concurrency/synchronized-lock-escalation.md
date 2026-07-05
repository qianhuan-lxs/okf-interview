---
type: question
id: concurrency/synchronized-lock-escalation
title: synchronized 锁升级 (偏向/轻量/重量 + MarkWord)
category: concurrency
subcategory: concurrency
difficulty: hard
tags: [synchronized, lock-escalation, markword, jvm, concurrency]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-05-26
---

# synchronized 锁升级 (偏向/轻量/重量 + MarkWord)

## 问题描述

synchronized 的锁升级过程？MarkWord 怎么记录锁状态？为什么 JDK 15 默认禁用偏向锁？

## 解答

### 锁升级路径
```
无锁 → 偏向锁 → 轻量级锁 → 重量级锁
```
**不可降级**（理论上 GC safepoint 时可批量撤销重偏向，但运行期不降级）。升级记录在**对象头 MarkWord**。

### 对象头 MarkWord（64 位 JVM）
- 64 bit，不同锁状态占用不同字段：
  - **无锁**：25 bit hash + 31 bit 分代年龄 + 1 bit biased 标志 + 2 bit 锁标志位(01)。
  - **偏向锁**：54 bit 线程 ID + 2 bit epoch + 1 bit 年龄 + 1 bit biased(1) + 2 bit 锁标志(01)。
  - **轻量锁**：62 bit 指向栈中 Lock Record 的指针 + 2 bit 锁标志(00)。
  - **重量锁**：62 bit 指向 ObjectMonitor 的指针 + 2 bit 锁标志(10)。
- 锁标志位区分状态，biased 标志位区分无锁/偏向。

### 偏向锁（Biased Locking）
- **场景**：单线程反复进入同步块。
- **机制**：首次进入 CAS 把线程 ID 写入 MarkWord。之后同一线程进出只需对比 ID，无 CAS、无自旋。
- **撤销**：另一线程来竞争 → 等全局安全点（safepoint）→ 撤销偏向，升级轻量锁。
- **批量重偏向 / 批量撤销**：同一类对象撤销到阈值（默认 20 次重偏向、40 次撤销）会批量处理，避免逐个撤销开销。
- **JDK 15 默认禁用**（JEP 374）：现代多线程应用偏向锁收益递减（多核 + 并发普遍），撤销的 safepoint STW 开销反而拖累。`-XX:+UseBiasedLocking` 仍可开，但废弃中。

### 轻量级锁（Lightweight / Thin Lock）
- **场景**：多线程交替进入，竞争不剧烈、持有时间短。
- **机制**：
  1. 当前栈帧建 Lock Record，拷贝对象 MarkWord（displaced mark word）。
  2. CAS 把 MarkWord 改为指向 Lock Record 的指针。成功 → 持锁。
  3. 失败 → 自旋（**自适应自旋**，根据历史成功率动态调整次数）。
  4. 自旋仍失败 → 升级重量锁，MarkWord 改指向 ObjectMonitor。
- 释放：CAS 把 displaced mark word 写回。若有竞争（CAS 失败）→ 说明有自旋等待者 → 唤醒。

### 重量级锁（Heavyweight / Inflated Lock）
- **场景**：竞争剧烈、持有时间长。
- **机制**：MarkWord 指向 `ObjectMonitor`（C++）。未抢到的线程进入 `_EntryList`，OS mutex 阻塞（`pthread_mutex` / `futex`）。
- 进入 `_Owner` 持锁；`wait()` 进 `_WaitSet`；`notify` 移回 `_EntryList`。
- 开销：系统调用 + 上下文切换 + 内核态切换。

### 自适应自旋
- 自旋次数不固定：上次自旋成功 → 这次多自旋；上次失败 → 减少或跳过自旋。
- 避免"自旋到底空耗"和"完全不自旋多一次 park"两个极端。

## 易错点
- 以为锁能降级 → 不能（运行期只升不降）。
- 以为偏向锁默认开 → JDK 15+ 默认禁。
- 把"轻量锁"等同 CAS 无锁 → 它有自旋，竞争一剧烈就膨胀。
- 以为 MarkWord 改了 hash 就坏了 → 偏向锁会覆盖 hash，所以 `hashCode()` 调用会触发偏向撤销。

## 延伸

## 延伸

- 关联题：[[concurrency/synchronized-vs-reentrantlock]]
- 关联题：[[concurrency/aqs-principle]]
- 关联题：[[concurrency/cas-mechanism]]
