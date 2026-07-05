#!/usr/bin/env python3
"""Tomcat servlet thread pool doc."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from ikf_writer import q

DATE = "2026-07-05"

q("backend/microservices/tomcat-servlet-thread-pool.md",
  "Tomcat Servlet 线程池 (acceptCount/maxConnections/maxThreads/TaskQueue/NIO)",
  "backend", "microservices", "hard",
  ["tomcat", "servlet", "thread-pool", "taskqueue", "nio", "acceptCount",
   "maxConnections", "maxThreads", "virtual-thread", "java"],
  [],
  """# Tomcat Servlet 线程池 (acceptCount/maxConnections/maxThreads/TaskQueue/NIO)

## 问题描述

Tomcat 线程池和 JDK 的 `ThreadPoolExecutor` 一样吗？`acceptCount` / `maxConnections` / `maxThreads` 三个参数什么关系？NIO 模式下 Acceptor/Poller/Worker 怎么分工？Spring Boot 嵌入式 Tomcat 怎么调？虚拟线程后呢？

## 解答

## 一、Tomcat 用的是它自己的 ThreadPoolExecutor

不是 `java.util.concurrent.ThreadPoolExecutor`，而是 `org.apache.tomcat.util.threads.ThreadPoolExecutor`（**继承** JDK 那个并扩展）。配套队列 `TaskQueue` 也继承 `LinkedBlockingQueue` 但**重写了 `offer`/`poll`**——这是 Tomcat 调优的核心，下面详讲。

关键参数（`server.xml` `<Connector>` 或 Spring Boot `server.tomcat.*`）：

| 参数 | 默认 | 含义 |
| --- | --- | --- |
| `acceptCount` | 100 | **OS 层全连接队列**大小（`backlog`） |
| `maxConnections` | NIO 10000 / BIO=maxThreads | Tomcat 层同时持有的连接上限 |
| `maxThreads` | 200 | **Servlet 处理线程池大小** |
| `minSpareThreads` | 10 | 核心线程（常驻预热） |
| `maxIdleTime` | 60000ms | 空闲线程回收时间（非核心） |
| `connectionTimeout` | 20000ms | keep-alive 等待下一请求超时 |
| `executor` | 可选 | 引用独立 `<Executor>` 配置，多 Connector 共享 |

## 二、三层限流：从客户端到 Servlet 线程（必背）

```
客户端 TCP connect
   │
   ▼  ① OS 全连接队列（容量 = acceptCount）
   │   超了 → 客户端收到 ECONNREFUSED / 连接被丢弃
   │
   ▼  Tomcat Acceptor 线程 accept()
   │
   ▼  ② Tomcat 连接层（计数器 <= maxConnections）
   │   超了 → Acceptor 不再 accept，OS 队列堆积
   │
   ▼  NIO: Poller 检测到可读 → 派发给 Worker
   │
   ▼  ③ Servlet 线程池（ThreadPoolExecutor，size <= maxThreads）
   │   池满 → 任务入 TaskQueue 排队；队列满 → 按拒绝策略
   │
   ▼  Servlet service() → 业务代码
```

三个限流点逐级缓存压力，避免下游被压垮。

## 三、NIO 模式的线程分工（重点）

`Http11NioProtocol`（Spring Boot 默认）的 `NioEndpoint` 用 3 类线程：

| 线程 | 数量 | 职责 |
| --- | --- | --- |
| **Acceptor** | 1（默认） | 阻塞 `ServerSocket.accept()`，拿到 socket 注册到 Poller 的 Selector |
| **Poller** | `Math.min(2, CPU核)` | Selector 轮询，检测可读/可写事件，把就绪的 socket 包成任务丢给 `ThreadPoolExecutor` |
| **Worker** | ≤ `maxThreads` | 跑 Servlet 链（filter→servlet→业务） |

Acceptor 和 Poller 极少，**真正承载并发的是 Worker 池**——这就是 `maxThreads` 调优对象。

BIO 模式（已弃用）每连接一线程，`maxConnections == maxThreads`；APR/Native 用 native epoll，性能近 NIO。

## 四、TaskQueue 反 JDK 行为（核心面试点）

### JDK `ThreadPoolExecutor` 默认扩容顺序
1. 线程数 < core → 新建线程跑。
2. 线程数 == core → **入队列**。
3. 队列满 → 继续新建到 max。
4. 满 → 拒绝。

→ **队列满才扩到 max**。适合批处理：不轻易扩线程，避免上下文切换。

### Tomcat `TaskQueue` 重写 `offer` 反过来
```java
// TaskQueue.offer 伪代码
public boolean offer(Runnable r) {
    if (parent.getSubmittedCount() < parent.getMaximumPoolSize())
        return false;   // 让父类以为入队失败 → 触发新建线程到 max
    return super.offer(r);  // 已到 max 才真入队
}
```
→ **扩到 max 才排队**。理由：Web 请求对**延迟敏感**，队列长 = 尾延迟高，宁可多开线程（IO 等 socket 时让出 CPU）也要快点接请求。

⚠️ **业务池别照抄**：业务任务（尤其 CPU 密集）扩线程过头反而上下文切换重。Tomcat 这样做是因为请求线程大部分时间在等 socket/IO，开多也无害。

## 五、参数怎么调

### `maxThreads`（最关键）
- 默认 200，多数场景够。
- 调大前提：**CPU 有空、线程在等 IO**（DB/下游 RPC/外部 HTTP）。
- 上限看两个：
  1. **内存**：每线程栈 ~512KB~1MB + 请求对象 ~几 KB；400 线程 ~几百 MB。
  2. **下游承载**：maxThreads ≤ DB 连接池 + 下游服务能接的并发；超了 → 下游打满、Tomcat 线程都阻塞在等下游 → 反而更慢。
- CPU 密集接口 → 别调大，靠扩实例。

### `maxConnections`（NIO 默认 10000 够用）
- NIO 一个连接一个 socket channel，不占线程，所以可很大。
- 调小：限制服务总并发，保护下游。
- BIO 必须等于 maxThreads。

### `acceptCount`（默认 100）
- 削峰填谷：突发流量时 OS 队列先扛一会。
- 太大 → 用户等很久才被拒，体验差（不如快速拒绝 + 限流页）。
- 低延迟系统调小（10~50）；批量/能容忍排队调大。

### `minSpareThreads`
- 预热常驻线程，避免冷启动建线程延迟。
- 流量平稳的内部服务可调大减少抖动。

### `connectionTimeout` / keep-alive
- HTTP/1.1 keep-alive 复用连接——`connectionTimeout` 是连接空闲等待下一请求的超时。
- 太长：空闲连接占 `maxConnections` 名额，新请求进不来；太短：复用率低。
- 高 QPS 短连接场景调小；长轮询/WebSocket 要单独配。

## 六、Spring Boot 嵌入式 Tomcat 调优

`application.yml`：
```yaml
server:
  tomcat:
    threads:
      max: 400
      min-spare: 20
    max-connections: 10000
    accept-count: 100
    connection-timeout: 20000
    accepta-thread-count: 1   # Acceptor 线程数
```
或编程式 `TomcatServletWebServerFactory` 自定义 `Connector`/`ProtocolHandler`。

## 七、虚拟线程（Tomcat 10.1+ / Spring Boot 3.2+）

- `spring.threads.virtual.enabled=true` → **每 HTTP 请求一新虚拟线程**，不再用 Tomcat Worker 池。
- 底层 Poller/Acceptor 仍是平台线程，但 Servlet 跑在 VT 上——百万并发请求不卡 thread pool。
- **Tomcat 11 / Spring Boot 4（Java 21+）默认开启**（JEP 491 后 synchronized pinning 消除，安全）。
- 调优重心从"maxThreads 几个"转向**下游瓶颈**（DB 连接池、上游限流）——见 [协程池专题](concurrency/virtual-thread-pool-antipattern)。
- HikariCP `maximumPoolSize` 成新瓶颈，按 DB 承载调。

## 八、经典陷阱

### 1. maxThreads 远大于下游连接池
- 400 Tomcat 线程 vs 50 DB 连接 → 350 线程阻塞在等 HikariCP 连接，整体反而更慢。
- 解法：maxThreads ≈ 下游能承载的总并发（DB 连接 × 实例数 / 上游实例数）。

### 2. acceptCount 当限流
- acceptCount 是 OS 缓冲，不是限流器；用户等久了体验差。
- 真正限流用 Sentinel/Resilience4j 在业务层做，快速失败 + 降级页。

### 3. 业务任务丢 Tomcat 池跑
- Tomcat Worker 池是为 HTTP 请求短任务设计，**别在 Servlet 里 `executor.submit(长任务)` 给同一个池** → 挤占请求线程。
- 长任务/异步任务用独立业务池（见 [线程池调参](concurrency/threadpool-parameter-tuning)）。

### 4. TaskQueue 行为当业务池标准
- Tomcat TaskQueue 是为延迟敏感的请求场景定制，业务池（CPU 密集/批处理）该用 JDK 默认 offer 顺序（队列优先于扩 max）。

### 5. BIO 模式 maxConnections = maxThreads
- 老 BIO 每连接一线程，maxConnections 强等于 maxThreads；NIO/APR 才解耦。Spring Boot 默认 NIO，老配置注意。

### 6. keep-alive 占连接名额
- 长闲连接占 `maxConnections`，新连接被 Acceptor 拒入 OS 队列堆积。
- 短连接高 QPS：调小 `connectionTimeout`；WebSocket 用独立 Connector。

### 7. 单 Connector 跑多协议
- HTTP + HTTPS + AJP 多 Connector 共享 `executor` 时调优互相干扰，建议分 Connector 分 Executor。

## 九、监控

JMX MBean：`Tomcat:type=ThreadPool,name="*"` →
- `activeCount`：当前忙线程。
- `currentThreadCount`：已建线程。
- `maxThreads`：上限。
- `connectionCount`：当前连接数。

Spring Boot Actuator `/actuator/metrics/tomcat.*` 暴露同指标，配告警：
- `activeCount / maxThreads > 80%` 持续 1min → 扩容或调大。
- `connectionCount ≈ maxConnections` → 连接层瓶颈。
- 拒绝/超时计数上升 → 下游问题。

## 十、速查调优起点

| 场景 | maxThreads | maxConnections | acceptCount | 备注 |
| --- | --- | --- | --- | --- |
| 通用 Web API | 200 | 10000 | 100 | 默认够用 |
| IO 密集（重下游调用） | 400~600 | 10000 | 50 | 看下游连接池上限 |
| CPU 密集 | 100~200 | 10000 | 50 | 靠扩实例 |
| 短连接高 QPS | 200 | 5000 | 100 | 小 connectionTimeout |
| 长轮询/WebSocket | 200 | 50000 | 100 | 独立 Connector |
| JDK21+ 虚拟线程 | (不配) | 10000 | 100 | 每请求一 VT |

## 易错点
- 把 Tomcat `ThreadPoolExecutor` 当 JDK 那个 → 它是子类，行为不同（TaskQueue 反转扩容顺序）。
- maxThreads 调到很大但下游没扩 → 反而更慢。
- acceptCount 当限流 → 等久了体验差。
- 业务长任务丢 Tomcat 池 → 挤占请求线程。
- BIO 还在用 → 升 NIO/APR。
- maxConnections 当 maxThreads → NIO 两者解耦，含义不同。
- 虚拟线程后忘了调 HikariCP → DB 连接成瓶颈。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["concurrency/threadpool-parameter-tuning",
         "concurrency/thread-pool-principles",
         "concurrency/virtual-thread-pool-antipattern",
         "concurrency/coroutine-virtual-thread-principle",
         "backend/microservices/spring-vs-spring-boot",
         "languages/java/jdk-version-optimization-survey"])

print("\nDone: tomcat-servlet-thread-pool")
