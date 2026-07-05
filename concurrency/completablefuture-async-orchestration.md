---
type: question
id: concurrency/completablefuture-async-orchestration
title: CompletableFuture 异步编排
category: concurrency
subcategory: concurrency
difficulty: medium
tags: [completablefuture, async, juc, concurrency, future]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-05-26
---

# CompletableFuture 异步编排

## 问题描述

CompletableFuture 比 Future 好在哪？怎么编排异步任务？默认线程池有什么坑？

## 解答

### Future 的局限
- `get()` 阻塞等结果，不能回调。
- 不能组合多个任务（等全部完成、取最快、串接转换）。
- 不能手动完成（设结果/异常）。

### CompletableFuture 核心能力
- **回调链**：`thenApply`/`thenAccept`/`thenRun`（前一步完成后做转换/消费/动作）。
- **异常处理**：`exceptionally`/`handle`/`whenComplete`。
- **组合**：
  - `thenCompose`：前一步结果传给下一个 CF（flatMap，避免 `Future<Future<T>>`）。
  - `thenCombine`：两个 CF 都完成后合并结果。
- **多任务**：
  - `allOf(cf1, cf2, ...)`：全部完成才完成（返回 CF<Void>，需自己 join 取结果）。
  - `anyOf(...)`：任一完成即完成。
- **手动完成**：`complete(value)` / `completeExceptionally(throwable)` / `cancel`。

### 同步 vs 异步执行
- 默认 `thenApply` 等**在完成当前 CF 的线程执行**（如 CF 已完成则在调用线程同步执行）。
- `thenApplyAsync` / `thenAcceptAsync`：**提交到线程池异步执行**，可指定 Executor。
- `runAsync` / `supplyAsync`：起始异步任务，可指定 Executor。

### 默认线程池的坑（重点）
- 不传 Executor 时用 `ForkJoinPool.commonPool()`：
  - **全 JVM 共享**一个 commonPool，所有未指定池的 parallelStream / CF 都抢它。
  - 默认线程数 = CPU 核数 - 1，**任务多则排队甚至饿死**。
  - 任务里若阻塞（IO/远程调用）→ 占住 commonPool 线程，拖垮所有 parallelStream 和其他 CF。
- **生产建议**：业务异步任务**显式传业务线程池**，尤其涉及 IO 的；只把 CPU 短任务留给 commonPool。

### 编排示例
```java
ExecutorService pool = Executors.newFixedThreadPool(8);
CompletableFuture<User> userF = CompletableFuture.supplyAsync(() -> getUser(id), pool);
CompletableFuture<Order> orderF = userF.thenComposeAsync(u -> getOrders(u.id), pool);
CompletableFuture<List<Item>> itemsF = orderF.thenCombineAsync(
    CompletableFuture.supplyAsync(() -> getRecommendations(id), pool),
    (order, recs) -> merge(order, recs), pool);
List<Item> result = itemsF.join();   // 阻塞点，尽量在最外层
```

### 异常传播
- 链上任一步抛异常 → 沿链传播到最终 `join`/`get`（抛 `CompletionException` 包装）。
- `exceptionally(ex -> fallback)` 捕获返回兜底值。
- `handle((value, ex) -> ...)` 同时处理正常与异常。

## 易错点
- 用默认 commonPool 跑 IO 任务 → 拖垮全局 parallelStream。
- `thenApply` 期望异步却同步执行（CF 已完成时）→ 用 `thenApplyAsync` 显式异步。
- `allOf().join()` 后忘取各 CF 结果 → allOf 只返回 CF<Void>。
- 异常未处理 → `join` 抛 `CompletionException`，链断了。

## 延伸

## 延伸

- 关联题：[[concurrency/thread-pool-principles]]
- 关联题：[[concurrency/forkjoinpool-parallelstream]]
- 关联题：[[concurrency/countdownlatch-cyclicbarrier-semaphore]]
