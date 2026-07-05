---
type: question
id: algorithms/trees-graphs/union-find
title: 并查集 Union-Find (路径压缩/按秩合并/Kruskal/连通性)
category: algorithms
subcategory: trees-graphs
difficulty: medium
tags: [union-find, disjoint-set, kruskal, data-structure, connectivity, path-compression]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-07-05
---

# 并查集 Union-Find (路径压缩/按秩合并/Kruskal/连通性)

## 问题描述

并查集是什么？路径压缩和按秩合并怎么做？为什么均摊 O(α(n))？应用有哪些？

## 解答

## 一、并查集是什么

**管理不相交集合**的数据结构，支持：
- `find(x)`：找 x 所属集合的根（代表）。
- `union(x, y)`：合并 x 和 y 所在集合。
- `connected(x, y)`：x 和 y 是否同一集合（`find(x) == find(y)`）。

底层是**森林**：每个集合一棵树，根是代表，节点 parent 指针指向父。

```
集合 {1,2,3,4}（根 1）:    集合 {5,6}（根 5）:
       1                        5
      /|\                      /
     2 3 4                     6
```

## 二、朴素实现复杂度

- `find`/`union` 最坏 O(n)（树退化成链）。
- 加**路径压缩 + 按秩合并**后均摊 **O(α(n))**（α 是反阿克曼函数，n ≤ 10^80 时 α < 5，可视为常数）。

## 三、路径压缩（核心优化）

`find` 时把路径上所有节点直接挂到根下，让树变扁平：

```java
int find(int x) {
    if (parent[x] != x) parent[x] = find(parent[x]);   // 路径压缩
    return parent[x];
}
```
- 递归回溯时把 x 的 parent 直接指向根。
- 下次 find O(1)。

## 四、按秩合并（合并时优化）

`union` 时把**矮树挂到高树下**，避免树变深：

```java
void union(int x, int y) {
    int rx = find(x), ry = find(y);
    if (rx == ry) return;
    if (rank[rx] < rank[ry]) parent[rx] = ry;
    else if (rank[rx] > rank[ry]) parent[ry] = rx;
    else { parent[ry] = rx; rank[rx]++; }   // 等高时任一为父，秩+1
}
```

## 五、两者结合均摊 O(α(n))

- 单用路径压缩：均摊 O(log n)。
- 单用按秩合并：O(log n)。
- **两者结合**：均摊 **O(α(n))**，α 是反阿克曼函数，对任何工程规模都是常数。
- 实际写代码两个都加，最稳。

## 六、完整模板

```java
class UnionFind {
    int[] parent, rank;
    int count;                              // 集合数
    UnionFind(int n) {
        parent = new int[n]; rank = new int[n];
        for (int i = 0; i < n; i++) parent[i] = i;
        count = n;
    }
    int find(int x) {
        if (parent[x] != x) parent[x] = find(parent[x]);
        return parent[x];
    }
    boolean union(int x, int y) {
        int rx = find(x), ry = find(y);
        if (rx == ry) return false;          // 已同集合，没合并
        if (rank[rx] < rank[ry]) parent[rx] = ry;
        else if (rank[rx] > rank[ry]) parent[ry] = rx;
        else { parent[ry] = rx; rank[rx]++; }
        count--;
        return true;
    }
    boolean connected(int x, int y) { return find(x) == find(y); }
}
```

## 七、应用

### 1. Kruskal 最小生成树
- 边按权重排序，从小到大加边，若边的两端不在同一集合则加入并 union。
- 用并查集判环 O(α)。
- 总复杂度 O(E log E + E α)。

### 2. 连通分量
- 无向图连通分量数 = 初始 n 个集合 → union 后剩下的集合数。
- 例：社交网络好友圈数量、岛屿数量（LeetCode 200）。

### 3. 动态连通性
- 边加边查"两节点是否连通"——并查集是唯一 O(α) 的解。
- 例：网络连通性判断、等价关系判定。

### 4. 检测无向图环
- 加边时两端已同集合 → 这条边成环。

### 5. 域名/邮箱归属判定
- 等价类合并：同一组的元素 union 起来。

## 八、变种

- **带权并查集**：节点带"到父的权值"，路径压缩时累加。例：食物链关系、相对位置约束。
- **可撤销并查集**：用栈记录 union 操作，支持回滚（不在路径压缩下，因为路径压缩破坏可逆）。

## 易错点
- 只用路径压缩或只用按秩合并 → 性能不够最优，两个都加。
- find 用迭代不用递归 → 迭代版要手动两层压缩，递归版最简。
- `rank` 当节点数 → 是树高（近似），按秩合并按高不是按 size。
- 期望"严格 O(α)" → 是均摊，不是每次。
- 路径压缩破坏了 rank 的准确性 → 是近似 rank，不影响均摊。
- 用路径压缩后还要按 size 合并 → 也行（按 size 也是常见优化，效果接近按秩）。

## 延伸

- 关联题：[[algorithms/trees-graphs/red-black-tree.md]]
- 关联题：[[algorithms/trees-graphs/trie-prefix-tree.md]]
