# Index — distributed-systems

## 题目

| 标题 | 难度 | 标签 |
| --- | --- | --- |
| [2PC / 3PC / XA 协议 (协调者 / prepare / 阻塞问题 / 3PC 解决了什么)](distributed-systems/2pc-3pc-protocol.md) | hard | 2pc, 3pc, xa, distributed-transaction, strong-consistency, coordinator, blocking, mysql |
| [CAP 理论](distributed-systems/cap-theory.md) | easy | cap, consistency, availability, partition-tolerance, distributed |
| [Kafka vs RocketMQ 场景选择](distributed-systems/kafka-vs-rocketmq-scenarios.md) | medium | kafka, rocketmq, message-queue, comparison, selection |
| [Kafka 偏移量 / Rebalance](distributed-systems/kafka-offset-rebalance.md) | medium | kafka, offset, consumer-group, rebalance, message-queue |
| [Kafka 重复消费 / 丢消息](distributed-systems/kafka-duplicate-consumption-message-loss.md) | medium | kafka, duplicate-consumption, message-loss, idempotent, message-queue |
| [RPC 调用与分布式事务 (超时/重试/幂等 / XID 透传 / 大事务 / 降级)](distributed-systems/rpc-and-distributed-txn.md) | hard | rpc, dubbo, grpc, feign, distributed-transaction, xid, timeout, retry, idempotent, circuit-breaker, java |
| [Redis 做 MQ vs Kafka / RocketMQ](distributed-systems/redis-mq-vs-kafka-rocketmq.md) | medium | redis, kafka, rocketmq, message-queue, comparison |
| [Redlock / Redis 主从切换丢锁](distributed-systems/redlock-redis-lock-loss.md) | hard | redlock, redis, distributed-lock, consensus, failover |
| [Saga 模式 (长事务 / 编排 vs 协同 / 补偿顺序 / 隔离性)](distributed-systems/saga-pattern.md) | hard | saga, distributed-transaction, compensation, long-running, orchestration, choreography, eventual-consistency |
| [Seata 框架 (AT/TCC/SAGA/XA 四模式 / TC/TM/RM / AT 原理 / 生产坑)](distributed-systems/seata-framework.md) | hard | seata, at-mode, tcc, saga, xa, distributed-transaction, undo-log, global-lock, java, spring-cloud, dubbo |
| [TCC 事务 (Try-Confirm-Cancel / 业务侵入 / 三大坑: 空回滚/悬挂/幂等)](distributed-systems/tcc-transaction.md) | hard | tcc, distributed-transaction, eventual-consistency, compensation, idempotent, business-transaction |
| [分布式事务全景 (方案分类 / 强一致 vs 最终一致 / 选型决策树)](distributed-systems/distributed-txn-overview.md) | hard | distributed-transaction, 2pc, tcc, saga, xa, eventual-consistency, seata, base, cap, consistency |
| [分布式选举](distributed-systems/distributed-election.md) | medium | election, leader, raft, paxos, bully, distributed |
| [分布式锁 (Redis vs ZK)](distributed-systems/distributed-lock-redis-vs-zk.md) | medium | distributed-lock, redis, zookeeper, redlock, consensus |
| [最终一致性方案 (本地消息表 / 事务消息 / Outbox+CDC / 最大努力通知 / 对账)](distributed-systems/eventual-consistency-patterns.md) | hard | eventual-consistency, local-message-table, transaction-message, outbox, cdc, rocketmq, debezium, best-effort, reconciliation |
| [限流方案 (令牌桶 / 漏桶 / 滑动窗口 / Redis)](distributed-systems/rate-limiting-redis-token-bucket.md) | medium | rate-limiting, token-bucket, sliding-window, redis, lua |

## 被引用 (cited by)

- [[backend/microservices/spring-cloud-microservice-ecosystem]] — Spring Cloud 微服务生态
- [[concurrency/optimistic-vs-pessimistic-lock]] — 乐观锁 vs 悲观锁
- [[databases/redis/redis-cache-avalanche]] — 缓存雪崩 / 穿透 / 击穿
- [[databases/redis/redis-distributed-architecture]] — Redis 分布式架构 (主从 / 哨兵 / Cluster)
- [[ml-ai/mcp/mcp-gateway-architecture]] — MCP 网关架构 (鉴权 / 限流 / 降级 / 缓存 / Tool 注册)
- [[networks/okhttpclient-design]] — OkHttpClient 设计 (拦截器链 / 连接池 / Dispatcher / Okio)

<!-- 由 `tools/okf.py gen-index` 自动生成，请勿手动编辑正文。 -->
