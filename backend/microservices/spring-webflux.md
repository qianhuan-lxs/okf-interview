---
type: question
id: backend/microservices/spring-webflux
title: Spring WebFlux (Reactor/Mono/Flux/Netty/背压 + 2026 vs 虚拟线程)
category: backend
subcategory: microservices
difficulty: hard
tags: [webflux, reactor, reactive-streams, mono, flux, netty, backpressure, r2dbc, webclient, java, spring, virtual-thread]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-07-05
---

# Spring WebFlux (Reactor/Mono/Flux/Netty/背压 + 2026 vs 虚拟线程)

## 问题描述

Spring WebFlux 是什么？和 Spring MVC 什么区别？Reactor 的 Mono/Flux 怎么用？背压怎么实现？什么时候选 WebFlux，什么时候选 MVC + 虚拟线程？

## 解答

## 一、WebFlux 是什么

Spring 5（2017）引入的**响应式 Web 框架**，与 Spring MVC（Servlet 栈，命令式）平行存在。**非阻塞 + 响应式流（Reactive Streams）**，跑在 Netty / Undertow / Tomcat reactive / Jetty reactive 上（不是 Servlet 同步模型）。

设计目的：**少量线程承载高并发 IO**——线程不阻塞等 IO，事件循环复用，吞吐高、内存低。适合 IO 密集高并发场景（API 网关、聚合服务、流式推送）。

## 二、Reactive Streams 规范（必背基础）

JDK 9 起 `java.util.concurrent.Flow` 标准化（与 RS 规范一致）。4 个接口：

| 接口 | 角色 |
| --- | --- |
| `Publisher<T>` | 数据源，`subscribe(Subscriber)` |
| `Subscriber<T>` | 消费者，`onSubscribe`/`onNext`/`onError`/`onComplete` |
| `Subscription` | 桥，`request(n)` 拉取 n 个 / `cancel()` 取消——**背压核心** |
| `Processor<T,R>` | 既是 Publisher 又是 Subscriber（中间环节） |

**背压**：消费方按自己速度 `request(n)` 拉，生产方不主动推送超出请求数。防止快生产慢消费拖垮消费者。

## 三、Reactor 核心（WebFlux 的引擎）

Reactor 是 Reactive Streams 的 Java 实现，两个核心类型：

| 类型 | 语义 | 类比 |
| --- | --- | --- |
| `Mono<T>` | 0 或 1 个元素的异步序列 | `CompletableFuture<T>` + 背压 |
| `Flux<T>` | 0..N 个元素的异步序列 | 异步 Stream + 背压 |

### 操作符（高频）
- 转换：`map` / `flatMap`（异步展开）/ `concatMap`（保序）/ `switchMap`
- 组合：`zip`（并行等齐）/ `merge`（交错）/ `concat`（顺序）
- 错误：`onErrorReturn` / `onErrorResume` / `retry(n)` / `onErrorMap`
- 背压：`onBackpressureBuffer(n)` / `onBackpressureDrop` / `onBackpressureLatest`
- 副作用：`doOnNext` / `doOnError` / `doFinally`
- 控制：`filter` / `take(n)` / `delayElements` / `timeout`

### 调度器（Scheduler）
| Scheduler | 用途 |
| --- | --- |
| `Schedulers.immediate()` | 当前线程 |
| `Schedulers.single()` | 单线程 |
| `Schedulers.boundedElastic()` | **阻塞任务专用**（弹性有界，默认 10×核数，上限 100k 任务排队） |
| `Schedulers.parallel()` | CPU 密集（ForkJoinPool，核数） |

- `publishOn(s)`：**之后**的操作符在 s 跑。
- `subscribeOn(s)`：**整个链**的源头 subscribe 在 s 跑（影响上游）。

## 四、WebFlux 编程模型

### 1. Annotated Controller（像 MVC）
```java
@RestController
@RequestMapping("/users")
public class UserController {
    @GetMapping("/{id}")
    public Mono<User> get(@PathVariable String id) {
        return userService.findById(id);   // 返回 Mono，框架订阅
    }
    @GetMapping
    public Flux<User> list() {
        return userService.findAll();      // 返回 Flux，流式写回
    }
}
```

### 2. Functional Router（函数式）
```java
@Bean
RouterFunction<?> routes(UserService svc) {
    return route(GET("/users/{id}"), req ->
        ok().body(svc.findById(req.pathVariable("id")), User.class));
}
```

## 五、WebFlux vs Spring MVC

| 维度 | Spring MVC | Spring WebFlux |
| --- | --- | --- |
| 编程模型 | 命令式阻塞 | 声明式响应式 |
| 服务器 | Servlet 容器（Tomcat/Jetty） | Netty/Undertow/Tomcat reactive |
| 线程模型 | 一请求一线程（servlet 池） | few event-loop 线程复用 |
| IO | 阻塞（JDBC/RestTemplate） | 非阻塞（R2DBC/WebClient） |
| 背压 | 无（请求一次性返回） | 有（Flux 流式 + request(n)） |
| 调试 | 栈清楚 | 栈难追（声明式 + 跨线程） |
| 学习曲线 | 平 | 陡 |
| 库兼容 | 几乎所有 Java 库 | 仅 reactive 库（或 `boundedElastic` 包阻塞调用） |

## 六、线程模型（关键陷阱：别阻塞 Event Loop）

- **Netty Event Loop**（worker，默认 ≈ CPU 核数）跑响应式链。
- **绝对不能在链里阻塞**（`Thread.sleep` / `JDBC` / `synchronized` 包阻塞 IO / 阻塞 HTTP）→ 钉住 event loop，吞吐崩。
- 必须阻塞时 → 丢 `boundedElastic`：`Mono.fromCallable(() -> jdbcCall()).subscribeOn(boundedElastic())`。
- 但这样混用就违背了 WebFlux 的初衷——不如直接用 MVC + VT。

## 七、配套生态

- **WebClient**：非阻塞 HTTP 客户端，替代 `RestTemplate`（Spring 5+ 推荐，`RestTemplate` 进 maintenance）。
- **R2DBC**：非阻塞 DB 访问规范，替代 JDBC。驱动：PostgreSQL/MySQL/H2/SQL Server 等都有。
- **Reactive Kafka / RSocket / reactive Redis (Lettuce)**。
- **Spring Data Reactive Repositories**：返回 `Mono<User>` / `Flux<User>`。

## 八、背压实战

```java
@GetMapping(value = "/events", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<Event> stream() {
    return eventRepo.findAllAsStream()
        .delayElements(Duration.ofMillis(100))   // 模拟慢生产
        .onBackpressureBuffer(1000, buf -> log.warn("drop"))
        .onErrorResume(e -> Flux.empty());
}
```
- SSE / WebSocket 流式推送是 WebFlux 的强项——背压防止慢客户端拖垮服务。
- 命令式阻塞代码 + 虚拟线程**做背压要手撸**（Semaphore/队列），不如 Flux 自然。

## 九、2026 年最关键问题：WebFlux vs MVC + 虚拟线程

JDK 21 虚拟线程 + Spring Boot 3.2（`spring.threads.virtual.enabled=true`）改变了格局：**MVC 写阻塞代码也能拿到接近 WebFlux 的吞吐**。

### 基准对比（典型 IO 密集，10k 并发）
| 方案 | 吞吐 | 说明 |
| --- | --- | --- |
| MVC + 200 平台线程（旧默认） | ~3.5k req/s | 80% 饱和后延迟飙升 |
| WebFlux | ~14k req/s | 延迟平稳 |
| **MVC + 虚拟线程** | 接近 WebFlux | 阻塞代码 + 一行配置 |

### 2026 业界共识决策表

| 场景 | 推荐 |
| --- | --- |
| 普通 CRUD / REST API / 内部微服务 | **MVC + 虚拟线程**（默认） |
| 调多个外部 IO 的同步业务编排 | MVC + VT（直写阻塞代码，无 `Mono.zip` 套娃） |
| 团队没 reactive 经验 | MVC + VT |
| **流式推送（SSE/WebSocket fan-out）** | **WebFlux**（背压是它强项） |
| 100k+ 持久 WebSocket 连接 | WebFlux + Netty |
| Kafka Streams / RSocket / 已有 reactive 生态 | **WebFlux** |
| CPU 密集 | 固定 platform 线程池 / `parallelStream`（VT 无收益） |
| 极致低延迟 + 超高并发网关 | WebFlux 仍略优 |

### 为什么 VT 抢了 WebFlux 大部分地盘
- **代码简单**：阻塞代码可读、可调试，栈正常。
- **库兼容广**：JDBC/JPA/任何阻塞库都能直接用。
- **学习曲线 0**：Java 开发者本就会。
- **配置一行**：`spring.threads.virtual.enabled=true`。
- WebFlux 的复杂度税（reactive 学习曲线、调试难、生态受限）只对**流式/背压/已有 reactive 投入**值得。

### VT 时代的坑（迁移要小心）
- **JDK 21~23 synchronized 包 IO 会 pin carrier** → JDK 24 JEP 491 消除（详见 [虚拟线程原理](concurrency/coroutine-virtual-thread-principle)）。
- ThreadLocal 大对象 × 百万 VT → 内存爆炸，用 Scoped Values。
- HikariCP 连接池成新瓶颈，要按 DB 承载调。
- 三方库旧版本可能仍 pin（JDBC 驱动、HTTP 客户端老版本）。

### 双向迁移成本
- WebFlux → MVC+VT：撕掉所有 `Mono`/`Flux`、改 controller 签名、换 reactive 驱动 → **3~6 个月**。
- MVC+VT → WebFlux：同样 3~6 个月反向。
- 不为性能迁——为可维护性迁。

## 十、WebFlux 经典陷阱

### 1. 阻塞 Event Loop
- `Thread.sleep` / JDBC / `synchronized` 包阻塞 IO / 阻塞 HTTP / `Object.wait` → 整个 event loop 卡死。
- 检测：`BlockHound`（Reactor 提供，运行时检测阻塞调用）。

### 2. 忘记 `subscribe()` / 没组装链
- `Mono`/`Flux` 是冷发布者，**没人订阅就不执行**。
- 控制器返回 `Mono` 由框架订阅；自己调用业务 `Mono` 须 `flatMap` 进链而非 `.subscribe()` 然后丢。

### 3. `flatMap` vs `concatMap` 顺序
- `flatMap` 并发执行不保序；`concatMap` 保序但慢。按需选。

### 4. 错误处理漏
- 响应式链异常不会自动抛到外面——必须 `onErrorResume`/`onErrorReturn` 兜底，否则订户收到 `onError` 终止，HTTP 500。

### 5. 无限 buffer 内存泄漏
- `onBackpressureBuffer()` 无上限 → 慢消费者堆积爆内存；用 `onBackpressureBuffer(n, ...)` 限。

### 6. Hot vs Cold
- 大部分 Reactor 源是 **Cold**（每次 subscribe 重新产生）；`share()`/`cache()`/`replay()` 转 Hot。误用导致重复执行或共享副作用。

### 7. ThreadLocal 不传递
- 响应式链跨线程，`ThreadLocal` 默认不传 → 用 `Reactor Context` 或 `MDC` 配 `Hooks.enableAutomaticContextPropagation()`。

### 8. 混用阻塞库不丢调度器
- 在 event loop 线程调 JDBC → 卡死。要 `subscribeOn(boundedElastic())`。

## 十一、调试

- `Hooks.onOperatorDebug()` 开调试模式，栈带操作符位置。
- `Mono.log()` 链路上每个事件打日志（含线程名）。
- `BlockHound` 集成测试期检测阻塞。
- 比 MVC 调试难得多——这是 WebFlux 复杂度税的核心。

## 十二、速查决策（2026）

```
新服务 + IO 密集 + 团队普通 → Spring MVC + spring.threads.virtual.enabled=true
新服务 + SSE/WebSocket 流式 / 100k+ 连接 / Kafka Streams / 已有 reactive → WebFlux
CPU 密集 → MVC + 固定 platform 线程池（VT 无收益）
老 WebFlux 服务运行良好 → 别为性能迁，迁要算可维护性账
```

## 易错点
- 把 WebFlux 当 MVC 的"升级版" → 是平行栈，不是替代关系。
- 在响应式链里阻塞 → 钉 event loop，吞吐崩。
- 忘 `subscribe()` → Mono/Flux 不执行。
- `flatMap` 当 `map` 用 → 并发不保序，bug 难发现。
- 错误不处理 → 订户静默收到 onError，HTTP 500。
- 无限 `onBackpressureBuffer` → 内存爆。
- JDK 21~23 用 VT 还开 WebFlux → 双重复杂度，多数场景该二选一。
- 2026 还盲目推 WebFlux 给 CRUD → 已不是默认，VT 抢了大部分场景。

## 延伸

## 延伸

- 关联题：[[concurrency/coroutine-virtual-thread-principle]]
- 关联题：[[concurrency/virtual-thread-pool-antipattern]]
- 关联题：[[backend/microservices/tomcat-servlet-thread-pool]]
- 关联题：[[backend/microservices/spring-vs-spring-boot]]
- 关联题：[[languages/java/jdk-version-optimization-survey]]
- 关联题：[[languages/java/completablefuture-async-orchestration]]
