#!/usr/bin/env python3
"""Seeder: Java concurrency + Java language basics from 2026-05 Louis面经."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from seed_louis_ai import q  # reuse the writer helper

# --- concurrency/ ---------------------------------------------------------- #

q("concurrency/synchronized-vs-reentrantlock.md",
  "synchronized vs ReentrantLock 区别",
  "concurrency", "concurrency", "medium",
  ["synchronized", "reentrantlock", "lock", "aqs", "juc"],
  ["恩士讯", "北京用友"],
  """# synchronized vs ReentrantLock 区别

## 问题描述

说一下 synchronized 和 ReentrantLock 的区别？你知道 AQS 原理吗？

## 解答

| 维度 | synchronized | ReentrantLock |
| --- | --- | --- |
| 性质 | JVM 关键字（monitorenter/monitorexit） | JDK 类（java.util.concurrent.locks） |
| 实现 | 对象头 MarkWord + Monitor，重量级走 ObjectMonitor | AQS（CLH 变体 + state + FIFO 队列） |
| 公平性 | 非公平（不可配） | 可配 fair/non-fair |
| 中断 | 不可中断 | `lockInterruptibly()` 可响应中断 |
| 超时 | 不支持 | `tryLock(timeout)` |
| 条件变量 | 单条件（wait/notify） | 多 Condition |
| 释放 | 自动（出块/异常） | 必须 `finally { unlock() }`，否则死锁 |
| 锁状态 | 不可查询 | `isLocked() / getHoldCount()` |
| 性能 | JDK6+ 优化（偏向→轻量→重量）后接近 | 高竞争下略优 |

### 选型
- 简单同步、不需可中断/超时 → synchronized（语法糖，自动释放）
- 需公平/中断/超时/多条件/可观测 → ReentrantLock

### AQS 原理（追问）
- 核心是一个 `volatile int state` + 双向 FIFO 等待队列（CLH 变体）。
- 独占模式：`tryAcquire` CAS 改 state，失败则构造 Node 入队、park；前驱唤醒后 `tryAcquire` 重试。
- 共享模式：`tryAcquireShared`，state 表示许可数（Semaphore/CountDownLatch）。
- Condition 是独立等待队列，`await` 释放锁并入 cond 队列，`signal` 转移到主队列。

## 易错点
- ReentrantLock 忘 `finally unlock` —— 异常路径死锁。
- 以为 synchronized 一定慢 —— JDK6 之后锁升级优化下差距很小。

## 延伸
""",
  links=["concurrency/aqs-principle", "concurrency/cas-mechanism",
         "concurrency/optimistic-vs-pessimistic-lock"])

q("concurrency/cas-mechanism.md",
  "CAS 机制理解",
  "concurrency", "concurrency", "medium",
  ["cas", "compare-and-swap", "atomic", "aba"],
  ["有赞", "探迹", "北京用友"],
  """# CAS 机制理解

## 问题描述
你对 CAS 怎么理解？

## 解答
**CAS (Compare-And-Swap)**：无锁原子操作。三参数 (内存位置 V, 期望值 A, 新值 B)，仅当 V==A 时把 V 改为 B，否则返回当前值。底层是 CPU 的 `cmpxchg` 指令（x86）/LL-SC（ARM），单条指令保证原子。

### 为什么需要 CAS
- synchronized 太重（系统调用、上下文切换）。
- 高并发下 CAS 无锁自旋，竞争不剧烈时性能更好。

### Java 中的 CAS
- `sun.misc.Unsafe.compareAndSwapXxx` / JDK 9+ `VarHandle`。
- 封装为 `AtomicInteger / AtomicReference / LongAdder`。
- AQS 的 state 修改、ConcurrentHashMap 的节点插入都用 CAS。

### ABA 问题
- 线程 1 读到 A，线程 2 把 A→B→A，线程 1 CAS 仍成功，但中间状态丢失。
- 解法：**版本号** —— `AtomicStampedReference` 加 stamp；或 `AtomicMarkableReference`。

### 自旋开销
- 高竞争下 CAS 自旋空耗 CPU。解法：
  - `LongAdder` 分段累加，hot 字段分散。
  - 自旋次数限制 / 退避。
  - 极高竞争下反而 synchronized 更优（排队而非空转）。

## 易错点
- 把 CAS 当万能 —— 高竞争场景退化为自旋空耗。

## 延伸
""",
  links=["concurrency/aqs-principle", "concurrency/synchronized-vs-reentrantlock"])

q("concurrency/aqs-principle.md",
  "AQS 原理",
  "concurrency", "concurrency", "hard",
  ["aqs", "clh-queue", "juc", "concurrency"],
  ["北京用友"],
  """# AQS 原理

## 问题描述
AQS 原理知道吗？

## 解答
**AQS (AbstractQueuedSynchronizer)** 是 JUC 锁与同步器的基础框架。ReentrantLock / Semaphore / CountDownLatch / ReentrantReadWriteLock 都基于它。

### 核心结构
- `volatile int state`：同步状态，语义由子类定义（ReentrantLock 表示锁是否被持有/重入次数；Semaphore 表示剩余许可）。
- **CLH 变体双向队列**：获取失败的线程封装为 `Node` 入队、`LockSupport.park`。
- `Node` 有 CANCELLED/SIGNAL/CONDITION/PROPAGATE 等等待状态。

### 独占获取流程（以 ReentrantLock 非公平为例）
1. `tryAcquire`：CAS 把 state 从 0 改为 1，成功则设当前线程为 owner。
2. 若 state != 0 但 owner==当前线程 → state++（重入）。
3. 否则构造 Node 入队，`acquireQueued` 自旋：前驱是 head 且 `tryAcquire` 成功则出队；否则 `shouldParkAfterFailedAcquire` 把前驱设为 SIGNAL 后 park。
4. head 节点释放时 `unparkSuccessor` 唤醒后继。

### 公平 vs 非公平
- 非公平：`tryAcquire` 上来就 CAS 抢，允许插队（吞吐高）。
- 公平：先检查队列是否有前驱 `hasQueuedPredecessors`，有则排队。

### 共享模式
- `tryAcquireShared` 返回 >=0 表示成功；释放时 `doReleaseShared` 传播唤醒。

## 易错点
- 以为 AQS 队列是普通 FIFO 链表 —— 是带等待状态的 CLH 变体，SIGNAL 标志决定是否该 park。

## 延伸
""",
  links=["concurrency/synchronized-vs-reentrantlock", "concurrency/cas-mechanism",
         "concurrency/thread-pool-principles"])

q("concurrency/threadlocal-usage-pitfalls.md",
  "ThreadLocal 使用场景与内存泄漏",
  "concurrency", "concurrency", "medium",
  ["threadlocal", "memory-leak", "context", "juc"],
  ["中泓一线", "有赞"],
  """# ThreadLocal 使用场景与内存泄漏

## 问题描述
ThreadLocal 是什么？用在什么场景？使用注意的点？为什么会脏掉？

## 解答
**ThreadLocal** = 线程本地变量，每个线程一份独立副本，线程间隔离。

### 实现原理
- 每个 `Thread` 持有 `ThreadLocalMap threadLocals`。
- Map 的 **key 是 ThreadLocal 的弱引用**，**value 是强引用**。
- `ThreadLocal.get()` → 取当前线程的 map → 按 this 查 Entry。

### 典型场景
1. **用户上下文传递**：HTTP 请求进网关，在 filter 把 userId 放 ThreadLocal，整个调用链免传参。
2. **数据库连接 / 事务绑定**：Spring 的 `TransactionSynchronizationManager`。
3. **SimpleDateFormat 隔离**（非线程安全）。
4. **MDC 日志 traceId**。

### 内存泄漏机制
- key 是弱引用，ThreadLocal 实例若无外部强引用会被 GC，Entry 变成 `(null, value)`。
- value 是强引用，**只要线程活着**就回收不掉。
- 线程池里线程长生不死 → value 永久泄漏。

### 注意点
- **用完必须 `remove()`**，尤其在线程池场景（finally 块）。
- 不要把大对象塞进去。
- 不要用 `static ThreadLocal` 滥用，会造成全局隐式状态。

### 为什么会"脏"
线程池复用线程，上一个任务没 `remove()`，下一个任务 `get()` 拿到上一个任务的残留。见 [[concurrency/threadlocal-threadpool-problems]]。

## 延伸
""",
  links=["concurrency/threadlocal-threadpool-problems",
         "concurrency/thread-pool-principles",
         "backend/microservices/microservice-user-context-propagation"])

q("concurrency/threadlocal-threadpool-problems.md",
  "ThreadLocal 在线程池中的问题 (闭环追问)",
  "concurrency", "concurrency", "hard",
  ["threadlocal", "thread-pool", "inheritable-threadlocal", "transmittable-threadlocal"],
  ["有赞"],
  """# ThreadLocal 在线程池中的问题 (闭环追问)

## 问题描述
一个请求在线程池里，中间调了异步线程，ThreadLocal 会不会丢？能从子线程拿到主线程的 ThreadLocal 吗？线程池运行机制下 ThreadLocal 会有什么问题？

## 解答

### 会不会丢
**会丢**。线程池里任务由池中线程执行，不是调用线程；新线程不复制父线程的 ThreadLocalMap。

### 能否从子线程拿到主线程的 ThreadLocal
- 普通 `ThreadLocal` —— **不能**，子线程的 threadLocals 是空的。
- `InheritableThreadLocal` —— **能**，但**仅在线程创建时**复制一次父线程的 inheritableThreadLocals。线程池线程是复用的，创建时机早于任务提交，**所以线程池场景下 InheritableThreadLocal 也失效**。
- **`TransmittableThreadLocal` (阿里 TTL)** —— 线程池场景正确方案。通过装饰 `Runnable`，在任务执行前后做"快照-回放-还原"，把提交线程的 TTL 值透传到池线程，执行完再清理，避免污染。

### 线程池运行机制（追问）
1. 任务提交 → `execute()`
2. 若当前线程数 < corePoolSize → 新建线程跑任务。
3. 否则入阻塞队列 `workQueue`。
4. 队列满且线程数 < maxPoolSize → 再建非核心线程。
5. 否则走拒绝策略 `RejectedExecutionHandler`（AbortPolicy 抛异常 / CallerRuns 调用方跑 / Discard 丢弃）。
6. 空闲非核心线程超过 keepAliveTime → 回收。
7. 线程复用：worker 循环 `getTask()` 从队列 take 任务。

### 闭环：线程池下 ThreadLocal 的问题
- **脏数据**：池线程复用，上一个任务未 `remove()`，下一个任务读到残留。
- **泄漏**：key 弱引用被 GC，value 强引用 + 线程长生 → 永久泄漏。
- **上下文丢失**：跨线程/异步没有 TTL 透传，业务上下文丢失。

### 解法
1. `finally { threadLocal.remove(); }` 强制清理。
2. 跨线程用 `TransmittableThreadLocal` + `TtlRunnable.get(runnable)` 包装。
3. 用 Spring 的 `TaskDecorator` 在线程池提交时拷贝 MDC/上下文。

## 延伸
""",
  links=["concurrency/threadlocal-usage-pitfalls", "concurrency/thread-pool-principles",
         "backend/microservices/microservice-user-context-propagation"])

q("concurrency/thread-pool-principles.md",
  "线程池运行原理",
  "concurrency", "concurrency", "medium",
  ["thread-pool", "juc", "threadpoolexecutor", "concurrency"],
  ["有赞"],
  """# 线程池运行原理

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
""",
  links=["concurrency/threadlocal-threadpool-problems", "concurrency/aqs-principle"])

q("concurrency/optimistic-vs-pessimistic-lock.md",
  "乐观锁 vs 悲观锁",
  "concurrency", "concurrency", "easy",
  ["optimistic-lock", "pessimistic-lock", "cas", "version"],
  ["海颐"],
  """# 乐观锁 vs 悲观锁

## 问题描述
说一下乐观锁跟悲观锁。

## 解答

| 维度 | 悲观锁 | 乐观锁 |
| --- | --- | --- |
| 假设 | 假设冲突高，先锁再操作 | 假设冲突少，先操作提交时校验 |
| 实现 | `SELECT ... FOR UPDATE`、synchronized | CAS / version 字段 |
| 并发 | 串行化，吞吐低 | 不阻塞，吞吐高 |
| 适用 | 写多读少、强一致 | 读多写少、冲突少 |

### 乐观锁典型实现（version）
```sql
UPDATE t SET stock = stock - 1, version = version + 1
WHERE id = ? AND version = ?;
-- 影响行数=0 说明被别人改过，重试或失败
```

### 取舍
- 冲突率高 → 悲观锁（避免乐观锁大量重试）。
- 冲突率低 → 乐观锁（无阻塞）。
- 极端高并发抢购 → 都不理想，用 Redis 预扣 + 异步落库 / 分布式锁。

## 延伸
""",
  links=["concurrency/cas-mechanism", "distributed-systems/distributed-lock-redis-vs-zk"])

# --- languages/java/ ------------------------------------------------------- #

q("languages/java/hashmap-vs-concurrenthashmap.md",
  "HashMap vs ConcurrentHashMap",
  "languages", "java", "medium",
  ["hashmap", "concurrenthashmap", "juc", "java"],
  ["有赞"],
  """# HashMap vs ConcurrentHashMap

## 问题描述
HashMap 和 ConcurrentHashMap 有什么区别？resize 为什么危险？

## 解答

| 维度 | HashMap | ConcurrentHashMap |
| --- | --- | --- |
| 线程安全 | 否 | 是 |
| null key/value | 允许 1 null key / 多 null value | 都不允许（NPE） |
| 1.7 实现 | 数组+链表，头插法 | Segment 分段锁（16 段） |
| 1.8 实现 | 数组+链表+红黑树，尾插法 | 数组+链表+红黑树，CAS + synchronized 锁桶 |

### ConcurrentHashMap 1.8 细节
- `put`：空桶 CAS 插入；非空桶 `synchronized` 锁该桶头节点插入。
- 锁粒度从 Segment（段）降到桶节点，并发度大幅提升。
- `size` 用 `LongAdder` 思路（baseCount + CounterCell 数组）减少竞争。

### resize 为什么危险
- 1.7 HashMap 扩容用**头插法**，多线程并发扩容会形成**链表环**，后续 `get` 死循环 100% CPU（经典面试题）。
- 1.8 改尾插法，环问题消除，但 HashMap 仍**非线程安全**：并发 put 可能丢数据、size 不准、扩容期间 get 到 null。
- 任何并发场景都必须用 ConcurrentHashMap 或外置锁。

## 延伸
""",
  links=["languages/java/hashmap-resize-jdk17-jdk18",
         "concurrency/threadlocal-usage-pitfalls"])

q("languages/java/hashmap-resize-jdk17-jdk18.md",
  "HashMap resize (1.7 头插法死循环 / 1.8 尾插法)",
  "languages", "java", "hard",
  ["hashmap", "resize", "jdk17", "jdk18", "concurrent-modification"],
  ["有赞"],
  """# HashMap resize (1.7 头插法死循环 / 1.8 尾插法)

## 问题描述
1.7 HashMap 扩容有什么危险？1.8 是什么方式扩容？尾插法最终会导致什么问题？

## 解答

### 1.7 头插法 + 并发扩容 → 链表环
1.7 transfer 时：遍历旧桶，每个节点用头插法插入新桶。
```
newTable[e.next] 头插: e.next = newTable[i]; newTable[i] = e;
```
两个线程同时扩容，互相读取对方部分迁移的状态，可能让 A→B→A 形成环。
之后 `get(key)` 走链表死循环，CPU 100%。

### 1.8 改造
- 数组 + 链表 + 红黑树（链表长度 ≥8 且容量 ≥64 转树；≤6 退链表）。
- 扩容用**尾插法**，保留原顺序，**消除链表环**。
- 扩容时新容量 = 旧 ×2，rehash 时元素要么留原位要么 "原位 + oldCap"（高位 bit 判断），1.8 优化了这个判断。

### 1.8 尾插法还遗留什么问题
- **仍是非线程安全**：并发 put 可能丢数据、size 不准、扩容瞬间 get 到 null。
- **ConcurrentModificationException**：迭代期间结构性修改会 fail-fast。
- 解法：并发场景一律 ConcurrentHashMap。

## 易错点
- 以为 1.8 后 HashMap 就线程安全 —— 仅消除了死循环，丢数据问题仍在。

## 延伸
""",
  links=["languages/java/hashmap-vs-concurrenthashmap"])

q("languages/java/jdk17-new-features.md",
  "JDK 17 新特性",
  "languages", "java", "medium",
  ["jdk17", "jvm", "java", "features", "lts"],
  ["中泓一线"],
  '''# JDK 17 新特性

## 问题描述
JDK 17 有什么新特性？抛开语法不说，JDK 层面有什么新的？

## 解答

JDK 17 是 LTS（2021.09），从 8/11 升级主要收益。

### 语法/API
- **Records**（14 预览，16 正式）：`record Point(int x, int y) {}` 自动生成 equals/hashCode/toString。
- **Sealed Classes**（17 正式）：`sealed interface Shape permits Circle, Square;` 限制继承。
- **Pattern Matching for instanceof**（16 正式）：`if (o instanceof String s) ...`。
- **Switch 表达式**（14 正式）：`case "a" -> 1;`。
- **Text Blocks**（15 正式）：三引号 `"""..."""` 多行字符串。
- **Helpful NullPointerExceptions**：NPE 指明哪个变量为 null。

### JDK/JVM 层面（面试官追问重点）
- **ZGC**：低延迟垃圾回收器，亚毫秒停顿（17 时正式 production-ready，支持 16GB~16TB 堆）。
- **G1** 进一步优化（NUMA 感知、堆 Region 更灵活）。
- **Deprecated Security Manager**：逐步废弃，未来用 module + JEP 411。
- **Strongly Encapsulate JDK Internals**：默认封锁 `--add-opens`，反射访问 JDK 私有 API 受限（影响很多老库如 Lombok、ReflectASM、Spring AOP 早期版本）。
- **Packaging Tool**（jpackage，16 正式）：原生可执行包，无需 JVM。
- **Foreign Function & Memory API**（孵化）：替代 JNI 访问本地代码/堆外内存。

### 生态
- Spring Boot 3 要求 JDK 17+。
- GC 选型：低延迟用 ZGC/Shenandoah；吞吐用 G1（默认）。

## 延伸
''',
  links=["languages/java/jvm-garbage-collection", "languages/java/g1-gc-changes"])

q("languages/java/jvm-garbage-collection.md",
  "JVM 垃圾回收 (可达性分析 / GC)",
  "languages", "java", "medium",
  ["jvm", "gc", "reachability", "garbage-collection", "java"],
  ["恩士讯", "海颐"],
  """# JVM 垃圾回收 (可达性分析 / GC)

## 问题描述
JVM 是怎么把对象判定为垃圾的？了解过垃圾回收吗？大概讲一下。

## 解答

### 判活：可达性分析（替代引用计数）
- 通过一系列 **GC Roots** 作为起点，沿引用链遍历，可达 = 活，不可达 = 垃圾。
- 引用计数有循环引用问题，JVM 不用。
- **GC Roots**：
  1. 虚拟机栈帧中的局部变量、操作数栈引用
  2. 方法区中类静态变量、常量引用
  3. 本地方法栈 JNI 引用
  4. 同步锁持有的对象
  5. JVM 内部引用（如基本类型异常对象）

### 回收算法
- **标记-清除**：碎片多。
- **复制**：新生代用， eden + 2 survivor，空间换时间。
- **标记-整理**：老年代用，无碎片但慢。
- **分代**：新生代（朝生夕死，复制算法）+ 老年代（标记整理/G1）。

### 引用强度
强 → 软（内存不足才回收，适合缓存）→ 弱（下次 GC 必回收，WeakHashMap）→ 虚（跟踪回收时机）。

### 垃圾回收器演进
Serial → ParNew → Parallel Scavenge → CMS（并发标记清除，已废弃）→ **G1**（JDK9 默认）→ ZGC / Shenandoah（低延迟）。

## 延伸
""",
  links=["languages/java/g1-gc-changes", "languages/java/jvm-oom-analysis"])

q("languages/java/g1-gc-changes.md",
  "G1 相对之前回收器的改变",
  "languages", "java", "medium",
  ["g1", "gc", "jvm", "java"],
  ["恩士讯"],
  """# G1 相对之前回收器的改变

## 问题描述
G1 相对之前的回收器有什么改变？

## 解答

### 之前：CMS / Parallel
- 物理分代（新生代/老年代是连续内存段）。
- CMS：并发标记清除，低停顿但**有碎片**、Concurrent Mode Failure 退化为 Serial Old。

### G1（Garbage First）
- **Region 化堆**：堆分成 2048 个左右等大 Region（1~32MB），逻辑分代不物理连续。每个 Region 可动态充当 Eden/Survivor/Old/Humongous。
- **Garbage First**：优先回收垃圾最多的 Region，停顿可控。
- **可预测停顿**：用户设 `-XX:MaxGCPauseMillis`，G1 用历史数据估算能在停顿时间内回收多少 Region。
- **混合回收**：不再严格分新生代/老年代 GC，一次回收可同时含新生代 Region + 部分老年代 Region。
- **RSet（Remembered Set）**：每个 Region 记录"谁引用了我"，避免全堆扫描；用写屏障维护。
- **SATB（Snapshot-At-The-Beginning）**：并发标记阶段，引用变更通过写屏障记录，保证标记正确性。
- 无碎片（Region 整体回收，复制算法）。

### 代价
- 内存开销：RSet + Collection Set 卡表约占堆 5%~10%。
- 写屏障开销。

### JDK 9+ 默认 G1；JDK 17+ ZGC 成熟，超低延迟场景可换 ZGC。

## 延伸
""",
  links=["languages/java/jvm-garbage-collection", "languages/java/jdk17-new-features"])

q("languages/java/jvm-oom-analysis.md",
  "OOM 分析过程",
  "languages", "java", "medium",
  ["oom", "jvm", "heap-dump", "java", "troubleshooting"],
  ["恩士讯"],
  """# OOM 分析过程

## 问题描述
怎么分析 OOM 的？具体过程？

## 解答

### 第一步：保留现场
- JVM 启动参数加 `-XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/var/log/oom.hprof`，OOM 时自动 dump。
- 容器场景挂 PV，避免 dump 随容器销毁。

### 第二步：定位 OOM 类型
| 类型 | 触发 | 常见原因 |
| --- | --- | --- |
| `Java heap space` | 堆满 | 大对象、内存泄漏、堆太小 |
| `GC overhead limit` | GC 回收 <2% 但耗时 >98% | 内存泄漏 |
| `Metaspace` | 元空间满 | 动态类生成（CGLIB/反射） |
| `Direct buffer memory` | 堆外内存满 | NIO ByteBuffer 泄漏 |
| `unable to create new native thread` | 线程数超限 | 线程泄漏 |

### 第三步：分析 hprof
- **MAT (Memory Analyzer)**：打开 hprof → 看 Dominator Tree 找最大对象 → Leak Suspects 报告 → 查 GC Root 引用链。
- **Arthas**（线上热查）：`dashboard / heapdump / vmtool`。
- **jmap -histo:live | head`**：快速看对象 TopN。

### 第四步：常见根因
- 静态集合无限增长（缓存无淘汰）。
- ThreadLocal 线程池泄漏。
- 连接/Statement 未关闭。
- 大结果集一次查回。
- 第三方库内存泄漏（如 fastjson 某版本）。

### 第五步：验证
- 修复后压测 + 监控堆增长曲线 + 配 G1/ZGC 日志 `-Xlog:gc*`。

## 延伸
""",
  links=["languages/java/jvm-garbage-collection",
         "concurrency/threadlocal-usage-pitfalls"])

q("languages/java/jre-vs-jdk.md",
  "JRE 和 JDK 的区别",
  "languages", "java", "easy",
  ["jre", "jdk", "java", "basics"],
  ["海颐"],
  """# JRE 和 JDK 的区别

## 解答
- **JRE (Java Runtime Environment)** = JVM + 核心类库（rt.jar / java.base 模块）。能**运行** Java 程序，不能编译。
- **JDK (Java Development Kit)** = JRE + 开发工具（javac / java / jdb / jstack / jmap / jar ...）。能**开发 + 运行**。

关系：`JDK ⊃ JRE ⊃ JVM`。

JDK 11+ 起不再单独提供 JRE 发行包（模块化后用 `jlink` 按需裁出运行时）。

## 延伸
""",
  links=["languages/java/jdk17-new-features"])

q("languages/java/stringbuilder-vs-stringbuffer.md",
  "StringBuilder 和 StringBuffer 的区别",
  "languages", "java", "easy",
  ["stringbuilder", "stringbuffer", "java", "basics"],
  ["海颐"],
  """# StringBuilder 和 StringBuffer 的区别

## 解答

| 维度 | StringBuilder | StringBuffer |
| --- | --- | --- |
| 线程安全 | 否 | 是（synchronized） |
| 性能 | 高（无锁） | 低（锁开销） |
| 引入版本 | JDK 5 | JDK 1.0 |
| 适用 | 单线程拼接 | 多线程共享拼接 |

- 都继承 `AbstractStringBuilder`，底层是可变 char[]/byte[]，扩容 `原容量*2 + 2`。
- **单线程拼接优先 StringBuilder**；多线程共享才用 StringBuffer（实际极少见，更推荐用 `StringJoiner` 或不可变 + 锁外部控制）。
- 编译器会把 `+` 拼接优化成 StringBuilder.append（循环内 `+` 除外，循环内每次 new StringBuilder，应手动用 builder）。

## 延伸
""",
  links=[])

q("languages/java/java-io-stream-types.md",
  "Java IO 流的种类",
  "languages", "java", "easy",
  ["io", "stream", "nio", "java", "basics"],
  ["海颐"],
  """# Java IO 流的种类

## 解答

按**流向**：输入流 / 输出流（相对程序而言）。
按**数据单位**：字节流（InputStream/OutputStream，1 byte）/ 字符流（Reader/Writer，1 char，需 charset 解码）。
按**功能**：节点流（直接连数据源） / 处理流（包装别的流加缓冲/转换/对象序列化）。

### 字节流
- `FileInputStream / FileOutputStream`
- `BufferedInputStream / BufferedOutputStream`（处理流，缓冲）
- `DataInputStream / DataInputStream`（读基本类型）

### 字符流
- `FileReader / FileWriter`
- `BufferedReader / BufferedReader`（行读 `readLine`）
- `InputStreamReader / OutputStreamWriter`（字节↔字符桥接，指定 charset）

### NIO（JDK 1.4+）
- **Channel + Buffer + Selector**，面向缓冲、可非阻塞、多路复用。
- `ByteBuffer / FileChannel / SocketChannel / Selector`。
- 适合高并发 IO（Netty 基于 NIO）。

### 选型
- 文本 → 字符流或 InputStreamReader 指定 UTF-8。
- 二进制 → 字节流。
- 高并发网络 → NIO / Netty / AIO。

## 延伸
""",
  links=[])

q("languages/java/template-method-pattern.md",
  "模板方法模式",
  "languages", "java", "easy",
  ["design-pattern", "template-method", "java", "oop"],
  ["中泓一线"],
  """# 模板方法模式

## 问题描述
模板方法模式简单介绍一下？

## 解答
**模板方法模式**：在父类定义算法骨架（一个 `final` 的 templateMethod 串联步骤），把可变步骤声明为抽象方法由子类实现。即"骨架不变，步骤可换"。

```java
abstract class AsyncTask {
    public final void run() {       // 模板方法，final 防止子类改骨架
        prepare();
        doExecute();                // 抽象步骤
        cleanup();
    }
    protected void prepare() { /* 默认实现 */ }
    protected abstract void doExecute();
    protected void cleanup() { /* 默认实现 */ }
}

class DownloadTask extends AsyncTask {
    @Override protected void doExecute() { /* 下载逻辑 */ }
}
```

### 优点
- 复用骨架，避免子类重复编排。
- 钩子方法（hook）提供默认实现，子类按需覆盖。

### 经典应用
- Spring `JdbcTemplate / RestTemplate / RedisTemplate` —— 都是模板方法 + Callback。
- `AbstractApplicationContext.refresh()` 是模板方法，子类 refreshBeanFactory 等步骤可定制。
- HttpServlet `service()` 调 doGet/doPost。

### 与策略模式区别
- 模板方法：用**继承**，子类覆盖个别步骤；骨架固定。
- 策略：用**组合**，整个算法可替换；上下文不变。

## 延伸
""",
  links=["backend/microservices/spring-boot-autoconfig"])

print("\nDone: concurrency + languages/java")
