---
type: question
id: databases/mysql/btree-vs-binary-tree
title: B+ 树 vs 二叉树对比
category: databases
subcategory: mysql
difficulty: easy
tags: [mysql, b-tree, binary-tree, index, database]
languages: []
role: [ai-app, sde, backend]
companies: [拼多多]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# B+ 树 vs 二叉树对比

## 问题描述
二叉树也是针对查询优化过的，跟 B+ 树相比呢？

## 解答

| 维度 | 二叉树（含 AVL/红黑） | B+ 树 |
| --- | --- | --- |
| 分支数 | 2 | 几百~上千（高扇出） |
| 层数 h | log2 N，百万数据 ~20 | log120 N，百万数据 ~3 |
| 单次 IO | 一层一次 IO | 一个节点一个 page（16KB） |
| 磁盘 IO 次数 | 多（~20） | 少（~3） |
| 范围查询 | 需中序遍历多次回溯 | 叶子链表顺序扫 |

### 核心结论
数据库瓶颈是**磁盘 IO**，不是 CPU 比较。二叉树层数高 → IO 次数多 → 慢。B+ 树靠高扇出把层数压到 3~4，IO 次数极小。

即便二叉树本身"平衡且查询 O(log N)"，在磁盘存储上仍然不如 B+ 树，因为它的"fan-out"太小。

## 延伸

## 延伸

- 关联题：[[databases/mysql/mysql-btree-index]]
