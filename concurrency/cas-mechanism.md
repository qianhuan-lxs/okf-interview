---
type: question
id: concurrency/cas-mechanism
title: CAS 机制 (cmpxchg + lock 前缀 / Unsafe / ABA / LongAdder)
category: concurrency
subcategory: concurrency
difficulty: hard
tags: [cas, compare-and-swap, atomic, aba, unsafe, varhandle]
languages: [java]
role: [sde, backend]
companies: [有赞, 探迹, 北京用友]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# CAS 机制 (cmpxchg + lock 前缀 / Unsafe / ABA / LongAdder)

## 问题描述

你对 CAS 怎么理解？底层怎么保证原子性？ABA 问题真实危害？高竞争下怎么办？

## 解答

**CAS (Compare-And-Swap)**：无锁原子操作。三参数 `(V, A, B)`——仅当 `V==A` 时把 `V` 改为 `B`，否则返回当前值。是乐观锁、无锁数据结构的基石。

### 底层原子性保证（重点）
- **x86**：`lock cmpxchg` 指令。`cmpxchg` 本身非原子的（读-比较-写三步），但加 **`lock` 前缀** → 锁总线或锁缓存行（MESI 协议 + cache line lock），保证整条指令原子。
- **ARM/PowerPC**：LL-SC（Load-Linked / Store-Conditional）循环，硬件层面"乐观"——若期间缓存行被改则 SC 失败，重试。
- **Java 层**：`sun.misc.Unsafe.compareAndSwapXxx`（JDK 9 前）/ `VarHandle.compareAndSet`（JDK 9+，标准 API）。最终走 native → CPU 指令。
- `AtomicInteger.compareAndSet` → `Unsafe.compareAndSwapInt` → JNI → `cmpxchg`。

### 为什么需要 CAS
- `synchronized` 太重（系统调用、上下文切换、OS mutex）。
- 高并发低竞争场景，CAS 自旋无锁、无线程切换，性能远优于阻塞锁。

### Java 中的 CAS
- `AtomicInteger / AtomicLong / AtomicReference / AtomicStampedReference`。
- AQS 的 `state` 修改、`ConcurrentHashMap` 节点插入、`LongAdder` 的 Cell 累加都用 CAS。
- `VarHandle`（JDK 9+）是标准替代 Unsafe 的 API，支持字段内存序（`OPAQUE`/`VOLATILE`/`ACQUIRE`/`RELEASE`）。

### ABA 问题（真实危害场景）
- 线程 1 读到 A，线程 2 把 A→B→A，线程 1 CAS 仍成功——值"看起来"没变，但中间状态已变化。
- **危害场景**：无锁栈。线程 1 准备 CAS 顶 `A`→下一个 `B`，被抢占；线程 2 pop A、pop B、push A（A 的 next 已变）。线程 1 恢复 CAS 成功，但此时栈顶 A 的 next 已是 null 或悬空 → 栈结构破坏。
- **解法**：
  - `AtomicStampedReference`：加 int stamp 版本号，CAS 必须匹配 `(expectedRef, expectedStamp)`。
  - `AtomicMarkableReference`：boolean 标记（更轻，仅二态）。
  - GC 隐式缓解：对象引用版本变化伴随新对象分配，但**不解决同一对象被复用**的情况。

### 自旋开销与高竞争解法
- 高竞争下 CAS 自旋空耗 CPU，吞吐反而比 synchronized 差。
- **`LongAdder`**：分段累加。`base` + `Cell[]`，线程 hash 到不同 Cell 各自 CAS，`sum()` 时求和。极高并发下热点分散，吞吐数倍于 `AtomicLong`。代价：`sum()` 非精确瞬时值（遍历期间可能变化）。
- **`LongAccumulator`**：LongAdder 泛化版，可传自定义累加函数。
- **自旋退避**：限制重试次数 / `Thread.onSpinWait()`（JDK 9+，提示 CPU 自旋等待，x86 发 `PAUSE` 降功耗防乱序）。
- **极高竞争下反而 `synchronized`/ReentrantLock 更优**——排队阻塞而非空转，JVM 锁升级到重量锁走 park。

### CAS 与 volatile 的关系
- `AtomicInteger.value` 是 volatile，保证读的可见性；CAS 保证写原子。两者结合才完整。

## 易错点
- 把 CAS 当万能 → 高竞争退化为自旋空耗。
- 以为 ABA 只是理论 → 无锁链表/栈场景会真实破坏结构。
- 以为 `AtomicReference` 能防 ABA → 不能，要用 `AtomicStampedReference`。
- `LongAdder.sum()` 当精确快照 → 它是估算求和，期间 Cell 仍在变。

## 延伸

## 延伸

- 关联题：[[concurrency/aqs-principle]]
- 关联题：[[concurrency/synchronized-vs-reentrantlock]]
- 关联题：[[concurrency/longadder-vs-atomiclong]]
- 关联题：[[concurrency/volatile-principle]]
