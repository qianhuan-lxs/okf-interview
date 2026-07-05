#!/usr/bin/env python3
"""Rewrite AQS/CAS for beginner friendliness + add threadpool source analysis
and Java built-in Executors pools design doc."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from ikf_writer import q

DATE = "2026-07-05"

# =========================================================================== #
# REWRITE: AQS — beginner-friendly progressive disclosure
# =========================================================================== #

q("concurrency/aqs-principle.md",
  "AQS 原理 (从直觉到源码)",
  "concurrency", "concurrency", "hard",
  ["aqs", "clh-queue", "juc", "condition", "concurrency"],
  ["北京用友"],
  """# AQS 原理 (从直觉到源码)

## 问题描述

AQS 是什么？为什么 JUC 的锁都基于它？独占和共享怎么实现？Condition 怎么工作？

## 一、先建直觉：AQS 在解决什么问题

想象银行大厅：你抢不到柜员（资源）就得**排队等**，柜员空了**叫下一个**。AQS 就是干这个的——它给"抢不到资源就排队、资源空了唤醒队首"提供了一个通用骨架。

没有 AQS 之前，每个锁自己写一套等待队列 + park/unpark 逻辑，重复且容易错。AQS 把这套排队逻辑抽成框架，子类只管"什么算抢到、什么算释放"。

> **一句话**：AQS = 一个 `state` 变量 + 一个等待队列 + park/unpark 调度。子类实现"怎么改 state 算成功"，AQS 管"失败了怎么排队、成功了怎么唤醒"。

## 二、核心三件套

### 1. `volatile int state`——资源的"状态"
- 一个 int，语义由子类定义：
  - `ReentrantLock`：0=没人拿，>0=拿了几个（重入次数）。
  - `Semaphore`：还剩几个许可。
  - `CountDownLatch`：还差几个计数。
  - `ReentrantReadWriteLock`：**高 16 位=读者数，低 16 位=写者重入数**（一个 int 装两个数）。
- `volatile` 保证多线程可见，修改用 CAS 保证原子。

### 2. 等待队列——CLH 变体双向链表
- 抢不到的线程被包成 `Node` 挂到队尾，线程自己 `park`（挂起）。
- 队首线程被唤醒后重新尝试抢。
- **为什么叫"CLH 变体"**：原版 CLH 是单向、自旋（不 park，死循环检查前驱）。AQS 改成**双向 + park/unpark**——能 park 省 CPU，双向是为了取消节点时能找到前驱。所以是"借鉴 CLH 思想的变体"，不是原版 CLH。

### 3. `Node.waitStatus`——节点状态
| 值 | 名 | 含义 |
| --- | --- | --- |
| 0 | 初始 | 刚入队 |
| -1 | SIGNAL | "我后面有人，我释放时要唤醒后继"——**最关键** |
| -2 | CONDITION | 在 Condition 等待队列里 |
| -3 | PROPAGATE | 共享模式传播唤醒 |
| 1 | CANCELLED | 取消了，可剔除 |

> 新手记住 SIGNAL 就够：**每个节点要把前驱设成 SIGNAL 才能 park**，意思是"前驱你走的时候记得叫我"。

## 三、独占模式获取流程（用 ReentrantLock 讲）

### 白话版
1. 我要锁 → 看 `state` 是 0 吗？是 0 就 CAS 抢（设成 1，记自己为 owner）。
2. 不是 0 但 owner 是我自己 → 重入，`state++`。
3. 都不是 → 我抢不到，**入队排队**，把自己 park 挂起。
4. 前面的人用完释放 → 把 `state` 改回 0 → 唤醒队首（我）→ 我醒来重试第 1 步。

### 源码版（`acquire` 主干）
```java
public final void acquire(int arg) {
    if (!tryAcquire(arg) &&                              // 子类实现：尝试抢
        acquireQueued(addWaiter(Node.EXCLUSIVE), arg))   // 抢失败：入队 + 自旋park
        selfInterrupt();                                  // 补中断标志
}
```
- `tryAcquire`：子类实现（ReentrantLock 的非公平版上来 CAS 抢 state）。
- `addWaiter`：把当前线程包成 Node，CAS 挂到队尾。
- `acquireQueued`：自旋——**只有前驱是 head 且 tryAcquire 成功**才出队当 head；否则把前驱 waitStatus 设成 SIGNAL，然后 `park`。
- `selfInterrupt`：park 期间若被中断，AQS 不立即响应，但补回中断标志（`Thread.currentThread().interrupt()`），让上层感知。

### 公平 vs 非公平（新手易混）
- **非公平**（默认）：`tryAcquire` 上来就 CAS 抢，**不管队列有没有人在等** → 新来的能"插队" → 吞吐高（少一次 park/unpark）。
- **公平**：`tryAcquire` 先 `hasQueuedPredecessors()` 查队列有没有前驱，有就去排队 → 严格 FIFO、不饿死队尾但慢。
- 为什么默认非公平？线程 park/unpark 一次开销大，让刚释放的线程或新来的直接抢，能减少切换。

## 四、释放流程

```java
public final boolean release(int arg) {
    if (tryRelease(arg)) {              // 子类：state-- 到 0
        Node h = head;
        if (h != null && h.waitStatus != 0)
            unparkSuccessor(h);          // 唤醒后继
        return true;
    }
    return false;
}
```
- `tryRelease`：`state--`，到 0 清 owner。
- `unparkSuccessor`：从**队尾向前**找第一个未 CANCELLED 的后继，`LockSupport.unpark` 它。（从尾向前是因为中间节点可能已取消，正向 next 链可能断。）

## 五、共享模式（Semaphore / CountDownLatch）

- `tryAcquireShared` 返回值：
  - `>0`：成功，且**继续唤醒后继**（还有许可，传播）。
  - `=0`：成功，但不再传播（许可刚好用完）。
  - `<0`：失败，入队。
- `CountDownLatch` 的 `tryAcquireShared` 返回 `state==0 ? 1 : -1`——**只有计数归零才放行所有等待者**。
- 共享模式有 PROPAGATE 状态：确保多个许可被连续获取，不会"唤醒一个就停"。

## 六、Condition（条件变量，重点追问）

### 直觉
synchronized 只有一个等待室（`wait/notify`）。ReentrantLock 可以有**多个独立等待室**（Condition）——比如"满了的等待室"和"空了的等待室"，生产者等"非满"、消费者等"非空"，互不干扰。

### 实现
- 每个 `Condition` 是 AQS 内的**独立单向链表**（firstWaiter/lastWaiter），与主队列分离。
- `await()`：
  1. **释放全部锁**（`fullyRelease`，否则别的线程进不来）。
  2. 把当前线程包成 CONDITION 节点挂到 Condition 队列。
  3. `park`。
  4. 被 `signal` 唤醒后，节点从 Condition 队列**转移到主队列**（状态改 SIGNAL），重新排队抢锁；抢到后恢复重入数。
- `signal()`：取 Condition 队首节点，CAS 转移到主队列。
- **坑**：`await` 必须在 `lock.lock()` 之后调（持有锁才能释放锁），否则 `IllegalMonitorStateException`。

## 七、面试高频追问速答

| 问题 | 答 |
| --- | --- |
| AQS 队列是普通 FIFO 吗？ | 是 FIFO，但带 waitStatus 的 CLH 变体，SIGNAL 决定该不该 park。 |
| 为什么用双向链表？ | 取消节点时要找前驱改 next；共享模式传播也要看前驱。 |
| 公平锁一定更好吗？ | 不，吞吐更低，只在需要防饿死时用。 |
| Condition 和 wait/notify 区别？ | Condition 支持多等待队列、可超时、可响应中断；必须在 lock 内用。 |
| AQS 为什么用 LockSupport 而不是 wait/notify？ | park/unpark 无需持锁、可先 unpark 后 park（不丢信号）、精准唤醒指定线程。 |

## 易错点
- `await()` 没 lock 就调 → `IllegalMonitorStateException`。
- 以为公平锁更快 → 严格 FIFO 牺牲吞吐。
- 以为 Condition 是同步队列一部分 → 它是独立队列，signal 时才转移到主队列。
- 以为队列是原版 CLH → 是 park 版变体，原版 CLH 是自旋不 park。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source="_interviews/2026-05-louis-ai-java", status="reviewed", timestamp=DATE,
  links=["concurrency/synchronized-vs-reentrantlock",
         "concurrency/cas-mechanism",
         "concurrency/thread-pool-principles",
         "concurrency/locksupport-park-unpark",
         "concurrency/readwritelock-stampedlock"])

# =========================================================================== #
# REWRITE: CAS — beginner-friendly progressive disclosure
# =========================================================================== #

q("concurrency/cas-mechanism.md",
  "CAS 机制 (从直觉到 cmpxchg 底层)",
  "concurrency", "concurrency", "hard",
  ["cas", "compare-and-swap", "atomic", "aba", "unsafe", "varhandle"],
  ["有赞", "探迹", "北京用友"],
  """# CAS 机制 (从直觉到 cmpxchg 底层)

## 问题描述

CAS 是什么？为什么需要它？底层怎么保证原子？ABA 真有那么严重？高并发下 CAS 为什么反而差？

## 一、先建直觉：CAS 在解决什么

多线程改一个共享变量，最朴素是加锁：
```java
synchronized (lock) { i++; }   // 串行化，慢
```
锁太重——要系统调用、上下文切换。**CAS 给了一种"不加锁"的乐观做法**：

> "我觉得现在 i 是 5，如果是 5 就把它改成 6；如果不是 5，那说明被别人改过了，我重试。"

这就是 **Compare-And-Swap**：三参数 `(内存位置 V, 期望值 A, 新值 B)`，仅当 `V==A` 时把 V 改成 B，否则返回当前值。**比较和替换是 CPU 一条指令完成的**，中间不会被别的线程插足。

类比：你改 git 文件前先 `git pull`，发现远程比你新就 rebase 重来，不冲突就 push。乐观、不阻塞、冲突才重试。

## 二、为什么需要 CAS（而非只用锁）
- 锁（synchronized/ReentrantLock）阻塞 → 系统调用 + 上下文切换，高并发低竞争时开销占大头。
- CAS 无锁自旋 → 竞争不剧烈时几乎零开销，性能远超锁。
- 是无锁数据结构（ConcurrentHashMap 空槽插入、AtomicInteger 自增、AQS 改 state）的基石。

## 三、底层怎么保证原子（重点）

CAS 在 Java 层是 `Unsafe.compareAndSwapXxx` / JDK 9+ `VarHandle.compareAndSet`，最终走 JNI 到 CPU 指令：

- **x86**：`lock cmpxchg`。`cmpxchg` 本身是"读-比较-写"三步，**不是原子的**；但加 **`lock` 前缀** → 锁缓存行（MESI 协议）或锁总线，保证整条指令原子。
- **ARM/PowerPC**：LL-SC（Load-Linked / Store-Conditional）循环——硬件层"乐观"：若加载后该缓存行被改，SC 失败，重试。

> 新手理解到这层就够：**CAS 原子性靠 CPU 硬件指令，不是 Java 自己实现的**。

## 四、Java 里的 CAS 封装

| API | 用途 |
| --- | --- |
| `AtomicInteger / AtomicLong / AtomicReference` | 基本原子类，封装 volatile 字段 + CAS |
| `AtomicStampedReference` | 带 int 版本号的引用（防 ABA） |
| `AtomicMarkableReference` | 带 boolean 标记的引用（防 ABA 简化版） |
| `Unsafe.compareAndSwapXxx` | JDK 9 前的底层 native API（内部用） |
| `VarHandle.compareAndSet` | JDK 9+ 标准替代 Unsafe，支持内存序 |

AQS 的 `state` 修改、`ConcurrentHashMap` 空槽插入、`LongAdder` 的 Cell 累加都用 CAS。

## 五、ABA 问题（新手最难理解，用例子讲）

### 现象
线程 1 读到值 A，准备 CAS A→C。被抢占期间，线程 2 把 A→B→A（值"回到"A 但中间变过）。线程 1 恢复，CAS A→C 仍成功——值"看起来"没变，但中间状态丢失了。

### 真实危害场景（无锁栈）
- 栈顶是 A，A 的 next 指向 B。
- 线程 1 要 pop：记下 top=A、next=B，准备 CAS top A→B。被抢占。
- 线程 2：pop A、pop B、又 push A（A 的 next 现在变了，可能指向 null 或别的）。
- 线程 1 恢复：CAS top A→B 成功——**但此时 A 的 next 早已不是 B**，栈结构破坏，B 可能丢失或重复。

### 解法
- `AtomicStampedReference`：每次改动带版本号，CAS 必须匹配 `(值, 版本)`。A→B→A 时版本也变了，线程 1 的旧版本 CAS 失败。
- `AtomicMarkableReference`：boolean 标记，更轻（仅二态）。
- GC 隐式缓解对象引用场景，但**不解决同一对象被复用**。

> 新手要点：**ABA 不是值错了，是"中间过程"丢了**。值类的计数器 ABA 通常无害（值对就行），但**指针/引用型的数据结构**会真出问题。

## 六、高并发下 CAS 为什么反而差

- CAS 失败就自旋重试 → 高竞争下大量线程同时 CAS 同一字段，只有一个成功，其余空转耗 CPU。
- 极端情况吞吐比 synchronized 还差（锁至少排队不空转）。

### 解法
- **`LongAdder`**：把一个热点字段拆成 `base + Cell[]`，线程 hash 到不同 Cell 各自 CAS，`sum()` 求和。热点分散，吞吐数倍于 `AtomicLong`。代价：`sum()` 非精确瞬时值。
- **自旋退避**：限制重试次数、`Thread.onSpinWait()`（JDK 9+，x86 发 `PAUSE` 指令降功耗防乱序）。
- **极高竞争用锁更优**：synchronized 升级到重量锁后 park 阻塞，不空转。

## 七、CAS 和 volatile 的关系（易混）
- `AtomicInteger.value` 是 **volatile** → 保证读的可见性。
- **CAS** → 保证写的原子性。
- 两者结合才完整：volatile 管"看得见"，CAS 管"改得对"。
- 所以 `AtomicInteger` 不是"只靠 CAS"，是 volatile + CAS。

## 八、面试高频追问速答

| 问题 | 答 |
| --- | --- |
| CAS 原子性谁保证？ | CPU 硬件指令（x86 `lock cmpxchg`，ARM LL-SC）。 |
| CAS 能替代锁吗？ | 低竞争可以（原子类）；复合操作（先读再判断再写多步）不行。 |
| ABA 何时真有害？ | 引用/指针型数据结构（无锁栈、链表）；纯计数器通常无害。 |
| `i++` 加 volatile 行吗？ | 不行，volatile 不保证原子；用 `AtomicInteger` 或锁。 |
| 高并发计数器选什么？ | `LongAdder`（远优于 `AtomicLong`）。 |

## 易错点
- 把 CAS 当万能 → 高竞争退化为自旋空耗。
- 以为 `AtomicReference` 防 ABA → 不能，要用 `AtomicStampedReference`。
- `i++` 用 volatile 想原子 → 不行，复合操作。
- `LongAdder.sum()` 当精确快照 → 它是估算求和，期间 Cell 仍在变。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source="_interviews/2026-05-louis-ai-java", status="reviewed", timestamp=DATE,
  links=["concurrency/aqs-principle",
         "concurrency/synchronized-vs-reentrantlock",
         "concurrency/longadder-vs-atomiclong",
         "concurrency/volatile-principle"])

# =========================================================================== #
# NEW: ThreadPoolExecutor 源码解析
# =========================================================================== #

q("concurrency/threadpool-source-analysis.md",
  "ThreadPoolExecutor 源码解析 (ctl / execute / Worker / transfer)",
  "concurrency", "concurrency", "hard",
  ["thread-pool", "threadpoolexecutor", "source", "juc", "concurrency"],
  [],
  """# ThreadPoolExecutor 源码解析 (ctl / execute / Worker / transfer)

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
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["concurrency/thread-pool-principles",
         "concurrency/executors-built-in-pools",
         "concurrency/aqs-principle",
         "concurrency/completablefuture-async-orchestration"])

# =========================================================================== #
# NEW: Executors 内置线程池设计 + 源码
# =========================================================================== #

q("concurrency/executors-built-in-pools.md",
  "Executors 内置线程池设计 (Fixed/Cached/Single/Scheduled/WorkStealing)",
  "concurrency", "concurrency", "hard",
  ["executors", "thread-pool", "fixed", "cached", "scheduled", "workstealing", "juc"],
  [],
  """# Executors 内置线程池设计 (Fixed/Cached/Single/Scheduled/WorkStealing)

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
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["concurrency/thread-pool-principles",
         "concurrency/threadpool-source-analysis",
         "concurrency/forkjoinpool-parallelstream",
         "concurrency/threadlocal-threadpool-problems"])

print("\nDone: AQS/CAS rewrite + threadpool source + executors pools")
