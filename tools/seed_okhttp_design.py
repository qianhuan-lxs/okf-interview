#!/usr/bin/env python3
"""Add OkHttpClient design doc under networks/."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from ikf_writer import q

DATE = "2026-07-05"

q("networks/okhttpclient-design.md",
  "OkHttpClient 设计 (拦截器链 / 连接池 / Dispatcher / Okio)",
  "networks", "networks", "hard",
  ["okhttp", "http-client", "interceptor", "connection-pool", "dispatcher",
   "okio", "design-pattern", "android"],
  [],
  """# OkHttpClient 设计 (拦截器链 / 连接池 / Dispatcher / Okio)

## 问题描述

OkHttpClient 的整体架构？拦截器链怎么工作？连接池怎么复用？Dispatcher 怎么调度异步请求？Okio 在其中起什么作用？用了哪些设计模式？

## 解答

OkHttp 是 Square 出的 Java/Android HTTP 客户端，设计上是 Java 库设计的教科书级范本——大量经典设计模式、清晰的分层、高性能 IO。下面按"一次请求的生命周期"拆。

## 一、整体架构：Facade + Builder + 拦截器链

```
OkHttpClient (Facade，集中所有配置)
   │  newCall(Request) → Call
   ▼
RealCall
   │  execute() / enqueue(Callback)
   ▼
拦截器链 (Interceptor Chain，核心)
   ├─ 用户 Application Interceptors
   ├─ RetryAndFollowUpInterceptor  (重试 + 重定向)
   ├─ BridgeInterceptor            (补请求头 / 处理压缩 / cookie)
   ├─ CacheInterceptor             (HTTP 缓存)
   ├─ ConnectInterceptor           (从连接池拿/建连接)
   ├─ 用户 Network Interceptors
   └─ CallServerInterceptor        (真正写请求读响应)
   │
   ▼
ConnectionPool + RealConnection + HttpCodec (Okio)
```

## 二、设计模式速览

| 模式 | 在 OkHttp 中的体现 |
| --- | --- |
| **Facade** | `OkHttpClient` 集中暴露 dispatcher/proxy/authenticator/cache/...等几十个配置 |
| **Builder** | `OkHttpClient.Builder`、`Request.Builder`、`Response.Builder`、`FormBody.Builder`、`MultipartBody.Builder` |
| **Chain of Responsibility** | 拦截器链——每个 `Interceptor` 调 `chain.proceed(request)` 传给下一个 |
| **Strategy** | `CacheStrategy`（用缓存还是发网络）、`Authenticator`（鉴权策略）、`Dns`（DNS 解析策略） |
| **Object Pool** | `ConnectionPool` 复用 keep-alive 连接 |
| **Producer-Consumer** | Dispatcher 的 `readyAsyncCalls`/`runningAsyncCalls` 双队列 + ExecutorService |
| **Factory** | `Call.Factory`（OkHttpClient 实现）、`ResponseBody` |
| **Template Method** | `Interceptor.intercept` 是模板，子类填逻辑 |
| **Listener / Observer** | `EventListener` 钩子（callStart/connectStart/responseBodyStart...） |

## 三、Call：一次请求的封装

- `Call` 是接口（"一次 ready-to-execute 的请求"），`RealCall` 是实现。`OkHttpClient.newCall(request)` 工厂方法创建。
- 同步：`call.execute()` —— **在调用线程直接跑拦截器链**，阻塞返回 `Response`。
- 异步：`call.enqueue(Callback)` —— 包成 `AsyncCall`（实现 `Runnable`）交给 `Dispatcher` 调度。
- `cancel()`：取消（中断 IO，标记 canceled）。
- 一个 `Call` 只能执行一次（`executed` 标志）。

## 四、拦截器链（核心，必懂）

### Interceptor 接口
```java
public interface Interceptor {
    Response intercept(Chain chain) throws IOException;
    interface Chain {
        Request request();
        Response proceed(Request request) throws IOException;
        Connection connection();
        Call call();
        int index();
    }
}
```

### RealInterceptorChain.proceed
- 持有 `List<Interceptor> interceptors` + `int index`。
- `proceed(request)`：取 `interceptors[index]`，构造新的 `RealInterceptorChain(index+1)`，调 `interceptor.intercept(newChain)`。
- 每个 interceptor 调 `chain.proceed(request)` 把控制权交给下一个；下一层返回 `Response` 后再处理后返回上层——**洋葱模型**（请求从外到内，响应从内到外）。

### 五个内置拦截器（顺序固定）
1. **RetryAndFollowUpInterceptor**：失败重试（IO 异常）、处理重定向（3xx）、处理鉴权挑战（401/407 → 调 `Authenticator`）。维护 `StreamAllocation`/`Exchange` 生命周期，跟踪重试次数（默认 20 次跟随）。
2. **BridgeInterceptor**：补全请求头（`Host`/`Connection`/`Accept-Encoding: gzip`/`Cookie`/`User-Agent`），解压响应体（`Content-Encoding: gzip` → 自动解压并修正 `Content-Length`）。
3. **CacheInterceptor**：HTTP 缓存（RFC 7234）。有缓存且新鲜 → 直接返回缓存响应；否则发网络，网络响应可写回 `Cache`（`DiskLruCache`）。`CacheStrategy` 决定用网络还是缓存。
4. **ConnectInterceptor**：从 `ConnectionPool` 找可用连接，没有就建新 `RealConnection`（TCP/TLS 握手）。详见第六节。
5. **CallServerInterceptor**：**真正写请求读响应**——通过 `HttpCodec` 写请求行/头/体，读响应行/头/体。最后一个拦截器，不调 `proceed`。

### 用户拦截器位置
- **Application Interceptors**（`addInterceptor`）：在最外层，只调用一次（不跟随重试/重定向）——适合做统一日志、签名、改请求/响应。
- **Network Interceptors**（`addNetworkInterceptor`）：在 ConnectInterceptor 之后、CallServerInterceptor 之前，**每次实际网络调用都触发**（重定向/重试会多次）——适合做真实网络层的监控、压缩、重试。

## 五、Dispatcher：异步请求调度

- 字段：`Deque<AsyncCall> readyAsyncCalls`（待执行）、`Deque<AsyncCall> runningAsyncCalls`（执行中）、`Deque<RealCall> runningSyncCalls`（同步，仅统计）、`ExecutorService executorService`（默认 `ThreadPoolExecutor`：核心 0、max 64、SynchronousQueue、60s）。
- `enqueue(AsyncCall)`：
  1. 加入 `readyAsyncCalls`。
  2. `promoteAndExecute()`：若 `runningAsyncCalls.size() < maxRequests(64)` 且该 host 在跑数 `< maxRequestsPerHost(5)` → 移到 `runningAsyncCalls`，`executorService.execute(call)`。
  3. 否则留在 `readyAsyncCalls` 等空位。
- `finished(AsyncCall)`：从 running 移除，调 `promoteAndExecute()` 提升 ready 队首。
- **同步请求不走 Dispatcher**——直接在调用线程执行拦截器链。
- 可调 `Dispatcher.setMaxRequests`/`setMaxRequestsPerHost`/`setExecutorService` 自定义调度。
- `shutdown()`/`shutdownNow()`：关闭线程池（优雅停机）。

> Dispatcher 本质是个**信号量式限流器**：全局并发上限 + 单 host 并发上限，用双队列 + 线程池实现。

## 六、ConnectionPool：连接复用（keep-alive）

- `ConnectionPool`：默认 **5 个空闲连接、5 分钟 keep-alive**。可自定义。
- `RealConnection`：真正的 TCP/TLS socket + `HttpCodec`。带 `route`、`allocationLimit`（HTTP/2 多路复用可被多个 Call 共享）。
- `Connection` 复用判定（`Connection.isEligible`）：相同 `Address`（URL scheme+host+port+proxy+sslConfig+...）+ 连接未关闭 + 未超限。
- **清理线程**：`ConnectionPool` 有个后台 `Runnable` 定时清理空闲超时的连接（`cleanup` 算法：按"最快多久会过期"调度下次清理）。
- HTTP/2 多路复用：一个 `RealConnection` 可同时承载多个 `Exchange`（`allocationLimit > 1`），HTTP/1.x 一个连接同时只能一个。
- `StreamAllocation`/`Transmitter`：管"Call → Connection → Exchange"的分配关系，连接释放回池。

## 七、Route / RouteSelector：路由选择与故障转移

- `Address`：逻辑地址（scheme+host+port+proxy+dns+sslConfig+...）。
- `Route`：具体一条路由（proxy + InetAddress + 端口）——一个 host 可能解析出多个 IP。
- `RouteSelector`：迭代选择 `Route`，维护 `failedRoutes`，**自动跳过失败 IP**（failover 到下一个 IP）。`ProxySelector` 支持代理轮询。
- 这是 OkHttp 网络韧性的关键：DNS 多 IP + 失败 IP 跳过 + 代理 fallback。

## 八、Exchange / HttpCodec：一次 HTTP 交换

- `Exchange`：一次请求-响应交换的逻辑封装（在 `Transmitter` 之上，给拦截器用）。
- `HttpCodec`：编码请求/解码响应的抽象，两个实现：
  - `Http1ExchangeCodec`：HTTP/1.1，按行读响应头、按 Content-Length/chunked 读体。
  - `Http2ExchangeCodec`：HTTP/2，基于 `Http2Connection` 的 `Http2Stream`，多路复用。
- `Transmitter`：管 IO 状态、超时、连接绑定、异常传播。

## 九、Okio：高性能 IO 基础

OkHttp 的 IO 全用 Okio（Square 的 IO 库），不是 `java.io`/`java.nio` 直接用。

- **`Source`/`Sink`**：替代 `InputStream`/`OutputStream`，API 更简洁（`read`/`write`/`close`/`timeout`）。
- **`BufferedSource`/`BufferedSink`**：自带缓冲，提供 `readUtf8Line`/`readInt`/`writeUtf8` 等便捷方法。
- **`Buffer`（核心）**：内部是 `Segment` 双向链表，每个 `Segment` 是 8KB 字节数组。
  - **Segment 池**（`SegmentPool`）：全局复用 8KB Segment，避免反复分配。
  - **Segment 共享**：`Buffer.copyTo`/`split` 时多个 Buffer 共享同一 `Segment`（写时复制 head），**零拷贝**转移数据——这是 Okio 性能的关键。
- **`Timeout`**：每个 Source/Sink 自带 deadline timeout（OkHttp 的 connect/write/read 超时基于此）。
- 对比 `java.io`：BufferedInputStream/OutputStream 是单缓冲区，跨流拷贝要逐字节或 System.arraycopy；Okio 的 Segment 链 + 共享让大块数据移动近乎免费。

## 十、Cache：HTTP 缓存

- `Cache`：磁盘缓存，内部 `DiskLruCache`（LRU，按 URL key 存请求-响应快照）。
- `CacheInterceptor` 用 `CacheStrategy` 决策：
  - 缓存新鲜（未过 max-age）→ 直接用缓存。
  - 缓存过期但有 `ETag`/`Last-Modified` → 发条件请求（`If-None-Match`/`If-Modified-Since`）→ 304 用缓存，否则用新响应并写回 cache。
  - `no-cache`/`no-store` → 不用/不存。
- 缓存键是 URL + 请求方法。

## 十一、超时体系

- `OkHttpClient.Builder` 配置 `connectTimeout`/`readTimeout`/`writeTimeout`/`callTimeout`/`pingInterval`。
- 底层每个 `Socket`/`Source`/`Sink` 的 `Timeout` 协同：connect 阶段管 socket connect，read/write 阶段管 IO，callTimeout 管整个 Call 总时长。
- 异步 call 的 callTimeout 由 Dispatcher 线程池外的 watchdog 检查。

## 十二、WebSocket

- `OkHttpClient.newWebSocket(Request, WebSocketListener)` → `RealWebSocket`。
- 长连接、双向消息（text/binary）、ping/pong 心跳（`pingInterval`）、自动重连（在 `onFailure` 自定义）。
- 内部用 Okio 的 `BufferedSink`/`BufferedSource` + 帧编解码。

## 十三、一次完整请求的流程（串起来）

1. `client.newCall(request)` 创建 `RealCall`。
2. `call.enqueue(callback)` → `Dispatcher` 包成 `AsyncCall`，加入队列，线程池调度。
3. 线程池执行 `AsyncCall.execute()` → `getResponseWithInterceptorChain()`。
4. 拦截器链从外到内：
   - 用户 application interceptors
   - RetryAndFollowUp：建 `Transmitter`/`Exchange`，准备重试循环
   - Bridge：补头、加 gzip
   - Cache：查缓存，决定是否走网络
   - Connect：从 `ConnectionPool` 拿 `RealConnection`，没有就建（DNS→RouteSelector→TCP/TLS）
   - 用户 network interceptors
   - CallServer：`HttpCodec` 写请求行/头/体 → 读响应行/头/体
5. 响应从内到外回传，各拦截器可改响应（解压、写缓存、跟随重定向）。
6. `Dispatcher.finished()` 提升队列下一个。
7. 连接归还 `ConnectionPool`（keep-alive），空闲超时由清理线程回收。

## 十四、面试高频追问

| 问题 | 答 |
| --- | --- |
| OkHttp 最核心的设计是什么？ | 拦截器链（责任链模式），把缓存/重试/连接/编码分层解耦。 |
| Application 和 Network 拦截器区别？ | 前者最外层只调一次；后者在 Connect 后每次真实网络调用都触发（含重定向/重试）。 |
| Dispatcher 默认并发？ | 全局 64、单 host 5。 |
| 连接池默认配置？ | 5 个空闲连接、5 分钟 keep-alive。 |
| 为什么用 Okio 不用 java.io？ | Segment 链 + Segment 池 + 共享实现零拷贝大块移动，性能更好，API 更简洁。 |
| HTTP/2 连接和 HTTP/1.x 区别？ | HTTP/2 一个连接多路复用多个 Exchange；HTTP/1.x 一个连接同时只能一个。 |
| 多 IP 怎么 failover？ | RouteSelector 维护 failedRoutes，跳过失败 IP 用下一个。 |
| 同步和异步走的拦截器链一样吗？ | 一样，只是同步在调用线程跑，异步在 Dispatcher 线程池跑。 |

## 易错点
- 一个 Call 执行两次 → 抛 `IllegalStateException`。
- 同步 `execute()` 在主线程调 → ANR；要异步用 `enqueue`。
- 拿到 Response 后不 `close()` → 连接不归还、资源泄漏（try-with-resources）。
- 自定义拦截器不调 `chain.proceed` → 链断、无响应。
- 改 `OkHttpClient` 配置要 `newBuilder()` 建新实例——`OkHttpClient` 不可变，共享单例时改配置要派生。

## 延伸
""",
  languages=["java", "kotlin"], role=["sde", "backend", "android"],
  source="", status="reviewed", timestamp=DATE,
  links=["networks/tcp-handshake-teardown",
         "concurrency/thread-pool-principles",
         "concurrency/juc-concurrent-queues",
         "concurrency/aqs-principle",
         "distributed-systems/kafka-duplicate-consumption-message-loss"])

print("\nDone: OkHttpClient design doc")
