---
type: question
id: concurrency/thread-pool-principles
title: 线程池运行原理 (ctl 高低位 / execute 流程 / Worker / 钩子)
category: concurrency
subcategory: concurrency
difficulty: hard
tags: [thread-pool, juc, threadpoolexecutor, concurrency]
languages: [java]
role: [sde, backend]
companies: [有赞]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 线程池运行原理 (ctl 高低位 / execute 流程 / Worker / 钩子)

## 问题描述

线程池的运行原理是什么？怎么运行的？用完的线程执行完之后呢？核心线程能被回收吗？

## 解答

### 核心参数（`ThreadPoolExecutor`）
- `corePoolSize` / `maximumPoolSize` / `keepAliveTime` / `unit`
- `workQueue`（阻塞队列）/ `threadFactory` / `rejectedExecutionHandler`（拒绝策略）

### ctl 字段（源码细节）
- `private final AtomicInteger ctl = new AtomicInteger(ctlOf(-1, 0));`
- **高 3 位 = workerCountOf（线程数，上限约 2^29-1）**，低 29 位 = runState（RUNNING/-1、SHUTDOWN/0、STOP/1、TIDYING/2、TERMINATED/3）。
- 用一个 AtomicInteger 同时管状态和线程数，避免两字段间的竞态。

### `execute(Runnable)` 提交流程（源码三段）
```
1. workerCountOf < corePoolSize  → addWorker(command, true)（核心线程）；失败走 step 2
2. isRunning && offer(workQueue) → 入队成功后 double-check isRunning，否则走 step 3
   入队后又检测到线程数为 0 → addWorker(null, false) 补一个空 worker 拉队列
3. !addWorker(command, false)（非核心线程）→ reject(command)
```
**注意顺序：核心 → 队列 → 非核心 → 拒绝**。队列满才会创建非核心线程，所以用无界队列时 maxPoolSize 永不生效。

### Worker 机制（"用完的线程去哪了"）
- `Worker` 实现 Runnable，封装了 firstTask 和一个独占锁（继承 AQS，不可重入）。
- `runWorker`：
  ```
  while (task != null || (task = getTask()) != null) {
      w.lock();        // 期间检查 interrupt
      beforeExecute(wt, task);   // 钩子，可重写
      try { task.run(); }
      catch (Throwable x) { after = x; threw = true; }
      finally { afterExecute(wt, after); }
      w.unlock();
  }
  completedAtomicTask();
  ```
- **核心线程不会"用完就死"**——循环 `getTask()` 继续取队列任务。
- `getTask()`：核心线程默认 `workQueue.take()`（无限阻塞）；非核心线程 `poll(keepAliveTime)`，超时返回 null → worker 退出（线程被回收）。
- **`allowCoreThreadTimeOut(true)`**：核心线程也走 `poll` 超时逻辑，可被回收（默认 false）。
- **异常处理**：`task.run()` 抛异常会被吞掉（除非重写 `afterExecute`），**且会导致 worker 退出并被新建替代**（这就是为什么异常会"丢"但池还活着）。

### 阻塞队列选择
| 队列 | 特点 | 适用 |
| --- | --- | --- |
| `SynchronousQueue` | 无容量，直接 hand-off | `CachedThreadPool`，短任务高吞吐 |
| `LinkedBlockingQueue` | 默认 `Integer.MAX_VALUE` 无界 | `FixedThreadPool`，易 OOM |
| `ArrayBlockingQueue` | 有界，需显式容量 | 推荐，可控 |
| `PriorityBlockingQueue` | 优先级 | 任务有优先级 |

### 拒绝策略
- `AbortPolicy`（默认，抛 `RejectedExecutionException`）
- `CallerRunsPolicy`（调用线程自己跑，反压，最常用线上兜底）
- `DiscardPolicy` / `DiscardOldestPolicy`

### 关闭
- `shutdown()`：不再接新任务，**处理完队列剩余任务**，状态 SHUTDOWN。
- `shutdownNow()`：返回未执行任务 List，**中断正在执行的**，状态 STOP。
- `awaitTermination(timeout)`：阻塞等终止。

### 钩子方法（可重写做监控）
- `beforeExecute` / `afterExecute` / `terminated`。
- `prestartAllCoreThreads()`：预热全部核心线程，避免冷启动延迟。

### 配置经验
- **CPU 密集**：core ≈ N+1（+1 防偶发停顿）。
- **IO 密集**：core ≈ 2N 或 `N * (1 + 等待/计算)`。
- **队列务必有界**，否则 maxPoolSize 永不生效、OOM 风险（阿里规约禁止 `Executors` 工厂方法，要求手动 `new ThreadPoolExecutor` + 有界队列 + 命名线程工厂 + 明确拒绝策略）。

## 易错点
- `Executors.newFixedThreadPool` / `newCachedThreadPool` → 队列无界或线程无界，OOM 隐患。
- 以为核心线程一定不回收 → `allowCoreThreadTimeOut(true)` 可回收。
- 任务异常被静默吞掉 → 重写 `afterExecute` 捕获，或用 `FutureTask` 提交（`get()` 会重抛）。
- 以为先创建非核心线程 → 错，是 core→queue→non-core→reject。

## 延伸

## 延伸

- 关联题：[[concurrency/threadlocal-threadpool-problems]]
- 关联题：[[concurrency/aqs-principle]]
- 关联题：[[concurrency/completablefuture-async-orchestration]]
