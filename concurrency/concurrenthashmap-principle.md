---
type: question
id: concurrency/concurrenthashmap-principle
title: ConcurrentHashMap 原理 (1.7 vs 1.8 / sizeCtl / 转移节点)
category: concurrency
subcategory: concurrency
difficulty: hard
tags: [concurrenthashmap, juc, cas, synchronized, concurrency]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-05-26
---

# ConcurrentHashMap 原理 (1.7 vs 1.8 / sizeCtl / 转移节点)

## 问题描述

ConcurrentHashMap 1.7 和 1.8 实现区别？为什么 1.8 改用 CAS + synchronized？扩容怎么做？sizeCtl 是什么？

## 解答

### JDK 1.7：Segment 分段锁
- 结构：`Segment[]`（默认 16 段，继承 ReentrantLock）+ 每段内 `HashEntry[]` 链表。
- 并发度 = Segment 数（16，创建后不可扩）。
- 写：锁单个 Segment（`lock()`），其他 Segment 不阻塞。
- 读：volatile 读 `HashEntry.value`，**不加锁**（首节点 volatile）。
- 扩容：段内独立扩容。
- 缺点：并发度固定、Segment 重、内存占用大。

### JDK 1.8：CAS + synchronized + 链表/红黑树
- 结构：`Node[] table`（无 Segment），槽位是链表或红黑树（链表 ≥8 且容量 ≥64 转树；扩容或元素减少回退链表）。
- 写（`put`）：
  1. 空槽位 → **CAS 插入首节点**（无锁）。
  2. 非空槽位 → **`synchronized` 锁住首节点**，链表尾插或红黑树插入。
  3. 检查扩容。
- 读（`get`）：volatile 读 table 槽位首节点，沿链/树找，**不加锁**。
- 并发度 = 桶数（默认 16，随扩容增大），远高于 1.7。

### 为什么 1.8 弃 Segment
- synchronized 在 JDK 6+ 锁升级后性能不输 ReentrantLock，且内存更省（无 AQS 队列开销）。
- 桶粒度锁比段粒度锁并发度更高。
- CAS 处理空槽，synchronized 处理非空槽，分工最优。

### sizeCtl（核心控制变量）
- `volatile int sizeCtl`：
  - `-1` → 正在初始化。
  - `-(1 + N)` → 有 N 个线程正在扩容（`-N`，N 个 resize 线程）。
  - 正数 → 下次扩容的阈值（初始 = 容量 × 0.75）。
- 初始化：CAS 把 sizeCtl 从 0/正数改 -1，独占初始化，完后设回阈值。
- 扩容：触发时 CAS 调整 sizeCtl 协调多线程并发扩容。

### 多线程并发扩容（亮点）
- 1.8 CHM 扩容**多线程协助**：每个线程领取一段 stride（默认最小 16 桶），从后往前迁移。
- 迁移完一个桶，在旧表该槽放 **`ForwardingNode`（hash=MOVED=-1）**：`get` 遇到它转去新表查；`put` 遇到它 → 协助扩容。
- `transfer` 协调：线程领完 stride 或发现全部领完就退出；最后一个线程收尾建新表。
- 迁移时拆分链表：原链按 `hash & oldCap` 拆成两条（低位链留原 index，高位链去 index+oldCap），无需重 hash。

### 计数 size()
- `baseCount` + `CounterCell[]`（类似 LongAdder 分段计数），高并发分散热点。
- `size()` = baseCount + Σ CounterCell，**非精确瞬时值**。

## 易错点
- 以为 1.8 完全无锁 → 非空桶用 synchronized。
- 以为 size 精确 → 是估算，并发下可能偏。
- put 返回 null 当成功 → 也可能是该 key 原值为 null，要看 `containsKey`。
- 1.7 的并发度 16 是写并发度，不是读。

## 延伸

## 延伸

- 关联题：[[concurrency/cas-mechanism]]
- 关联题：[[concurrency/synchronized-vs-reentrantlock]]
- 关联题：[[concurrency/longadder-vs-atomiclong]]
- 关联题：[[concurrency/aqs-principle]]
