---
type: question
id: algorithms/trees-graphs/trie-prefix-tree
title: 字典树 Trie (前缀匹配/复杂度/应用: 补全/敏感词/IP 路由)
category: algorithms
subcategory: trees-graphs
difficulty: medium
tags: [trie, prefix-tree, data-structure, autocomplete, word-filter, ip-routing]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-07-05
---

# 字典树 Trie (前缀匹配/复杂度/应用: 补全/敏感词/IP 路由)

## 问题描述

字典树是什么？为什么前缀匹配 O(L)？有哪些应用？空间复杂度怎么优化？

## 解答

## 一、Trie 是什么

**多叉树**，每条边代表一个字符，从根到某节点的路径拼成一个字符串。
- 共享前缀的字符串共享树路径。
- 适合**前缀匹配** / **批量字符串查找**。

```
存 "cat", "car", "dog", "door":

         root
        /    \
       c      d
      / \    / \
     a   a?  o   o?
    / \      |    |
   t   r     g    o
                / \
               r   o
                  / \
                 r   ?
```

## 二、复杂度

设 n = 字符串个数，L = 字符串平均长度，Σ = 字符集大小。

| 操作 | Trie | 哈希表 | BST |
| --- | --- | --- | --- |
| 查找一个字符串 | **O(L)** | O(L) 平均 | O(L log n) |
| 插入 | O(L) | O(L) 平均 | O(L log n) |
| **前缀匹配** | **O(L + matches)** | 不支持 | 不支持 |
| 空间 | **O(n×L)**（最坏） | O(n×L) | O(n×L) |

- **Trie 查找与字符串数量无关**——只跟字符串长度有关，n 很大时优势明显。
- 前缀匹配是 Trie 的杀手锏——哈希表/BST 做不到。

## 三、节点结构

```java
class TrieNode {
    TrieNode[] children = new TrieNode[26];   // 假设小写字母
    boolean isEnd;                              // 是否一个完整单词的结尾
}
```
- 通用版本用 `HashMap<Character, TrieNode>` 支持任意字符集。
- `isEnd` 区分"前缀"和"完整词"：`"cat"` 在 `"category"` 中只是路径，不是单词。

## 四、基本操作

### 插入
```java
void insert(String word) {
    TrieNode cur = root;
    for (char c : word.toCharArray()) {
        int i = c - 'a';
        if (cur.children[i] == null) cur.children[i] = new TrieNode();
        cur = cur.children[i];
    }
    cur.isEnd = true;
}
```

### 查找完整词
```java
boolean search(String word) {
    TrieNode cur = root;
    for (char c : word.toCharArray()) {
        cur = cur.children[c - 'a'];
        if (cur == null) return false;
    }
    return cur.isEnd;       // 必须是单词结尾
}
```

### 前缀判断
```java
boolean startsWith(String prefix) {
    TrieNode cur = root;
    for (char c : prefix.toCharArray()) {
        cur = cur.children[c - 'a'];
        if (cur == null) return false;
    }
    return true;            // 不需要 isEnd
}
```

## 五、空间优化

### 1. 压缩 Trie（Radix Tree / Patricia Trie）
- 单个子节点直接合并成字符串路径，减少节点数。
- 适合前缀长的场景（如 IP 路由）。
- Linux 内核 IP 路由表用压缩 Trie。

### 2. Ternary Search Trie (TST)
- 每节点三叉（<, =, >），空间 O(n×L) 但常数小，不需大数组。
- 适合字符集大但稀疏的场景。

### 3. 用 HashMap 代替数组
- 字符集大或稀疏（如中文、Unicode）时，`HashMap<Character, TrieNode>` 比 26/65536 数组节省空间。

## 六、应用

### 1. 搜索框自动补全
- 用户输入前缀 → 走 Trie 到该节点 → DFS/BFS 输出所有 `isEnd` 子树 → 按热度排序。

### 2. 敏感词过滤
- 预先把敏感词建 Trie → 文本扫描时对每个起点在 Trie 上走 → 命中即过滤。
- AC 自动机（Aho-Corasick）：Trie + 失败指针，一次扫描匹配多模式串，O(n+m)。

### 3. IP 路由（最长前缀匹配）
- 路由表 CIDR 前缀建 Trie → 数据包目的 IP 在 Trie 上走，找最长匹配前缀。
- Linux 内核用压缩 Trie（FIB）。

### 4. 拼写检查 / 模糊搜索
- 编辑距离 + Trie 剪枝：搜索单词的近似拼写。

### 5. 单词游戏
- Boggle / Scrabble 找所有有效单词：DFS 棋盘 + Trie 实时剪枝。

### 6. DNS 解析
- 域名按层级缓存（如 `com.` → `example.com.`），天然 Trie 结构。

## 七、Trie vs 哈希表 vs BST

| 场景 | 选 |
| --- | --- |
| 仅精确查找 | 哈希表（O(L) 平均，简单） |
| 范围查找 / 排序 | BST / 红黑树 |
| **前缀匹配 / 自动补全** | **Trie** |
| 多模式串匹配 | AC 自动机（Trie 扩展） |
| 字符串集 + 内存敏感 | 压缩 Trie / TST |

## 易错点
- Trie 查找当 O(1) → 是 O(L)，L = 字符串长度。
- 忘 `isEnd` 标记 → "ca" 在 "cat" 路径上但不是单词，会误判命中。
- 字符集数组开太大 → 中文字符集 65536 数组浪费，用 HashMap。
- 以为 Trie 一定省空间 → 最坏（无共享前缀）和哈希表一样，甚至更多。
- 前缀匹配忘记限深度 → 子树巨大时全 DFS 慢，要加排序/限流。

## 延伸

- 关联题：[[algorithms/trees-graphs/red-black-tree.md]]
- 关联题：[[algorithms/linked-lists/skip-list.md]]
- 关联题：[[algorithms/heap/heap-data-structure.md]]
