---
type: question
id: ml-ai/rag/heterogeneous-data-vectorization
title: 异构数据向量化 (文本 / 语音 / 视频)
category: ml-ai
subcategory: rag
difficulty: medium
tags: [multimodal, embedding, audio, video, image]
languages: []
role: [ai-app, sde, backend]
companies: [中泓一线]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 异构数据向量化 (文本 / 语音 / 视频)

## 问题描述

不同文件类型（文本/语音/视频）转成向量后，怎么存储这个字段？维度长度是多少？

## 解答

### 各模态向量化路径

| 模态 | 路径 | 典型模型 |
| --- | --- | --- |
| **文本** | text → embedding | bge-m3 / OpenAI |
| **图像** | image → embedding | CLIP / SigLIP（图文共用空间） |
| **语音** | audio → ASR 转文本 → 文本 embedding；或 audio → CLAP 音频 embedding | Whisper + bge / CLAP |
| **视频** | 抽关键帧 → 图像 embedding；或 ASR 字幕 + 视觉特征融合 | CLIP + Whisper |

### 存储策略

1. **统一向量空间**：用 CLIP 类多模态模型，文/图/音在**同一向量空间**，可跨模态检索（用文本搜图）。存同一张向量表的 `vec` 列。
2. **分模态向量空间**：各模态各用各的 embedding 模型，分表存。检索时按模态分别召回再融合。
3. **向量 + 原始引用**：向量库只存 embedding + `modality` + `source_uri`，原始媒体落对象存储。

### 维度

- 不强制统一——文本 1024、图像 512（CLIP）、音频 1024（CLAP）可各不相同。
- 若要同一空间（CLIP 系），各模态维度一致（如 512/768）。

### 字段 schema（pgvector 示例）

```sql
CREATE TABLE chunks (
  id bigint primary key,
  modality text,          -- text/image/audio/video
  source_uri text,
  embedding vector(1024), -- 文本
  -- 或分列：text_vec vector(1024), img_vec vector(512)
  payload jsonb
);
```

## 易错点

- 强行把不同模态向量塞同一空间却用了不同模型——跨模态检索结果无意义。
- 把原始音视频也塞向量库——应只存引用。

## 延伸

## 延伸

- 关联题：[[ml-ai/rag/vector-dimension-tradeoff]]
- 关联题：[[ml-ai/rag/vector-database-selection]]
