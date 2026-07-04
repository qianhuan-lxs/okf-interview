---
type: question
id: distributed-systems/redis-mq-vs-kafka-rocketmq
title: Redis 做 MQ vs Kafka / RocketMQ
category: distributed-systems
subcategory: distributed-systems
difficulty: medium
tags: [redis, kafka, rocketmq, message-queue, comparison]
languages: []
role: [ai-app, sde, backend]
companies: [恩士讯]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# Redis 做 MQ vs Kafka / RocketMQ

## 问题描述
项目上消息队列用的什么？Redis 做 MQ 比 Kafka/RocketMQ 有什么缺点？

## 解答

### Redis 做 MQ 的方式
- List + `BRPOP`：简单队列。
- Pub/Sub：广播，但**无持久化、离线订阅者丢消息**。
- Stream（5.0+）：接近 Kafka 的 consumer group + 持久化，最像 MQ。

### Redis 做 MQ 的缺点
| 维度 | Redis Stream | Kafka/RocketMQ |
| --- | --- | --- |
| 吞吐 | 万级 TPS | 百万级 TPS |
| 持久化 | 受限于 Redis 内存 + AOF/RDB | 专门顺序写磁盘 + 副本 |
| 堆积能力 | 内存限制，堆积会拖垮 | TB 级堆积无压力 |
| 顺序/分片 | 弱 | 分区强顺序 |
| 事务消息 | 无 | RocketMQ 支持 |
| 回溯 | 有限 | 按时间/offset 回溯 |
| 运维 | 简单 | 重（Kafka 需 ZK/KRaft） |
| 生态 | 弱 | 流计算、Connector、Schema Registry |

### 结论
- Redis MQ 适合**轻量、低吞吐、无严格堆积需求**的场景（如内部任务队列、限流提示）。
- 严肃 MQ 场景（订单、日志、流处理）选 Kafka（吞吐/流式）或 RocketMQ（事务消息/电商）。

## 延伸

## 延伸

- 关联题：[[distributed-systems/kafka-offset-rebalance]]
- 关联题：[[distributed-systems/kafka-vs-rocketmq-scenarios]]
