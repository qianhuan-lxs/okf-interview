---
type: question
id: ml-ai/rag/rag-recall-algorithms
title: 召回算法 (余弦 / KNN / Reranker / 混合检索)
category: ml-ai
subcategory: rag
difficulty: medium
tags: [recall, cosine, knn, rerank, hybrid-search]
languages: []
role: [ai-app, sde, backend]
companies: [中泓一线]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 召回算法 (余弦 / KNN / Reranker / 混合检索)

## 问题描述

用户提问的时候，召回算法有哪些种？匹配算法？

## 解答

### 一阶段：召回（Recall，求快求全）

| 算法 | 类型 | 说明 |
| --- | --- | --- |
| **余弦相似度 (Cosine)** | 稠密向量 | 文本语义最常用，归一化后等价内积 |
| **L2 / 欧式距离** | 稠密向量 | 对模长敏感，图像场景多 |
| **内积 (IP)** | 稠密向量 | 归一化向量等价 cosine，更快 |
| **KNN（精确）** | 暴力扫描 | O(n)，小数据或 ground truth |
| **ANN（近似 KNN）** | 索引加速 | HNSW / IVF / PQ，牺牲少量精度换速度 |
| **BM25** | 稀疏关键词 | 精确匹配、专有名词、ID 类强 |

### 二阶段：重排（Rerank，求准）

- **Cross-encoder Reranker**（bge-reranker / Cohere rerank）：把 (query, doc) 一起送模型打分，精度远高于向量相似度，但慢——只对 top-50 重排。

### 三阶段：混合检索（Hybrid）

- **向量 + BM25 并联召回** → **RRF（Reciprocal Rank Fusion）融合** → reranker 重排。
- 解决"语义召回好但专名漏"和"关键词召回好但语义漏"的互补问题。

### 流水线

```
Query → [Dense ANN top-100] + [BM25 top-100] → RRF 融合 top-50 → Reranker top-5 → LLM
```

## 易错点

- 只用向量召回——专有名词、代码、ID 召回差。
- 不做 rerank——top-1 常不是最相关。

## 延伸

## 延伸

- 关联题：[[ml-ai/rag/rag-full-pipeline]]
- 关联题：[[ml-ai/rag/vector-normalization]]
