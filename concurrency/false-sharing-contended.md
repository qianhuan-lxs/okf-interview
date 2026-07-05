---
type: question
id: concurrency/false-sharing-contended
title: 伪共享 false sharing 与 @Contended
category: concurrency
subcategory: concurrency
difficulty: medium
tags: [false-sharing, contended, cache-line, concurrency, performance]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-05-26
---

# 伪共享 false sharing 与 @Contended

## 问题描述

什么是伪共享？为什么它拖累并发性能？@Contended 怎么解决？LongAdder 为什么用它？

## 解答

### 缓存行 (Cache Line)
- CPU 缓存以 cache line 为单位加载/同步，通常 64 字节。
- 一次加载 64 字节即使你只读 1 个变量；写入会让该行其他变量在别的核心缓存中失效（MESI 协议）。

### 伪共享问题
- 两个不相关的 volatile 字段 A、B 恰好落在**同一 cache line**。
- 线程 1（核 1）写 A → 整行失效 → 线程 2（核 2）读 B 时 cache miss → 重新从主存加载。
- 反之亦然。结果：A、B 逻辑上无共享，却因同 cache line 互相 invalidate，**性能比单线程还差**。
- 经典案例：两个线程分别自增相邻的 `volatile long` 字段，比相隔远的字段慢几倍到几十倍。

### 解决：缓存行填充 (Padding)
- 在字段前后加填充变量，让目标字段独占一个 cache line。
- 手动填充（JDK 7 前）：
  ```java
  class Padded {
      public volatile long p1,p2,p3,p4,p5,p6,p7;  // 56 字节填充
      public volatile long value;                  // 独占行
      public volatile long q1,q2,q3,q4,q5,q6,q7;
  }
  ```
- **`@Contended`（JDK 8+）**：注解自动填充，需 `-XX:-RestrictContended`（默认生产关闭，JDK 内部用）。
  ```java
  @jdk.internal.vm.annotation.Contended
  volatile long value;
  ```

### LongAdder 的 Cell 用 @Contended
- `Cell` 类的 value 字段标 `@Contended`，保证不同 Cell 落在不同 cache line。
- 否则多线程打不同 Cell 仍同 cache line → 退化成伪共享，CAS 互相 invalidate，热点分散失效。
- 这就是 LongAdder 高并发性能的关键之一（另一个是热点分散本身）。

### 何时关心
- 极高并发写同一对象的相邻字段、无锁数据结构（Disruptor 也大量用 padding）。
- 普通业务代码不必过度优化——伪共享是热点路径的微优化。

### 检测
- `perf c2c`（Linux）看 cache line contention。
- `JMH` 基准对比带 padding vs 不带，差距大说明有伪共享。

## 易错点
- 以为字段独立就无共享 → 同 cache line 仍互相干扰。
- `@Contended` 不加 `-XX:-RestrictContended` → 应用代码里不生效。
- 手动 padding 用 long 而非对象引用 → 注意对象头也占字节（64 位 JVM 普通对象头 12 字节，压缩后 8）。

## 延伸

## 延伸

- 关联题：[[concurrency/longadder-vs-atomiclong]]
- 关联题：[[concurrency/cas-mechanism]]
- 关联题：[[concurrency/concurrenthashmap-principle]]
