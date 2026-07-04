---
type: question
id: ml-ai/rag/embedding-model-selection
title: Embedding 模型选型 (bge / OpenAI / m3e)
category: ml-ai
subcategory: rag
difficulty: easy
tags: [embedding, bge, openai, m3e, model-selection]
languages: []
role: [ai-app, sde, backend]
companies: [中泓一线]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# Embedding 模型选型 (bge / OpenAI / m3e)

## 问题描述

Embedding 用的什么模型？

## 解答

| 模型 | 维度 | 语言 | 部署 | 特点 |
| --- | --- | --- | --- | --- |
| **OpenAI text-embedding-3-small/large** | 1536 / 3072（可降维） | 多语 | 闭源 API | 效果稳、贵、需出境 |
| **bge-large-zh / bge-m3**（智源） | 1024 / 1024 | 中/多语 | 可本地 | 中文 SOTA、开源、可私有化 |
| **m3e-base/large** | 768 / 1024 | 中文 | 可本地 | 中文老牌开源，效果略逊 bge |
| **Cohere embed-v3** | 1024 | 多语 | 闭源 API | 英文强 |
| **GTE（阿里）** | 768/1024 | 中英 | 可本地 | 开源、长文本友好 |

**选型建议（中文场景）：**
- 私有化 + 中文 SOTA → **bge-m3**（支持稀疏+稠密+多向量，长文本好）
- 不愿出境 + 快速验证 → m3e
- 英文为主 / 接受 API → OpenAI 3-small

## 易错点

- 中英文混用却选了纯中文模型——英文召回差。
- embedding 模型和 LLM 混为一谈——embedding 只做向量化，不生成文本。

## 延伸

## 延伸

- 关联题：[[ml-ai/rag/rag-full-pipeline]]
- 关联题：[[ml-ai/rag/vector-dimension-tradeoff]]
