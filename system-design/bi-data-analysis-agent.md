---
type: question
id: system-design/bi-data-analysis-agent
title: BI 数据分析智能体设计
category: system-design
subcategory: system-design
difficulty: hard
tags: [system-design, bi, ai-agent, rag, nl2sql]
languages: []
role: [ai-app, sde, backend]
companies: [广州大娱]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# BI 数据分析智能体设计

## 问题描述
让你做一个 AI 智能体对 BI 系统里的报表做数据分析，怎么实现？后台 BI 系统，通过微信/钉钉对话来分析数据，智能体应该怎么做？

## 思路

关键：**对话入口 → 意图识别 → NL2SQL/取数 → 分析 → 图文回填**。不是简单套 LLM，要拆清楚每一步对应什么方案。

## 解答

### 系统分层

```
[微信/钉钉] → [接入网关(钉钉/企微回调)] 
            → [对话编排 Agent]
                ├─ 意图识别：闲聊 / 取数分析 / 报表订阅 / 异常追问
                ├─ 上下文记忆：多轮指代"上个月的销售额"→ 解析时间
                ├─ NL2SQL：把自然语言 → SQL（限定库表 schema 注入）
                ├─ 取数执行：调 BI 数据源（MySQL/ClickHouse/Doris）
                ├─ 分析洞察：LLM 基于结果生成解读 + 异常归因
                └─ 回填渲染：图表（折线/柱/饼）+ 文字 → 卡片消息
```

### 各环节方案
1. **入口**：钉钉/企微机器人 webhook；OAuth 绑定企业账号 → 拿到数据权限。
2. **意图识别**：轻量分类器或 LLM router，区分"取数分析 / 闲聊 / 配置订阅"。
3. **NL2SQL**：
   - 把库 schema、维度指标字典、示例 QA 作为 few-shot 注入 prompt。
   - 用 SQL 语法校验 + 沙箱执行（只读账号 + 行数限制 + 超时）。
   - 加 RAG：把历史成功 SQL 当召回库，提精度。
   - 复杂指标预定义成"指标 API"，LLM 选指标而非裸写 SQL，降错率。
4. **取数**：调 BI 后端既有数据接口（不要让 agent 直连生产 DB），保留 BI 的权限/缓存。
5. **分析**：LLM 拿到表格数据 → 生成"环比/同比/异常点/归因"文字。
6. **可视化**：服务端用 ECharts 服务端渲染图，转图片或卡片消息发回。
7. **多轮记忆**：保留最近 N 轮 + 指代消解（"上个月"= 哪月）。

### 工程难点
- **NL2SQL 准确率**：宽表多指标时易错。策略：限定 schema + 指标白名单 + 校验 + 失败重写。
- **权限**：按企业账号 + 角色 + 行级权限控制可查数据范围。
- **性能**：慢查询保护（超时即返回"查询中，结果稍后推送"）。
- **可观测**：每次 NL2SQL 记录 query/SQL/结果/是否人工修正，回流评测改进。

### 反例（面试官追问"没有系统性思路"）
不能只说"用 LLM 调一调"，要分阶段给方案：意图、NL2SQL、取数、分析、渲染、回填，每段都有选型。

## 延伸

## 延伸

- 关联题：[[ml-ai/agent/multi-agent-orchestration-architecture]]
- 关联题：[[ml-ai/rag/rag-full-pipeline]]
- 关联题：[[system-design/short-url-system]]
