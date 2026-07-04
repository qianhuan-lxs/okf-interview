---
type: question
id: ml-ai/rag/vector-dimension-tradeoff
title: 向量维度 trade-off (1024 vs 3072 vs 128)
category: ml-ai
subcategory: rag
difficulty: medium
tags: [vector-dimension, storage, recall, tradeoff]
languages: []
role: [ai-app, sde, backend]
companies: [中泓一线]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 向量维度 trade-off (1024 vs 3072 vs 128)

## 问题描述

向量字段一般设置多长？1024 设的长还是短？对我们有什么影响？可以设两万多吗？128 可以吗？

## 解答

维度 d 是 **召回精度 / 存储 / 计算成本** 的三角 trade-off：

| 维度 | 存储（每向量） | 召回精度 | 查询耗时 | 适用 |
| --- | --- | --- | --- | --- |
| 128 | 0.5 KB | 低 | 极快 | 原型、粗排、人脸/图像 |
| 768 | 3 KB | 中 | 快 | m3e/GTE-base |
| 1024 | 4 KB | 中高 | 中 | bge-m3、主流选择 |
| 1536 | 6 KB | 高 | 较慢 | OpenAI 3-small |
| 3072 | 12 KB | 很高 | 慢 | OpenAI 3-large、长尾精度 |

### 经验

- **1024 是当前主流甜点**——精度够、成本可控。
- **3072 一般不值**——精度边际收益小，存储/索引/查询成本翻倍。OpenAI 3-large 支持 **Matryoshka 降维**：直接取前 1536/768 维即可降维（损失很小）。
- **128 对中文文本检索太短**——语义信息丢太多，召回差。
- **两万多**（如一些大模型 hidden）几乎没人用全量，会降维或蒸馏。

### 影响

- 存储：`N × d × 4 bytes`，1M 条 3072 维 = 12GB。
- 索引构建时间随 d 近似线性增长。
- HNSW 内存占用 ≈ 向量本体 × 1.5。

## 延伸

## 延伸

- 关联题：[[ml-ai/rag/embedding-model-selection]]
- 关联题：[[ml-ai/rag/vector-database-selection]]
