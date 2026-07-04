---
type: question
id: ml-ai/rag/vector-normalization
title: 向量归一化 (L2 / 余弦相似度)
category: ml-ai
subcategory: rag
difficulty: medium
tags: [normalization, l2, cosine, similarity]
languages: []
role: [ai-app, sde, backend]
companies: [中泓一线]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 向量归一化 (L2 / 余弦相似度)

## 问题描述

放到数据库里面之前，要不要归一化？

## 解答

**视距离度量而定，但生产实践强烈建议归一化。**

### 数学关系

- **余弦相似度** = `(A·B) / (||A||·||B||)`
- 若 A、B 都已 L2 归一化（||A||=||B||=1），则 **余弦 = 内积 A·B**。
- 此时可用 `vector_ip_ops`（内积）替代 `vector_cosine_ops`，**查询更快**（少两次范数计算）。

### 是否归一化

| 度量 | 是否需归一化 | 说明 |
| --- | --- | --- |
| 余弦 | 建议但非必须 | 归一化后可走内积索引加速 |
| 内积 (IP) | **必须** | 否则结果受向量模长污染 |
| L2 | 不需要 | L2 本身就含模长信息 |

### 工程做法

- 入库前统一 `vec = vec / np.linalg.norm(vec)`。
- 用 OpenAI / bge 模型时，部分模型默认输出已归一化（OpenAI text-embedding-3 已归一化；bge 需手动）。

## 易错点

- 模型输出未归一化却用内积检索——结果受向量模长影响，召回错乱。

## 延伸

## 延伸

- 关联题：[[ml-ai/rag/pgvector-index-types]]
- 关联题：[[ml-ai/rag/rag-recall-algorithms]]
