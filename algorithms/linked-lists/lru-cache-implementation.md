---
type: question
id: algorithms/linked-lists/lru-cache-implementation
title: LRU 缓存 (HashMap+双向链表/Java LinkedHashMap/LFU 对比)
category: algorithms
subcategory: linked-lists
difficulty: medium
tags: [lru, lfu, cache, linked-hash-map, data-structure, java, redis]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-07-05
---

# LRU 缓存 (HashMap+双向链表/Java LinkedHashMap/LFU 对比)

## 问题描述

LRU 怎么实现？为什么 HashMap + 双向链表？Java LinkedHashMap 怎么直接做 LRU？LFU 和 LRU 区别？

## 解答

## 一、LRU（Least Recently Used）

淘汰**最久没访问**的元素。两个核心操作 O(1)：
- `get(key)`：返回 value，并把该节点移到"最近用"端。
- `put(key, value)`：插入/更新，并把节点移到"最近用"端；超容量则淘汰"最久未用"端。

## 二、数据结构：HashMap + 双向链表

- **HashMap**：key → 链表节点，O(1) 找节点。
- **双向链表**：节点带 prev/next，O(1) 移动到头部 / 删除尾部。
- 头 = 最近用，尾 = 最久未用（或反之，约定即可）。

```
HashMap: key -> Node(value, prev, next)

head ⇄ [A] ⇄ [B] ⇄ [C] ⇄ tail
       最近用         最久未用 → 淘汰这里
```

## 三、为什么必须双向链表

- 单向链表删节点要知道前驱，单向找前驱要 O(n)。
- 双向链表节点自带 prev，O(1) 摘除（自己 prev.next = next, next.prev = prev）。
- 移到头：摘除 + 头插 O(1)。

## 四、Java 实现（手写）

```java
class LRUCache<K, V> {
    static class Node<K, V> { K k; V v; Node<K,V> prev, next; }
    private final int capacity;
    private final Map<K, Node<K,V>> map = new HashMap<>();
    private final Node<K,V> head = new Node<>(), tail = new Node<>();

    public LRUCache(int capacity) {
        this.capacity = capacity;
        head.next = tail; tail.prev = head;
    }

    public V get(K key) {
        Node<K,V> n = map.get(key);
        if (n == null) return null;
        moveToHead(n);                  // 访问过移到头
        return n.v;
    }

    public void put(K key, V value) {
        Node<K,V> n = map.get(key);
        if (n != null) { n.v = value; moveToHead(n); return; }
        n = new Node<>(); n.k = key; n.v = value;
        map.put(key, n); addToHead(n);
        if (map.size() > capacity) {
            Node<K,V> tailNode = tail.prev;
            removeNode(tailNode); map.remove(tailNode.k);
        }
    }

    private void addToHead(Node<K,V> n) {
        n.next = head.next; n.prev = head;
        head.next.prev = n; head.next = n;
    }
    private void removeNode(Node<K,V> n) {
        n.prev.next = n.next; n.next.prev = n.prev;
    }
    private void moveToHead(Node<K,V> n) { removeNode(n); addToHead(n); }
}
```

## 五、Java `LinkedHashMap` 直接做 LRU

`LinkedHashMap` 内部就是 HashMap + 双向链表，开 `accessOrder=true` 就按访问顺序排：

```java
LRUMap<K, V> extends LinkedHashMap<K, V> {
    private final int capacity;
    LRUMap(int capacity) {
        super(capacity, 0.75f, true);   // ★ true = accessOrder
        this.capacity = capacity;
    }
    @Override
    protected boolean removeEldestEntry(Map.Entry<K,V> eldest) {
        return size() > capacity;       // ★ 超 capacity 自动淘汰最老
    }
}
```

- `accessOrder=false`（默认）= 按插入顺序。
- `accessOrder=true` = 按访问顺序，`get` 也会把节点移到尾部（"最近用"端）。
- 重写 `removeEldestEntry` 控制 LRU 淘汰。

## 六、LFU（Least Frequently Used）

淘汰**访问次数最少**的元素。
- 实现：HashMap + 多个按频次分桶的双向链表（频次 → 链表）+ minFreq 记录最低频次。
- 同频次内按 LRU 排（最近用的在头）。
- `get/put` O(1)（频次变化时节点跨桶移动）。

## 七、LRU vs LFU vs FIFO

| 策略 | 淘汰依据 | 优点 | 缺点 |
| --- | --- | --- | --- |
| **FIFO** | 先入先出 | 简单 | 不考虑访问模式 |
| **LRU** | 最久未访问 | 贴近时间局部性 | 偶发扫描污染（一次遍历把热数据全踢） |
| **LFU** | 访问次数最少 | 抗扫描污染 | 老热点难下沉（历史频次高不再访问仍占位） |
| **W-TinyLFU** | 频次 + 时间衰减 | 综合 LRU/LFU 优点 | Caffeine 用，复杂 |

## 八、Redis 的近似 LRU

- Redis 全量 LRU 要维护链表，内存贵 → 用**近似 LRU**：
  - 随机采样 N 个 key（`maxmemory-samples`，默认 5），淘汰其中最久未访问的。
  - N 越大越接近真实 LRU，但 CPU 开销大。
- Redis 4.0+ 引入 **LFU** 模式（`maxmemory-policy allkeys-lfu`）。
- 详见 [Redis 数据结构](databases/redis/redis-data-structures.md)。

## 九、应用

- **CPU 缓存 / TLB**：硬件级 LRU。
- **操作系统页面置换**：Linux 用近似 LRU（双链表 active/inactive）。
- **Redis**：近似 LRU/LFU。
- **Guava Cache / Caffeine**：W-TinyLFU。
- **MyBatis 二级缓存**：默认 LRU。
- **浏览器缓存**：LRU 淘汰旧资源。

## 易错点
- LRU 用单向链表 → 删节点找前驱 O(n)，必须双向（占位，下方统一处理）。
- `LinkedHashMap` 忘 `accessOrder=true` → 按"插入顺序"不是"访问顺序"，不是 LRU。
- 忘重写 `removeEldestEntry` → 不会自动淘汰，会一直涨。
- LRU 当万能 → 偶发扫描污染严重场景用 LFU 或 W-TinyLFU。
- 以为 Redis 是严格 LRU → 是近似 LRU（随机采样）。
- 手写 LRU 忘 dummy head/tail → 边界条件多，dummy 简化。

## 延伸

- 关联题：[[algorithms/linked-lists/skip-list.md]]
- 关联题：[[databases/redis/redis-data-structures.md]]
- 关联题：[[concurrency/concurrenthashmap-principle.md]]
