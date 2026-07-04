---
type: question
id: databases/mysql/mysql-btree-index
title: MySQL 索引为什么用 B+ 树
category: databases
subcategory: mysql
difficulty: medium
tags: [mysql, b-tree, index, database]
languages: []
role: [ai-app, sde, backend]
companies: [拼多多]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# MySQL 索引为什么用 B+ 树

## 问题描述
你知道 MySQL 的索引是怎么实现的吗？为什么 B+ 树？B+ 树有什么好处？

## 解答

InnoDB 索引数据结构是 **B+ 树（B+ Tree）**。

### B+ 树结构
- 所有数据只存在**叶子节点**，内部节点只存索引（指针）。
- 叶子节点用**双向链表**串起来，便于范围扫描。
- 每个节点通常对应一个 InnoDB page（默认 16KB）。

### 为什么是 B+ 树而不是其他

| 候选 | 问题 |
| --- | --- |
| 二叉搜索树 | 退化为链表；层数太高，磁盘 IO 多 |
| AVL/红黑树 | 二叉 → 层数 h = log2 N，百万数据 ~20 层 = 20 次 IO |
| B 树 | 内部节点也存数据，单节点 key 数少 → 层更高；范围查询要中序遍历多次回溯 |
| Hash | O(1) 等值快，但**不支持范围/排序/最左前缀** |
| **B+ 树** | 内部节点不存数据 → 单节点可塞更多 key → **扇出大、层数低**；范围查询沿叶子链表扫 |

### B+ 树好处
1. **IO 少**：3 层 B+ 树可撑 2000 万行（每节点扇出 ~1200）。
2. **范围查询快**：叶子链表顺序扫。
3. **稳定**：所有数据都在叶子，查询路径长度恒定。

### InnoDB 聚簇索引
- 主键索引 = 聚簇索引，叶子节点存**整行数据**。
- 二级索引叶子存主键值（不是行指针），需**回表**到聚簇索引取行。

## 延伸

## 延伸

- 关联题：[[databases/mysql/btree-vs-binary-tree]]
- 关联题：[[databases/mysql/clustered-vs-secondary-index]]
- 关联题：[[databases/mysql/index-failure-scenarios]]
