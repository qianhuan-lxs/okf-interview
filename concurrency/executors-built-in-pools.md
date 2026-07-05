---
type: question
id: concurrency/executors-built-in-pools
title: Executors 内置线程池设计 (Fixed/Cached/Single/Scheduled/WorkStealing)
category: concurrency
subcategory: concurrency
difficulty: hard
tags: [executors, thread-pool, fixed, cached, scheduled, workstealing, juc]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-07-05
---

# Executors 内置线程池设计 (Fixed/Cached/Single/Scheduled/WorkStealing)

## 问题描述

`Executors` 提供哪些内置线程池？各自的设计意图、参数、源码实现、坑？为什么不推荐用？

## 解答

`Executors` 是线程池工厂类，提供 5 种内置池。**阿里规约禁止用**（OOM 风险），但面试必考——既要懂设计意图，也要懂为什么坑。

## 一、`newFixedThreadPool(n)`

```java
public static ExecutorService newFixedThreadPool(int nThreads) {
    return new ThreadPoolExecutor(nThreads, nThreads,
                                  0L, TimeUnit.MILLISECONDS,
                                  new LinkedBlockingQueue<Runnable>());
}
```
- **core == max == n**，无超时，**`LinkedBlockingQueue` 默认无界**（`Integer.MAX_VALUE`）。
- 设计意图：固定 n 个线程常驻，任务排队。
- **流程**：核心线程满 → 任务全入无界队列 → 永不创建非核心线程 → 永不拒绝。
- **坑**：队列无界 → 任务堆积 → **OOM**（任务对象 + 队列节点）。这是阿里禁用的主因。
- 适用：已知任务量可控、且确实要固定并发度的场景；生产建议手动 `new ThreadPoolExecutor` + 有界队列。

## 二、`newCachedThreadPool()`

```java
public static ExecutorService newCachedThreadPool() {
    return new ThreadPoolExecutor(0, Integer.MAX_VALUE,
                                  60L, TimeUnit.SECONDS,
                                  new SynchronousQueue<Runnable>());
}
```
- **core=0, max=Integer.MAX_VALUE**，60s 超时，**`SynchronousQueue`**（无容量，直接 hand-off）。
- 设计意图：短任务高吞吐，来任务就建线程跑，空闲 60s 回收。
- **流程**：`SynchronousQueue.offer` 必须有线程正在 `take` 才成功——没有就建新线程跑（不进队列）。线程空闲 60s 被回收。
- **坑**：max 无界 → 突发流量下建海量线程 → **OOM**（线程栈开销，每线程约 1MB）。
- 适用：短促、轻量、突发任务；不适合长任务或 IO 阻塞任务（线程数爆炸）。

## 三、`newSingleThreadExecutor()`

```java
public static ExecutorService newSingleThreadExecutor() {
    return new ThreadPoolExecutor(1, 1,
                                  0L, TimeUnit.MILLISECONDS,
                                  new LinkedBlockingQueue<Runnable>());
}
```
- **core == max == 1**，无界队列。
- 设计意图：单线程串行执行，保证任务按顺序（FIFO）。
- `newSingleThreadExecutor` 返回的是 `FinalizableDelegatedExecutorService`（包装类），**禁止强转 `ThreadPoolExecutor` 改参数**——和直接 `new ThreadPoolExecutor(1,1,...)` 的区别在此。
- **坑**：同样无界队列 OOM；单线程一旦异常死亡会新建一个继续（所以任务不会因异常停滞，但异常被吞）。
- 适用：需要严格串行的场景（如日志顺序写入、事件顺序处理）。

## 四、`newScheduledThreadPool(n)` / `newSingleThreadScheduledExecutor()`

```java
public static ScheduledExecutorService newScheduledThreadPool(int corePoolSize) {
    return new ScheduledThreadPoolExecutor(corePoolSize);
}
```
- 实现：`ScheduledThreadPoolExecutor extends ThreadPoolExecutor`，用 **`DelayedWorkQueue`**（基于堆的延迟队列，按到期时间排序）。
- **core 可配，max = Integer.MAX_VALUE**，队列 `DelayedWorkQueue` 无界。
- API：
  - `schedule(task, delay, unit)`：延迟执行一次。
  - `scheduleAtFixedRate(task, initDelay, period, unit)`：固定频率（不管上次跑多久，每 period 一次；若任务执行 > period 则按执行时间连续跑）。
  - `scheduleWithFixedDelay(task, initDelay, delay, unit)`：固定延迟（上次结束后再过 delay 才下一次）。
- **坑**：
  - 队列无界 → OOM。
  - **任务异常会导致后续不再调度**（任务抛异常后线程被替换，但该周期任务不再被调度）→ 必须在任务内部 try-catch。
  - `scheduleAtFixedRate` 不保证并发，单线程池里任务超时会被串行连续执行。

## 五、`newWorkStealingPool(n)` (JDK 8)

```java
public static ExecutorService newWorkStealingPool(int parallelism) {
    return new ForkJoinPool(parallelism,
                            ForkJoinPool.defaultForkJoinWorkerThreadFactory,
                            null, true);
}
```
- 实现：`ForkJoinPool`，**工作窃取**——每个 worker 有自己的 deque，空闲时从别的 worker 队尾偷任务。
- 默认 `parallelism = Runtime.getRuntime().availableProcessors()`（CPU 核数）。
- 设计意图：CPU 密集 + 可分治任务，负载均衡。
- **坑**：
  - 不适合 IO 密集/阻塞任务（占住 worker，窃取也救不了）。
  - 任务依赖关系复杂时可能死锁（如一个任务 join 等另一个，但另一个排在被占的 worker 上）。
  - 默认 `asyncMode=false`（LIFO），适合分治；`asyncMode=true` 才适合 FIFO 事件流。

## 六、对比总表

| 池 | core | max | 队列 | 超时 | 风险 | 适用 |
| --- | --- | --- | --- | --- | --- | --- |
| Fixed | n | n | LinkedBlockingQueue(无界) | 无 | 队列 OOM | 固定并发、任务量可控 |
| Cached | 0 | MAX | SynchronousQueue | 60s | 线程 OOM | 短促突发任务 |
| Single | 1 | 1 | LinkedBlockingQueue(无界) | 无 | 队列 OOM | 严格串行 |
| Scheduled | n | MAX | DelayedWorkQueue(无界) | 可配 | 队列 OOM + 异常停调度 | 延迟/周期 |
| WorkStealing | n | n | 各 worker deque | — | IO 阻塞/依赖死锁 | CPU 分治 |

## 七、为什么不推荐用 Executors（阿里规约）

1. **Fixed/Single**：`LinkedBlockingQueue` 默认无界 → 任务堆积 OOM。
2. **Cached**：max 无界 → 线程数爆炸 OOM（线程栈开销）。
3. **Scheduled**：`DelayedWorkQueue` 无界 + 异常停调度。
4. 错误掩盖：工厂方法屏蔽了参数细节，使用者不感知队列/拒绝策略。

**正确做法**：手动 `new ThreadPoolExecutor`：
```java
new ThreadPoolExecutor(
    corePoolSize, maximumPoolSize, keepAliveTime, unit,
    new ArrayBlockingQueue<>(capacity),     // 有界队列
    new ThreadFactoryBuilder().setNameFormat("biz-%d").build(),  // 命名线程
    new ThreadPoolExecutor.CallerRunsPolicy());  // 明确拒绝策略
```

## 八、面试高频追问

| 问题 | 答 |
| --- | --- |
| Fixed 为什么 max 不生效？ | 队列无界，永远不满，走不到创建非核心线程那步。 |
| Cached 队列为什么用 SynchronousQueue？ | 它无容量，offer 必须有 take 才成功——逼着建新线程即时 hand-off。 |
| Single 和 `new ThreadPoolExecutor(1,1,...)` 区别？ | 前者包装后禁止强转改参数，后者可改。 |
| Scheduled 任务异常会怎样？ | 线程被替换，但该周期任务不再被调度——必须任务内 try-catch。 |
| WorkStealing 适合 IO 吗？ | 不适合，阻塞任务占住 worker，窃取救不了。 |

## 易错点
- 用 `Executors` 工厂方法 → OOM 风险（阿里规约禁止）。
- Fixed 以为 max 会生效 → 队列无界永不走非核心。
- Scheduled 任务不 catch 异常 → 静默停调度。
- WorkStealingPool 跑 IO → 线程占满、窃取无效。

## 延伸

## 延伸

- 关联题：[[concurrency/thread-pool-principles]]
- 关联题：[[concurrency/threadpool-source-analysis]]
- 关联题：[[concurrency/forkjoinpool-parallelstream]]
- 关联题：[[concurrency/threadlocal-threadpool-problems]]
