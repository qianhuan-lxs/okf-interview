---
type: question
id: databases/redis/redis-persistence
title: Redis 持久化 (RDB / AOF)
category: databases
subcategory: redis
difficulty: medium
tags: [redis, rdb, aof, persistence]
languages: []
role: [ai-app, sde, backend]
companies: [海颐]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# Redis 持久化 (RDB / AOF)

## 解答

### RDB (Redis Database)
- 全量快照，二进制 dump。
- 触发：`SAVE`/`BGSAVE`、配置 `save m n`、主从同步。
- 优点：体积小、恢复快、适合备份。
- 缺点：宕机丢最后一次快照后的数据；`BGSAVE` fork 大内存实例慢。

### AOF (Append Only File)
- 追加写命令日志。
- 刷盘策略：`always`（每条 fsync，最安全最慢）/ `everysec`（默认，每秒）/ `no`（OS 决定）。
- 重写（rewrite）：fork 子进程按当前内存状态生成最小等价 AOF，避免文件膨胀。
- 优点：丢数据少（everysec 最多丢 1 秒）。
- 缺点：体积大、恢复慢。

### Redis 4.0+ 混合持久化
- `aof-use-rdb-preamble yes`：AOF 重写时前半段写 RDB 快照 + 后半段追加 AOF 命令。
- 兼顾 RDB 恢复快 + AOF 丢数据少。

### 选型
- 纯缓存可关持久化。
- 允许丢几分钟 → RDB。
- 不允许丢 → AOF everysec + 混合持久化。
- 金融级不应只用 Redis 做主存。

## 延伸

## 延伸

- 关联题：[[databases/redis/redis-data-types]]
