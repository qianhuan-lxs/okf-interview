---
type: question
id: languages/java/hashmap-vs-concurrenthashmap
title: HashMap vs ConcurrentHashMap
category: languages
subcategory: java
difficulty: medium
tags: [hashmap, concurrenthashmap, juc, java]
languages: []
role: [ai-app, sde, backend]
companies: [有赞]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# HashMap vs ConcurrentHashMap

## 问题描述
HashMap 和 ConcurrentHashMap 有什么区别？resize 为什么危险？

## 解答

| 维度 | HashMap | ConcurrentHashMap |
| --- | --- | --- |
| 线程安全 | 否 | 是 |
| null key/value | 允许 1 null key / 多 null value | 都不允许（NPE） |
| 1.7 实现 | 数组+链表，头插法 | Segment 分段锁（16 段） |
| 1.8 实现 | 数组+链表+红黑树，尾插法 | 数组+链表+红黑树，CAS + synchronized 锁桶 |

### ConcurrentHashMap 1.8 细节
- `put`：空桶 CAS 插入；非空桶 `synchronized` 锁该桶头节点插入。
- 锁粒度从 Segment（段）降到桶节点，并发度大幅提升。
- `size` 用 `LongAdder` 思路（baseCount + CounterCell 数组）减少竞争。

### resize 为什么危险
- 1.7 HashMap 扩容用**头插法**，多线程并发扩容会形成**链表环**，后续 `get` 死循环 100% CPU（经典面试题）。
- 1.8 改尾插法，环问题消除，但 HashMap 仍**非线程安全**：并发 put 可能丢数据、size 不准、扩容期间 get 到 null。
- 任何并发场景都必须用 ConcurrentHashMap 或外置锁。

## 延伸

## 延伸

- 关联题：[[languages/java/hashmap-resize-jdk17-jdk18]]
- 关联题：[[concurrency/threadlocal-usage-pitfalls]]
