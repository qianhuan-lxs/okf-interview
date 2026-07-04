---
type: question
id: ml-ai/rag/vector-database-selection
title: 向量数据库选型 (PG Vector / Milvus / ...)
category: ml-ai
subcategory: rag
difficulty: easy
tags: [vector-database, pgvector, milvus, qdrant, selection]
languages: []
role: [ai-app, sde, backend]
companies: [中泓一线]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 向量数据库选型 (PG Vector / Milvus / ...)

## 问题描述

熟悉的向量数据库有哪些？PG Vector 怎么样？

## 解答

| 方案 | 类型 | 适合规模 | 优势 | 劣势 |
| --- | --- | --- | --- | --- |
| **pgvector** | Postgres 扩展 | <10M | 复用 PG 生态、事务、SQL 混合查询 | 规模上限低、ANN 算法少 |
| **Milvus** | 专用 | 1B+ | 分布式、多索引、高性能 | 部署重（etcd+minio+pv） |
| **Qdrant** | 专用 | 中大 | Rust 实现、轻、filter 强 | 生态略小 |
| **Chroma** | 嵌入式 | 小/原型 | 零部署 | 不适合生产 |
| **Weaviate** | 专用 | 中大 | 内置混合检索、schema 灵活 | 资源占用高 |
| **Elasticsearch** | 搜索引擎 | 大 | BM25+vector 混合天然 | 向量性能弱于专用 |

**选型经验：**
- 已有 PG + 数据量 < 千万 → **pgvector**（运维零增量）
- 亿级以上 + 严肃生产 → **Milvus**
- 中等规模 + 重过滤 → **Qdrant**

## 延伸

## 延伸

- 关联题：[[ml-ai/rag/pgvector-index-types]]
- 关联题：[[ml-ai/rag/rag-full-pipeline]]
