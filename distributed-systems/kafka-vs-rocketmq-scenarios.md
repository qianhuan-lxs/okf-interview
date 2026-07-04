---
type: question
id: distributed-systems/kafka-vs-rocketmq-scenarios
title: Kafka vs RocketMQ 场景选择
category: distributed-systems
subcategory: distributed-systems
difficulty: medium
tags: [kafka, rocketmq, message-queue, comparison, selection]
languages: []
role: [ai-app, sde, backend]
companies: [海颐]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# Kafka vs RocketMQ 场景选择

## 问题描述
Kafka 跟 RocketMQ 对比，各自适合什么场景？

## 解答

| 维度 | Kafka | RocketMQ |
| --- | --- | --- |
| 起源 | LinkedIn，流处理 | 阿里，电商场景 |
| 语言 | Scala/Java | Java |
| 事务消息 | 0.11+ 支持但弱 | 原生强支持（半消息 + 回查） |
| 顺序消息 | 分区内有序 | 分区内有序，且支持全局顺序 |
| 延时消息 | 需自己实现 | 原生支持（18 个级别） |
| 消息回溯 | 按 offset/时间 | 按时间 |
| 吞吐 | 极高（百万级） | 高（十万级） |
| 堆积 | TB 级 | 亿级（优化好） |
| 生态 | Kafka Streams / Connect / Schema Registry | 弱 |
| 运维 | 重（ZK/KRaft） | 中（NameServer） |

### 场景选型
- **日志/流式处理/大数据管道** → Kafka（生态成熟、吞吐极致）。
- **电商交易/订单/事务消息/延时任务** → RocketMQ（事务消息、延时、可靠投递）。
- **金融/严格不丢** → RocketMQ（双刷 + 同步刷盘 + 同步复制）。

## 延伸

## 延伸

- 关联题：[[distributed-systems/kafka-offset-rebalance]]
- 关联题：[[distributed-systems/kafka-duplicate-consumption-message-loss]]
