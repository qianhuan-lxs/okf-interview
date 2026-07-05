#!/usr/bin/env python3
"""Thread pool parameter tuning classic doc."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from ikf_writer import q

DATE = "2026-07-05"

q("concurrency/threadpool-parameter-tuning.md",
  "线程池参数怎么设 (7 参数 / CPU-IO 公式 / 队列 / 拒绝策略 / 动态调参 / 陷阱)",
  "concurrency", "", "hard",
  ["thread-pool", "threadpool", "tuning", "cpu-bound", "io-bound",
   "queue", "reject-policy", "monitoring", "java"],
  [],
  """# 线程池参数怎么设 (7 参数 / CPU-IO 公式 / 队列 / 拒绝策略 / 动态调参 / 陷阱)

## 问题描述

线程池参数怎么设？CPU 密集和 IO 密集分别多少？队列怎么选？拒绝策略怎么选？线上怎么动态调？有哪些经典陷阱？

## 解答

## 一、先认清 7 个参数（`ThreadPoolExecutor` 构造）

```java
new ThreadPoolExecutor(
    int corePoolSize,                  // 1. 核心线程数
    int maximumPoolSize,               // 2. 最大线程数
    long keepAliveTime, TimeUnit unit, // 3+4. 非核心空闲存活时间
    BlockingQueue<Runnable> workQueue, // 5. 任务队列
    ThreadFactory threadFactory,       // 6. 线程工厂（命名、daemon、UncaughtExceptionHandler）
    RejectedExecutionHandler handler   // 7. 拒绝策略
)
```

| 参数 | 作用 | 调优要点 |
| --- | --- | --- |
| `corePoolSize` | 常驻线程 | 多数场景 = max（见下"要不要弹性"） |
| `maximumPoolSize` | 上限线程 | CPU 密集 ~N+1；IO 密集 ~2N 起 |
| `keepAliveTime` | 非核心线程空闲回收时间 | 弹性池才设，常 60s |
| `workQueue` | 任务排队 | **必须有界**，否则 max 永不触发 + OOM 风险 |
| `threadFactory` | 建线程 | 必给命名（`AtomicInteger` 编号 + 业务前缀）+ 设 UncaughtExceptionHandler |
| `handler` | 满了怎么办 | 线上兜底 `CallerRunsPolicy`（反压）；交易类 `AbortPolicy`+告警 |

## 二、按任务类型估线程数（经典公式 + 批判）

### 1. CPU 密集（纯计算：编解码、序列化、加密、数值）
- 推荐 **`N + 1`**（N = CPU 核数）。
- +1 防偶发停顿（GC、缺页）让 CPU 不闲置。
- **多于 N 无益**：CPU 已打满，更多线程只增加上下文切换。

### 2. IO 密集（网络/磁盘/DB）
- 经典：**`2N`** 起。
- **Brian Goetz 公式**（更精确）：
  `threads = N * U * (1 + W/C)`
  - `N` = 核数，`U` = 目标 CPU 利用率（0~1），`W` = 任务等待时间，`C` = 任务计算时间。
  - 例：8 核、U=1、W:C=10:1 → `8 * 1 * (1+10) = 88` 线程。
- 直觉：线程大部分时间在等 IO，多开几个填满等待空隙。

### 3. 混合型（既有 CPU 又有 IO）
- 拆两个池：CPU 任务一池（N+1），IO 任务一池（2N+）。
- 不拆 → 一个任务算一半堵 IO 一半占 CPU，参数难调。

### 4. 公式的局限（面试加分点）
- **假设单核线性**：现代 CPU 有超线程、NUMA，N 不一定准。
- **忽略队列**：公式只算线程，没算队列容量——队列大小直接影响延迟和内存。
- **忽略下游瓶颈**：IO 线程数不该超过下游能承受并发（DB 连接池、对端 QPS 限流）。
- **忽略 GC/JIT 抖动**：高负载时 JVM 停顿让"理论线程数"失真。
- **实测为准**：压测调，公式只是起点。

## 三、core vs max：要不要弹性？

| 方案 | 适用 | 说明 |
| --- | --- | --- |
| `core == max` 固定 | 多数线上 | 行为可预测，避免频繁建/销线程 |
| `core < max` 弹性 | 流量波动大 | 队列满才扩到 max，需配 `allowCoreThreadTimeOut=true` 让核心也能回收 |

- **弹性池的坑**：队列满才扩容——如果队列太大，max 永远不触发（等于固定 core 池）。所以**弹性必须配小队列**（如 `SynchronousQueue` 直接握手，或 `ArrayBlockingQueue` 容量小）。
- Tomcat 用 `TaskQueue`（继承 `LinkedBlockingQueue` 重写 `offer`）让 max 先于队列生效——业务池别照抄。

## 四、队列怎么选

| 队列 | 行为 | 用在哪 |
| --- | --- | --- |
| `ArrayBlockingQueue` | 有界 FIFO | **推荐默认**，行为可预测 |
| `LinkedBlockingQueue` | 默认 `Integer.MAX_VALUE` 无界 | ⚠️ 别用默认，要么设容量要么换 Array |
| `SynchronousQueue` | 直接握手（无容量） | `CachedThreadPool`，高吞吐但可瞬时建 max 线程 |
| `PriorityBlockingQueue` | 优先级 | 任务有优先级（要 Comparable） |
| `DelayQueue` | 延迟取 | 定时任务（`ScheduledThreadPool` 用 `DelayedWorkQueue`） |

### 队列容量怎么定
- 不该"尽量大"——队列大 = max 不触发 + 内存压力 + 延迟堆积。
- 按**可接受延迟**算：`容量 = 可接受延迟 / 单任务平均耗时 × 并发线程数`。
- 按**内存**算：任务对象大小 × 容量 ≤ 预算。
- 线上常配 **几百~几千**，配合监控告警。

## 五、拒绝策略选型

| 策略 | 行为 | 用在哪 |
| --- | --- | --- |
| `AbortPolicy`（默认） | 抛 `RejectedExecutionException` | 调用方必须处理；交易/关键路径 + 告警 |
| `CallerRunsPolicy` | 调用线程自己跑 | **线上兜底反压**——降速保护下游 |
| `DiscardPolicy` | 静默丢 | ⚠️ 慎用，问题难发现 |
| `DiscardOldestPolicy` | 丢队首老任务再入队 | 丢弃过期任务（实时报价等） |
| 自定义 | 记日志+降级+持久化重试 | 高可靠场景 |

线上常见：`CallerRunsPolicy` 反压 + 监控拒绝次数 + 告警阈值。

## 六、线程工厂 + 异常处理（常被忽略）

```java
ThreadFactory factory = r -> {
    Thread t = new Thread(r, "biz-pool-" + name.getAndIncrement());
    t.setUncaughtExceptionHandler((thr, ex) ->
        log.error("thread {} uncaught", thr.getName(), ex));
    t.setDaemon(false);
    return t;
};
```
- **必须命名**：jstack/arthas 里全是 `pool-1-thread-3` → 排查灾难。
- **必须捕获**：`Runnable` 抛出未捕获异常会让 Worker 线程退出（线程数悄悄降），任务静默丢失。要么 `Thread.setUncaughtExceptionHandler`，要么 `Runnable` 内 `try-catch`。
- `FutureTask` 内异常会被 `Future.get()` 包 `ExecutionException` 抛——不调 `get()` 的话**任务异常静默**。

## 七、动态调参（线上不停机）

### 1. JDK 自带
- `ThreadPoolExecutor.setCorePoolSize(int)` / `setMaximumPoolSize(int)`：**运行时改**，HotSpot 不重建实例。
- 配合配置中心（Nacos/Apollo）监听改值。

### 2. 开源方案
- **美团 Dynamic-TP**、**Hippo4j**：基于配置中心 + 监控告警，可视化调参。
- 监控指标：活跃线程数、队列大小、已完成任务数、拒绝次数、最大耗时。

### 3. 钩子监控
```java
@Override protected void beforeExecute(Thread t, Runnable r) { ctx.set(System.nanoTime()); }
@Override protected void afterExecute(Runnable r, Throwable ex) {
    long cost = System.nanoTime() - ctx.get();
    metrics.record(cost); if (ex != null) log.error("task fail", ex);
}
```
推到 Prometheus / Micrometer，配告警：拒绝次数 > 0、队列占用 > 80%、活跃线程 = max 持续 > 1min。

## 八、经典陷阱（高频面试追问）

### 1. 父子任务同池 → 死锁/饥饿
- `CompletableFuture` 链 / `thenCombine` / `allOf`：父任务占线程等子任务，子任务又排队等线程 → **池满互等**。
- 解法：父子用**不同池**，或子任务用 `ForkJoinPool.commonPool()`（注意 commonPool 也可能满）。

### 2. 队列无界 → max 永不触发 + OOM
- `Executors.newFixedThreadPool` 用无界 `LinkedBlockingQueue` → 任务堆积 OOM。阿里规约禁止 `Executors` 工厂方法，要求手动 `new ThreadPoolExecutor` + 有界队列。

### 3. ThreadLocal 不传递
- 父线程的 ThreadLocal 不会自动到池线程——要用 `TransmittableThreadLocal`（阿里 TTL）或显式传上下文（TraceId/MDC）。

### 4. 长任务饿死短任务
- 一个池里跑 30s 长任务 + 100ms 短任务 → 长任务占满 core，短任务全进队列堆积。
- 解法：**隔离池**——长任务慢池、短任务快池。

### 5. 任务间有依赖 → 池满互等
- A 任务 submit B 任务等 B 结果 → A 占线程等 B，B 在队列 → 死锁式阻塞。

### 6. Spring `@Async` 默认池
- `@Async` 不配 `TaskExecutor` 时用 `SimpleAsyncTaskExecutor`——**每次新建线程，不池化**！必须显式配 `ThreadPoolTaskExecutor` bean。

### 7. Tomcat 线程池与业务池要分
- Tomcat 用 `TaskQueue`（重写 `offer`）让 max 先于队列生效——业务池**别照抄** Tomcat 行为。

### 8. CPU 密集开太多线程
- N=8 开 80 线程 → 上下文切换比计算还重，吞吐反降。

## 九、与虚拟线程的关系（JDK 21+）

- **IO 密集** → 直接用虚拟线程（`newVirtualThreadPerTaskExecutor`），不用纠结池大小，每任务一新 VT（详见 [协程池专题](concurrency/virtual-thread-pool-antipattern)）。
- **CPU 密集** → 仍用固定大小 platform 池（N+1），VT 无收益。
- **混合** → IO 跑 VT，CPU 跑 platform 池。
- VT 时代"线程池参数怎么设"的痛点**主要消失**——只 CPU 池仍要调。

## 十、速查决策表

| 场景 | core/max | 队列 | 拒绝策略 |
| --- | --- | --- | --- |
| CPU 密集 | N+1 / N+1 | 有界小（100~500） | Abort+告警 |
| IO 密集（传统） | 2N~10N / 同 | 有界中（500~2000） | CallerRuns 反压 |
| IO 密集（JDK21+） | 虚拟线程，无池 | — | — |
| 突发流量 | N / 2N~5N | SynchronousQueue 或小队列 | CallerRuns |
| 实时低延迟 | N+1 / N+1 | SynchronousQueue | Abort+告警 |
| 后台批处理 | 弹性 | 大队列 | DiscardOldest |

## 易错点
- 公式当万能 → 公式是起点，必须压测。
- 队列无界 → OOM + max 永不触发。
- 线程不命名 → jstack 排查灾难。
- 任务不 try-catch → Worker 退出线程数悄悄降。
- 父子同池 → 死锁。
- @Async 不配池 → 每次新建线程。
- 长短任务同池 → 短任务饿死。
- 弹性池配大队列 → max 永不触发（等于固定 core）。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["concurrency/thread-pool-principles",
         "concurrency/threadpool-source-analysis",
         "concurrency/executors-built-in-pools",
         "concurrency/completablefuture-async-orchestration",
         "concurrency/threadlocal-usage-pitfalls",
         "concurrency/virtual-thread-pool-antipattern",
         "concurrency/forkjoinpool-parallelstream"])

print("\nDone: threadpool-parameter-tuning")
