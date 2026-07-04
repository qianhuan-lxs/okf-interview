---
type: question
id: databases/redis/redis-distributed-architecture
title: Redis 分布式架构 (主从 / 哨兵 / Cluster)
category: databases
subcategory: redis
difficulty: medium
tags: [redis, replication, sentinel, cluster, ha]
languages: []
role: [ai-app, sde, backend]
companies: [中泓一线]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# Redis 分布式架构 (主从 / 哨兵 / Cluster)

## 问题描述
Redis 有哪些分布式架构？Redis 搭过高可用？

## 解答

### 1. 主从复制
- 一主多从，写主读从，读写分离。
- 同步方式：全量（bgsync + RDB 传输）+ 增量（repl_backlog）。
- 异步复制 → 主从延迟、主挂丢数据。
- 不自动故障转移。

### 2. Sentinel（哨兵）
- Sentinel 集群（≥3 节点）监控主从。
- 主挂时哨兵**投票选新主**，应用通过 Sentinel 拿最新主地址。
- 适合**小规模、不需水平扩容**的高可用。
- 故障转移：主观下线 → 客观下线 → 选举 leader sentinel → 选新主 → 通知客户端。

### 3. Cluster
- **数据分片**：16384 个 slot，按 `CRC16(key) % 16384` 分配到节点。
- 每个节点负责一部分 slot，节点间 Gossip 通信。
- **去中心化**，无单独代理；客户端缓存 slot 路由表，MOVED 重定向。
- 每个主节点配一个从节点，主挂从提升（半自动）。
- 适合**大数据量 + 水平扩容**。
- 限制：跨 slot 操作需 hash tag（`{user}:1`）；事务/多键受限；不支持 select db（只用 db0）。

### 选型
- 数据量小、要 HA → Sentinel。
- 数据量大、要水平扩展 → Cluster。
- 极致性能 + HA → 代理层（Codis/Twemproxy，已渐少用）或自研。

## 延伸

## 延伸

- 关联题：[[databases/redis/redis-persistence]]
- 关联题：[[distributed-systems/distributed-lock-redis-vs-zk]]
