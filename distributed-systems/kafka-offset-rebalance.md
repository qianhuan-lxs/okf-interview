---
type: question
id: distributed-systems/kafka-offset-rebalance
title: Kafka 偏移量 / Rebalance
category: distributed-systems
subcategory: distributed-systems
difficulty: medium
tags: [kafka, offset, consumer-group, rebalance, message-queue]
languages: []
role: [ai-app, sde, backend]
companies: [中泓一线, 拼多多]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# Kafka 偏移量 / Rebalance

## 问题描述
Kafka 偏移量有哪几种？常见设置偏移量有哪些？Topic 和 Group 哪个大？换 group 要重置偏移量吗？有没有了解过 Rebalance 概念？

## 解答

### 偏移量 (offset)
- 每个分区一个单调递增 offset，标识消费位置。
- 提交方式：
  - **自动提交**：`enable.auto.commit=true`，每 `auto.commit.interval.ms` 提交，可能**重复/丢失**。
  - **手动提交**：`commitSync()` / `commitAsync()`，业务处理完再提交，精确但需自己管。
- 初始位置 `auto.offset.reset`：`earliest` / `latest` / `none`。

### 常见设置
- 至少一次：手动提交 + 幂等消费。
- 至多一次：自动提交 + 处理前提交。
- 精确一次：事务/幂等生产 + 事务消费（Kafka 0.11+）。

### Topic vs Group
- **Topic 是数据维度**，**Group 是消费维度**，二者正交，没有"谁大"。
- 一个 Topic 可被多个 Group 独立消费（各自 offset），互不干扰。
- 一个 Group 内分区被瓜分：组内消费者数 ≤ 分区数才有意义，多了空闲。

### 换 group 要重置 offset 吗
- 新 group 第一次消费按 `auto.offset.reset` 决定（earliest/latest）。
- 不存在"重置"，因为是全新 group，没有历史 offset。
- 老群体改 `auto.offset.reset` 不影响已提交的 offset，要重置需用 `kafka-consumer-groups --reset-offsets` 工具。

### Rebalance
- 触发：消费者加入/退出、订阅变化、分区数变化、心跳超时。
- 过程：所有消费者暂停消费 → 协调器重新分配分区 → 消费者继续。
- 问题：**Stop-The-World**，期间全组不消费；频繁 rebalance 影响吞吐。
- 优化：
  - `session.timeout.ms` / `heartbeat.interval.ms` 调大避免误判。
  - `max.poll.interval.ms` 调大避免长处理被踢。
  - **Sticky Assignor / Cooperative Rebalance**（2.4+）：增量 rebalance，减少抖动。
  - 静态成员 `group.instance.id`：消费者重启不触发 rebalance。

## 延伸

## 延伸

- 关联题：[[distributed-systems/kafka-duplicate-consumption-message-loss]]
- 关联题：[[distributed-systems/kafka-vs-rocketmq-scenarios]]
