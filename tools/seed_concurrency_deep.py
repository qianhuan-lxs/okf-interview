#!/usr/bin/env python3
"""Deep Java concurrency interview docs.

Rewrites 5 shallow docs with source-level depth and adds 12 high-value gap
docs. New docs are general concurrency knowledge (companies=[]), rewrites
preserve original company attribution.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from seed_louis_ai import q

SRC = "_interviews/2026-05-louis-ai-java"
DATE = "2026-07-05"

# =========================================================================== #
# REWRITES (deeper) — same file ids, overwrite
# =========================================================================== #

q("concurrency/aqs-principle.md",
  "AQS 原理 (CLH 变体 / state / Condition / 独占共享)",
  "concurrency", "concurrency", "hard",
  ["aqs", "clh-queue", "juc", "condition", "concurrency"],
  ["北京用友"],
  """# AQS 原理 (CLH 变体 / state / Condition / 独占共享)

## 问题描述

AQS 原理知道吗？为什么它是 JUC 锁的基础框架？独占和共享怎么实现？Condition 是怎么工作的？

## 解答

**AQS (AbstractQueuedSynchronizer)** 是 JUC 锁与同步器的基础框架。`ReentrantLock / Semaphore / CountDownLatch / ReentrantReadWriteLock / CyclicBarrier` 底层都基于它。核心思想：**模板方法模式**——AQS 管队列与 park/unpark，子类只实现 `tryAcquire/tryRelease/tryAcquireShared/tryReleaseShared`。

### 核心结构
- `volatile int state`：同步状态，语义由子类定义。
  - `ReentrantLock`：0=未持有；>0=重入次数（owner 线程独占）。
  - `Semaphore`：剩余许可数。
  - `CountDownLatch`：剩余计数。
  - `ReentrantReadWriteLock`：高 16 位=共享读数，低 16 位=独占写重入数。
- **CLH 变体双向队列**：head / tail 指向哨兵 `Node`。注意 **AQS 的队列不是原版 CLH**——原版 CLH 是单向、自旋、无 park；AQS 改成**双向 + park/unpark + 检查前驱状态**，因此叫 "CLH variant"。
- `Node` 字段：`waitStatus`（CANCELLED=1 / SIGNAL=-1 / CONDITION=-2 / PROPAGATE=-3 / 0 初始）、`prev`、`next`、`thread`、`nextWaiter`（Condition 队列用单向链）。

### 独占获取流程（ReentrantLock 非公平 `nonfairTryAcquire`）
1. `state==0` → CAS 改 1，设 owner=当前线程，返回 true。
2. `owner==当前线程` → `state++`（重入），返回 true。
3. 否则返回 false，进入 `acquireQueued`：
   - `addWaiter(Node.EXCLUSIVE)`：CAS 入队尾，初始化时若 head 为空先 CAS 建哨兵。
   - 自旋 `acquireQueued`：**只有前驱是 head 且 `tryAcquire` 成功**才出队（setHead）；否则 `shouldParkAfterFailedAcquire` 把前驱 waitStatus 设为 SIGNAL，再 `parkAndCheckInterrupt`。
   - 被唤醒后继续自旋尝试。若 park 期间被中断，记录 interrupted，**最后 `selfInterrupt()` 补上中断标志**（AQS 不响应中断但保留标志）。

### 释放（独占）
- `tryRelease`：`state--`，到 0 则清 owner、返回 true。
- `unparkSuccessor`：把 head.waitStatus 清 0，从尾向前找第一个未 CANCELLED 的后继，`LockSupport.unpark`。

### 公平 vs 非公平
- **非公平** `nonfairTryAcquire`：上来就 CAS 抢，允许插队 → 吞吐高（默认）。
- **公平** `fairTryAcquire`：先 `hasQueuedPredecessors()` 检查队列有无前驱，有则排队 → 严格 FIFO、防饿死但慢。
- **为什么默认非公平**：线程切换成本高，非公平让刚释放锁的线程或新来的线程直接抢，减少 park/unpark 开销；代价是队尾线程可能延迟。

### 共享模式（Semaphore / CountDownLatch）
- `tryAcquireShared` 返回 `>=0` 表示成功且可传播；`<0` 表示失败需排队。
- 释放 `doReleaseShared`：**PROPAGATE 机制**——唤醒后继后，若 head 状态变化继续传播，确保多个共享许可被连续获取。
- `CountDownLatch` 的 `tryAcquireShared` 返回 `state==0 ? 1 : -1`——只有计数归零才放行所有等待者。

### ConditionObject（条件变量，重点）
- 每个 `Condition` 是 AQS 内的**独立单向等待队列**（firstWaiter/lastWaiter），与主同步队列分离。
- `await()`：**先释放全部锁（fullyRelease）**→ 把当前线程封装成 CONDITION 节点入 Condition 队列 → `park`。被 `signal` 唤醒后，节点从 Condition 队列**转移到主队列**（`transferForSignal`，状态改 SIGNAL），重新参与抢锁；抢到后恢复原重入数。
- `signal()`：移 firstWaiter，CAS 状态转主队列。
- 这就是 ReentrantLock 能有**多个 Condition** 的原理：一个锁多个等待队列，而 synchronized 的 wait/notify 只有一个。
- **坑**：`await` 必须先 `lock.lock()` 拿到锁（在 lock 块内调），否则 `IllegalMonitorStateException`。

### AQS 不保证可见性的细节
- `state` 是 volatile，子类修改 state 用 CAS 或 volatile 写；节点入队用 CAS tail；这些保证队列操作的可见性与有序性。

## 易错点
- 以为 AQS 队列是普通 FIFO 链表——是带 waitStatus 的 CLH 变体，SIGNAL 决定是否该 park。
- `await()` 没 lock 就调 → `IllegalMonitorStateException`。
- 以为公平锁一定更好——吞吐更低，只在需要防饿死时用。
- 以为 Condition 是同步队列的一部分——它是独立单向队列，signal 时才转移到主队列。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source=SRC, status="reviewed",
  links=["concurrency/synchronized-vs-reentrantlock",
         "concurrency/cas-mechanism",
         "concurrency/thread-pool-principles",
         "concurrency/locksupport-park-unpark",
         "concurrency/readwritelock-stampedlock"])

q("concurrency/synchronized-vs-reentrantlock.md",
  "synchronized vs ReentrantLock 区别 (含锁升级与选型)",
  "concurrency", "concurrency", "hard",
  ["synchronized", "reentrantlock", "lock", "aqs", "juc", "lock-escalation"],
  ["恩士讯", "北京用友"],
  """# synchronized vs ReentrantLock 区别 (含锁升级与选型)

## 问题描述

说一下 synchronized 和 ReentrantLock 的区别？你知道 AQS 原理吗？synchronized 的锁升级过程？

## 解答

| 维度 | synchronized | ReentrantLock |
| --- | --- | --- |
| 性质 | JVM 关键字（`monitorenter`/`monitorexit`） | JDK 类（`java.util.concurrent.locks`） |
| 实现 | 对象头 MarkWord + Monitor，重量级走 ObjectMonitor（C++ ObjectWaiter/ObjectMonitor） | AQS（CLH 变体 + volatile state + FIFO 队列） |
| 公平性 | 非公平（不可配） | 可配 `fair`/`nonfair` |
| 中断 | 不可中断 | `lockInterruptibly()` 可响应中断 |
| 超时 | 不支持 | `tryLock(timeout)` |
| 条件变量 | 单条件（`wait`/`notify`） | 多 `Condition`（独立等待队列） |
| 释放 | 自动（出块/异常，JVM 保证 monitorexit） | 必须 `finally { unlock() }`，否则死锁 |
| 锁状态查询 | 不可查 | `isLocked()` / `getHoldCount()` / `getQueueLength()` |
| 锁升级 | 偏向→轻量→重量（JVM 自动） | 无升级，直接 AQS 队列 |
| 性能 | JDK6+ 优化后接近 ReentrantLock | 高竞争下略优 |

### synchronized 锁升级（高频追问，详见 [锁升级专篇](concurrency/synchronized-lock-escalation)）
- **无锁→偏向锁→轻量锁→重量锁**，记录在对象头 MarkWord。
- 偏向锁：单线程访问，CAS 设线程 ID，无同步开销。竞争出现 → 升级。
- 轻量锁：竞争但不剧烈，CAS 自旋（自适应自旋）。自旋失败 → 升级。
- 重量锁：走 ObjectMonitor，OS mutex，线程 park。
- JDK 15+ 偏向锁默认禁用（标记位不再用），因收益递减。

### AQS 原理（追问要点，详见 [AQS 专篇](concurrency/aqs-principle)）
- `volatile int state` + CLH 变体双向队列。
- 独占：`tryAcquire` CAS 改 state，失败入队 park，前驱唤醒重试。
- 共享：`tryAcquireShared`，state 表示许可（Semaphore/CountDownLatch）。
- Condition 是独立单向队列，`await` 释放锁入队，`signal` 转移到主队列。

### 选型
- 简单同步、不需可中断/超时/多条件 → **synchronized**（语法糖，自动释放，JVM 优化足）。
- 需公平/中断/超时/多条件/可观测/与 AQS 生态配合 → **ReentrantLock**。
- 高并发读多写少 → **ReentrantReadWriteLock** 或 **StampedLock**。

## 易错点
- ReentrantLock 忘 `finally unlock` → 异常路径死锁。
- 以为 synchronized 一定慢 → JDK6 锁升级后差距很小，简单场景反而更优。
- `wait()/notify()` 在 ReentrantLock 上调 → 必须用 `Condition.await()/signal()`，否则 `IllegalMonitorStateException`。
- ReentrantLock 设 `fair=true` 但 `tryLock()` 无参仍插队 → `tryLock()` 不看队列公平性。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source=SRC, status="reviewed",
  links=["concurrency/aqs-principle",
         "concurrency/cas-mechanism",
         "concurrency/synchronized-lock-escalation",
         "concurrency/readwritelock-stampedlock"])

q("concurrency/thread-pool-principles.md",
  "线程池运行原理 (ctl 高低位 / execute 流程 / Worker / 钩子)",
  "concurrency", "concurrency", "hard",
  ["thread-pool", "juc", "threadpoolexecutor", "concurrency"],
  ["有赞"],
  """# 线程池运行原理 (ctl 高低位 / execute 流程 / Worker / 钩子)

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
""",
  languages=["java"], role=["sde", "backend"],
  source=SRC, status="reviewed",
  links=["concurrency/threadlocal-threadpool-problems",
         "concurrency/aqs-principle",
         "concurrency/completablefuture-async-orchestration"])

q("concurrency/cas-mechanism.md",
  "CAS 机制 (cmpxchg + lock 前缀 / Unsafe / ABA / LongAdder)",
  "concurrency", "concurrency", "hard",
  ["cas", "compare-and-swap", "atomic", "aba", "unsafe", "varhandle"],
  ["有赞", "探迹", "北京用友"],
  """# CAS 机制 (cmpxchg + lock 前缀 / Unsafe / ABA / LongAdder)

## 问题描述

你对 CAS 怎么理解？底层怎么保证原子性？ABA 问题真实危害？高竞争下怎么办？

## 解答

**CAS (Compare-And-Swap)**：无锁原子操作。三参数 `(V, A, B)`——仅当 `V==A` 时把 `V` 改为 `B`，否则返回当前值。是乐观锁、无锁数据结构的基石。

### 底层原子性保证（重点）
- **x86**：`lock cmpxchg` 指令。`cmpxchg` 本身非原子的（读-比较-写三步），但加 **`lock` 前缀** → 锁总线或锁缓存行（MESI 协议 + cache line lock），保证整条指令原子。
- **ARM/PowerPC**：LL-SC（Load-Linked / Store-Conditional）循环，硬件层面"乐观"——若期间缓存行被改则 SC 失败，重试。
- **Java 层**：`sun.misc.Unsafe.compareAndSwapXxx`（JDK 9 前）/ `VarHandle.compareAndSet`（JDK 9+，标准 API）。最终走 native → CPU 指令。
- `AtomicInteger.compareAndSet` → `Unsafe.compareAndSwapInt` → JNI → `cmpxchg`。

### 为什么需要 CAS
- `synchronized` 太重（系统调用、上下文切换、OS mutex）。
- 高并发低竞争场景，CAS 自旋无锁、无线程切换，性能远优于阻塞锁。

### Java 中的 CAS
- `AtomicInteger / AtomicLong / AtomicReference / AtomicStampedReference`。
- AQS 的 `state` 修改、`ConcurrentHashMap` 节点插入、`LongAdder` 的 Cell 累加都用 CAS。
- `VarHandle`（JDK 9+）是标准替代 Unsafe 的 API，支持字段内存序（`OPAQUE`/`VOLATILE`/`ACQUIRE`/`RELEASE`）。

### ABA 问题（真实危害场景）
- 线程 1 读到 A，线程 2 把 A→B→A，线程 1 CAS 仍成功——值"看起来"没变，但中间状态已变化。
- **危害场景**：无锁栈。线程 1 准备 CAS 顶 `A`→下一个 `B`，被抢占；线程 2 pop A、pop B、push A（A 的 next 已变）。线程 1 恢复 CAS 成功，但此时栈顶 A 的 next 已是 null 或悬空 → 栈结构破坏。
- **解法**：
  - `AtomicStampedReference`：加 int stamp 版本号，CAS 必须匹配 `(expectedRef, expectedStamp)`。
  - `AtomicMarkableReference`：boolean 标记（更轻，仅二态）。
  - GC 隐式缓解：对象引用版本变化伴随新对象分配，但**不解决同一对象被复用**的情况。

### 自旋开销与高竞争解法
- 高竞争下 CAS 自旋空耗 CPU，吞吐反而比 synchronized 差。
- **`LongAdder`**：分段累加。`base` + `Cell[]`，线程 hash 到不同 Cell 各自 CAS，`sum()` 时求和。极高并发下热点分散，吞吐数倍于 `AtomicLong`。代价：`sum()` 非精确瞬时值（遍历期间可能变化）。
- **`LongAccumulator`**：LongAdder 泛化版，可传自定义累加函数。
- **自旋退避**：限制重试次数 / `Thread.onSpinWait()`（JDK 9+，提示 CPU 自旋等待，x86 发 `PAUSE` 降功耗防乱序）。
- **极高竞争下反而 `synchronized`/ReentrantLock 更优**——排队阻塞而非空转，JVM 锁升级到重量锁走 park。

### CAS 与 volatile 的关系
- `AtomicInteger.value` 是 volatile，保证读的可见性；CAS 保证写原子。两者结合才完整。

## 易错点
- 把 CAS 当万能 → 高竞争退化为自旋空耗。
- 以为 ABA 只是理论 → 无锁链表/栈场景会真实破坏结构。
- 以为 `AtomicReference` 能防 ABA → 不能，要用 `AtomicStampedReference`。
- `LongAdder.sum()` 当精确快照 → 它是估算求和，期间 Cell 仍在变。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source=SRC, status="reviewed",
  links=["concurrency/aqs-principle",
         "concurrency/synchronized-vs-reentrantlock",
         "concurrency/longadder-vs-atomiclong",
         "concurrency/volatile-principle"])

q("concurrency/threadlocal-usage-pitfalls.md",
  "ThreadLocal 用法陷阱 (内存泄漏 / 弱引用 key / 回收)",
  "concurrency", "concurrency", "hard",
  ["threadlocal", "memory-leak", "weak-reference", "concurrency"],
  ["安克创新", "有赞"],
  """# ThreadLocal 用法陷阱 (内存泄漏 / 弱引用 key / 回收)

## 问题描述

ThreadLocal 为什么会内存泄漏？key 是弱引用为什么还会泄漏？怎么解决？为什么要用 `remove()`？

## 解答

### 结构
- **每个 `Thread` 持有 `ThreadLocalMap`**（不是 ThreadLocal 自己持有 Map，方向反了）。
- `ThreadLocalMap` 的 entry 是 `WeakReference<ThreadLocal>` 当 key，value 是强引用。
- 每个 ThreadLocal 实例的 `threadLocalHashCode` 决定其在数组中的槽位（开放定址法，非 HashMap 的链表法）。

### 为什么 key 用弱引用
- 防止 ThreadLocal 对象本身泄漏：当外部 ThreadLocal 引用消失（如方法栈出栈），GC 能回收 key。
- 但 **value 是强引用**——这是泄漏根源。

### 泄漏场景（核心面试点）
- 线程池场景：**线程长期存活**，ThreadLocalMap 也长期存活。
- ThreadLocal 外部引用消失 → key 被 GC 回收 → entry 变成 `(null, value)`（stale entry）。
- **value 强引用链**：`Thread → ThreadLocalMap → Entry.value → 大对象`。只要线程不死，value 永远不被回收 → 泄漏。
- 弱引用 key 只防"ThreadLocal 对象本身"泄漏，**不防 value 泄漏**。

### 为什么 set/get/cleanStaleEntry 不够
- ThreadLocal 源码在 `set`/`get`/`remove` 时会扫到 key==null 的 stale entry 做 `value=null` 清理（`expungeStaleEntry` / `replaceStaleEntry`）。
- **但**：只在访问到那个槽位时才清理，不访问就一直堆着。线程池长任务可能长期不触发清理。

### 解法（必答）
1. **`finally { threadLocal.remove(); }`**——最根本，显式断 value 引用。用完即清。
2. **线程池场景务必 remove**——线程复用，ThreadLocalMap 跟着复用，上轮残留污染下一轮。
3. 不要用 `static ThreadLocal` 长期持有大 value（生命周期被拉到类级）。
4. 谨慎用 `InheritableThreadLocal`——子线程继承父线程的 value，线程池下父子关系混乱。

### 阿里规约
- ThreadLocal 必须在 `finally` 中 `remove()`，尤其线程池场景。

### 真实应用场景
- **Spring `RequestContextHolder`**：HTTP 请求线程绑定 RequestContext，请求结束清理。
- **`TransactionSynchronizationManager`**：事务资源绑定到当前线程（Connection）。
- **`SimpleDateFormat` 线程安全**：SimpleDateFormat 非线程安全，用 `ThreadLocal<SimpleDateFormat>` 每线程一份。
- **MDC（日志链路追踪）**：`MDC.put(traceId)` 存链路 ID，日志输出时取。

## 易错点
- 以为弱引用 key 就不泄漏了 → value 是强引用，照样漏。
- 忘 `remove()`，尤其线程池 → 下一轮任务读到上一轮残留。
- 用 `ThreadLocal` 当全局变量缓存大对象且不清理 → 线程池 OOM。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source=SRC, status="reviewed",
  links=["concurrency/threadlocal-threadpool-problems",
         "concurrency/thread-pool-principles",
         "concurrency/volatile-principle"])

# =========================================================================== #
# NEW (12 high-value gap docs) — general concurrency knowledge
# =========================================================================== #

q("concurrency/volatile-principle.md",
  "volatile 原理 (JMM / happens-before / 内存屏障 / DCL)",
  "concurrency", "concurrency", "hard",
  ["volatile", "jmm", "memory-barrier", "happens-before", "concurrency"],
  [],
  """# volatile 原理 (JMM / happens-before / 内存屏障 / DCL)

## 问题描述

volatile 的原理？能保证什么不能保证什么？为什么 DCL 单例的实例字段要 volatile？volatile 和 synchronized 区别？

## 解答

### volatile 两大语义
1. **可见性**：写 volatile 变量 → 刷新到主内存；读 volatile 变量 → 从主内存重新加载，不缓存到工作内存（CPU 缓存/寄存器）。一写多读立即可见。
2. **禁止指令重排**：在 volatile 读/写前后插入**内存屏障**，阻止编译器与 CPU 重排跨 volatile 的指令。

### volatile 不能保证什么
- **不保证原子性**。`i++` 是读-改-写三步，volatile 只保证每步可见，但三步之间可被打断 → 多线程下仍丢更新。要原子用 `AtomicInteger` 或 `synchronized`。
- 只能用在"一写多读"的标志位/状态发布场景。

### 内存屏障（底层）
- JSR-133 规范的屏障规则：
  - volatile 写前插入 `StoreStore`（禁止前面普通写与 volatile 写重排）。
  - volatile 写后插入 `StoreLoad`（禁止 volatile 写与后面 volatile 读/写重排，最重）。
  - volatile 读后插入 `LoadLoad` + `LoadStore`（禁止后面普通读/写与 volatile 读重排）。
- x86 上 volatile 写实际生成 `lock addl $0,0,(%rsp)` 或 `lock cmpxchg`——`lock` 前缀既保证原子又充当全屏障。所以 x86 上 volatile 写较便宜，volatile 读几乎免费（TSO 内存模型）。

### happens-before（详见 [JMM 专篇](concurrency/jmm-happens-before)）
- volatile 写 happens-before 后续 volatile 读。这是 volatile 可见性的 JMM 层保证。
- volatile 写前的所有普通写，对 volatile 读后的所有普通读可见（因为 StoreStore + LoadLoad 屏障）。

### DCL 单例为什么必须 volatile（高频）
```java
class Singleton {
    private static volatile Singleton instance;  // 必须 volatile
    public static Singleton getInstance() {
        if (instance == null) {
            synchronized (Singleton.class) {
                if (instance == null) {
                    instance = new Singleton();  // 非原子
                }
            }
        }
        return instance;
    }
}
```
- `instance = new Singleton()` 在字节码层是三步：
  1. 分配内存
  2. 调构造器初始化对象
  3. 把引用指向内存地址
- **没有 volatile 时，2 和 3 可能被重排**（JIT 优化），变成 1→3→2。
- 线程 A 执行到 3（已赋值但未初始化），线程 B 第一次 `if (instance == null)` 看到**非 null 但未初始化的对象**，直接 return → 用到半个对象 → NPE 或脏值。
- volatile 禁止 2、3 重排，保证对象完全构造好后才发布。

### volatile 与 synchronized 区别
| 维度 | volatile | synchronized |
| --- | --- | --- |
| 原子性 | ❌（单次读/写原子，复合操作不原子） | ✅ |
| 可见性 | ✅ | ✅ |
| 有序性 | ✅（禁止重排） | ✅（临界区串行） |
| 阻塞 | 不阻塞 | 阻塞 |
| 粒度 | 变量级 | 块/方法级 |
| 适用 | 一写多读标志位、安全发布 | 复合操作临界区 |

## 易错点
- volatile 当原子计数器用 → 多线程 `i++` 丢更新。
- DCL 单例不加 volatile → 偶发拿到半初始化对象。
- 以为 volatile 写一定贵 → x86 上 `lock` 前缀成本可接受，读几乎免费。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed",
  links=["concurrency/jmm-happens-before",
         "concurrency/dcl-singleton-volatile-why",
         "concurrency/synchronized-vs-reentrantlock",
         "concurrency/cas-mechanism"])

q("concurrency/jmm-happens-before.md",
  "JMM 与 happens-before 八大原则",
  "concurrency", "concurrency", "hard",
  ["jmm", "happens-before", "memory-model", "concurrency", "java"],
  [],
  """# JMM 与 happens-before 八大原则

## 问题描述

什么是 Java 内存模型 (JMM)？happens-before 是什么？有哪些规则？为什么需要它？

## 解答

### 为什么需要 JMM
- 真实硬件：CPU 多级缓存 + 寄存器 + 指令重排 + 写缓冲区 → 每个线程"看到"的内存视图不一致。
- 没有内存模型，多线程程序行为不可预测（不同 CPU 架构结果不同）。
- **JSR-133 (JMM)** 定义了一套抽象规则，规定在什么条件下一个线程的写对另一个线程可见，以及编译器/CPU 能怎么重排。

### JMM 抽象结构
- **主内存** vs **工作内存**（抽象，对应 CPU 缓存/寄存器）。
- 线程不能直接读写主内存，必须经过工作内存：`read`/`load`/`use`/`assign`/`store`/`write`/`lock`/`unlock` 八大原子操作。
- 这套操作描述太底层，JSR-133 用 **happens-before** 替代表达。

### happens-before 八大规则（必背）
如果一个操作 A happens-before B，则 A 的结果对 B 可见，且 A 的执行顺序先于 B（**语义顺序，不是实际指令顺序**——只要不改变结果，CPU/编译器可重排）。

1. **程序顺序规则**：同一线程内，前面的操作 happens-before 后面的操作（as-if-serial）。
2. **volatile 变量规则**：volatile 写 happens-before 后续对该变量的读。
3. **锁规则（monitor lock）**：unlock happens-before 后续对同一把锁的 lock。
4. **线程启动规则**：`Thread.start()` happens-before 该线程的所有操作（所以启动前赋值的变量对新线程可见）。
5. **线程终止规则**：线程所有操作 happens-before `Thread.join()` 返回（所以 join 后能读到子线程结果）。
7. **线程中断规则**：`Thread.interrupt()` happens-before 被中断线程检测到中断。
7. **对象终结规则**：构造函数执行结束 happens-before `finalize()`。
8. **传递性**：A happens-before B，B happens-before C → A happens-before C。

> 注：编号按 JSR-133 通行表述，实际是 8 条（程序顺序/volatile/锁/启动/终止/中断/终结/传递性）。

### happens-before 不是"执行时序"
- 不是说 A 一定先执行完再执行 B，而是说 **A 的效果对 B 可见，且 A 不被重排到 B 之后**。
- 编译器/CPU 仍可重排，只要不违反 happens-before 关系（结果一致）。

### 实战推导
- 双重检查锁（DCL）：构造函数初始化 `happens-before` 把引用赋给 `instance`（程序顺序规则）→ 加 volatile 后赋值 `happens-before` 外部读（volatile 规则）→ 传递性 → 外部读到完全初始化的对象。

## 易错点
- 把 happens-before 当"执行先后" → 是可见性 + 重排约束，不是时序。
- 忘了传递性 → 无法跨多条规则推导可见性。
- 以为线程 start 前的赋值不可见 → 启动规则保证可见。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed",
  links=["concurrency/volatile-principle",
         "concurrency/synchronized-vs-reentrantlock",
         "concurrency/dcl-singleton-volatile-why"])

q("concurrency/synchronized-lock-escalation.md",
  "synchronized 锁升级 (偏向/轻量/重量 + MarkWord)",
  "concurrency", "concurrency", "hard",
  ["synchronized", "lock-escalation", "markword", "jvm", "concurrency"],
  [],
  """# synchronized 锁升级 (偏向/轻量/重量 + MarkWord)

## 问题描述

synchronized 的锁升级过程？MarkWord 怎么记录锁状态？为什么 JDK 15 默认禁用偏向锁？

## 解答

### 锁升级路径
```
无锁 → 偏向锁 → 轻量级锁 → 重量级锁
```
**不可降级**（理论上 GC safepoint 时可批量撤销重偏向，但运行期不降级）。升级记录在**对象头 MarkWord**。

### 对象头 MarkWord（64 位 JVM）
- 64 bit，不同锁状态占用不同字段：
  - **无锁**：25 bit hash + 31 bit 分代年龄 + 1 bit biased 标志 + 2 bit 锁标志位(01)。
  - **偏向锁**：54 bit 线程 ID + 2 bit epoch + 1 bit 年龄 + 1 bit biased(1) + 2 bit 锁标志(01)。
  - **轻量锁**：62 bit 指向栈中 Lock Record 的指针 + 2 bit 锁标志(00)。
  - **重量锁**：62 bit 指向 ObjectMonitor 的指针 + 2 bit 锁标志(10)。
- 锁标志位区分状态，biased 标志位区分无锁/偏向。

### 偏向锁（Biased Locking）
- **场景**：单线程反复进入同步块。
- **机制**：首次进入 CAS 把线程 ID 写入 MarkWord。之后同一线程进出只需对比 ID，无 CAS、无自旋。
- **撤销**：另一线程来竞争 → 等全局安全点（safepoint）→ 撤销偏向，升级轻量锁。
- **批量重偏向 / 批量撤销**：同一类对象撤销到阈值（默认 20 次重偏向、40 次撤销）会批量处理，避免逐个撤销开销。
- **JDK 15 默认禁用**（JEP 374）：现代多线程应用偏向锁收益递减（多核 + 并发普遍），撤销的 safepoint STW 开销反而拖累。`-XX:+UseBiasedLocking` 仍可开，但废弃中。

### 轻量级锁（Lightweight / Thin Lock）
- **场景**：多线程交替进入，竞争不剧烈、持有时间短。
- **机制**：
  1. 当前栈帧建 Lock Record，拷贝对象 MarkWord（displaced mark word）。
  2. CAS 把 MarkWord 改为指向 Lock Record 的指针。成功 → 持锁。
  3. 失败 → 自旋（**自适应自旋**，根据历史成功率动态调整次数）。
  4. 自旋仍失败 → 升级重量锁，MarkWord 改指向 ObjectMonitor。
- 释放：CAS 把 displaced mark word 写回。若有竞争（CAS 失败）→ 说明有自旋等待者 → 唤醒。

### 重量级锁（Heavyweight / Inflated Lock）
- **场景**：竞争剧烈、持有时间长。
- **机制**：MarkWord 指向 `ObjectMonitor`（C++）。未抢到的线程进入 `_EntryList`，OS mutex 阻塞（`pthread_mutex` / `futex`）。
- 进入 `_Owner` 持锁；`wait()` 进 `_WaitSet`；`notify` 移回 `_EntryList`。
- 开销：系统调用 + 上下文切换 + 内核态切换。

### 自适应自旋
- 自旋次数不固定：上次自旋成功 → 这次多自旋；上次失败 → 减少或跳过自旋。
- 避免"自旋到底空耗"和"完全不自旋多一次 park"两个极端。

## 易错点
- 以为锁能降级 → 不能（运行期只升不降）。
- 以为偏向锁默认开 → JDK 15+ 默认禁。
- 把"轻量锁"等同 CAS 无锁 → 它有自旋，竞争一剧烈就膨胀。
- 以为 MarkWord 改了 hash 就坏了 → 偏向锁会覆盖 hash，所以 `hashCode()` 调用会触发偏向撤销。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed",
  links=["concurrency/synchronized-vs-reentrantlock",
         "concurrency/aqs-principle",
         "concurrency/cas-mechanism"])

q("concurrency/concurrenthashmap-principle.md",
  "ConcurrentHashMap 原理 (1.7 vs 1.8 / sizeCtl / 转移节点)",
  "concurrency", "concurrency", "hard",
  ["concurrenthashmap", "juc", "cas", "synchronized", "concurrency"],
  [],
  """# ConcurrentHashMap 原理 (1.7 vs 1.8 / sizeCtl / 转移节点)

## 问题描述

ConcurrentHashMap 1.7 和 1.8 实现区别？为什么 1.8 改用 CAS + synchronized？扩容怎么做？sizeCtl 是什么？

## 解答

### JDK 1.7：Segment 分段锁
- 结构：`Segment[]`（默认 16 段，继承 ReentrantLock）+ 每段内 `HashEntry[]` 链表。
- 并发度 = Segment 数（16，创建后不可扩）。
- 写：锁单个 Segment（`lock()`），其他 Segment 不阻塞。
- 读：volatile 读 `HashEntry.value`，**不加锁**（首节点 volatile）。
- 扩容：段内独立扩容。
- 缺点：并发度固定、Segment 重、内存占用大。

### JDK 1.8：CAS + synchronized + 链表/红黑树
- 结构：`Node[] table`（无 Segment），槽位是链表或红黑树（链表 ≥8 且容量 ≥64 转树；扩容或元素减少回退链表）。
- 写（`put`）：
  1. 空槽位 → **CAS 插入首节点**（无锁）。
  2. 非空槽位 → **`synchronized` 锁住首节点**，链表尾插或红黑树插入。
  3. 检查扩容。
- 读（`get`）：volatile 读 table 槽位首节点，沿链/树找，**不加锁**。
- 并发度 = 桶数（默认 16，随扩容增大），远高于 1.7。

### 为什么 1.8 弃 Segment
- synchronized 在 JDK 6+ 锁升级后性能不输 ReentrantLock，且内存更省（无 AQS 队列开销）。
- 桶粒度锁比段粒度锁并发度更高。
- CAS 处理空槽，synchronized 处理非空槽，分工最优。

### sizeCtl（核心控制变量）
- `volatile int sizeCtl`：
  - `-1` → 正在初始化。
  - `-(1 + N)` → 有 N 个线程正在扩容（`-N`，N 个 resize 线程）。
  - 正数 → 下次扩容的阈值（初始 = 容量 × 0.75）。
- 初始化：CAS 把 sizeCtl 从 0/正数改 -1，独占初始化，完后设回阈值。
- 扩容：触发时 CAS 调整 sizeCtl 协调多线程并发扩容。

### 多线程并发扩容（亮点）
- 1.8 CHM 扩容**多线程协助**：每个线程领取一段 stride（默认最小 16 桶），从后往前迁移。
- 迁移完一个桶，在旧表该槽放 **`ForwardingNode`（hash=MOVED=-1）**：`get` 遇到它转去新表查；`put` 遇到它 → 协助扩容。
- `transfer` 协调：线程领完 stride 或发现全部领完就退出；最后一个线程收尾建新表。
- 迁移时拆分链表：原链按 `hash & oldCap` 拆成两条（低位链留原 index，高位链去 index+oldCap），无需重 hash。

### 计数 size()
- `baseCount` + `CounterCell[]`（类似 LongAdder 分段计数），高并发分散热点。
- `size()` = baseCount + Σ CounterCell，**非精确瞬时值**。

## 易错点
- 以为 1.8 完全无锁 → 非空桶用 synchronized。
- 以为 size 精确 → 是估算，并发下可能偏。
- put 返回 null 当成功 → 也可能是该 key 原值为 null，要看 `containsKey`。
- 1.7 的并发度 16 是写并发度，不是读。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed",
  links=["concurrency/cas-mechanism",
         "concurrency/synchronized-vs-reentrantlock",
         "concurrency/longadder-vs-atomiclong",
         "concurrency/aqs-principle"])

q("concurrency/readwritelock-stampedlock.md",
  "ReentrantReadWriteLock / StampedLock (读写锁 + 乐观读)",
  "concurrency", "concurrency", "hard",
  ["readwritelock", "stampedlock", "aqs", "optimistic-read", "concurrency"],
  [],
  """# ReentrantReadWriteLock / StampedLock (读写锁 + 乐观读)

## 问题描述

读写锁怎么实现？读写锁有什么问题？StampedLock 的乐观读怎么解决？什么时候用 StampedLock？

## 解答

### ReentrantReadWriteLock（基于 AQS）
- **state 高低位复用**：高 16 位 = 共享读次数（多个读者），低 16 位 = 独占写重入数（最多一个写者）。
- 读锁 `tryAcquireShared`：写锁未被持（低 16 位=0）且读者数未超上限 → CAS 高 16 位 +1。
- 写锁 `tryAcquire`：state==0 或 owner==当前线程（重入）→ CAS 低 16 位 +1。
- **支持重入**：读者可再读，写者可重入写、也可"锁降级"（持写锁时再获取读锁，再释放写锁）。
- **不支持锁升级**：持读锁时不能直接拿写锁（会死锁——写锁等所有读者释放，而自己就是读者）。

### 读写锁的问题
1. **写饥饿**：读多写少场景，读者源源不断，写者永远等不到所有读者释放 → 写饿死。
   - 解法：公平模式（写者优先排队）或写锁设超时。
2. **读不可并发升级**。
3. 高并发读时 CAS 改高 16 位竞争激烈（同一 state 字段）。

### StampedLock（JDK 8，乐观读）
- 三种模式：**写锁 / 悲观读锁 / 乐观读**。
- **乐观读（核心）**：
  ```java
  long stamp = lock.tryOptimisticRead();   // 读一个 stamp，不加锁
  // ... 读数据到本地变量 ...
  if (!lock.validate(stamp)) {             // 期间有写？
      stamp = lock.readLock();             // 升级悲观读锁
      try { /* 重新读 */ } finally { lock.unlockRead(stamp); }
  }
  ```
- `validate` 是**轻量级**：仅检查 stamp 对应的版本是否变化（volatile 读 + 屏障），不加锁不阻塞。
- 乐观读期间若无写，**全程零开销**（无 CAS、无队列）；有写才升级悲观读重试。
- **不可重入**：同一线程重复 `readLock` 会死锁。所以**不用在嵌套场景**。
- 写锁、悲观读锁用法类似 ReentrantReadWriteLock。

### 三者对比
| 维度 | synchronized | ReentrantReadWriteLock | StampedLock |
| --- | --- | --- | --- |
| 读写分离 | ❌ | ✅ | ✅ |
| 乐观读 | ❌ | ❌ | ✅ |
| 可重入 | ✅ | ✅ | ❌ |
| 写饥饿缓解 | — | 公平模式 | 乐观读不阻塞写 |
| 适用 | 简单临界 | 读多写少、需重入 | 读多写少、不重入、极致性能 |

### 何时用 StampedLock
- 读远多于写、且不重入、不需 Condition → StampedLock 乐观读性能最优。
- 需要重入 / Condition / 普遍场景 → ReentrantReadWriteLock 更安全。
- 简单同步 → synchronized。

## 易错点
- StampedLock 当可重入用 → 同线程重复 readLock 死锁。
- 持读锁尝试升级写锁 → 死锁（锁升级不支持）。
- 乐观读不 validate 直接用 → 读到中间态脏数据。
- 乐观读升级悲观读后忘 unlock → 锁泄漏。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed",
  links=["concurrency/aqs-principle",
         "concurrency/synchronized-vs-reentrantlock",
         "concurrency/cas-mechanism"])

q("concurrency/countdownlatch-cyclicbarrier-semaphore.md",
  "CountDownLatch / CyclicBarrier / Semaphore 区别",
  "concurrency", "concurrency", "medium",
  ["countdownlatch", "cyclicbarrier", "semaphore", "juc", "concurrency"],
  [],
  """# CountDownLatch / CyclicBarrier / Semaphore 区别

## 问题描述

CountDownLatch、CyclicBarrier、Semaphore 三个同步器区别？各自适用场景？

## 解答

| 维度 | CountDownLatch | CyclicBarrier | Semaphore |
| --- | --- | --- | --- |
| 基于 | AQS 共享 | AQS 共享 + ReentrantLock Condition | AQS 共享 |
| 计数 | 不可重置（一次性） | 可重置（cyclic） | 许可数，可增减 |
| 动作 | 一个线程等多 N 个完成 | N 个线程互相等到达屏障点 | 控制并发访问数 |
| 释放 | 计数归零自动放行 | 全到后全部放行 + 可执行 barrier action | acquire 拿许可，release 还 |
| 不可重用 | ✅ 一次性 | ❌ 可循环 | — |

### CountDownLatch
- `countDown()` 每次使 state -1；`await()` 阻塞到 state==0。
- **不可重置**——countDown 完就废。要循环用得新建。
- 场景：主线程等 N 个子任务完成（如多服务并行加载后汇总）；启动时等多个依赖就绪。
- 基于 AQS 共享：`tryAcquireShared` 返回 `state==0 ? 1 : -1`。

### CyclicBarrier
- `await()` 到达屏障点阻塞，等 parties 个线程都到 → 全部释放；**自动重置**计数，可再次 await（cyclic）。
- 可指定 `barrierAction`：所有线程到齐后、释放前执行一个动作（最后一个到的线程执行）。
- `BrokenBarrierException`：任一等待线程被中断或超时 → 屏障 broken，所有等待者抛异常。
- 场景：多线程分阶段计算，每阶段全员到齐再进下一阶段（如多阶段批处理、并行算法的同步步）。
- 实现是 `ReentrantLock` + `Condition` + `Generation`（每次重置换 generation）。

### Semaphore
- `acquire()` 拿许可（state -1），不够则阻塞；`release()` 还许可（state +1）。
- **可公平可非公平**（`new Semaphore(permits, fair)`）。
- 场景：限流（接口并发数上限）、资源池（连接池大小）、限制并发访问。
- 注意：`release()` 可以不配对 acquire（释放多于获取）→ 实际增加许可数，慎用。

### 选型
- 等 N 个完成 → CountDownLatch。
- N 个互等到齐再继续 → CyclicBarrier。
- 限并发数 → Semaphore。

## 易错点
- 想循环等待却用 CountDownLatch → 不可重置，得重建。
- Semaphore release 多于 acquire → 许可数越界增多。
- CyclicBarrier 一个线程被中断 → 整个屏障 broken，全抛异常。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed",
  links=["concurrency/aqs-principle",
         "concurrency/completablefuture-async-orchestration",
         "concurrency/thread-pool-principles"])

q("concurrency/completablefuture-async-orchestration.md",
  "CompletableFuture 异步编排",
  "concurrency", "concurrency", "medium",
  ["completablefuture", "async", "juc", "concurrency", "future"],
  [],
  """# CompletableFuture 异步编排

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
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed",
  links=["concurrency/thread-pool-principles",
         "concurrency/forkjoinpool-parallelstream",
         "concurrency/countdownlatch-cyclicbarrier-semaphore"])

q("concurrency/deadlock-detection-prevention.md",
  "死锁四条件 + 排查 + 避免",
  "concurrency", "concurrency", "medium",
  ["deadlock", "jstack", "lock-ordering", "concurrency"],
  [],
  """# 死锁四条件 + 排查 + 避免

## 问题描述

死锁的四个必要条件？怎么排查？怎么避免？

## 解答

### 四个必要条件（Coffman）
1. **互斥**：资源同一时刻只能一个进程/线程用。
2. **持有并等待**：持着资源 A 又请求资源 B。
3. **不可剥夺**：资源不能强行抢，只能自愿释放。
4. **循环等待**：存在线程链 T1 等 T2 持的资源、T2 等 T3……Tn 等 T1。

破坏任一条件即可避免死锁。

### 经典场景
```java
// 线程1
synchronized(A) { synchronized(B) { ... } }
// 线程2
synchronized(B) { synchronized(A) { ... } }
```
循环等待：T1 持 A 等 B，T2 持 B 等 A。

### 排查
- **`jstack <pid>`**：直接看 "Found one Java-level deadlock" 段，列出死锁链和持有/等待的锁。
- **`jconsole` / `VisualVM`**：图形界面看线程标签页的 deadlock 检测。
- **`ThreadMXBean.findDeadlockedThreads()`**：代码内检测，可埋点告警。
- 日志特征：线程长期 BLOCKED，且 `waiting to lock <0x...addr>` 与 `locked <0x...addr>` 形成环。

### 避免策略
1. **锁顺序**：全系统约定按固定顺序获取锁（如按锁对象 hash 排序）→ 破坏循环等待。最实用。
2. **锁超时**：`tryLock(timeout)` 拿不到就回退或释放已有锁重试 → 破坏不可剥夺。
3. **一次性获取所有锁**：用 `tryLock` 同时锁多把，失败全部释放重试（带随机退避防活锁）。
4. **粗粒度锁 / 单锁**：用一个锁代替多把 → 破坏持有并等待（牺牲并发度）。
5. **无锁数据结构**：CAS / `Atomic*` / `ConcurrentHashMap` → 破坏互斥。
6. **更高层抽象**：用 `Semaphore`/`CompletableFuture` 编排，避免手动多锁嵌套。

### 活锁与饥饿
- **活锁**：线程不阻塞但一直重试失败（互相让步退避相同）→ 加随机退避。
- **饥饿**：优先级/公平性问题导致某线程长期拿不到锁 → 用公平锁或限流队列。

## 易错点
- 锁顺序按 hash 排序但两对象 hash 相同（碰撞）→ 用 `System.identityHashCode` 仍可能同；终极方案：再加一把 tie-break 锁。
- `tryLock` 拿到后忘 `unlock` → 锁泄漏。
- 死锁不抛异常、不报错，进程"卡住"——靠监控 + jstack 才发现。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed",
  links=["concurrency/synchronized-vs-reentrantlock",
         "concurrency/aqs-principle",
         "concurrency/thread-pool-principles"])

q("concurrency/longadder-vs-atomiclong.md",
  "LongAdder vs AtomicLong (分段累加 Cell)",
  "concurrency", "concurrency", "medium",
  ["longadder", "atomiclong", "cas", "juc", "concurrency"],
  [],
  """# LongAdder vs AtomicLong (分段累加 Cell)

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
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed",
  links=["concurrency/cas-mechanism",
         "concurrency/concurrenthashmap-principle",
         "concurrency/false-sharing-contended"])

q("concurrency/dcl-singleton-volatile-why.md",
  "DCL 单例为什么必须 volatile",
  "concurrency", "concurrency", "medium",
  ["dcl", "singleton", "volatile", "instruction-reorder", "concurrency"],
  [],
  """# DCL 单例为什么必须 volatile

## 问题描述

双重检查锁 (DCL) 单例的 instance 字段为什么要加 volatile？不加会出什么问题？

## 解答

### DCL 写法
```java
class Singleton {
    private static volatile Singleton instance;   // volatile 必须
    public static Singleton getInstance() {
        if (instance == null) {                    // 第一次检查，无锁
            synchronized (Singleton.class) {
                if (instance == null) {            // 第二次检查，防重复创建
                    instance = new Singleton();
                }
            }
        }
        return instance;
    }
}
```

### 为什么需要 volatile（核心）
`instance = new Singleton()` 在字节码/JIT 层不是原子的，分三步：
1. 分配对象内存
2. 调用构造器，初始化对象字段
3. 把 `instance` 引用指向内存地址

**没有 volatile 时，JIT 可能重排 2 和 3**（1→3→2），因为单线程内重排不影响结果。

### 不加 volatile 的故障
- 线程 A 执行到 1→3（已赋值，但对象未初始化完）。
- 线程 B 第一次 `if (instance == null)`：**`instance != null`**（看到非 null），直接 `return instance`。
- 线程 B 拿到的是**半初始化对象**（字段是默认值/null），使用时 NPE 或脏值。
- 这个 bug 是**偶发**的，难复现，压测或生产偶现崩溃。

### volatile 怎么解决
- volatile 写前插 `StoreStore` 屏障 → 禁止 2（普通写/构造器写）与 3（volatile 写）重排。
- volatile 写后插 `StoreLoad` 屏障 → 保证写对后续读可见。
- 结果：1→2→3 顺序固定，对象完全初始化后才发布，其他线程要么看到 null，要么看到完整对象。

### DCL 的其他要点
- **两次检查都必要**：第一次避免已创建对象每次都进同步块（性能）；第二次防多线程同时通过第一次检查后重复创建。
- **锁用 class 对象**（`Singleton.class`），静态字段属于 Class。
- 1.5 之后 volatile 语义完善（JSR-133），DCL 才真正可靠；1.4 之前 volatile 语义弱，DCL 仍不安全。

### 更好的替代
- **静态内部类持有**（推荐，无 volatile）：
  ```java
  class Singleton {
      private Singleton() {}
      private static class Holder { static final Singleton INSTANCE = new Singleton(); }
      public static Singleton getInstance() { return Holder.INSTANCE; }
  }
  ```
  类加载时初始化，JVM 保证类初始化线程安全（`<clinit>` 加锁），且延迟到首次 `getInstance` 才加载 Holder。
- **枚举单例**（Effective Java 推荐）：天然线程安全、防反射、防序列化。

## 易错点
- 不加 volatile → 偶发半初始化对象，难复现。
- 以为 synchronized 就够了 → synchronized 保证原子与可见性，但不禁止重排（2 和 3 在锁内仍可重排）。
- 第一次检查不在锁内读 instance → 没 volatile 时连可见性都不保证，更危险。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed",
  links=["concurrency/volatile-principle",
         "concurrency/jmm-happens-before",
         "concurrency/synchronized-vs-reentrantlock"])

q("concurrency/locksupport-park-unpark.md",
  "LockSupport.park / unpark 原理 (vs wait/notify)",
  "concurrency", "concurrency", "medium",
  ["locksupport", "park", "unpark", "concurrency", "juc"],
  [],
  """# LockSupport.park / unpark 原理 (vs wait/notify)

## 问题描述

LockSupport.park/unpark 的原理？和 wait/notify 有什么区别？为什么 AQS 用它而不是 wait/notify？

## 解答

### LockSupport.park / unpark
- `park()`：阻塞当前线程，许可不可用则进入 WAITING/TIMED_WAITING。
- `unpark(Thread t)`：给线程 t 一个许可（permit），使其从 `park()` 返回。
- **许可最多一个**（不会累加）：连续 `unpark` 多次也只是 1 个许可，下一次 `park` 直接返回不阻塞。

### 关键区别：unpark 可先于 park
- **wait/notify**：`notify` 必须在 `wait` 之后调用——先 notify 后 wait 会丢信号（线程永远等）。
- **park/unpark**：`unpark` 可以在 `park` 之前调用——先 unpark 给了许可，之后 `park` 直接返回不阻塞。
- 这让 AQS 等无锁等待的实现更安全（不会因先唤醒后等待丢信号）。

### 实现（底层）
- 每个 Thread 有一个 `parkBlocker` 字段和许可（用 `Parker` 实现，C++ 层基于 `pthread_mutex` + `pthread_cond` 或 futex）。
- `park` 检查许可：有则消耗并返回，无则阻塞。
- `unpark` 设置许可（若线程在阻塞则唤醒）。
- 中断也会使 `park` 返回（需检查 `Thread.interrupted()`）。

### 对比表
| 维度 | wait/notify | park/unpark |
| --- | --- | --- |
| 所属 | Object 方法 | LockSupport 静态方法 |
| 前置条件 | 必须持有对象 monitor（synchronized 块内） | 无需任何锁 |
| 唤醒顺序 | notify 必须在 wait 后 | unpark 可在 park 前 |
| 许可累加 | 一次 notify 唤醒一个/全部 | 许可最多 1，不累加 |
| 阻塞对象 | 对象的 wait set | 线程本身 |
| 精准唤醒 | ❌（随机一个或全部） | ✅（指定线程） |

### AQS 为什么用 LockSupport
- AQS 的 Node 队列不依赖对象 monitor，park/unpark 无需持锁即可唤醒后继节点。
- `unparkSuccessor` 精准 `unpark` 后继线程，不唤醒无关线程。
- 避免 wait/notify 必须在 synchronized 块内的耦合（AQS 用 CAS + volatile 管队列，不用对象锁）。

### blocker 用法
- `park(blocker)` 传入对象，记录到 `parkBlocker` 字段，jstack 能看到"为什么阻塞"，便于诊断：
  `LockSupport.park(this)`。

## 易错点
- 连续 unpark 当多次许可 → 只 1 个，下次 park 仍阻塞。
- park 被中断后不检查 `interrupted()` → 中断信号丢失（AQS 在 `parkAndCheckInterrupt` 里检查并 selfInterrupt 补回）。
- 用 wait/notify 思路先 notify 后 wait → 永久阻塞。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed",
  links=["concurrency/aqs-principle",
         "concurrency/synchronized-vs-reentrantlock"])

q("concurrency/forkjoinpool-parallelstream.md",
  "ForkJoinPool 工作窃取 + parallelStream 坑",
  "concurrency", "concurrency", "medium",
  ["forkjoinpool", "work-stealing", "parallelstream", "juc", "concurrency"],
  [],
  """# ForkJoinPool 工作窃取 + parallelStream 坑

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
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed",
  links=["concurrency/completablefuture-async-orchestration",
         "concurrency/thread-pool-principles"])

q("concurrency/false-sharing-contended.md",
  "伪共享 false sharing 与 @Contended",
  "concurrency", "concurrency", "medium",
  ["false-sharing", "contended", "cache-line", "concurrency", "performance"],
  [],
  """# 伪共享 false sharing 与 @Contended

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
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed",
  links=["concurrency/longadder-vs-atomiclong",
         "concurrency/cas-mechanism",
         "concurrency/concurrenthashmap-principle"])

print("\nDone: deep concurrency docs (5 rewrites + 12 new)")
