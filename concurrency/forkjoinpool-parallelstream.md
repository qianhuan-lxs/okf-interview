---
type: question
id: concurrency/forkjoinpool-parallelstream
title: ForkJoinPool 工作窃取 + parallelStream 坑
category: concurrency
subcategory: concurrency
difficulty: medium
tags: [forkjoinpool, work-stealing, parallelstream, juc, concurrency]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-05-26
---

# ForkJoinPool 工作窃取 + parallelStream 坑

## 问题描述

ForkJoinPool 的工作窃取是什么？parallelStream 默认用哪个池？有什么坑？

## 解答

### ForkJoinPool 核心：工作窃取 (Work-Stealing)
- 每个 worker 线程有自己的**双端队列 (deque)**。
- 自己的任务在 deque 一端 LIFO（后进先出，利用缓存局部性）。
- 别的线程来**窃取**时从另一端 FIFO（减少竞争）。
- 空闲 worker 从其他 worker 的 deque 尾部偷任务。
- 优点：负载均衡，少空闲；适合**分治任务**（递归拆分，子任务量不均）。

### 适用场景
- **CPU 密集 + 可分治**：归并排序、并行数组处理、矩阵运算、大任务拆子任务。
- **不适合 IO 密集 / 阻塞任务**：见下方坑。

### ForkJoinTask
- `RecursiveTask<V>`（有返回值）/ `RecursiveAction`（无返回值）。
- `fork()`：子任务丢到自己 deque。
- `join()`：等待子任务完成（阻塞当前 worker，期间可偷别的任务——`ManagedBlocker` 让池在阻塞时补偿扩容）。

### parallelStream 默认池
- `parallelStream()` 默认用 `ForkJoinPool.commonPool()`（JVM 全局共享）。
- 默认并行度 = CPU 核数 - 1。
- 所有未指定池的 parallelStream / CompletableFuture 默认都抢这同一个池。

### parallelStream 的坑（重点）
1. **阻塞任务拖垮全局**：stream 里做 IO/远程调用/`Thread.sleep` → 占住 commonPool 线程，**所有 parallelStream 和默认 CompletableFuture 都饿死**。
   - 解法：IO 任务别用 parallelStream，或自己 `submit` 到业务线程池。
2. **共享可变状态**：`forEach` 并行执行，操作共享变量非线程安全 → 用 `reduce`/`collect` 而非外部累加。
3. **顺序依赖**：`forEach` 顺序不定；`findFirst`/`limit` 在并行下语义微妙。
4. **小数据集**：并行拆分 + 调度开销 > 收益 → 反而更慢。
5. **任务量不均**：某子任务特别慢 → 整个 stream 等它（虽有 work-stealing 但仍可能拖尾）。

### 自定义 ForkJoinPool
- `submit(() -> stream.parallel().collect(...))` 把 parallelStream 提交到自己 ForkJoinPool → 隔离，不污染 commonPool。
- 注意：parallelStream 内部仍会找"当前线程所属的 ForkJoinPool"，所以在自己池里 submit 才能生效。

## 易错点
- parallelStream 里写共享变量 → 数据竞争。
- parallelStream 跑 IO → 拖垮 commonPool 全局。
- 小集合用并行 → 开销 > 收益。
- 以为 parallelStream 一定快 → 数据量小/任务轻时反而慢。

## 延伸

## 延伸

- 关联题：[[concurrency/completablefuture-async-orchestration]]
- 关联题：[[concurrency/thread-pool-principles]]
