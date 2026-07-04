---
type: question
id: concurrency/cas-mechanism
title: CAS 机制理解
category: concurrency
subcategory: concurrency
difficulty: medium
tags: [cas, compare-and-swap, atomic, aba]
languages: []
role: [ai-app, sde, backend]
companies: [有赞, 探迹, 北京用友]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# CAS 机制理解

## 问题描述
你对 CAS 怎么理解？

## 解答
**CAS (Compare-And-Swap)**：无锁原子操作。三参数 (内存位置 V, 期望值 A, 新值 B)，仅当 V==A 时把 V 改为 B，否则返回当前值。底层是 CPU 的 `cmpxchg` 指令（x86）/LL-SC（ARM），单条指令保证原子。

### 为什么需要 CAS
- synchronized 太重（系统调用、上下文切换）。
- 高并发下 CAS 无锁自旋，竞争不剧烈时性能更好。

### Java 中的 CAS
- `sun.misc.Unsafe.compareAndSwapXxx` / JDK 9+ `VarHandle`。
- 封装为 `AtomicInteger / AtomicReference / LongAdder`。
- AQS 的 state 修改、ConcurrentHashMap 的节点插入都用 CAS。

### ABA 问题
- 线程 1 读到 A，线程 2 把 A→B→A，线程 1 CAS 仍成功，但中间状态丢失。
- 解法：**版本号** —— `AtomicStampedReference` 加 stamp；或 `AtomicMarkableReference`。

### 自旋开销
- 高竞争下 CAS 自旋空耗 CPU。解法：
  - `LongAdder` 分段累加，hot 字段分散。
  - 自旋次数限制 / 退避。
  - 极高竞争下反而 synchronized 更优（排队而非空转）。

## 易错点
- 把 CAS 当万能 —— 高竞争场景退化为自旋空耗。

## 延伸

## 延伸

- 关联题：[[concurrency/aqs-principle]]
- 关联题：[[concurrency/synchronized-vs-reentrantlock]]
