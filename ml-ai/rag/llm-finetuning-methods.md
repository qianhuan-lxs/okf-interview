---
type: question
id: ml-ai/rag/llm-finetuning-methods
title: 大模型微调训练方式 (LoRA / QLoRA / SFT / RLHF)
category: ml-ai
subcategory: rag
difficulty: medium
tags: [finetuning, lora, qlora, sft, rlhf, dpo]
languages: []
role: [ai-app, sde, backend]
companies: [中泓一线]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 大模型微调训练方式 (LoRA / QLoRA / SFT / RLHF)

## 问题描述

大模型微调训练部署怎么训练？训练方式有哪些种？

## 解答

训练方式分两个正交维度：**训练目标** 和 **参数效率**。

### 按训练目标

| 方式 | 目标 | 数据 | 用途 |
| --- | --- | --- | --- |
| **Pretrain** | 自回归下一个 token | 海量无标注 | 从零训基座（一般不做） |
| **SFT (Supervised Fine-Tuning)** | 模仿标注样本 | (instruction, response) 对 | 教模型按指令回答 |
| **RLHF** | 人类偏好强化学习 | 偏好对 + reward model | 对齐人类偏好 |
| **DPO** | 直接偏好优化 | 偏好对（chosen/rejected） | RLHF 的简化，无需 reward model |
| **Continued Pretrain** | 领域语料继续预训练 | 领域无标注 | 注入领域知识 |

### 按参数效率（PEFT）

| 方式 | 可训参数 | 显存 | 适用 |
| --- | --- | --- | --- |
| **Full FT** | 100% | 极高 | 资源充足、效果上限最高 |
| **LoRA** | 低秩矩阵 A·B，<1% | 中 | 主流，性价比最高 |
| **QLoRA** | LoRA + 基座 4bit 量化 | 低 | 单卡可训大模型 |
| **Adapter / Prefix Tuning** | 插入小模块 | 中 | 老牌 PEFT，渐被 LoRA 替代 |

### 典型组合

- **领域注入**：Continued Pretrain + SFT
- **指令对齐**：SFT + DPO
- **资源紧张 + 7B/13B**：QLoRA + SFT

### 部署

合并 LoRA 权重回基座 → 量化（GPTQ/AWQ/GGUF）→ vLLM / TGI / Ollama 服务化。

## 易错点

- 把 SFT 当成预训练——SFT 不会注入大量新知识，只是改变行为风格。
- RLHF/DPO 想在 RAG 场景直接用——通常应先 SFT 让模型学会用检索片段再 DPO。

## 延伸

## 延伸

- 关联题：[[ml-ai/rag/rag-full-pipeline]]
