---
type: question
id: databases/redis/redis-data-types
title: Redis 数据类型
category: databases
subcategory: redis
difficulty: easy
tags: [redis, data-structure, cache]
languages: []
role: [ai-app, sde, backend]
companies: [海颐, 北京用友]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# Redis 数据类型

## 问题描述
Redis 具体支持哪些数据类型？你知道它的这个数据结构吗？

## 解答

### 5 大基础类型
| 类型 | 底层结构 | 典型用途 |
| --- | --- | --- |
| **String** | SDS（简单动态字符串） | 计数器、缓存、分布式锁 |
| **List** | quicklist（ziplist + linkedlist，7.0 改 listpack） | 消息队列、最新列表 |
| **Hash** | ziplist / hashtable | 对象存储（用户信息） |
| **Set** | intset / hashtable | 去重、标签、共同好友 |
| **ZSet** | ziplist / skiplist + hashtable | 排行榜、延时队列、范围查 |

### 扩展类型（4+）
- **Stream**（5.0+）：持久化消息流，替代 List 做可靠 MQ。
- **Bitmap**：位图，签到、活跃统计、布隆过滤器。
- **HyperLogLog**：基数估算（UV），12KB 估 12 亿去重。
- **Geo**：基于 ZSet，经纬度范围查。
- **5 种新结构**：Stream / Listpack / BF/CF/...（RedisBloom 模块）。

### 底层编码选择
- 数据少用 ziplist/listpack（紧凑省内存），达到阈值切换 hashtable/skiplist（性能优先）。
- 阈值由 `hash-max-ziplist-entries` 等配置控制。

## 延伸

## 延伸

- 关联题：[[databases/redis/redis-persistence]]
- 关联题：[[databases/redis/redis-cache-avalanche]]
