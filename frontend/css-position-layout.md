---
type: question
id: frontend/css-position-layout
title: CSS 定位布局
category: frontend
subcategory: frontend
difficulty: easy
tags: [css, position, layout, flexbox, frontend]
languages: []
role: [ai-app, sde, backend]
companies: [中泓一线]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# CSS 定位布局

## 问题描述
CSS 前端的定位布局有哪些种？

## 解答

### position 定位
| 值 | 脱离文档流 | 参照 |
| --- | --- | --- |
| `static`（默认） | 否 | 正常流 |
| `relative` | 否 | 自身原位置 |
| `absolute` | 是 | 最近非 static 祖先 |
| `fixed` | 是 | 视口（或 transform 祖先） |
| `sticky` | 否 | 滚动到阈值前 relative，越界后 fixed |

### 布局方案
- **正常流**：block / inline / inline-block。
- **Float**：老布局，已少用。
- **Flexbox**（一维）：`display:flex; justify-content; align-items`。
- **Grid**（二维）：`display:grid; grid-template-columns`。
- **定位**：上述 position 组合。
- **多列**：column-count。

### 居中速查
- Flex：`display:flex; justify-content:center; align-items:center;`（最通用）
- Grid：`place-items:center`
- 绝对定位：`position:absolute; top:50%; left:50%; transform:translate(-50%,-50%)`
- 行内：父 `text-align:center`；行高 = 高度则垂直居中

### BFC（块级格式化上下文）
- 触发：overflow 非 visible / float / position:absolute,fixed / display:flex,inline-block 等。
- 作用：清浮动、避免 margin 重叠、隔离布局。

## 延伸

## 延伸

- 关联题：[[frontend/vue-interceptors]]
