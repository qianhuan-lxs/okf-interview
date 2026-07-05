#!/usr/bin/env python3
"""Coroutine / Virtual Thread docs: principle + pool antipattern."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from ikf_writer import q

DATE = "2026-07-05"

q("concurrency/coroutine-virtual-thread-principle.md",
  "协程原理 (Java VT/Kotlin/Go/Python 对比 + mount-unmount + pinning)",
  "concurrency", "", "hard",
  ["coroutine", "virtual-thread", "loom", "kotlin", "goroutine", "asyncio",
   "pinning", "java", "go", "python", "kotlin"],
  [],
  """# 协程原理 (Java VT/Kotlin/Go/Python 对比 + mount-unmount + pinning)

## 问题描述

什么是协程？和线程/进程什么区别？Java 虚拟线程怎么工作？各语言的"协程"实现有什么差别？什么是 pinning？

## 解答

## 一、协程是什么

**协程（coroutine）= 用户态、协作/抢占调度、可挂起恢复的轻量执行单元**。一个 OS 线程上可跑成千上万个协程；协程在阻塞时**主动或被动挂起（yield）**让出线程，等就绪再恢复。

| 维度 | 进程 | 线程（平台线程） | 协程/虚拟线程 |
| --- | --- | --- | --- |
| 调度者 | OS | OS | 用户态运行时/JVM |
| 切换成本 | 高（页表/TLB） | 中（内核上下文） | 低（寄存器+栈） |
| 栈 | 独立虚拟地址空间 | 固定 1MB 栈 | 几 KB~几十 KB，可增长 |
| 数量上限 | 千级 | 千级（受内存） | 百万级 |
| 是否抢占 | 是 | 是 | 协作（多数）/ 抢占（Go） |

## 二、各语言协程实现对比

### 1. Java Virtual Threads（JDK 21 GA, JEP 444）
- **M:N 调度**：M 个虚拟线程映射到 N 个载体平台线程（carrier），N 默认 = CPU 核数（共享 ForkJoinPool）。
- **continuation 机制**：VT 在 carrier 上跑；遇阻塞 I/O（JDK 已改写的 blocking point：`InputStream.read`、`Socket`、`LockSupport.park` 等）→ **unmount**，continuation 栈存到堆，carrier 释放给别的 VT；I/O 就绪 → continuation 重新提交，**remount** 到某个 carrier。
- 栈：存堆上为 continuation 对象，可增长，按需分配，几 KB 起。
- API：`Thread.startVirtualThread(Runnable)` / `Executors.newVirtualThreadPerTaskExecutor()`。
- 适合：IO 密集（HTTP、DB、RPC）。不适合：CPU 密集（用 platform pool）。
- **JDK 24 JEP 491 消除 synchronized pinning**（见下），是 JDK 24 升级的核心收益。

### 2. Kotlin Coroutines
- **suspend 函数**：编译器做 CPS（continuation-passing-style）变换，把 suspend 函数编译成接收 `Continuation` 参数的状态机。
- **CoroutineContext / Dispatcher**：`Dispatchers.Default`（CPU，ForkJoinPool-like）/ `Dispatchers.IO`（IO 池，64~线程可扩）/ `Dispatchers.Main`（UI 线程）/ `Unconfined`。
- **结构化并发**：`coroutineScope { }` / `SupervisorJob`，父作用域取消则子协程级联取消。
- `runBlocking` 桥接阻塞世界；`async`/`await`；`Channel`/`Flow` 做背压和流。
- 协程不是 OS 线程，可百万级。

### 3. Go goroutine
- **G-M-P 调度模型**：G=goroutine、M=OS 线程、P=Processor（逻辑 CPU，持有本地 run queue，`GOMAXPROCS` 控制 P 数量）。
- 抢占式（Go 1.14+ 基于信号的异步抢占）+ 协作（函数调用点）。
- 栈：初始 2KB，可增长到 1GB（按需复制）。
- 通信：`chan`（CSP 模型）+ `select`；`sync.Mutex`/`WaitGroup`。
- goroutine 泄漏：channel 没人收/发送 → goroutine 永久阻塞。

### 4. Python asyncio
- **单线程事件循环**（`asyncio.get_event_loop()`），`async def`/`await`（基于生成器/coroutine 协议）。
- **不是 M:N**：默认一个 OS 线程，协作式调度，CPU 密集任务会阻塞整个 loop（要丢 `ProcessPoolExecutor`）。
- `asyncio.gather` / `asyncio.TaskGroup`（3.11+）/ `Semaphore` 限并发。
- `uvloop` 用 libuv 加速。

### 5. Rust / Lua / JS
- Rust `async`/`await`：编译为 `Future` 状态机，零成本，运行时自选（tokio/async-std）。
- Lua coroutine：协作式，`coroutine.create`/`resume`/`yield`，无调度器（用户手动驱动）。
- JS：单线程事件循环 + Promise/async-await，本质是协程式但单线程。

## 三、Java Virtual Threads 深入

### mount/unmount 流程
```
VT.run() on carrier T1
  → socket.read() 阻塞
  → JDK 改写的 read 检测到 VT 上下文
  → unmount: continuation 栈拷到堆, VT park
  → T1 释放, 调度器把另一个 VT mount 到 T1
  → 数据到达, read 完成
  → continuation 重新入队
  → 调度器把 VT remount 到某 carrier T2 (不一定是 T1)
  → 继续 run
```

### carrier pool
- 默认 `ForkJoinPool` 共享实例，parallelism = `Runtime.availableProcessors()`。
- 可自定义：`Thread.builder().virtualThreadFactory(schedulerExecutor)`。
- carrier 数 = 并行度（CPU 核数），不是并发上限——VT 数才是并发上限。

### ThreadLocal 继承
- VT 默认继承**创建它的载体线程**的 ThreadLocal（拷贝快照）。
- 大量 VT + ThreadLocal 大对象 → 内存爆炸。**推荐用 Scoped Values（JEP 446/506, JDK 25 正式）**：不可变、共享、JVM 优化。

## 四、Pinning（虚拟线程固定，重点）

### JDK 21~23 的 pinning 场景
1. **`synchronized` 块/方法内阻塞**（最常见！）—— VT 持有 monitor 期间不能 unmount，carrier 被钉住。
2. **JNI native 帧** 内阻塞。
3. **某些 VM 操作**（类初始化等）。

### JDK 24 JEP 491：消除 synchronized pinning
- 重新实现 monitor：VT 可独立于 carrier 持有/释放 monitor，synchronized 内阻塞 I/O 也能 unmount。
- **JDK 24+ 不再推荐**把 synchronized 换 ReentrantLock 仅为避 pinning。
- 仍会 pin 的剩余场景：JNI native 帧、`Object.wait` 旧路径、个别类初始化边缘。
- 监控：`jdk.VirtualThreadPinned` JFR 事件（`-XX:StartFlightRecording`）+ `jcmd JFR.check`。

### JDK 21~23 迁移建议（已被 JEP 491 大幅缓解）
- 把 synchronized 包 I/O 的热点换成 `ReentrantLock`。
- 升级第三方库（JDBC 驱动、HTTP 客户端）到支持 VT 的版本。
- 测试期开 `jdk.tracePinnedThreads=full` 排查。

## 五、协程不是银弹

- **CPU 密集任务不要用协程**：协程数 > CPU 核数不会更快，反而增加调度开销。用 platform 线程池 + `parallelStream` / `ForkJoinPool`。
- **共享可变状态仍需同步**：协程不解决数据竞争，仍要锁/原子/CAS。
- **阻塞 native/JNI 仍钉 carrier**：JEP 491 不覆盖。
- **ThreadLocal 大对象慎用**：百万 VT × 大 ThreadLocal = 内存爆炸。

## 易错点
- 把 Java VT 当"线程池里的线程"——VT 不该池化（见 [协程池专题](concurrency/virtual-thread-pool-antipattern)）。
- 把 Python asyncio 当 M:N——是单线程协作式。
- 以为 JDK 24 完全没 pinning——JNI/Object.wait 仍可能 pin。
- 以为协程让 CPU 密集变快——只解决 IO 阻塞调度问题。
- Kotlin 协程当 OS 线程——是 CPS 变换的状态机，跑在 Dispatcher 线程池上。

## 延伸
""",
  languages=["java", "kotlin", "go", "python"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["concurrency/virtual-thread-pool-antipattern",
         "concurrency/thread-pool-principles",
         "concurrency/forkjoinpool-parallelstream",
         "concurrency/threadlocal-usage-pitfalls",
         "languages/java/jdk-version-optimization-survey",
         "languages/java/completablefuture-async-orchestration"])

q("concurrency/virtual-thread-pool-antipattern.md",
  "协程池 / 虚拟线程池 (该不该用 + 限流 + 与线程池配合)",
  "concurrency", "", "hard",
  ["coroutine", "virtual-thread", "thread-pool", "antipattern", "semaphore",
   "java", "kotlin", "go", "python"],
  [],
  """# 协程池 / 虚拟线程池 (该不该用 + 限流 + 与线程池配合)

## 问题描述

协程这么轻，还要不要池化？Java 虚拟线程要不要"虚拟线程池"？怎么限制并发数？协程和传统线程池怎么配合？各语言协程的"池"长什么样？

## 解答

## 一、核心结论：虚拟线程/协程不该池化

**"线程池"存在的两个理由：**
1. **创建/销毁 OS 线程贵**（1MB 栈 + 内核调用）→ 复用。
2. **限流**（避免同时跑成千上万任务拖垮下游/本机）。

**协程/虚拟线程使这两点失效：**
- 创建/销毁近乎免费（几 KB，JVM 内分配）→ 不需要复用。
- 限流不该靠"复用协程"——那是错位的工具。限流要用专门的限流器。

**Java 官方明确建议（JEP 444）**：
> **Don't pool virtual threads.** Virtual threads should be created per-task and discarded when the task is done.

用 `Thread.startVirtualThread(task)` 或 `Executors.newVirtualThreadPerTaskExecutor()`——**每任务一新 VT，用完即弃**，不要复用。

## 二、为什么不池化虚拟线程（深层原因）

1. **复用 = 状态污染**：池化的 VT 会带上一次任务的 ThreadLocal、继承的 scoped value、未捕获异常 handler，难清理。
2. **复用 = 占内存**：池里闲着的 VT 仍占栈内存（哪怕几 KB），不池则 GC 掉。
3. **复用 = 反模式**：VT 本就是为"百万并发、即用即弃"设计，池化让它退化回平台线程思路。
4. **限流可独立做**：池化混了"复用"和"限流"两件事，VT 时代该拆开。

## 三、那"协程池"是什么——各语言澄清

### Java Virtual Threads
- **没有"虚拟线程池"概念**。`newVirtualThreadPerTaskExecutor()` 返回的 ExecutorService 每提交一个任务就建一个新 VT，不池化 VT 本身。
- **被池化的是 carrier（载体平台线程）**：底层 ForkJoinPool 池化 carrier，parallelism = CPU 核数。这层是 JVM 管，用户不用管。

### Kotlin Coroutines
- Kotlin "协程池"通常指 **Dispatcher**（线程池，不是协程池）：
  - `Dispatchers.Default`：CPU 任务，ForkJoinPool，线程数 = CPU 核数（最少 2）。
  - `Dispatchers.IO`：IO 任务，线程数最多 64 或 `kotlinx.coroutines.io.parallelism`。
  - 自定义：`Executors.newFixedThreadPool(n).asCoroutineDispatcher()`。
- **限并发**：`Semaphore(n).withPermit { }` / `Channel(capacity)` 做 actor / `Flow.flowOn(dispatcher).buffer(n)`。
- 协程本身不池化（每 `launch`/`async` 新建），但跑在共享 Dispatcher 上。

### Go goroutine
- **不池化 goroutine**——`go f()` 即用即弃。
- 限并发：带缓冲 `chan struct{}` 当信号量（`sem := make(chan struct{}, N); sem <- struct{}{}; defer func() { <-sem }()`）。
- 控制并行度（CPU）：`runtime.GOMAXPROCS(n)`——控制 P 数（即同时跑 goroutine 的 OS 线程数）。
- "goroutine 池"是社区库（如 `ants`）为**限制 goroutine 总数**做的，不是复用 goroutine 跑多任务，而是限并发。

### Python asyncio
- **不池化协程**——`asyncio.create_task(coro())` 即用即弃。
- 限并发：`asyncio.Semaphore(n)` / `asyncio.TaskGroup` + `Semaphore` / `aiohttp.TCPConnector(limit=n)` 限连接。
- 线程池：`loop.run_in_executor(ThreadPoolExecutor(max_workers=n), blocking_fn)`——把阻塞函数丢线程池，避免阻塞事件循环。

## 四、Java 中正确限流的方式

### 1. 用 Semaphore 限 VT 并发
```java
Semaphore limiter = new Semaphore(100);   // 同时最多 100 个 VT 跑这段
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    for (var task : tasks) {
        executor.submit(() -> {
            limiter.acquire();
            try { doIO(); } finally { limiter.release(); }
        });
    }
}
```

### 2. 用阻塞队列 / 有界 ExecutorService 包下游
- 调下游服务：用 `ArrayBlockingQueue` + 固定大小 platform pool 当"下游并发闸"，VT 在队列前 park（不占 carrier），不丢吞吐又不压垮下游。

### 3. HTTP 客户端连接池
- OkHttp `Dispatcher.setMaxRequests` / `setMaxRequestsPerHost`——限并发请求，比限 VT 数更精准。
- HttpClient 连接池限连接数。

### 4. 数据库连接池
- HikariCP `maximumPoolSize`——DB 连接是真正的稀缺资源，限连接数即可，VT 数不限。

## 五、协程/虚拟线程 与 传统线程池 怎么配合

| 任务类型 | 推荐 |
| --- | --- |
| **IO 密集**（HTTP/DB/RPC/文件） | 虚拟线程，每任务一新 VT |
| **CPU 密集**（计算/编解码/序列化） | 固定大小 platform 线程池（CPU 核数）或 `parallelStream` |
| **阻塞 native/JNI** | 单独 platform 线程池（VT 跑会被 pin） |
| **阻塞旧库（不支持 VT）** | 丢 platform 线程池（`runInExecutor`） |

**Java 混用范式**：
```java
try (var vtExecutor = Executors.newVirtualThreadPerTaskExecutor();
     var cpuExecutor = Executors.newFixedThreadPool(Runtime.availableProcessors())) {
    // IO 跑 VT
    var ioFutures = ioTasks.stream().map(t -> vtExecutor.submit(() -> doIO(t))).toList();
    // CPU 跑 platform pool
    var cpuFutures = cpuTasks.stream().map(t -> cpuExecutor.submit(() -> doCPU(t))).toList();
}
```

## 六、Spring Boot 与虚拟线程

- **Spring Boot 3.2+**：`spring.threads.virtual.enabled=true` 让 Tomcat/Jetty 每请求一新 VT。
- **Spring Boot 4（Java 21+）**：在 Tomcat/Jetty handler 默认开虚拟线程（JEP 491 后基本无风险）。
- 配 HikariCP 时 DB 连接数才是瓶颈，不是线程数。

## 七、协程"池"反模式清单

- ❌ 自己写 `VirtualThreadPool` 复用 VT 跑多任务。
- ❌ 用 `Executors.newFixedThreadPool` 装 VT（VT 不该固定数量复用）。
- ❌ 用池化限流（应该用 Semaphore/连接池/Dispatcher 限流）。
- ❌ CPU 密集任务丢 VT 跑（VT 数 > 核数无收益）。
- ❌ synchronized 包大段 I/O（JDK 21~23 会 pin carrier；24+ 才安全）。
- ❌ 百万 VT + 大 ThreadLocal（内存爆炸，用 Scoped Values）。

## 易错点
- "虚拟线程池"当成传统线程池理解——是 per-task executor，不池化 VT。
- 用 `Executors.newFixedThreadPool(n).newVirtualThread...`——没有这种 API，VT executor 不可有界。
- 限流靠"少建 VT"——错，应该全建 VT + Semaphore 限同时在跑的。
- CPU 任务也丢 VT——浪费，VT 不增并行度（并行度由 carrier 数决定）。
- Spring 开 VT 后忘了调 HikariCP 连接数——连接池成瓶颈。

## 延伸
""",
  languages=["java", "kotlin", "go", "python"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["concurrency/coroutine-virtual-thread-principle",
         "concurrency/thread-pool-principles",
         "concurrency/executors-built-in-pools",
         "concurrency/forkjoinpool-parallelstream",
         "concurrency/threadlocal-usage-pitfalls",
         "languages/java/jdk-version-optimization-survey"])

print("\nDone: 2 coroutine/virtual-thread docs")
