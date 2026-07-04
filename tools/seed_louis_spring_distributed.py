#!/usr/bin/env python3
"""Seeder: Spring / microservices / distributed-theory from 2026-05 Louis面经."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from seed_louis_ai import q

# --- backend/microservices/ ------------------------------------------------ #

q("backend/microservices/spring-boot-autoconfig.md",
  "Spring Boot 自动配置原理",
  "backend", "microservices", "medium",
  ["spring-boot", "autoconfig", "spring", "java"],
  ["恩士讯", "海颐"],
  """# Spring Boot 自动配置原理

## 问题描述
Spring Boot 的自动配置原理是什么？

## 解答

### 入口：@SpringBootApplication
- = `@SpringBootConfiguration` + `@EnableAutoConfiguration` + `@ComponentScan`。

### 核心：@EnableAutoConfiguration
- 通过 `@Import(AutoConfigurationImportSelector.class)` 引入选择器。
- `AutoConfigurationImportSelector.selectImports()` 调 `SpringFactoriesLoader.loadFactoryNames(...)`，从所有 jar 的 `META-INF/spring.factories`（2.7+ 改用 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`）加载 `EnableAutoConfiguration` 配置的全限定名列表。
- 加载后逐个 `@Conditional` 过滤：
  - `@ConditionalOnClass` —— classpath 有指定类才生效（如引入 Redis starter 才有 RedisAutoConfig）。
  - `@ConditionalOnMissingBean` —— 用户没自定义才生效（默认配置可被覆盖）。
  - `@ConditionalOnProperty` —— 配置项满足才生效。
  - `@ConditionalOnWebApplication` 等。

### 优势
- "约定大于配置"：引入 starter 即生效默认配置。
- 用户自定义 Bean 优先（@ConditionalOnMissingBean 兜底）。

### 自定义 starter
- 写 `XxxAutoConfiguration` + `@ConditionalOnClass` + `@ConditionalOnProperties`。
- 在 `META-INF/spring/...AutoConfiguration.imports` 注册。
- 配 `@ConfigurationProperties` 暴露配置项。

## 易错点
- 以为自动配置全量加载 —— 实际是按 Conditional 动态裁剪。
- 排查"为什么没生效"：开 `--debug` 看 `Conditions Evaluation Report`。

## 延伸
""",
  links=["backend/microservices/spring-vs-spring-boot",
         "backend/microservices/spring-ioc-di-injection",
         "languages/java/template-method-pattern"])

q("backend/microservices/spring-vs-spring-boot.md",
  "Spring 和 Spring Boot 的区别",
  "backend", "microservices", "easy",
  ["spring", "spring-boot", "java"],
  ["海颐"],
  """# Spring 和 Spring Boot 的区别

## 解答

| 维度 | Spring | Spring Boot |
| --- | --- | --- |
| 定位 | 框架（IoC/AOP 容器 + 生态） | 之上做的"约定配置 + 起步依赖"封装 |
| 配置 | 大量 XML / 注解，需手动配 | 自动配置 + application.yml，零 XML |
| 依赖 | 手动管 jar 版本 | starter 聚合版本，开箱即用 |
| 内嵌容器 | 需部署 war 到 Tomcat | 内嵌 Tomcat/Jetty/Undertow，jar 直接跑 |
| 监控 | 自建 | actuator 开箱（/health /metrics） |
| 生产 | 配一堆才能跑 | `java -jar` 即跑 |

一句话：Spring 是引擎，Spring Boot 是装好引擎+座椅+方向盘的整车，开箱即开。

## 延伸
""",
  links=["backend/microservices/spring-boot-autoconfig",
         "backend/microservices/spring-ioc-di-injection"])

q("backend/microservices/spring-ioc-di-injection.md",
  "Spring IOC / DI 注入方式",
  "backend", "microservices", "easy",
  ["spring", "ioc", "di", "java", "injection"],
  ["海颐"],
  """# Spring IOC / DI 注入方式

## 问题描述
说一下 Spring 的注入方式有哪一些？再说一下你对 IOC 的理解。

## 解答

### IOC（Inversion of Control）
- 对象创建和依赖关系**由容器管理**，而非对象自己 new。
- "控制"指对象创建控制权，反转 = 从对象转移到容器。
- 好处：解耦、易测试（mock）、生命周期统一。

### DI（Dependency Injection）—— IOC 的实现方式
- 容器主动把依赖"注入"对象，对象被动接收。

### 注入方式（3 种）
1. **构造器注入**（推荐）：`@Autowired` 在构造方法。不可变、强制依赖、易测、避免循环依赖（启动期暴露）。
2. **Setter 注入**：可选依赖，可重新注入。
3. **字段注入** `@Autowired private X x;`：最简洁但**不推荐**——不能 final、无法脱离容器测试、隐藏依赖。

### @Resource vs @Autowired
- `@Autowired` byType，可选 `@Qualifier` byName。
- `@Resource`（JSR-250）默认 byName，找不到再 byType。

### 循环依赖
- Spring 用三级缓存解决单例 setter/字段循环依赖：singletonObjects / earlySingletonObjects / singletonFactories。
- **构造器循环依赖无法解决**（对象都还没建出来）。
- Spring Boot 2.6+ 默认 `spring.main.allow-circular-references=false`。

## 易错点
- 字段注入 + 循环依赖能跑但埋雷；新代码强制构造器注入。

## 延伸
""",
  links=["backend/microservices/spring-vs-spring-boot",
         "backend/microservices/spring-boot-autoconfig"])

q("backend/microservices/spring-cloud-microservice-ecosystem.md",
  "Spring Cloud 微服务生态",
  "backend", "microservices", "medium",
  ["spring-cloud", "microservices", "service-discovery", "gateway", "config"],
  ["中泓一线"],
  """# Spring Cloud 微服务生态

## 问题描述
Spring Cloud 有吗？微服务的这些生态应该是不是？

## 解答

Spring Cloud 是微服务治理全家桶，分两套主流栈：**Netflix（停更）** 和 **Alibaba**。

| 治理能力 | Spring Cloud Netflix | Spring Cloud Alibaba |
| --- | --- | --- |
| 注册中心 | Eureka | Nacos / Eureka |
| 配置中心 | Config + Bus | Nacos Config |
| 网关 | Zuul（1 停更）/ Spring Cloud Gateway | Gateway / Higress |
| 负载均衡 | Ribbon（停更）→ LoadBalancer | LoadBalancer / Dubbo 内置 |
| 声明式调用 | Feign / OpenFeign | OpenFeign / Dubbo RPC |
| 熔断限流 | Hystrix（停更）→ Resilience4j | Sentinel |
| 链路追踪 | Sleuth + Zipkin | SkyWalking / Zipkin |
| 分布式事务 | — | Seata |

### 核心组件职责
- **注册中心**：服务上下线发现，心跳保活。
- **配置中心**：动态配置，热刷新（`@RefreshScope`）。
- **网关**：统一入口、路由、鉴权、限流、跨域。
- **熔断器**：下游故障时快速失败、降级，防雪崩。
- **RPC**：服务间调用。

### 选型建议（2026）
- 新项目：Nacos + Gateway + OpenFeign + Sentinel + Seata。
- 监控：SkyWalking / OpenTelemetry + Prometheus + Grafana + Loki。

## 延伸
""",
  links=["backend/microservices/spring-boot-autoconfig",
         "distributed-systems/cap-theory",
         "backend/microservices/microservice-user-context-propagation"])

q("backend/microservices/microservice-user-context-propagation.md",
  "微服务跨服务用户上下文传递 (设计题)",
  "backend", "microservices", "hard",
  ["microservice", "context-propagation", "threadlocal", "redis", "design"],
  ["中泓一线"],
  """# 微服务跨服务用户上下文传递 (设计题)

## 问题描述
用户信息基础服务，多个业务服务需要获取用户信息，怎么设计使得带宽性能高、并发最高？不同微服务什么时候放到 ThreadLocal？怎么获取上下文信息？业务服务从哪里获取？在哪个阶段查 Redis？用户 ID 从哪里来？

## 思路

目标是**最小化重复查询、最小化跨服务带宽、最大化并发**。核心：**用户 ID 沿链路透传，用户详细信息本地缓存懒加载**。

## 解答

### 全链路设计

1. **入口（网关层）**
   - 网关解析 JWT/token → 拿到 `userId`、`tenantId`、`roles`。
   - 把 `userId` 等轻量身份信息塞进 HTTP 头 `X-User-Id` / `X-Tenant-Id` 透传下游。
   - **不在网关查用户详情**（避免网关成为瓶颈）。

2. **业务服务接收（Filter/Interceptor）**
   - 在 Servlet Filter / Spring Interceptor 拦截，从请求头读 `userId`。
   - 把 `userId` 放进当前线程 `ThreadLocal`（或 RequestScope Context）。
   - 此时 ThreadLocal 只放 **userId 等轻量字段**，不放整个 User 对象。

3. **懒加载用户详情 + 多级缓存**
   - 业务代码用 `UserContext.getUserId()` 拿到 id 后，需要详情时走：
     - **L1 进程内缓存（Caffeine）**：1~5s TTL，热点 user 命中率高、零网络。
     - **L2 Redis 缓存**：进程缓存未命中 → 查 Redis，缓存用户 JSON，5~30min TTL。
     - **L3 用户服务 + DB**：Redis 未命中 → 调用户基础服务（带本地缓存兜底）。
   - 用 **Cache-Aside**：读时回填，写时失效（用户信息变更发 MQ 广播失效）。

4. **查 Redis 的时机**
   - 不在 Filter 阶段全局查（每个请求都查会浪费，很多请求不需详情）。
   - 在 **业务代码第一次访问 UserContext.getUserDetail()** 时按需查缓存。可用 `Supplier.memoized` / `ThreadLocal` 存已加载的 User 对象，**同请求内只查一次**。

5. **跨线程透传**
   - 异步/线程池场景用 `TransmittableThreadLocal` 或 `TaskDecorator` 把 userId/userContext 透传到子线程，避免上下文丢失。

6. **RPC 透传**
   - OpenFeign/Dubbo 用 RequestInterceptor / Filter 把 `X-User-Id` 自动加到下游调用头。

### 性能要点
- **userId 走 Header，不查 DB**——零开销。
- **详情懒加载 + 进程缓存**——同一服务对同一 user 的 N 次访问只查一次外部。
- **Redis Pipeline / 本地缓存兜底**——高并发下 Redis 也不成瓶颈。
- **不要每个服务都全量查用户信息**——只取需要的字段，用 projection。

### 防雪崩
- 用户服务故障时本地缓存继续撑、Sentinel 降级返回最小信息（仅 userId + 默认权限）。

## 易错点
- 在 Filter 里无脑查用户详情 → 每个请求都查，浪费严重。
- ThreadLocal 不 remove → 线程池脏数据/泄漏（见 [[concurrency/threadlocal-threadpool-problems]]）。

## 延伸
""",
  links=["concurrency/threadlocal-usage-pitfalls",
         "concurrency/threadlocal-threadpool-problems",
         "databases/redis-cache-avalanche",
         "backend/microservices/spring-cloud-microservice-ecosystem"])

# --- distributed-systems/ -------------------------------------------------- #

q("distributed-systems/cap-theory.md",
  "CAP 理论",
  "distributed-systems", "distributed-systems", "easy",
  ["cap", "consistency", "availability", "partition-tolerance", "distributed"],
  ["中泓一线"],
  """# CAP 理论

## 问题描述
分布式基本理论有接触吗？CAP？

## 解答
CAP：分布式系统在**分区（P）发生时**，只能在 **C（一致性）** 和 **A（可用性）** 之间二选一。

- **C (Consistency)**：所有节点同一时刻看到相同数据（线性一致性）。
- **A (Availability)**：每个请求都能收到非错误响应（不保证是最新）。
- **P (Partition tolerance)**：网络分区时系统继续运作。

### 关键澄清
- **P 不是可选的**——网络必定会分区，工程上必须保证 P。所以实际是 **CP vs AP** 二选一。
- **无分区时 CA 可兼得**；分区发生时必须取舍。

### 工程对照
| 系统 | 取舍 | 说明 |
| --- | --- | --- |
| ZooKeeper / etcd / HBase | CP | 分区时少数派不可用，保一致 |
| Eureka / Cassandra / Redis Cluster（部分场景） | AP | 分区时各分区自服务，允许不一致，最终一致 |
| MySQL 主从 | 默认 AP（异步复制） | 主从延迟，从库可读旧数据 |

### BASE
CAP 工程折中：**Basically Available + Soft state + Eventually consistent**——多数互联网系统选 AP + 最终一致。

## 延伸
""",
  links=["distributed-systems/distributed-election",
         "distributed-systems/distributed-lock-redis-vs-zk"])

q("distributed-systems/distributed-election.md",
  "分布式选举",
  "distributed-systems", "distributed-systems", "medium",
  ["election", "leader", "raft", "paxos", "bully", "distributed"],
  ["恩士讯"],
  """# 分布式选举

## 问题描述
分布式选举你了解哪一块？

## 解答

**选举**：集群中选一个 master/leader 节点协调工作，避免多主冲突。

### 常见算法

| 算法 | 思路 | 应用 |
| --- | --- | --- |
| **Bully** | 选 id 最大的节点当 leader，简单粗暴 | 较少生产用 |
| **Raft** | 任期(term) + 多数派投票，强领导者，易理解 | etcd / Consul / TiKV / RocketMQ Controller |
| **ZAB**（ZooKeeper Atomic Broadcast） | 类 Paxos，epoch + 多数派 | ZooKeeper |
| **Paxos** | 经典共识，难理解 | 很少直接用，理论基石 |
| **Gossip** | 流言式传播，最终一致 | Cassandra / Redis Cluster 节点发现 |

### Raft 要点（最常考）
- 节点三态：Follower / Candidate / Leader。
- **Leader 心跳**：Leader 定期发 AppendEntries 心跳，Follower 超时未收到则转 Candidate。
- **选举**：Candidate 自增 term、投票给自己、RequestVote 给其他节点；获多数派票则成 Leader。
- **任期（term）** 单调递增，过时 term 的消息被拒。
- **多数派（quorum = N/2 + 1）** 保证一致性。

### 选举触发场景
- Leader 宕机/网络隔离。
- 集群启动初始化。
- 节点加入/退出导致重新平衡。

### 脑裂（Split-Brain）
- 网络分区导致两个分区各选一个 Leader。
- 防护：**多数派 quorum**——少数派分区无法选出 leader，不会双主。
- 多数据中心：加 **witness / tiebreaker** 节点打破平局。

## 延伸
""",
  links=["distributed-systems/cap-theory",
         "distributed-systems/distributed-lock-redis-vs-zk"])

q("distributed-systems/distributed-lock-redis-vs-zk.md",
  "分布式锁 (Redis vs ZK)",
  "distributed-systems", "distributed-systems", "medium",
  ["distributed-lock", "redis", "zookeeper", "redlock", "consensus"],
  ["恩士讯"],
  """# 分布式锁 (Redis vs ZK)

## 问题描述
微服务多实例下 JVM 级别锁锁不住资源，有什么解决方案？Redis 和 ZK 实现分布式锁，各有什么优缺点？

## 解答

### 为什么 JVM 锁不够
JVM 锁（synchronized / ReentrantLock）只在单进程内有效。微服务多实例 = 多进程，各自 JVM 互不可见，锁失效。必须把锁放到**共享中间件**。

### Redis 分布式锁（SETNX + 过期）
```
SET lock:order:123 <requestId> NX PX 30000
```
- **加锁**：`SET key value NX PX ttl`，原子。
- **解锁**：Lua 脚本校验 value==requestId 再 DEL（避免误删别人锁）。
- **续期**：后台线程定时延长 TTL（Redisson 的 watchdog）。

**优点**：性能高（内存 + 简单命令）。
**缺点**：
- 主从异步复制，主挂从提升时锁可能丢（见 [[distributed-systems/redlock-redis-lock-loss]]）。
- 不是严格的 CP，极端情况锁不可靠。

### ZK 分布式锁（临时顺序节点 + Watch）
1. 在 `/lock` 下创建**临时顺序节点** `/lock/seq-001`。
2. 检查自己是不是最小序号 → 是则获锁。
3. 否则监听前一个节点删除事件，前驱释放时被唤醒。
4. 客户端断线 → 临时节点自动删，锁自动释放（避免死锁）。

**优点**：CP（ZAB 保证一致），锁可靠、不丢、客户端宕机自动释放。
**缺点**：性能低于 Redis（每次写要 quorum + 持久化）；写入频繁场景压力大。

### 选型
- 高性能、可容忍极端情况下锁失效 → Redis（Redisson）。
- 强一致、正确性优先（金融、库存）→ ZK / etcd。

## 延伸
""",
  links=["distributed-systems/redlock-redis-lock-loss",
         "concurrency/optimistic-vs-pessimistic-lock",
         "distributed-systems/cap-theory"])

q("distributed-systems/redlock-redis-lock-loss.md",
  "Redlock / Redis 主从切换丢锁",
  "distributed-systems", "distributed-systems", "hard",
  ["redlock", "redis", "distributed-lock", "consensus", "failover"],
  ["恩士讯"],
  """# Redlock / Redis 主从切换丢锁

## 问题描述
Redis 加锁后主节点挂了，从节点被提升为主，锁没同步导致丢失，怎么解决？

## 解答

### 问题根因
Redis 主从**异步复制**：客户端在主加锁成功返回，但还未同步到从；此时主挂、从提升为新主，新主没有这把锁 → 另一个客户端也能加锁成功 → **双持锁**。

### 方案一：Redlock（Antirez 提出）
- 用 **N（通常 5）个独立 Redis 实例**（不是主从，是独立部署）。
- 客户端向所有 N 个实例依次 `SET NX PX`，加锁成功率 = 在 **多数派 (N/2+1)** 实例上成功 + 总耗时 < TTL。
- 解锁：向所有实例发 DEL。
- 思路：多数派独立实例同时故障的概率远低于单主从切换。

### Redlock 争议
- Martin Kleppmann 批评：依赖时钟同步，GC 暂停/进程暂停会导致客户端持锁过期仍以为自己有锁。
- 实践中：对正确性要求极高的场景推荐 ZK/etcd（CP）而非 Redlock。

### 方案二：用 fencing token
- 每次加锁返回**单调递增 token**，下游服务（DB/存储）只接受更高 token 的写。
- 即便双持锁，旧 token 的写会被下游拒绝。这是更鲁棒的正确性保证，但要求下游支持 token 校验。

### 方案三：Redisson
- 单 Redis 主从场景下用 Redisson 的 watchdog 续期，降低 TTL 过期误判。
- 但仍不能解决主从切换丢锁的根本问题，需配合 Redlock 或换 ZK。

### 工程结论
- 业务能容忍偶发双持（幂等保护兜底）→ Redisson 单实例足够。
- 强一致 → ZK/etcd 临时顺序节点锁 + fencing token。

## 延伸
""",
  links=["distributed-systems/distributed-lock-redis-vs-zk",
         "distributed-systems/cap-theory"])

print("\nDone: spring/microservices + distributed-theory")
