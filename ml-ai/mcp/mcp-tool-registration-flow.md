---
type: question
id: ml-ai/mcp/mcp-tool-registration-flow
title: MCP Tool 注册流程
category: ml-ai
subcategory: mcp
difficulty: medium
tags: [mcp, tool-registry, registration, governance]
languages: []
role: [ai-app, sde, backend]
companies: [OPPO, 华大制造]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# MCP Tool 注册流程

## 问题描述

手工把 MCP 工具录进来？Tool 注册流程是怎样的？

## 解答

注册三种模式，生产通常**三者结合**：

### 1. 自动发现（Pull）
网关启动/定时拉取下游 MCP server 的 `tools/list`，把返回的 tool schema 写入 registry。
- 优点：零人工、新工具自动上架。
- 缺点：没有 owner/SLA/分类等治理元数据。

### 2. 手工录入（Push）
运营后台填表：name / description / 所属 server / owner / 分类 / 鉴权策略 / SLA。
- 优点：治理信息完整、可控。
- 缺点：慢、易和实际 schema 漂移。

### 3. 自动转换（Transform）
OpenAPI / GraphQL schema 自动转 MCP tool（见 [[ml-ai/mcp/openapi-to-mcp-auto-conversion]]）。

### 典型流程（生产）

```
[新工具接入]
  1. 工具方提供 OpenAPI 或 MCP server 地址
  2. 网关 pull 自动发现 / transform 生成 registry 草稿
  3. 工具方在后台补全 owner / 分类 / description（必要时 LLM 辅助生成）
  4. review 通过 → 发布到 production registry
  5. 灰度对 agent 可见，监控调用量/错误率
  6. 下线：标记 deprecated → 灰度摘流量 → 删除
```

### Registry 字段建议

`name` / `description` / `server_id` / `owner` / `category` / `auth_policy` / `rate_limit` / `sla` / `version` / `status` / `created_at` / `deprecated_at`。

## 易错点

- 只走自动发现、没人工 review——description 质量差导致模型乱选工具。
- 没有灰度/下线流程——工具方改动直接打挂线上 agent。

## 延伸

## 延伸

- 关联题：[[ml-ai/mcp/mcp-gateway-architecture]]
- 关联题：[[ml-ai/mcp/openapi-to-mcp-auto-conversion]]
