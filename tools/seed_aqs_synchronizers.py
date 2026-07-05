#!/usr/bin/env python3
"""Add aqs-based-synchronizers catalog doc."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from ikf_writer import q

DATE = "2026-07-05"

q("concurrency/aqs-based-synchronizers.md",
  "基于 AQS 的同步器逐一介绍 (Lock/RWLock/Semaphore/CountDownLatch/CyclicBarrier/Worker)",
  "concurrency", "concurrency", "hard",
  ["aqs", "reentrantlock", "readwritelock", "semaphore", "countdownlatch",
   "cyclicbarrier", "juc", "concurrency"],
  [],
  """# 基于 AQS 的同步器逐一介绍 (Lock/RWLock/Semaphore/CountDownLatch/CyclicBarrier/Worker)

## 问题描述

JUC 哪些工具类是基于 AQS 实现的？每个的 `state` 语义、`tryAcquire*` 怎么实现、独占还是共享、有什么坑？

## 解答

AQS 是模板方法框架——子类实现 `tryAcquire/tryRelease/tryAcquireShared/tryReleaseShared` 决定"什么算抢到"，AQS 管排队与 park。下表是 JUC 中直接或间接基于 AQS 的同步器，逐一拆解。

| 同步器 | state 语义 | 模式 | 是否直接继承 AQS |
| --- | --- | --- | --- |
| ReentrantLock | 重入次数（0=空闲，>0=持有） | 独占 | ✅ Sync extends AQS |
| ReentrantReadWriteLock | 高16=共享读数，低16=独占写重入 | 共享+独占 | ✅ Sync extends AQS |
| Semaphore | 剩余许可数 | 共享 | ✅ Sync extends AQS |
| CountDownLatch | 剩余计数 | 共享 | ✅ Sync extends AQS |
| CyclicBarrier | — | — | ❌ 基于 ReentrantLock+Condition（间接用 AQS） |
| ThreadPoolExecutor.Worker | AQS 锁状态（0/1） | 独占不可重入 | ✅ Worker extends AQS |

---

## 一、ReentrantLock（独占可重入锁）

- **state 语义**：`0` = 未被持有；`>0` = 持有线程的重入次数。
- **owner 字段**：AQS 自身没有 owner，`ReentrantLock.Sync` 用 `exclusiveOwnerThread`（AQS 父类 `AbstractOwnableSynchronizer` 提供）记录持锁线程。

### `tryAcquire`（非公平 `nonfairTryAcquire`）
```java
final boolean nonfairTryAcquire(int acquires) {
    Thread current = Thread.currentThread();
    int c = getState();
    if (c == 0) {
        if (compareAndSetState(0, acquires)) {           // CAS 抢
            setExclusiveOwnerThread(current);
            return true;
        }
    } else if (current == getExclusiveOwnerThread()) {   // 重入
        int nextc = c + acquires;
        if (nextc < 0) throw new Error("Maximum lock count exceeded");
        setState(nextc);                                  // 重入无需 CAS（只有自己能改）
        return true;
    }
    return false;
}
```
- **公平版差异**：`c == 0` 分支前先 `if (hasQueuedPredecessors()) return false;`——队列有人等就去排队，不插队。
- 重入时 `setState` 不用 CAS：只有持锁线程能走到这（已被 owner 判断保护），无竞态。

### `tryRelease`
```java
protected final boolean tryRelease(int releases) {
    int c = getState() - releases;
    if (Thread.currentThread() != getExclusiveOwnerThread())
        throw new IllegalMonitorStateException();         // 非持锁线程不能释放
    boolean free = false;
    if (c == 0) { free = true; setExclusiveOwnerThread(null); }  // 重入归零才真释放
    setState(c);
    return free;
}
```
- 重入要 `unlock` 对应次数才真正释放。

### 用法 / 坑
- 必须 `finally { lock.unlock(); }`。
- `tryLock()` 无参**不走公平判断**——即使 fair=true 也会插队；要公平的尝试用 `tryLock(0, TimeUnit)`。
- `lockInterruptibly()` 可响应中断；`tryLock(timeout)` 可超时。

---

## 二、ReentrantReadWriteLock（共享读 + 独占写）

- **state 语义**：一个 int 装两个数——**高 16 位 = 共享读次数（多个读者），低 16 位 = 独占写重入数**。
  ```java
  static final int SHARED_SHIFT   = 16;
  static final int SHARED_UNIT    = (1 << SHARED_SHIFT);
  static final int MAX_COUNT      = (1 << SHARED_SHIFT) - 1;
  static final int EXCLUSIVE_MASK = (1 << SHARED_SHIFT) - 1;
  static int sharedCount(int c)    { return c >>> SHARED_SHIFT; }   // 高16
  static int exclusiveCount(int c) { return c & EXCLUSIVE_MASK; }   // 低16
  ```
- **读锁**：共享模式，多个读者可同时持有。
- **写锁**：独占模式，最多一个写者，且排斥所有读者。

### `tryAcquire`（写锁）
```java
protected final boolean tryAcquire(int acquires) {
    Thread current = Thread.currentThread();
    int c = getState();
    int w = exclusiveCount(c);
    if (c != 0) {
        // 有读锁或有其他写锁 → 失败（除非自己是写者重入）
        if (w == 0 || current != getExclusiveOwnerThread()) return false;
        if (w + exclusiveCount(acquires) > MAX_COUNT) throw new Error("Maximum lock count exceeded");
        setState(c + acquires);   // 写重入
        return true;
    }
    if (writerShouldBlock() || !compareAndSetState(c, c + acquires)) return false;
    setExclusiveOwnerThread(current);
    return true;
}
```
- **关键约束**：只要有任何读者（`sharedCount(c) != 0`），写锁就拿不到——这就是**锁升级（读→写）会死锁**的根源（自己持读锁，写锁等所有读者释放，而自己就是读者）。
- `writerShouldBlock`：公平版查 `hasQueuedPredecessors`，非公平版返回 false（写优先）。

### `tryAcquireShared`（读锁）
```java
protected final int tryAcquireShared(int unused) {
    Thread current = Thread.currentThread();
    int c = getState();
    // 写锁被别人持有 → 失败
    if (exclusiveCount(c) != 0 && getExclusiveOwnerThread() != current)
        return -1;
    int r = sharedCount(c);
    if (!readerShouldBlock() &&
        r < MAX_COUNT &&
        compareAndSetState(c, c + SHARED_UNIT)) {        // 高16位 +1
        // ... 读锁计数（firstReader 优化 + cached counts）...
        return 1;
    }
    return fullTryAcquireShared(current);                 // CAS 失败走完整逻辑
}
```
- 公平版 `readerShouldBlock` 查队列前驱（防写饿死）；非公平版在"写锁等待中"时阻塞新读者（`apparentlyFirstQueuedThreadIsExclusive`）——缓解写饥饿。
- 读锁计数有 `firstReader` / `cachedHoldCounter` 优化，避免每个读者都走 ThreadLocal。

### `tryReleaseShared`（读锁释放）
- 高 16 位 -1，CAS 自旋（多读者并发释放，要 CAS）。

### 用法 / 坑
- **锁降级支持**：持写锁时可以再获取读锁，然后释放写锁（写→读）。常用于"写完立刻可读"场景。
- **锁升级不支持**：持读锁时直接拿写锁会死锁——要先 `unlockRead` 再 `lockWrite`。
- 读多写少但写不能饿死时用公平模式或 StampedLock。

---

## 三、Semaphore（信号量 / 许可）

- **state 语义**：剩余许可数。
- **模式**：共享（多个线程可同时持有一个许可）。

### `tryAcquireShared`（非公平）
```java
final int nonfairTryAcquireShared(int acquires) {
    for (;;) {
        int available = getState();
        int remaining = available - acquires;
        if (remaining < 0 || compareAndSetState(available, remaining))
            return remaining;        // >=0 成功，<0 失败入队
    }
}
```
- 返回值符合 AQS 共享约定：`>=0` 成功（且可传播唤醒），`<0` 失败排队。
- 许可不够就返回负数，AQS 框架把它入队。

### `tryReleaseShared`
```java
protected final boolean tryReleaseShared(int releases) {
    for (;;) {
        int current = getState();
        int next = current + releases;
        if (next < current) throw new Error("Maximum permit count exceeded");
        if (compareAndSetState(current, next)) return true;
    }
}
```
- **注意**：`release()` 可以不配对 `acquire()`——这会**实际增加许可数**。利用此特性可动态扩容许可，但易错。

### 公平 vs 非公平
- 公平版 `tryAcquireShared` 先 `hasQueuedPredecessors` 检查。
- 默认非公平（吞吐高）。

### 用法 / 坑
- 限流、资源池（连接池大小）、限制并发访问数。
- `release()` 多于 `acquire()` → 许可数越界增多。
-许可数可以是 0 甚至负（用作同步点）。

---

## 四、CountDownLatch（一次性倒计时）

- **state 语义**：剩余计数（初始 = count）。
- **模式**：共享。

### `tryAcquireShared`
```java
protected int tryAcquireShared(int acquires) {
    return (getState() == 0) ? 1 : -1;     // 计数归零才放行所有等待者
}
```
- **极简**：只有 `state==0` 才返回 1（成功 + 传播唤醒），否则 -1 入队等待。
- 这就是"主线程等 N 个子任务"的语义——所有 `await()` 的线程在 state 归零后一起放行。

### `tryReleaseShared`
```java
protected boolean tryReleaseShared(int releases) {
    for (;;) {
        int c = getState();
        if (c == 0) return false;          // 已归零，不再减
        int nextc = c - 1;
        if (compareAndSetState(c, nextc))
            return nextc == 0;             // 归零才返回 true 触发唤醒
    }
}
```
- `countDown()` 每次减 1；减到 0 时返回 true，AQS 框架 `doReleaseShared` 唤醒所有等待者。

### 用法 / 坑
- **不可重置**——计数归零后就废了，要再用得新建。要循环用选 CyclicBarrier。
- `countDown()` 必须在 `finally` 调，否则计数永不归零、`await()` 永久阻塞。
- 不能重复 countDown 超过初始 count（state 不会变负，`c==0` 后直接 return false）。

---

## 五、CyclicBarrier（可循环屏障，间接用 AQS）

- **不直接继承 AQS**——基于 `ReentrantLock` + `Condition` + `Generation` 实现。但 ReentrantLock 底层是 AQS，所以**间接用 AQS**。
- **核心字段**：`ReentrantLock lock`、`Condition trip = lock.newCondition()`、`int parties`（屏障容量）、`int count`（当前未到数）、`Generation generation`（每轮换代）。

### `await()` 主干
```java
public int await() throws InterruptedException, BrokenBarrierException {
    final ReentrantLock lock = this.lock;
    lock.lock();
    try {
        final Generation g = generation;
        if (g.broken) throw new BrokenBarrierException();
        if (Thread.interrupted()) { breakBarrier(); throw new InterruptedException(); }
        int index = --count;
        if (index == 0) {                       // 最后一个到达
            boolean ranAction = false;
            try {
                Runnable command = barrierAction;
                if (command != null) command.run();   // 执行屏障动作
                ranAction = true;
                nextGeneration();                      // 唤醒所有 + 开新一轮
                return 0;
            } finally {
                if (!ranAction) breakBarrier();
            }
        }
        // 不是最后一个 → 在 trip 上 await
        for (;;) {
            try { trip.await(); }
            catch (InterruptedException ie) { /* ... breakBarrier ... */ }
            if (g.broken) throw new BrokenBarrierException();
            if (g != generation) return index;        // 换代了说明本轮完成
        }
    } finally { lock.unlock(); }
}
```
- `nextGeneration()`：`trip.signalAll()`（唤醒所有在 Condition 上等的线程）+ 重置 `count=parties` + 新建 `generation`——这就是"可循环"的实现。
- `breakBarrier()`：`generation.broken=true` + `signalAll`——任一等待线程被中断/超时/屏障动作异常 → 整个屏障 broken，所有等待者抛 `BrokenBarrierException`。

### 与 CountDownLatch 的区别（关键面试点）
| 维度 | CountDownLatch | CyclicBarrier |
| --- | --- | --- |
| 基于 | AQS 共享 | ReentrantLock+Condition（间接 AQS） |
| 重置 | 不可 | 可（cyclic，自动换 generation） |
| 模型 | 一个线程等 N 个完成 | N 个线程互等到齐 |
| barrier action | 无 | 有（最后一个到达的线程执行） |
| broken | 无此概念 | 任一中断/超时 → 全体抛异常 |

### 用法 / 坑
- 多线程分阶段计算：每阶段全员到齐再进下一阶段。
- 一个线程被中断 → 整个屏障 broken，其他等待者全抛 `BrokenBarrierException`。
- `barrierAction` 抛异常 → 屏障 broken。

---

## 六、ThreadPoolExecutor.Worker（AQS 当不可重入锁）

- **Worker extends AbstractQueuedSynchronizer implements Runnable**——直接继承 AQS，但**不是同步器语义**，而是借 AQS 实现一把**不可重入独占锁**。
- **state 语义**：`0` = 未锁，`1` = 已锁。构造时 `setState(-1)` 抑制 runWorker 前的中断。

### `tryAcquire` / `tryRelease`
```java
protected boolean tryAcquire(int unused) {
    return compareAndSetState(0, 1);   // 不可重入：已锁(1)再 tryAcquire 永远失败
}
protected boolean tryRelease(int unused) {
    setState(0);
    return true;
}
```

### 为什么用 AQS 当锁（不是同步器用途）
- `runWorker` 执行任务前 `w.lock()`，执行后 `w.unlock()`——把"正在跑任务"编码成锁状态。
- `shutdown` 时调 `tryLock()`：**成功 = worker 空闲可中断**；**失败 = 正在跑任务**（STOP 才强中断）。
- **不可重入是故意的**：避免任务里调池方法重入锁造成状态混乱。

### 用法 / 坑
- 应用层一般不直接用 Worker；理解它有助于读懂线程池源码（见 [线程池源码解析](concurrency/threadpool-source-analysis)）。

---

## 七、不是基于 AQS 的同步器（澄清常被误认的）

| 同步器 | 是否 AQS | 实现方式 |
| --- | --- | --- |
| Phaser (JDK 7) | ❌ | `volatile long state` + Treiber 栈 + CAS，自实现 |
| Exchanger | ❌ | Slot 数组 + CAS + LockSupport.park |
| StampedLock | ❌ | 自实现（volatile state + 乐观读 + 读锁 CAS + 写锁 CAS），不用 AQS 队列 |
| LongAdder / Striped64 | ❌ | Cell 数组 + CAS |
| CompletableFuture | ❌ | Completion 链表 + CAS + 线程池 |

> StampedLock 是常被误以为基于 AQS 的——它**不是**，自己用 `volatile long state` + 自旋/CAS 实现，没有 AQS 的队列。

## 八、统一记忆框架

学任意一个 AQS 同步器，按这四步看：
1. **state 装什么**（重入数 / 许可 / 计数 / 高低位两个数）。
2. **tryAcquire 怎么算成功**（CAS 改 state 的条件）。
3. **独占还是共享**（决定走 `acquire` 还是 `acquireShared`）。
4. **公平性怎么处理**（`hasQueuedPredecessors` 在哪里挡）。

## 易错点
- 把 CyclicBarrier 当 AQS 子类——它是 ReentrantLock+Condition，间接用。
- 把 StampedLock / Phaser 当 AQS——都不是。
- 读锁尝试升级写锁——死锁。
- Semaphore release 多于 acquire——许可数异常增多。
- CountDownLatch 不 finally countDown——await 永久阻塞。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["concurrency/aqs-principle",
         "concurrency/readwritelock-stampedlock",
         "concurrency/countdownlatch-cyclicbarrier-semaphore",
         "concurrency/synchronized-vs-reentrantlock",
         "concurrency/threadpool-source-analysis"])

print("\nDone: aqs-based-synchronizers catalog")
