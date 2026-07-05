---
type: question
id: concurrency/threadpool-source-analysis
title: ThreadPoolExecutor 源码解析 (ctl / execute / Worker / transfer)
category: concurrency
subcategory: concurrency
difficulty: hard
tags: [thread-pool, threadpoolexecutor, source, juc, concurrency]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-07-05
---

# ThreadPoolExecutor 源码解析 (ctl / execute / Worker / transfer)

## 问题描述

ThreadPoolExecutor 源码怎么读？ctl 字段怎么编码状态和线程数？execute 流程细节？Worker 是什么？扩容/关闭怎么实现？

## 解答

本文按源码结构拆解 `java.util.concurrent.ThreadPoolExecutor`（JDK 8+）。

## 一、ctl 字段——一个 int 装两件事

```java
private final AtomicInteger ctl = new AtomicInteger(ctlOf(RUNNING, 0));
private static final int COUNT_BITS = Integer.SIZE - 3;   // 29
private static final int CAPACITY   = (1 << COUNT_BITS) - 1;  // 线程数上限 ~5亿

// runState 存在高 3 位
private static final int RUNNING    = -1 << COUNT_BITS;   // 111...  接新任务+处理队列
private static final int SHUTDOWN   =  0 << COUNT_BITS;   // 000...  不接新任务，处理队列剩余
private static final int STOP       =  1 << COUNT_BITS;   // 001...  不接新任务，丢弃队列，中断进行中
private static final int TIDYING    =  2 << COUNT_BITS;   // 010...  所有任务终止，terminated() 钩子待执行
private static final int TERMINATED =  3 << COUNT_BITS;   // 011...  terminated() 执行完

// 低 29 位 = workerCount
private static int runStateOf(int c)   { return c & ~CAPACITY; }   // 取高 3 位
private static int workerCountOf(int c){ return c & CAPACITY; }    // 取低 29 位
private static int ctlOf(int rs, int wc){ return rs | wc; }        // 拼接
```

**为什么用一个 int 装两件事**：线程数和运行状态总是要一起看一起改，放一个 AtomicInteger 里用一次 CAS 同时管，避免两字段间的竞态。这是并发设计的典型技巧（`ReentrantReadWriteLock` 的 state 高低位、`LongAdder` 的 Cell 也类似）。

**状态流转**：`RUNNING → SHUTDOWN`（`shutdown()`）；`RUNNING/SHUTDOWN → STOP`（`shutdownNow()`）；`STOP/TIDYING → TIDYING`（所有 worker 死了 `tryTerminate`）；`TIDYING → TERMINATED`（`terminated()` 钩子执行完）。

## 二、`execute(Runnable)`——三段式提交

```java
public void execute(Runnable command) {
    if (command == null) throw new NullPointerException();
    int c = ctl.get();
    // 1. 线程数 < corePoolSize → 新建核心 worker 跑这个任务
    if (workerCountOf(c) < corePoolSize) {
        if (addWorker(command, true))               // core=true
            return;
        c = ctl.get();                              // CAS 失败重新读
    }
    // 2. 还在 RUNNING 且能入队列 → 入队
    if (isRunning(c) && workQueue.offer(command)) {
        int recheck = ctl.get();                    // double-check
        if (!isRunning(recheck) && remove(command)) // 入队后池子关了 → 走拒绝
            reject(command);
        else if (workerCountOf(recheck) == 0)       // 入队后没线程了 → 补一个空 worker 拉队列
            addWorker(null, false);
    }
    // 3. 入队失败（队列满）→ 试建非核心 worker；再失败 → 拒绝
    else if (!addWorker(command, false))
        reject(command);
}
```

**顺序是核心面试点**：`核心 → 队列 → 非核心 → 拒绝`。所以**用无界队列时 maxPoolSize 永不生效**（队列永远不满，走不到第 3 步）——这是 `Executors.newFixedThreadPool` 用 `LinkedBlockingQueue`（默认无界）的 OOM 根因。

**double-check**：入队后再查一次状态，因为入队期间池可能被 `shutdown`。若关了且能 remove 就拒绝；若还在但线程数为 0，补一个空 worker（`addWorker(null, false)`）确保有人拉队列。

## 三、`addWorker`——创建 Worker 并启动

```java
private boolean addWorker(Runnable firstTask, boolean core) {
    // 外层循环：CAS 把 workerCount +1，直到成功或状态不允许
    retry:
    for (;;) {
        int c = ctl.get();
        int rs = runStateOf(c);
        // 状态检查：SHUTDOWN 不接新任务（firstTask!=null 直接 false）；
        //           SHUTDOWN 但 firstTask==null 且队列非空 仍允许补 worker 拉队列
        if (rs >= SHUTDOWN && !(rs == SHUTDOWN && firstTask == null && !workQueue.isEmpty()))
            return false;
        // 内层循环：CAS workerCount+1
        for (;;) {
            int wc = workerCountOf(c);
            if (wc >= CAPACITY || wc >= (core ? corePoolSize : maximumPoolSize))
                return false;
            if (compareAndIncrementWorkerCount(c)) break retry;
            c = ctl.get();
            if (runStateOf(c) != rs) continue retry;
        }
    }
    // 创建 Worker，加锁加入 workers 集合，启动线程
    Worker w = new Worker(firstTask);
    Thread t = w.thread;
    // ... workers.add(w) ... t.start() ...
    return true;
}
```

要点：
- 先 CAS 占线程数名额，再真正建 Worker 启动——避免建了线程又超限。
- SHUTDOWN 状态下不允许带 firstTask 的新 worker，但允许"空 worker"来拉干队列剩余任务。

## 四、`Worker`——一个线程 + 一把不可重入锁

```java
private final class Worker extends AbstractQueuedSynchronizer implements Runnable {
    final Thread thread;
    Runnable firstTask;
    volatile long completedTasks;
    Worker(Runnable firstTask) {
        setState(-1); // 抑制 runWorker 前的中断
        this.firstTask = firstTask;
        this.thread = getThreadFactory().newThread(this);
    }
    public void run() { runWorker(this); }
    // AQS 实现：不可重入独占锁，0=未锁，1=已锁
    protected boolean tryAcquire(int unused) { return compareAndSetState(0, 1); }
    protected boolean tryRelease(int unused) { setState(0); return true; }
}
```

**为什么 Worker 继承 AQS 当锁**：`runWorker` 执行任务前 `w.lock()`，执行后 `w.unlock()`。这把锁让 `shutdown` 能判断"这个 worker 是不是正在跑任务"——`tryLock` 成功说明空闲可中断，失败说明在跑任务（STOP 才强中断）。**不可重入**是故意的，避免任务里又调池方法重入造成状态混乱。

## 五、`runWorker`——Worker 的主循环

```java
final void runWorker(Worker w) {
    Thread wt = Thread.currentThread();
    Runnable task = w.firstTask;
    w.firstTask = null;
    w.unlock();                     // 抵消 Worker 构造时的 setState(-1)，允许中断
    boolean completedAbruptly = true;
    try {
        while (task != null || (task = getTask()) != null) {
            w.lock();               // 标记"正在执行任务"
            // 状态检查：若 STOP 则确保线程被中断；否则清中断标志
            if ((runStateAtLeast(ctl.get(), STOP) ||
                 (Thread.interrupted() && runStateAtLeast(ctl.get(), STOP))) &&
                !wt.isInterrupted())
                wt.interrupt();
            beforeExecute(wt, task);                 // 钩子
            Throwable thrown = null;
            try {
                task.run();
            } catch (RuntimeException x) { thrown = x; throw x; }
            finally {
                afterExecute(task, thrown);          // 钩子
            }
            w.unlock();
            completedAbruptly = false;
            w.completedTasks++;
        }
    } finally {
        processWorkerExit(w, completedAbruptly);     // worker 退出收尾（可能补一个）
    }
}
```

要点：
- **核心线程不会"用完就死"**——循环 `getTask()` 继续从队列拉任务。
- **任务异常被吞**：`task.run()` 抛异常会跳出 while，`completedAbruptly=true`，`processWorkerExit` 会**新建一个 worker 替代**（这就是异常"丢了"但池还活着的原因）。
- `beforeExecute`/`afterExecute` 是钩子，可重写做监控、埋点。
- `processWorkerExit`：若当前线程数低于应有下限（core 或 1），补建一个 worker。

## 六、`getTask`——核心 vs 非核心的"回收"分叉

```java
private Runnable getTask() {
    boolean timedOut = false;
    for (;;) {
        int c = ctl.get();
        int rs = runStateOf(c);
        // STOP 或 (SHUTDOWN 且队列空) → 返回 null，worker 退出
        if (rs >= SHUTDOWN && (rs >= STOP || workQueue.isEmpty())) {
            decrementWorkerCount();
            return null;
        }
        int wc = workerCountOf(c);
        boolean timed = allowCoreThreadTimeOut || wc > corePoolSize;  // 该线程是否要超时
        try {
            Runnable r = timed ?
                workQueue.poll(keepAliveTime, TimeUnit.NANOSECONDS) :  // 非核心/允许超时：超时返回 null
                workQueue.take();                                     // 核心：无限阻塞
            if (r != null) return r;
            timedOut = true;
        } catch (InterruptedException retry) {
            timedOut = false;
        }
    }
}
```

**关键**：
- **核心线程默认 `take()`**——无限阻塞等任务，不会因超时退出（所以"核心线程不回收"）。
- **非核心线程 `poll(keepAliveTime)`**——超时拿不到就返回 null → worker 退出（被回收）。
- **`allowCoreThreadTimeOut(true)`**——让核心线程也走 `poll`，可被回收（默认 false）。
- "核心/非核心"不是 Worker 的属性，是**按当前线程数动态判断**：`wc > corePoolSize` 就当非核心处理。

## 七、关闭：`shutdown` vs `shutdownNow`

- `shutdown()`：设 SHUTDOWN，中断所有**空闲** worker（`tryLock` 成功的），正在跑任务的不打断；队列剩余任务仍会被跑完。
- `shutdownNow()`：设 STOP，中断所有 worker（包括正在跑的），返回队列中未执行任务 List。
- `tryTerminate`：当最后一个 worker 死了、队列为空，状态转 TIDYING → 调 `terminated()` 钩子 → TERMINATED。
- `awaitTermination(timeout)`：阻塞等终止，配合关闭做优雅停机。

## 八、钩子与工具方法

- `beforeExecute`/`afterExecute`/`terminated`：可重写做监控、日志、指标。
- `prestartAllCoreThreads()`：预热全部核心线程，避免冷启动延迟。
- `prestartCoreThread()`：预热一个。
- `getActiveCount()`/`getCompletedTaskCount()`/`getQueue().size()`：运行时监控（非精确，并发下估值）。

## 九、源码阅读路线建议

1. 先看字段：`ctl`、`workers`、`workQueue`、7 个核心参数。
2. 看 `execute`——理解三段式提交流程。
3. 看 `addWorker`——理解线程创建与状态检查。
4. 看 `Worker` 内部类——理解"线程+锁"的封装。
5. 看 `runWorker` + `getTask`——理解线程复用与回收。
6. 看 `shutdown`/`shutdownNow`/`tryTerminate`——理解生命周期。
7. 看 `reject` 与 `RejectedExecutionHandler`——理解拒绝策略。

## 易错点
- 以为先创非核心线程 → 错，core→queue→non-core→reject。
- 以为核心线程一定不回收 → `allowCoreThreadTimeOut(true)` 可回收。
- 任务异常被静默吞掉 → 重写 `afterExecute` 捕获，或用 `FutureTask` 提交（`get()` 重抛）。
- 无界队列导致 maxPoolSize 永不生效 → OOM 隐患。

## 延伸

## 延伸

- 关联题：[[concurrency/thread-pool-principles]]
- 关联题：[[concurrency/executors-built-in-pools]]
- 关联题：[[concurrency/aqs-principle]]
- 关联题：[[concurrency/completablefuture-async-orchestration]]
