# Index — distributed-systems

## 题目

| 标题 | 难度 | 标签 |
| --- | --- | --- |
| [CAP 理论](distributed-systems/cap-theory.md) | easy | cap, consistency, availability, partition-tolerance, distributed |
| [Kafka vs RocketMQ 场景选择](distributed-systems/kafka-vs-rocketmq-scenarios.md) | medium | kafka, rocketmq, message-queue, comparison, selection |
| [Kafka 偏移量 / Rebalance](distributed-systems/kafka-offset-rebalance.md) | medium | kafka, offset, consumer-group, rebalance, message-queue |
| [Kafka 重复消费 / 丢消息](distributed-systems/kafka-duplicate-consumption-message-loss.md) | medium | kafka, duplicate-consumption, message-loss, idempotent, message-queue |
| [Redis 做 MQ vs Kafka / RocketMQ](distributed-systems/redis-mq-vs-kafka-rocketmq.md) | medium | redis, kafka, rocketmq, message-queue, comparison |
| [Redlock / Redis 主从切换丢锁](distributed-systems/redlock-redis-lock-loss.md) | hard | redlock, redis, distributed-lock, consensus, failover |
| [分布式选举](distributed-systems/distributed-election.md) | medium | election, leader, raft, paxos, bully, distributed |
| [分布式锁 (Redis vs ZK)](distributed-systems/distributed-lock-redis-vs-zk.md) | medium | distributed-lock, redis, zookeeper, redlock, consensus |
| [限流方案 (令牌桶 / 漏桶 / 滑动窗口 / Redis)](distributed-systems/rate-limiting-redis-token-bucket.md) | medium | rate-limiting, token-bucket, sliding-window, redis, lua |

## 被引用 (cited by)

- [[backend/microservices/spring-cloud-microservice-ecosystem]] — Spring Cloud 微服务生态
- [[concurrency/optimistic-vs-pessimistic-lock]] — 乐观锁 vs 悲观锁
- [[databases/redis/redis-cache-avalanche]] — 缓存雪崩 / 穿透 / 击穿
- [[databases/redis/redis-distributed-architecture]] — Redis 分布式架构 (主从 / 哨兵 / Cluster)
- [[ml-ai/mcp/mcp-gateway-architecture]] — MCP 网关架构 (鉴权 / 限流 / 降级 / 缓存 / Tool 注册)

<!-- 由 `tools/okf.py gen-index` 自动生成，请勿手动编辑正文。 -->
