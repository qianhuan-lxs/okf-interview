---
type: question
id: system-design/short-url-system
title: 短链接系统设计
category: system-design
subcategory: system-design
difficulty: hard
tags: [system-design, short-url, hash, base62, cache]
languages: []
role: [ai-app, sde, backend]
companies: [拼多多]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 短链接系统设计

## 问题描述
设计一个短链接系统。长链接映射到短链接，访问短链接时跳转回原始长链接。访问短链接怎么跳回？需要考虑哪些点？怎么生成短链接？数据结构具体什么样？

## 思路

核心三问：**短码怎么生成？长短怎么存？跳转怎么实现？**

## 解答

### 1. 短码生成
- **方案 A：发号器 + Base62**
  - 分布式发号器（Snowflake / Redis INCR / 数据库号段）产 `long id`。
  - `id` 转 Base62（0-9a-zA-Z，62 进制），6 位可表 568 亿，够用。
  - 优点：短、定长、不重复、不依赖 hash。
- **方案 B：MD5/MurmurHash 取前 6~7 位**
  - 优点：无需中心发号。缺点：冲突需处理（加盐或重试）。
- **方案 C：预生成短码池**：离线生成一批入库，用即取。

推荐 **A**：可控、可预测、无冲突。

### 2. 存储数据结构
```
short_url | long_url | create_time | expire_time | owner | click_count
```
- 主键 `short_url`，索引 `long_url`（防止重复生成、查重）。
- 量级估算：千亿级 → 分库分表，按 short_url hash 分片。
- 冷热分离：近期热点放 Redis，历史归档。

### 3. 跳转流程
```
1. 用户访问 s.xx/abc123
2. 网关/服务：先查 Redis（命中 99%+）→ 未命中查 DB 回填
3. 302 重定向到 long_url（302 不缓存，便于统计/过期控制；301 缓存则丢统计）
4. 异步记点击日志（UA/IP/referer/时间）→ Kafka → 分析
```

### 4. 关键考虑点
- **缓存**：短→长 高频读，Redis 缓存 + 本地 Caffeine 二级，命中率 >99%。
- **防滥用**：长链接白名单、限频、敏感域名拦截。
- **过期与失效**：expire_time + 失效返回 404 或兜底页。
- **自定义短码**：用户指定 slug，需查重。
- **HTTPS + 短域名**：越短越好。
- **防碰撞/防猜测**：发号器递增易被遍历，可加随机位或加密 id（如 Feistel 网络混淆）。
- **高可用**：服务多副本、缓存集群、DB 主从；跳转是核心链路不能挂。

### 5. 容量估算
- 100亿 短链 × 0.5KB/条 ≈ 5TB → 分 64 库 × 64 表。
- QPS：读 10w/s（302 跳转），写 1k/s。读多写少，缓存主导。

## 易错点
- 用 301 永久重定向 → 浏览器缓存导致后续跳转不经过服务，统计丢失。
- 用 hash 不处理冲突 → 同长链可能同短码。

## 延伸

## 延伸

- 关联题：[[system-design/bi-data-analysis-agent]]
- 关联题：[[system-design/vertical-observation-pipeline]]
