---
type: question
id: distributed-systems/distributed-election
title: 分布式选举
category: distributed-systems
subcategory: distributed-systems
difficulty: medium
tags: [election, leader, raft, paxos, bully, distributed]
languages: []
role: [ai-app, sde, backend]
companies: [恩士讯]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 分布式选举

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

## 延伸

- 关联题：[[distributed-systems/cap-theory]]
- 关联题：[[distributed-systems/distributed-lock-redis-vs-zk]]
