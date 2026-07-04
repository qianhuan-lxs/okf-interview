---
type: question
id: concurrency/thread-pool-principles
title: 线程池运行原理
category: concurrency
subcategory: concurrency
difficulty: medium
tags: [thread-pool, juc, threadpoolexecutor, concurrency]
languages: []
role: [ai-app, sde, backend]
companies: [有赞]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 线程池运行原理

## 问题描述
线程池的运行原理是什么？怎么运行的？用完的线程执行完之后呢？

## 解答

### 核心参数（ThreadPoolExecutor）
- `corePoolSize` / `maximumPoolSize` / `keepAliveTime` / `unit`
- `workQueue`（阻塞队列）
- `threadFactory`
- `rejectedExecutionHandler`（拒绝策略）

### 提交流程（execute）
```
1. workerCount < core        → new Worker(thread) 跑任务
2. 入 workQueue               → 队列满则下一步
3. workerCount < max          → 新建非核心线程跑任务
4. 走 RejectedExecutionHandler
```

### Worker 运行机制
- 每个 Worker 是一个 Thread，`runWorker` 循环：
  - `getTask()`：先 `poll(keepAliveTime)` 取非核心任务，超时返回 null → 该 worker 退出；核心线程默认 `take()` 阻塞。
  - 取到 task → `beforeExecute` → `task.run()` → `afterExecute` → 异常吞掉（除非重写）。
- "用完的线程"不会立刻死，回循环继续 `getTask()` 等下一个任务。

### 阻塞队列选择
- `SynchronousQueue`：无容量，直接 hand-off，适合 CachedThreadPool。
- `LinkedBlockingQueue`：默认 Integer.MAX_VALUE，FixedThreadPool 用，易堆积 OOM。
- `ArrayBlockingQueue`：有界，需显式容量。
- `PriorityBlockingQueue`：优先级。

### 拒绝策略
- AbortPolicy（默认，抛 RejectedExecutionException）
- CallerRunsPolicy（调用线程自己跑，反压）
- DiscardPolicy / DiscardOldestPolicy

### 配置经验
- CPU 密集：core ≈ N+1
- IO 密集：core ≈ 2N 或 `N * (1 + 等待/计算)`
- 队列务必有界，否则 maxPoolSize 永不生效、OOM 风险。

## 易错点
- 用 `Executors.newFixedThreadPool` —— 队列无界，OOM 隐患（阿里规约禁止）。应手动 `new ThreadPoolExecutor` + 有界队列。

## 延伸

## 延伸

- 关联题：[[concurrency/threadlocal-threadpool-problems]]
- 关联题：[[concurrency/aqs-principle]]
