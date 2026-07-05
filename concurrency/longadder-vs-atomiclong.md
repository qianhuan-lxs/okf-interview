---
type: question
id: concurrency/longadder-vs-atomiclong
title: LongAdder vs AtomicLong (分段累加 Cell)
category: concurrency
subcategory: concurrency
difficulty: medium
tags: [longadder, atomiclong, cas, juc, concurrency]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-05-26
---

# LongAdder vs AtomicLong (分段累加 Cell)

## 问题描述

LongAdder 比 AtomicLong 好在哪？原理是什么？什么时候用 AtomicLong？

## 解答

### AtomicLong
- 单 `volatile long value`，所有线程 CAS 同一个字段。
- 低竞争：性能足够。
- 高竞争：CAS 自旋空耗严重，热点集中在一个字段 → 吞吐崩。

### LongAdder（JDK 8）
- `base` + `Cell[]`（`@Contended` 避免伪共享）。
- `add(x)`：先尝试 CAS `base`；失败 → hash 到某个 `Cell` CAS 累加；Cell 也竞争则重 hash 到别的 Cell 或扩容 Cell 数组。
- `sum()`：`base + Σ Cell.value`，**非精确瞬时**（遍历期间 Cell 仍可能变）。
- `longValue()` ≈ `sum()`。
- 设计思想：**热点分散**——把一个热点字段拆成多 Cell，线程各自打到不同 Cell，竞争骤降。极像"分段计数" / `ConcurrentHashMap` 的分段思想 / `Striped64`。

### 性能对比
- 低并发：AtomicLong 略快（少一次 Cell 路由）。
- 高并发：LongAdder 吞吐数倍到几十倍于 AtomicLong（竞争越剧烈差距越大）。

### 选型
- **纯累加计数器**（计数器、统计、监控指标）→ **LongAdder**。
- **需要精确序列号 / 比较-交换 / 自增并返回值** → **AtomicLong**（`incrementAndGet` 返回精确值，LongAdder 没有等价）。
- **自定义累加函数** → `LongAccumulator`（LongAdder 泛化，可传 `LongBinaryOperator`）。

### LongAdder 的代价
- 内存：Cell 数组占更多内存（每 Cell `@Contended` 加 padding 进一步吃内存）。
- `sum()` 不精确：不适合当全局序号或需要精确快照的场景。
- 无 `compareAndSet`：不能做条件更新。

## 易错点
- 把 LongAdder 当全局唯一 ID 生成器 → `sum()` 不精确、并发下跳号。
- 以为 LongAdder 全场景更快 → 低并发 AtomicLong 略优。
- 用 `incrementAndGet` 风格逻辑选 LongAdder → 它没有这个 API。

## 延伸

## 延伸

- 关联题：[[concurrency/cas-mechanism]]
- 关联题：[[concurrency/concurrenthashmap-principle]]
- 关联题：[[concurrency/false-sharing-contended]]
