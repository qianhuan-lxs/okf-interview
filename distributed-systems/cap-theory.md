---
type: question
id: distributed-systems/cap-theory
title: CAP 理论
category: distributed-systems
subcategory: distributed-systems
difficulty: easy
tags: [cap, consistency, availability, partition-tolerance, distributed]
languages: []
role: [ai-app, sde, backend]
companies: [中泓一线]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# CAP 理论

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

## 延伸

- 关联题：[[distributed-systems/distributed-election]]
- 关联题：[[distributed-systems/distributed-lock-redis-vs-zk]]
