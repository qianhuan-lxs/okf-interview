---
type: question
id: distributed-systems/rate-limiting-redis-token-bucket
title: 限流方案 (令牌桶 / 漏桶 / 滑动窗口 / Redis)
category: distributed-systems
subcategory: distributed-systems
difficulty: medium
tags: [rate-limiting, token-bucket, sliding-window, redis, lua]
languages: []
role: [ai-app, sde, backend]
companies: [华大制造, 探迹, 恩士讯]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 限流方案 (令牌桶 / 漏桶 / 滑动窗口 / Redis)

## 问题描述
限流除了这种方式还有别的方式？单机怎么考量？不会成为单点故障的隐患吗？

## 解答

### 算法对比

| 算法 | 特点 | 实现 |
| --- | --- | --- |
| **固定窗口** | 简单，窗口边界突刺 | Redis INCR + EXPIRE |
| **滑动窗口** | 精确，无边界突刺 | Redis ZSET（按时间戳计数，删过期） |
| **令牌桶** | 平滑限流，允许突发 | Redis + Lua 原子扣 token |
| **漏桶** | 强制匀速，拒绝突发 | 队列 + 固定速率消费 |
| **自适应** | 按延迟/错误率动态调整 | Sentinel / BBR |

### 单机 vs 分布式
- 单机：Guava `RateLimiter`（令牌桶）/ Bucket4j。
- 多机：必须**共享存储**限流，否则总 QPS = 单机配额 × 副本数，超预期。
- 共享存储选型：Redis（主流）/ Sentinel 集群 / 自研中心化限流服务。

### Redis 令牌桶 Lua 原子脚本
```lua
-- KEYS[1]=key  ARGV[1]=capacity  ARGV[2]=refill_rate  ARGV[3]=now  ARGV[4]=requested
local last = tonumber(redis.call("hget", KEYS[1], "ts")) or ARGV[3]
local tokens = tonumber(redis.call("hget", KEYS[1], "tk")) or ARGV[1]
local delta = math.max(0, ARGV[3] - last) * ARGV[2]
tokens = math.min(ARGV[1], tokens + delta)
if tokens >= ARGV[4] then
  redis.call("hmset", KEYS[1], "tk", tokens - ARGV[4], "ts", ARGV[3])
  return 1
else
  return 0
end
```

### 单点故障隐患
- 限流器本身是单点 → 限流器挂了，要么全放行（DB 被打爆）要么全拒绝（服务不可用）。
- 解法：
  - 限流服务高可用（Redis Cluster / Sentinel）。
  - 客户端**本地兜底**：连不上限流器时走本地令牌桶（保守值）。
  - 多级：网关粗限流 + 服务细限流。

### 集群限流（更精确）
- 中心化 token 服务（每节点定时拉额度）或 Redis 集群分散热点 key。

## 易错点
- 用 `INCR + EXPIRE` 做固定窗口 → 边界突刺（窗口切换瞬间双倍流量）。
- 单机限流配多副本网关 → 总 QPS 失控。

## 延伸

## 延伸

- 关联题：[[ml-ai/mcp/mcp-gateway-architecture]]
- 关联题：[[distributed-systems/distributed-lock-redis-vs-zk]]
