---
type: question
id: ml-ai/rag/rag-full-pipeline
title: RAG 完整流程 (切分 → Embedding → 检索 → 生成)
category: ml-ai
subcategory: rag
difficulty: medium
tags: [rag, embedding, retrieval, generation]
languages: []
role: [ai-app, sde, backend]
companies: [中泓一线]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# RAG 完整流程 (切分 → Embedding → 检索 → 生成)

## 问题描述

说一下 RAG 的整个过程。（中泓一线总监面深挖）

## 解答

RAG = Retrieval-Augmented Generation，分 **离线索引** + **在线检索生成** 两大阶段。

### 离线索引（Indexing）

1. **Load** — 加载源文档（PDF/HTML/Markdown/DB）。
2. **Clean / Parse** — 去噪、提正文、OCR、表格识别。
3. **Chunk（切分）** — 按语义切块。策略：
   - 固定长度 + overlap（最简单）
   - 按结构（段落/标题/Markdown header）
   - 语义切分（SemanticChunker，按 embedding 相似度断句）
   - 父子切分（小粒度检索、大粒度返回）
4. **Embed** — 每个 chunk 过 embedding 模型得向量。
5. **Store** — 向量 + 原文 + 元数据写入向量库。

### 在线检索生成（Query）

1. **Query Transform** — 改写 / HyDE / 多 query 扩展，提升召回。
2. **Embed Query** — 用同一 embedding 模型向量化问题。
3. **Retrieve** — 向量库 top-k（余弦/KNN）+ 可选 BM25 混合检索。
4. **Rerank** — Cross-encoder reranker 重排，提精度。
5. **Context Assembly** — 拼 Prompt：system + 检索片段 + 问题。
6. **Generate** — LLM 基于片段生成答案，附引用。
7. **Cite / Grounding check** — 标注来源，必要时做幻觉检测。

## 易错点

- 切分粒度一刀切——短问题要小 chunk，长摘要要大 chunk，应父子分层。
- 检索只靠向量——关键词/精确匹配场景要加 BM25 混合。
- 不做 rerank——向量召回 recall 高但 precision 低，rerank 提精度。

## 延伸

## 延伸

- 关联题：[[ml-ai/rag/embedding-model-selection]]
- 关联题：[[ml-ai/rag/rag-recall-algorithms]]
- 关联题：[[ml-ai/rag/vector-database-selection]]
