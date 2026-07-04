---
type: question
id: ml-ai/mcp/mcp-gateway-architecture
title: MCP 网关架构 (鉴权 / 限流 / 降级 / 缓存 / Tool 注册)
category: ml-ai
subcategory: mcp
difficulty: hard
tags: [mcp, gateway, auth, rate-limiting, circuit-breaker, cache, tool-registry]
languages: []
role: [ai-app, sde, backend]
companies: [华大制造, OPPO, 探迹, 中泓一线, 北京用友]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# MCP 网关架构 (鉴权 / 限流 / 降级 / 缓存 / Tool 注册)

## 问题描述

MCP 网关做了什么事？用户端只配网关地址，网关再连具体 MCP 工具？网关鉴权限流细节？Tool 注册流程？流量大怎么解决？除了限流还有别的方式？

## 思路

MCP 网关 = **企业级 MCP 中间件**，把 N 个分散的 MCP server 收口，对 agent 暴露统一入口，叠加治理能力。类比 API Gateway（Kong/APISIX）之于 REST。

## 解答

### 核心职责

1. **统一入口** — agent 只配网关地址，网关后端连多个 MCP server。
2. **Tool Registry（注册中心）** — 维护 tool 元数据（schema、所属 server、owner、版本、SLA）。注册方式：
   - **手工录入**（运营后台填 schema）
   - **自动发现**（拉取下游 server 的 `tools/list`）
   - **OpenAPI 自动转换**（见 [[ml-ai/mcp/openapi-to-mcp-auto-conversion]]）
3. **鉴权 Auth** — 双向：
   - 入向：校 agent / tenant 的 token（JWT / mTLS）。
   - 出向：维护下游 MCP server 的凭证库（密钥/OAuth），按需注入。
4. **限流 Rate Limiting** — 多维度：tenant / tool / 全局。
5. **降级 / 熔断** — 下游 MCP 异常时返回兜底响应或短路。
6. **缓存** — 相同 (tool, args) 短 TTL 缓存，省下游调用与 token 成本。
7. **可观测** — 每次调用 trace、token 计费、成功率监控。

### 限流方案（华大/探迹追问"还有别的方式吗"）

| 方案 | 粒度 | 实现 |
| --- | --- | --- |
| **令牌桶** | 平滑限流 | Redis + Lua 原子扣 token |
| **漏桶** | 强制匀速 | 队列 + 固定速率消费 |
| **滑动窗口** | 精确窗口 | Redis ZSET 按时间戳计数 |
| **固定窗口** | 简单 | Redis INCR + EXPIRE |
| **自适应限流** | 根据延迟/错误率 | Sentinel / BBR 思路 |
| **排队 + 削峰** | 突发吸收 | MQ 异步化 |

**单机 vs 分布式**：网关多副本时，限流必须用 Redis 等共享存储做**分布式限流**，否则单机配额会被突破。

### 高并发流量打法（华大）

1. **水平扩容** — 网关无状态，多副本 + LB。
2. **分布式限流** — Redis 令牌桶，按 tenant/tool 维度。
3. **缓存** — 读多写少的 tool 结果缓存。
4. **异步化** — 长耗时 tool 改异步（提交任务 → webhook 回调）。
5. **降级** — 下游故障时返回兜底，避免雪崩。
6. **连接复用** — 对下游 MCP server 用连接池/长连接。

## 易错点

- 单机限流配多副本网关——总 QPS 超预期。
- 缓存对带副作用（写类）tool 也开——脏写。
- Tool 注册只走自动发现，没有 owner/SLA 治理——出问题无人认领。

## 延伸

## 延伸

- 关联题：[[ml-ai/mcp/openapi-to-mcp-auto-conversion]]
- 关联题：[[ml-ai/mcp/mcp-protocol-understanding]]
- 关联题：[[distributed-systems/rate-limiting-redis-token-bucket]]
