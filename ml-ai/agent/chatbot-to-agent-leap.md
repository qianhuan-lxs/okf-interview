---
type: question
id: ml-ai/agent/chatbot-to-agent-leap
title: Chatbot → Agent 的核心跨越
category: ml-ai
subcategory: agent
difficulty: easy
tags: [chatbot, agent, concept]
languages: []
role: [ai-app, sde, backend]
companies: [广州大娱]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# Chatbot → Agent 的核心跨越

## 问题描述

从一个 chatbot 到智能体，核心要解决的问题是什么？怎么从这步跨到这步？

## 解答

chatbot 是 **"输入文本 → 输出文本"** 的单轮映射；agent 是 **"目标 → 感知-决策-行动循环 → 状态变更"** 的闭环。核心跨越有三：

1. **行动能力（Actuation）** — chatbot 只能说话，agent 能调工具、改世界状态。技术上是 Function Call / Tool Use / MCP。
2. **自主决策循环（Autonomy Loop）** — chatbot 一问一答；agent 有 ReAct / Plan-Execute 循环：感知（读 observation）→ 思考（thought）→ 行动（action）→ 观察（observation）→ 继续，直到任务完成。
3. **状态与记忆（State & Memory）** — chatbot 无状态靠 prompt 拼历史；agent 维护持久 state、可跨轮跨会话记忆。

一句话：**chatbot 是"嘴"，agent 是"嘴+手+脑循环+记忆"**。

## 延伸

## 延伸

- 关联题：[[ml-ai/agent/agent-function-call-mechanism]]
- 关联题：[[ml-ai/agent/multi-agent-orchestration-architecture]]
