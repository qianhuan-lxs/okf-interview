---
type: question
id: languages/java/hashmap-resize-jdk17-jdk18
title: HashMap resize (1.7 头插法死循环 / 1.8 尾插法)
category: languages
subcategory: java
difficulty: hard
tags: [hashmap, resize, jdk17, jdk18, concurrent-modification]
languages: []
role: [ai-app, sde, backend]
companies: [有赞]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# HashMap resize (1.7 头插法死循环 / 1.8 尾插法)

## 问题描述
1.7 HashMap 扩容有什么危险？1.8 是什么方式扩容？尾插法最终会导致什么问题？

## 解答

### 1.7 头插法 + 并发扩容 → 链表环
1.7 transfer 时：遍历旧桶，每个节点用头插法插入新桶。
```
newTable[e.next] 头插: e.next = newTable[i]; newTable[i] = e;
```
两个线程同时扩容，互相读取对方部分迁移的状态，可能让 A→B→A 形成环。
之后 `get(key)` 走链表死循环，CPU 100%。

### 1.8 改造
- 数组 + 链表 + 红黑树（链表长度 ≥8 且容量 ≥64 转树；≤6 退链表）。
- 扩容用**尾插法**，保留原顺序，**消除链表环**。
- 扩容时新容量 = 旧 ×2，rehash 时元素要么留原位要么 "原位 + oldCap"（高位 bit 判断），1.8 优化了这个判断。

### 1.8 尾插法还遗留什么问题
- **仍是非线程安全**：并发 put 可能丢数据、size 不准、扩容瞬间 get 到 null。
- **ConcurrentModificationException**：迭代期间结构性修改会 fail-fast。
- 解法：并发场景一律 ConcurrentHashMap。

## 易错点
- 以为 1.8 后 HashMap 就线程安全 —— 仅消除了死循环，丢数据问题仍在。

## 延伸

## 延伸

- 关联题：[[languages/java/hashmap-vs-concurrenthashmap]]
