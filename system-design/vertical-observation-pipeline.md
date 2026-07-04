---
type: question
id: system-design/vertical-observation-pipeline
title: 垂直观测链路系统设计
category: system-design
subcategory: system-design
difficulty: hard
tags: [system-design, observability, tracing, evaluation, ai-agent]
languages: []
role: [ai-app, sde, backend]
companies: [探迹]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 垂直观测链路系统设计

## 问题描述
知道我们公司做什么？如果参与进来做垂直观测链路系统，你怎么设计？从买家消息到 AI 答案整个数据流转应该怎样？

## 思路

"垂直观测链路"= 把一条 AI 业务（买家消息→AI 答案）的**全链路数据流和评测**串起来，做问题定位、质量度量、回流改进。本质是 AI 版的 APM + 数据飞轮。

## 解答

### 全链路数据流
```
1. 买家消息 (IM/客服) 
   → 2. 接入网关 (脱敏、限流、traceId 注入)
   → 3. 编排 Agent (意图分类 → RAG/Tool/Memory)
       ├─ 3.1 RAG 检索 (query 改写 / 向量召回 / rerank)
       ├─ 3.2 Tool 调用 (CRM 查订单 / 知识库)
       └─ 3.3 LLM 生成 (prompt / model / params)
   → 4. 后处理 (审核 / 引用标注 / 安全过滤)
   → 5. 答案回传买家
   → 6. 用户反馈 (点赞/点踩/转人工)
   → 7. 评测回流 (自动指标 + 人工标注)
```

### 观测维度（每段都打点）
| 维度 | 指标 |
| --- | --- |
| 链路 | traceId 串联，每 step input/output/latency/token/cost |
| 业务 | 解决率、转人工率、满意度、首次响应时长 |
| RAG | 召回 recall@k、引用准确率、片段命中 |
| 安全 | 敏感词命中、PII 泄漏、幻觉率 |
| 成本 | token / 调用次数 / 单会话成本 |

### 系统架构
- **采集**：SDK / OpenTelemetry instrumentation 在各环节打 span + 事件。
- **传输**：Kafka 解耦，避免业务阻塞。
- **存储**：
  - trace：ClickHouse / Tempo / Jaeger（高写入、查链路）。
  - 事件明细：ES（全文搜"哪条会话出错"）。
  - 指标：Prometheus + VictoriaMetrics。
  - 原始会话：对象存储 + Hive/Iceberg 离线分析。
- **查询/展示**：Grafana 面板 + 自研会话回放页（按 traceId 还原全流程，含每步 prompt/response）。
- **评测回流**：
  - 在线：自动指标（回答长度、引用是否在召回集、用户点踩率）。
  - 离线：人工标注 + LLM-as-Judge 打分，导 bad case 给 prompt/skill 迭代。
  - 形成"线上观测→bad case→离线评测→prompt/RAG 改进→上线"闭环。

### 测试链路（追问）
- 录制线上流量做离线回放（影子库），新 prompt/模型灰度对比指标。
- 黄金集回归：固定一批 QA，每次模型/prompt 变更跑一遍，监控指标漂移。
- A/B：流量分桶对比新旧版本。

### 体量
- 假设 100w 会话/天，每会话 5 step → 500w span/天，单 span ~1KB → 5GB/天，ClickHouse 轻松。
- 保留热数据 7 天 + 冷归档。

## 延伸

## 延伸

- 关联题：[[ml-ai/agent/multi-agent-orchestration-architecture]]
- 关联题：[[ml-ai/rag/rag-recall-algorithms]]
- 关联题：[[devops/devops-direction-understanding]]
