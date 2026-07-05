---
type: question
id: algorithms/linked-lists/skip-list
title: 跳表 (Skip List) (结构/概率平衡/Redis Zset/为什么不用红黑树)
category: algorithms
subcategory: linked-lists
difficulty: medium
tags: [skip-list, redis, zset, data-structure, probabilistic, ordered-set]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-07-05
---

# 跳表 (Skip List) (结构/概率平衡/Redis Zset/为什么不用红黑树)

## 问题描述

跳表是什么？怎么做到 O(log n) 查询？为什么 Redis Zset 用跳表不用红黑树？跳表 vs 平衡树？

## 解答

## 一、跳表是什么

**多层链表**，用"空间换时间"让有序链表也能 O(log n) 查询。

```
Level 3:  HEAD ------------------------------> 50 ----------------------> NIL
Level 2:  HEAD -------------> 20 -----------> 50 ------------> 80 -----> NIL
Level 1:  HEAD ----> 10 ----> 20 ----> 30 --> 50 ----> 70 --> 80 -----> NIL
Level 0:  HEAD -> 5 -> 10 -> 20 -> 30 -> 40 -> 50 -> 60 -> 70 -> 80 -> NIL
```
- **底层 Level 0 是完整有序链表**。
- 每层是下层的"索引"：每隔几个节点抽一个上来。
- 查询从最高层开始，遇大就下沉一层，直到底层。

## 二、查询 O(log n) 怎么实现

查 60：
1. Level 3：HEAD → 50 < 60，往右没节点了 → 下沉。
2. Level 2：50 → 80 > 60 → 下沉（不前进）。
3. Level 1：50 → 70 > 60 → 下沉。
4. Level 0：50 → 60 → 命中。

- 每层最多走几步，层数 = O(log n) → 总 O(log n)。
- 类似二分，但用链表实现——不需要数组下标。

## 三、概率平衡（不用刻意再平衡）

- 插入新节点时**随机决定层数**：以概率 p（通常 1/2 或 1/4）决定是否升一层，直到不升或达上限。
- 期望层数 = `log_(1/p) n`。
- 不像红黑树要旋转维护平衡——**概率保证期望平衡**，实现简单。
- 极端情况会退化成单层链表（概率极低），但工程上可接受。

## 四、插入/删除

### 插入
1. 从最高层开始查找到插入位置，**记录每层的前驱**（update 数组）。
2. 随机生成层数 level。
3. 在 0~level 层插入新节点，更新前驱的 next 指针。
- 复杂度 O(log n) 期望。

### 删除
1. 查找节点，记录每层前驱。
2. 在所有出现该节点的层移除它。
- 复杂度 O(log n) 期望。

## 五、为什么 Redis Zset 用跳表不用红黑树

Redis 作者 antirez 给的理由：
1. **内存占用灵活**：跳表节点层数随机，平均每节点 1.33 指针（p=1/4）；红黑树每节点固定 2 子指针 + 父指针 + 颜色。实际相差不大，但跳表可通过调 p 控制内存/性能权衡。
2. **范围查询友好**：Zset 的 `ZRANGE` / `ZRANGEBYSCORE` 要范围扫，跳表底层是有序链表，找到起点后顺着 next 指针走即可 O(log n + m)；红黑树要中序遍历，回溯多。
3. **实现简单**：跳表代码远比红黑树简单（无旋转、无着色规则），易调试易维护。
4. **缓存局部性**：跳表底层链表连续遍历，比红黑树分散节点更缓存友好（部分场景）。

## 六、跳表 vs 红黑树

| 维度 | 跳表 | 红黑树 |
| --- | --- | --- |
| 查询/插入/删除 | O(log n) 期望 | O(log n) 最坏 |
| 平衡机制 | 概率（随机层数） | 严格规则（旋转+着色） |
| 范围查询 | O(log n + m) 链表顺序扫 | O(log n + m) 中序遍历（回溯） |
| 实现 | 简单 | 复杂 |
| 最坏退化 | 退化成链表（概率极低） | 不会退化 |
| 内存 | 平均 1.33 指针/节点 | 固定 2 子+父+颜色 |
| 并发 | 易加锁（层独立） | 旋转影响全局 |

## 七、Java 里的跳表

- `ConcurrentSkipListMap`：JUC 提供的并发跳表 Map，实现 `ConcurrentNavigableMap`。
- `ConcurrentSkipListSet`：并发跳表 Set。
- **为什么不用 TreeMap（红黑树）做并发版本**：红黑树旋转涉及多节点改指针，加锁复杂；跳表层层独立，CAS 加局部锁更易实现。

## 八、应用

- **Redis Zset**：score 排序的有序集合，跳表 + 哈希表（哈希表存 member→score，跳表存按 score 排序）。
- **LevelDB / RocksDB MemTable**：跳表存内存中的有序 KV。
- **Java `ConcurrentSkipListMap/Set`**：并发有序容器。
- **Lucene 倒排链表**：部分场景用跳表加速 docId 跳跃。

## 易错点
- 跳表当严格平衡 → 是概率平衡，最坏退化为链表。
- 以为层数固定 → 每个节点层数随机生成。
- Redis Zset 只用跳表 → 还有 hash 表配合（hash 查 member→score O(1)，跳表查 score 排序 O(log n)）。
- 以为跳表查询比红黑树快 → 渐近复杂度相同，常数和缓存局部性各有千秋。
- 跳表当无锁 → 单线程无锁，并发版（ConcurrentSkipListMap）用 CAS。

## 延伸

- 关联题：[[algorithms/trees-graphs/red-black-tree.md]]
- 关联题：[[algorithms/heap/heap-data-structure.md]]
- 关联题：[[databases/redis/redis-data-structures.md]]
- 关联题：[[concurrency/concurrenthashmap-principle.md]]
