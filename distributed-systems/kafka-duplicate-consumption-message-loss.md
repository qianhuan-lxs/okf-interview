---
type: question
id: distributed-systems/kafka-duplicate-consumption-message-loss
title: Kafka 重复消费 / 丢消息
category: distributed-systems
subcategory: distributed-systems
difficulty: medium
tags: [kafka, duplicate-consumption, message-loss, idempotent, message-queue]
languages: []
role: [ai-app, sde, backend]
companies: [拼多多, 海颐]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# Kafka 重复消费 / 丢消息

## 问题描述
怎么避免重复发送呢？Kafka 什么情况下会出现丢消息的情况？

## 解答

### 重复消费来源
1. 自动提交 offset 后业务才失败 → 重启后从已提交 offset 后消费，丢业务但 Kafka 认为已消费。
2. Rebalance 时部分消息已处理但未提交 offset → 新消费者重新消费。
3. 生产端重试（网络抖动）导致 broker 收到重复消息。

### 避免重复消费
- **手动提交**：业务处理成功后才 commit。
- **幂等消费**：用业务唯一键（订单号）去重，DB 唯一索引 / Redis SETNX 标记已处理。
- **事务**：消费 + 业务写 + 提交 offset 放同一事务。

### 丢消息场景
1. **生产端**：`acks=0`（不等任何确认）就丢； producer 异步 send 不处理回调。**解法**：`acks=all` + 重试 + `enable.idempotence=true`。
2. **Broker**：单副本 + 宕机；`min.insync.replicas` 设小。**解法**：副本 ≥3 + `min.insync.replicas=2` + 同步刷盘。
3. **消费端**：先提交 offset 再处理业务，处理失败就丢。**解法**：处理完再提交。
4. **缓冲区满**：buffer.memory 满且 block 超时丢。**解法**：调大 buffer 或处理背压。

### 精确一次（Exactly-Once）
- Kafka 0.11+：幂等 producer + 事务（producer 写 + consumer 提交 offset 同一事务）。
- 业务侧仍建议**幂等消费**做兜底，比依赖精确一次更稳。

## 延伸

## 延伸

- 关联题：[[distributed-systems/kafka-offset-rebalance]]
- 关联题：[[distributed-systems/kafka-vs-rocketmq-scenarios]]
