---
type: question
id: databases/mysql/inverted-index-es
title: 倒排索引原理 (ES)
category: databases
subcategory: mysql
difficulty: medium
tags: [elasticsearch, inverted-index, search, database]
languages: []
role: [ai-app, sde, backend]
companies: [恩士讯, 北京用友]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 倒排索引原理 (ES)

## 问题描述
ES 倒排索引的原理？还有哪些组成部分？

## 解答

**倒排索引 (Inverted Index)**：从"词"反查"文档列表"，是搜索引擎的核心结构。

### 结构
- **Term Dictionary（词典）**：所有出现过的词项。
- **Term Index（词典索引）**：FST/前缀树，快速定位 Term 在 Dictionary 中的位置。
- **Posting List（倒排表）**：每个 Term 对应的文档 ID 列表 + 词频 + 位置 + 偏移。
- 词典通常放内存，倒排表放磁盘（FOR + RBM 压缩）。

### 工作流程
1. **写入**：文档分析（分词）→ 每个 term 建倒排表项。
2. **查询**：query 分词 → 在词典查 term → 取 posting list → 交集/并集 → 打分（TF-IDF/BM25）排序。

### ES 倒排组成部分（追问）
- Doc Values（正排）：用于排序、聚合（避免 fielddata 反解倒排）。
- Source：原始 JSON。
- _id 索引、_all（已废弃）、_type（已废弃）。
- **分片（shard）** = 一个 Lucene 索引；副本（replica）。

### 与 B+ 树对比
- B+ 树擅长**等值/范围/排序**，对全文模糊匹配（LIKE '%x%'）无效。
- 倒排擅长**全文检索**，能秒级匹配千万文档关键词。

## 延伸

## 延伸

- 关联题：[[databases/mysql/mysql-btree-index]]
