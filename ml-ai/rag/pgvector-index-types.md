---
type: question
id: ml-ai/rag/pgvector-index-types
title: PG Vector 索引类型 (IVFFlat / HNSW)
category: ml-ai
subcategory: rag
difficulty: medium
tags: [pgvector, ivfflat, hnsw, ann-index]
languages: []
role: [ai-app, sde, backend]
companies: [中泓一线]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# PG Vector 索引类型 (IVFFlat / HNSW)

## 问题描述

PG Vector 对应有哪些索引类型、存储类型？

## 解答

pgvector 支持两种 ANN 索引（默认精确扫描，无索引时复杂度 O(n)）：

### IVFFlat（倒排文件 + 扁平量化）
- 把向量聚成 `lists` 个簇，查询时只扫 `probes` 个最相近簇。
- 建索引快、内存占用小。
- 召回率依赖 `probes` 调参，精度低于 HNSW。
- SQL：`CREATE INDEX ON t USING ivfflat (vec vector_cosine_ops) WITH (lists = 100);`

### HNSW（分层可导航小世界图）
- 多层图结构，查询沿图贪心走。
- 召回率高、查询快，**但建索引慢、内存占用大**。
- 参数：`m`（邻居数）、`ef_construction`、`ef_search`。
- SQL：`CREATE INDEX ON t USING hnsw (vec vector_cosine_ops) WITH (m = 16, ef_construction = 64);`

### 存储类型
- `vector(n)` 固定维度，存储为 float4 数组。
- `halfvec(n)` — pgvector 0.7+，半精度，**省一半空间**，精度损失可接受，生产推荐。

### ops 算子（必须匹配距离度量）
- `vector_cosine_ops`（余弦）/ `vector_l2_ops`（欧式）/ `vector_ip_ops`（内积）
- **索引的 ops 必须和查询用的距离函数一致**，否则索引失效。

## 易错点

- 用 `vector_cosine_ops` 建索引却用 `<->`（L2）查询——索引不走。
- 入库向量未归一化却用 cosine——结果对但浪费内积优化（见 [[ml-ai/rag/vector-normalization]]）。

## 延伸

## 延伸

- 关联题：[[ml-ai/rag/vector-normalization]]
- 关联题：[[ml-ai/rag/vector-database-selection]]
