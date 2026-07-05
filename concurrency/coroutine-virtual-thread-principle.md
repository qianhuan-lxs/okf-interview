---
type: question
id: concurrency/coroutine-virtual-thread-principle
title: 协程原理 (Java VT/Kotlin/Go/Python 对比 + mount-unmount + pinning)
category: concurrency
subcategory: ""
difficulty: hard
tags: [coroutine, virtual-thread, loom, kotlin, goroutine, asyncio, pinning, java, go, python, kotlin]
languages: [java, kotlin, go, python]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-07-05
---

# 协程原理 (Java VT/Kotlin/Go/Python 对比 + mount-unmount + pinning)

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

## 延伸

- 关联题：[[concurrency/virtual-thread-pool-antipattern]]
- 关联题：[[concurrency/thread-pool-principles]]
- 关联题：[[concurrency/forkjoinpool-parallelstream]]
- 关联题：[[concurrency/threadlocal-usage-pitfalls]]
- 关联题：[[languages/java/jdk-version-optimization-survey]]
- 关联题：[[languages/java/completablefuture-async-orchestration]]
