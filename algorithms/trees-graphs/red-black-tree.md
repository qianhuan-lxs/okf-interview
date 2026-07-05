---
type: question
id: algorithms/trees-graphs/red-black-tree
title: 红黑树 (5 性质/旋转着色/为什么不用 AVL/HashMap 树化)
category: algorithms
subcategory: trees-graphs
difficulty: hard
tags: [red-black-tree, balanced-tree, rotation, tree-map, hashmap, data-structure, java]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-07-05
---

# 红黑树 (5 性质/旋转着色/为什么不用 AVL/HashMap 树化)

## 问题描述

红黑树是什么？5 条性质？为什么不用 AVL？旋转和着色怎么工作？哪些地方用到？

## 解答

## 一、红黑树是什么

**自平衡二叉搜索树**，通过"节点染色 + 旋转"保证：任意节点到叶子的最长路径不超过最短路径的 2 倍 → 高度 O(log n)。

## 二、5 条性质（必背）

1. 每个节点**非红即黑**。
2. **根是黑**。
3. **每个叶子（NIL 空节点）是黑**。
4. **红节点的子节点必须黑**（不能连续两个红）。
5. **任意节点到其所有叶子节点的路径包含相同数量的黑节点**（黑高相同）。

由 4 和 5 推出：最长路径（红黑相间）≤ 2 × 最短路径（全黑）→ 树高 ≤ 2 log(n+1)。

## 三、为什么不用 AVL

| 维度 | AVL | 红黑树 |
| --- | --- | --- |
| 平衡严格度 | 严格（左右子树高度差 ≤1） | 弱平衡（最长 ≤ 2×最短） |
| 查询 | 略快（树更矮） | 略慢 |
| 插入/删除旋转 | 多（最多 2 次） | 少（插入最多 2 旋转，删除最多 3 旋转） |
| 适用 | **读多写少** | **写多读少 / 通用** |

红黑树**牺牲一点查询性能换更少的旋转**——通用场景（既有读又有写）更合适。AVL 严格平衡查询最优但写操作旋转代价高。

## 四、旋转与着色

### 左旋 / 右旋
```
    Y                X
   / \              / \
  X   C    →       A   Y
 / \                  / \
A   B                B   C
```
- 旋转不改中序遍历顺序（BST 性质保持）。
- 旋转是 O(1) 局部操作。

### 插入调整
- 新插入节点默认**红**（不影响黑高）。
- 若父是黑 → 直接结束。
- 若父是红（违反性质 4）：
  - 叔也是红 → 父和叔改黑，祖父改红，递归处理祖父。
  - 叔是黑 → 旋转 + 着色（4 种情况：LL/LR/RL/RR，类似 AVL）。
- 最多 2 次旋转 + O(log n) 次着色。

### 删除调整
- 更复杂，涉及"双重黑"节点的修复。
- 最多 3 次旋转。

## 五、复杂度

| 操作 | 时间 |
| --- | --- |
| 查询 | O(log n) |
| 插入 | O(log n) |
| 删除 | O(log n) |
| 旋转次数（插入） | ≤ 2 |
| 旋转次数（删除） | ≤ 3 |

## 六、应用（高频追问）

| 场景 | 用 |
| --- | --- |
| **Java `TreeMap` / `TreeSet`** | 红黑树 |
| **Java 8+ `HashMap` 链表树化** | 链表 ≥8 且容量 ≥64 → 红黑树 |
| **C++ `std::map` / `std::set`** | 红黑树 |
| **Linux 内核 CFS 调度器** | 红黑树管理进程（按 vruntime 排序） |
| **Linux epoll** | 红黑树管理监听 fd |
| **Nginx timer** | 红黑树 |
| **EXT3/EXT4 文件系统** | 红黑树管理目录项 |

## 七、为什么 HashMap 树化用红黑树

- 链表 O(n) → 树 O(log n)，防哈希冲突攻击（恶意 key 全冲突 → 链表超长 → 查找退化）。
- 用红黑树不用 AVL：HashMap 写多（put/remove 频繁），红黑树旋转少更适合。
- 树化是兜底（链表 ≥8 概率千万分之一，见 [HashMap 深讲](languages/java/hashmap-deep-dive)），不是常态。

## 八、TreeMap 源码要点

- `Entry<K,V>`：`key, value, left, right, parent, color`。
- `put`：BST 插入 + 调平衡（`fixAfterInsertion`）。
- `remove`：BST 删除 + `fixAfterDeletion`。
- `get`：BST 查找 O(log n)。
- 支持 `firstKey`/`lastKey`/`subMap`/`headMap`/`tailMap` 等有序操作——这是 TreeMap 比 HashMap 强的地方。
- **非线程安全**；并发用 `ConcurrentSkipListMap`（注意是跳表，不是红黑树并发版）。

## 易错点
- 红黑树当完全平衡 → 是弱平衡，最长 ≤ 2×最短。
- 以为根是红 → 根必须黑。
- 以为红节点不能有红子节点就够 → 还要黑高相同。
- 以为 AVL 总比红黑树好 → 写多场景红黑树优。
- TreeMap 当线程安全 → 否，并发用 ConcurrentSkipListMap。
- 以为 HashMap 链表 ≥8 必树化 → 还要 capacity ≥64。

## 延伸

- 关联题：[[languages/java/hashmap-deep-dive]]
- 关联题：[[algorithms/linked-lists/skip-list.md]]
- 关联题：[[databases/mysql/btree-vs-binary-tree.md]]
