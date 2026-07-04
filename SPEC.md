# Interview Knowledge Format (IKF) — v0.1

本规范定义本仓库面试题文档的格式。设计参考 [OKF v0.1](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)。

## 1. 文件即文档

一道题 = 一个 `.md` 文件，路径位于其所属分类目录下：

```
algorithms/dynamic-programming/longest-increasing-subsequence.md
```

路径即 ID。**文件一旦提交，路径不应再变**（否则会破坏所有引用链接）。重命名请用 `tools/okf.py move`，CLI 会同步更新反向链接。

## 2. YAML Frontmatter（必填 + 推荐 + 自由扩展）

### 2.1 必填字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `type` | string | 固定 `question`（保留以便日后支持 `note`/`case` 等） |
| `id` | string | 与相对路径一致（去 `.md`），如 `algorithms/dynamic-programming/longest-increasing-subsequence` |
| `title` | string | 人类可读标题 |
| `category` | string | 一级分类，必须与所在一级目录名一致 |
| `difficulty` | enum | `easy` / `medium` / `hard` |
| `timestamp` | date | ISO 日期 `YYYY-MM-DD`，最后修改时间 |

### 2.2 推荐字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `subcategory` | string | 二级分类，与所在二级目录名一致 |
| `tags` | list[string] | 细粒度考点标签，小写 kebab-case，如 `["binary-search", "monotonic-stack"]` |
| `languages` | list[string] | 涉及的编程语言代码标签，如 `["python", "cpp"]` |
| `role` | list[string] | 目标岗位：`sde` / `backend` / `frontend` / `ml-engineer` / `devops` / `data-engineer` / ... |
| `companies` | list[string] | 出题公司，如 `["Google", "ByteDance"]` |
| `source` | string | 题源，如 `leetcode-300` / `cracking-coding-interview-p123` / `interview-2026-06` |
| `status` | enum | `todo` / `draft` / `reviewed` / `mastered`，记录掌握程度 |

### 2.3 自由扩展

任何额外键都允许。建议前缀 `x-` 以避免与未来规范冲突，例如 `x-time-limit-sec: 30`。

### 2.4 Frontmatter 示例

```yaml
---
type: question
id: algorithms/dynamic-programming/longest-increasing-subsequence
title: 最长递增子序列
category: algorithms
subcategory: dynamic-programming
difficulty: medium
tags: [dynamic-programming, binary-search, sequence]
languages: [python, cpp]
role: [sde, backend]
companies: [Google, ByteDance]
source: leetcode-300
status: reviewed
timestamp: 2026-07-04
---
```

## 3. 正文结构

正文使用 markdown，推荐分节（不强制顺序，但建议至少包含"问题"和"解答"）：

```markdown
# <title>

## 问题描述
<题面，必要时贴原题链接>

## 输入输出 / 约束
<如果是算法题，列示例和约束>

## 思路
<关键洞察、推导过程、可能的多种解法对比>

## 解答

### 解法一：<名称>
\`\`\`python
<code>
\`\`\`

### 解法二：<名称>
...

## 复杂度
- 时间：O(...)
- 空间：O(...)

## 易错点
- ...

## 延伸
- 关联题：[[algorithms/dynamic-programming/longest-common-subsequence]]
- 进阶题：[[algorithms/dynamic-programming/russian-doll-envelopes]]
```

## 4. 链接与图谱

- 题目之间用 wiki-link 风格 `[[<id>]]` 或标准 markdown 链接 `[文本](../<path>.md)` 互引。
- `tools/okf.py gen-index` 会同时生成每个 `index.md` 的"被引用 (cited by)"反链列表。

## 5. index.md（Progressive Disclosure）

每个目录（含根）都有一个 `index.md`，列出该目录下：

1. 直接子目录（带简介 + 题目数）
2. 该目录下的题目（标题 + 难度 + 标签，一行一条）
3. 该目录被外部引用的反链

Agent 工作流推荐：**先读 `index.md` 决定下钻哪个子目录，再读具体题目文件**——避免一次性把全库塞进上下文。

## 6. Agent 查询契约

Agent 可信赖以下不变量：

1. **每个题目文件都有 frontmatter**，且包含 §2.1 全部必填字段。
2. **`id` 字段 = 相对路径（去 `.md`）**，可作主键。
3. **`category` / `subcategory` 与文件实际所在目录一致**。
4. **`tags` / `companies` / `role` / `languages` 永远是列表**（即使只有一个元素也用 `[]`），便于 `rg -l '^tags:.*xxx'` 一致命中。
5. **`index.md` 可被跳过**——它由工具生成，Agent 如需精确统计仍应以题目文件为源。

## 7. 命名规范

- 文件名：kebab-case，语义化，避免纯数字题号。例：`two-sum.md` 而非 `1.md`。
- 目录名：kebab-case，复数用于"集合"语义（如 `arrays-strings`），单数用于"领域"语义（如 `system-design`）。
- 标签：全小写 kebab-case。
- 公司名：使用官方英文品牌名（`Google`、`ByteDance`、`Meta`）。
