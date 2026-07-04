---
type: question
id: ml-ai/mcp/openapi-to-mcp-auto-conversion
title: OpenAPI → MCP Tool 自动转换
category: ml-ai
subcategory: mcp
difficulty: hard
tags: [mcp, openapi, conversion, tool-registry, automation]
languages: []
role: [ai-app, sde, backend]
companies: [华大制造, 有赞]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# OpenAPI → MCP Tool 自动转换

## 问题描述

简历提到把 OpenAPI 自动转换为 MCP Tool 定义。最难处理的点是什么？接口文档里没有描述怎么办？

## 解答

### 转换映射

| OpenAPI | MCP Tool |
| --- | --- |
| `operationId` (或 path+method) | tool name |
| `summary` / `description` | tool description（关键，模型靠它选工具） |
| `parameters` + `requestBody` | `inputSchema` (JSON Schema) |
| `servers` + `path` | 调用入口 |
| `responses` | 输出格式（MCP 通常返回 text，自行渲染） |

### 最难的点

1. **description 缺失或低质** — OpenAPI 里很多接口没 description 或只有"创建订单"这种给人看的标签。模型选工具靠 description，质量差就调错或漏调。
   - 解法：用 LLM **基于 path/params/schema 生成 description**，再人工 review；或拉接口文档/示例代码再生成。
2. **复杂参数 schema** — 嵌套 object、oneOf、$ref、文件上传、formData。MCP inputSchema 是扁平 JSON Schema，需要递归展开 + 去环。
3. **鉴权多样性** — Bearer / API Key / OAuth / 签名。要在网关层屏蔽，注入凭证。
4. **大响应裁剪** — 接口返回几 MB JSON，超过 LLM context。要按 schema 抽关键字段或摘要。
5. **副作用识别** — GET 安全可缓存，POST/PUT 有副作用，不能盲目缓存。
6. **跨团队推动** — 业务方 OpenAPI 文档质量参差，需要协作规范（这本身是工程难点）。

### description 生成最佳实践

- 风格：**"做什么 + 何时该用 + 输入要点 + 边界条件"**，给模型判断依据，不是给人看的标签。
- 例：`"按订单号查询订单详情。当用户问'我的订单''订单状态'时使用。输入 order_id（32位字符串）。仅返回最近 90 天订单。"`

## 易错点

- 直接用 `summary` 当 description——给模型看的判断信息严重不足。
- 不裁剪大响应——context 爆炸且成本高。

## 延伸

## 延伸

- 关联题：[[ml-ai/mcp/mcp-gateway-architecture]]
- 关联题：[[ml-ai/agent/skill-meaning-loading-evolution]]
