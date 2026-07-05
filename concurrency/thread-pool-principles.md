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
  processWorkerExit(w, completedAbruptly);   // getTask 返回 null 后真正回收
  ```
- **核心线程不会"用完就死"**——循环 `getTask()` 继续取队列任务。

### 非核心线程怎么"超时被回收"（源码级，重点）
**关键澄清**：池里没有"核心 vs 非核心"线程的**实体身份区分**——所有 `Worker` 是同一个类，`addWorker(firstTask, core)` 的 `core` 参数只用来判定"能否创建"，创建后进同一个 `HashSet<Worker>` 没标签。回收时靠运行时数量动态判定。

**核心源码 `getTask()`**：
```java
private Runnable getTask() {
    boolean timedOut = false;
    for (;;) {
        int c = ctl.get();
        int rs = runStateOf(c);
        if (rs >= SHUTDOWN && (rs >= STOP || workQueue.isEmpty())) {
            decrementWorkerCount(); return null;
        }
        int wc = workerCountOf(c);
        // ★ 是否受超时约束：当前总数 > core（或开了 allowCoreThreadTimeOut）
        boolean timed = allowCoreThreadTimeOut || wc > corePoolSize;
        // ★ 已超时 + (超上限 或 队列空) → CAS 减计数 + 返回 null
        if ((wc > maximumPoolSize || (timed && timedOut))
            && (wc > 1 || workQueue.isEmpty())) {
            if (compareAndDecrementWorkerCount(c)) return null;
            continue;
        }
        try {
            // ★ timed → poll 限时；!timed → take 永久阻塞
            Runnable r = timed ?
                workQueue.poll(keepAliveTime, TimeUnit.NANOSECONDS) :
                workQueue.take();
            if (r != null) return r;
            timedOut = true;        // poll 超时返回 null
        } catch (InterruptedException retry) { timedOut = false; }
    }
}
```

**机制拆解**：
1. **`timed = allowCoreThreadTimeOut || wc > corePoolSize`** —— 看的是池的**当前线程总数 `wc`**，不是这个 worker 的"身份"。`wc=8, core=5` → 8 个 worker **全部** `timed=true`（不是只"那 3 个非核心"约束）。
2. **`poll(keepAliveTime)` vs `take()`**：
   - `poll` 最多等 keepAliveTime，超时返回 **null**。
   - `take` 队列空时**永久阻塞**——这就是"核心线程不死"的真相。
3. **`poll` 返回 null → `timedOut=true`** → 下一轮 for 走 `timed && timedOut` 分支 → **CAS 减计数 + return null** → runWorker while 退出 → `processWorkerExit`：
   - `workers.remove(w)` 真正移除 worker。
   - ctl -1。
   - 视情况补 worker（低于 core 或队列还有任务但 worker=0）。
4. **回收的"平等竞争"**：`wc > core` 时所有 worker 都 `poll`，**谁先超时谁先死**；`wc` 降到 `core` 后剩余 worker 切回 `take()` 不再超时——"剩余的 core 个核心线程"就此稳态。不是挑"非核心"的回收。

**`allowCoreThreadTimeOut(true)`**：`timed` 恒真 → 所有 worker 永远 `poll` → 即使 `wc ≤ core` 空闲超 keepAliveTime 也会被回收到 **0**。适合流量波动大、空闲不想占内存的场景。默认 false（核心线程常驻）。

**生命周期图**：
```
wc > core (timed=true):
  getTask() → poll(keepAliveTime)
    拿到任务 → return task → runWorker 跑 → 继续循环
    超时 → timedOut=true → 下一轮 CAS decrement → return null
                                ↓
  runWorker while 退出 → processWorkerExit:
    workers.remove(w) + ctl-1 + 视情况补
                                ↓
  Worker.run() 返回 → 线程对象死亡

wc == core (timed=false, 默认 allowCoreThreadTimeOut=false):
  getTask() → take()  ← 队列空时永久阻塞等任务（核心线程不死）
```

### 异常与替换
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
- 以为"非核心线程"是创建时打的标签 → 不是，所有 Worker 同类，靠运行时 `wc > core` 动态判定 timed。
- 以为回收是定时器触发 → 不是，是 `poll(keepAliveTime)` 阻塞超时返回 null 触发，纯靠阻塞队列 API。
- 以为回收是挑"非核心的"回收 → 不是，`wc > core` 时所有 worker 平等竞争，谁 poll 先超时谁死。
- 忘 `processWorkerExit` → `getTask` 返回 null 只是让循环退出，真正移除 worker 是这步。

## 延伸

- 关联题：[[concurrency/threadlocal-threadpool-problems]]
- 关联题：[[concurrency/aqs-principle]]
- 关联题：[[concurrency/completablefuture-async-orchestration]]
