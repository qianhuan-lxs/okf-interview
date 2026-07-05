---
type: question
id: languages/java/hashmap-resize-jdk17-jdk18
title: HashMap resize (1.7 头插法死循环源码 / 1.8 尾插法+高位 bit rehash 优化)
category: languages
subcategory: java
difficulty: hard
tags: [hashmap, resize, jdk17, jdk18, concurrent-modification, head-insertion, tail-insertion, java, source]
languages: [java]
role: [sde, backend]
companies: [有赞]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-07-05
---

# HashMap resize (1.7 头插法死循环源码 / 1.8 尾插法+高位 bit rehash 优化)

## 问题描述

1.7 HashMap 扩容为什么并发死循环？1.8 尾插法怎么解决的？高位 bit 判断 rehash 怎么工作？尾插法后 HashMap 就线程安全了吗？

## 解答

## 一、1.7 头插法 + transfer 源码

```java
void transfer(Entry[] newTable, boolean rehash) {
    for (Entry<K,V> e : table) {
        while (null != e) {
            Entry<K,V> next = e.next;          // ① 记下 next
            int i = indexFor(e.hash, newCapacity);
            e.next = newTable[i];              // ② 头插：新桶头指向 e.next
            newTable[i] = e;                    // ③ e 成为新桶头
            e = next;                           // ④ 继续下一个
        }
    }
}
```

**头插法效果**：链表 `A → B → null` 迁移到新桶后变成 `B → A → null`（顺序倒置）。

## 二、1.7 并发扩容 → 链表环 → 死循环

### 触发条件
两个线程 T1、T2 同时触发 resize，各自建 `newTable`，并发执行 `transfer`。

### 形成环的过程（简化）
1. T1 执行到 `e = A, next = B`，**还没改 A.next**，被挂起。
2. T2 完整跑完 transfer：旧桶 `A → B → null` 在 T2 的新表里因头插法变成 `B → A → B → A ...`？不，T2 的新表是 `B → A → null`（B 头插后 A 头插，B.next = A，A.next = null）。
3. **关键**：T1 持有的 `e = A, next = B` 是旧引用，但 T2 已经把 `A.next` 改成了 `B`（头插时 `A.next = newTable[i]`，而当时 newTable[i] 是 B）。所以 T1 看到的 A.next 现在指向 B（在 T2 的新表里 B.next = A）。
4. T1 恢复：
   - `e = A, next = B` → 头插 A 进 T1 的新表 → `A.next = null`（T1 newTable[i] 初始 null）→ T1 newTable[i] = A。
   - `e = B` → `next = B.next` —— **B.next 在 T2 改后指向 A** → T1 的 next = A。
   - 头插 B：`B.next = newTable[i] = A` → T1 newTable[i] = B。
   - `e = A`（next 是 A） → `next = A.next` —— **A.next 在上一步被 T1 改成了 B** → T1 next = B。
   - 头插 A：`A.next = newTable[i] = B` → 形成 **A.next = B, B.next = A → 环**！
5. 之后任何线程 `get(key)` 命中这个桶 → 沿链表遍历陷入 `A → B → A → B → ...` **死循环 100% CPU**。

### 根因
- **头插法 + 共享旧链表 + 无同步**：T2 修改了 `A.next`，T1 持有旧的 `next` 局部变量但读到的 `e.next` 是 T2 改后的值，状态错乱形成环。
- 1.7 HashMap 完全非线程安全，扩容不是重入保护的操作。

## 三、1.8 改造：尾插法 + 高位 bit rehash

### 尾插法（保序）
```java
// resize 拆桶时
Node<K,V> loHead = null, loTail = null;
for (Node<K,V> e = oldTab[j]; e != null; ) {
    Node<K,V> next = e.next;
    if ((e.hash & oldCap) == 0) {
        if (loTail == null) loHead = e; else loTail.next = e;  // 尾部追加
        loTail = e;
    } else { /* 同上 hiHead/hiTail */ }
    e = next;
}
if (loTail != null) { loTail.next = null; newTab[j] = loHead; }
if (hiTail != null) { hiTail.next = null; newTab[j + oldCap] = hiHead; }
```

**为什么尾插法消除环？**
- 头插法会"反向读取 next"导致旧引用和新引用交错形成环。
- 尾插法**只追加不反向**，链表顺序保持原样，旧 next 关系不被颠覆 → 单线程下不会形成环。
- **但注意**：尾插法只是**消除了链表环**这个具体症状，**没有加任何同步**，并发写仍然不安全。

### 高位 bit 判断 rehash（1.8 优化）
- 旧 cap = 16 = `10000`，旧桶下标 = `hash & 1111`（低 4 位）。
- 新 cap = 32 = `100000`，新桶下标 = `hash & 11111`（低 5 位）。
- 多看的第 5 位 = `hash & 10000` = `hash & oldCap`。
- 该位 = 0 → 新下标 = 旧下标（留 j）。
- 该位 = 1 → 新下标 = 旧下标 + oldCap（去 j + 16）。
- **不需要重新算 `hash & (newCap-1)`**，O(1) 判断每个元素去向 → 扩容性能优于 1.7 全 rehash。

## 四、1.8 尾插法仍非线程安全（关键澄清）

很多人误以为 1.8 HashMap 线程安全了——**错**。1.8 只解决了"链表环死循环"这一具体问题，并发写仍会出：

| 并发问题 | 表现 |
| --- | --- |
| **丢数据** | 两线程同时判 `tab[i] == null` → 都 CAS/直接赋值 → 一个覆盖另一个 |
| **size 不准** | `size++` 非原子 |
| **扩容期 get null** | resize 中 table 在切换，旧数据未搬完 |
| **modCount 不一致** | 迭代期间结构性修改抛 `ConcurrentModificationException`（fail-fast） |
| **覆盖丢更新** | 两线程同时覆盖同一 key，后写胜出，先写丢失 |

**1.8 死循环虽消除，但数据丢失/不一致问题一个没少**。并发场景必须用 `ConcurrentHashMap`。

## 五、ConcurrentHashMap 的并发扩容（对比）

CHM 1.8 用 **多线程协作扩容** 避免 HashMap 的问题：
- `sizeCtl` 协调多线程，每个线程用 CAS 抢一段桶迁移（`stride` 个桶一段）。
- 迁移中的桶在旧表放 `ForwardingNode`（`hash = MOVED`）：
  - `get` 转发到新表查（不阻塞读）。
  - `put` 发现 Forwarding 调 `helpTransfer` 帮忙扩容（不阻塞写）。
- 全部迁移完才换 `table` 引用。
- 详见 [CHM 对比](languages/java/hashmap-vs-concurrenthashmap)。

## 六、为什么 HashMap 不直接同步

- 设计目标是**单线程高性能**，加同步会严重拖慢（CHM 比同 size HashMap 慢一些）。
- 并发需求用 `ConcurrentHashMap`（Doug Lea 精心设计的无锁/细粒度锁版本）。
- JDK 不打算给 HashMap 加同步——破坏单线程性能不划算。

## 七、面试速答

| 问 | 答 |
| --- | --- |
| 1.7 死循环根因 | 头插法扩容，并发下 `A.next` 被另一线程改后，本线程基于旧 `next` 局部变量继续插，形成 A↔B 环 |
| 1.8 怎么解决 | 尾插法保序，不反向读 next，单线程下不会成环 |
| 1.8 HashMap 线程安全了吗 | **没有**，只消除了环，丢数据/size 不准/get null 都还在 |
| 高位 bit rehash 原理 | `e.hash & oldCap == 0` 留原位，==1 去原位+oldCap |
| 并发用什么 | `ConcurrentHashMap` |
| CHM 扩容怎么并发 | ForwardingNode 转发 + helpTransfer 多线程协作 |

## 易错点
- 以为 1.8 HashMap 线程安全 → 只消除了死循环，丢数据问题仍在。
- 以为头插法本身错 → 单线程下头插法没问题，错的是"并发 + 头插 + 共享旧链表"。
- 以为 1.8 全 rehash → 高位 bit 判断 O(1) 决定去向。
- 以为尾插法加了锁 → 没加任何同步。
- 以为死循环是"扩容期间死循环" → 是扩容**完成后** `get` 走到环桶才死循环。

## 延伸

## 延伸

- 关联题：[[languages/java/hashmap-deep-dive]]
- 关联题：[[languages/java/hashmap-vs-concurrenthashmap]]
- 关联题：[[concurrency/concurrenthashmap-principle]]
- 关联题：[[concurrency/synchronized-lock-escalation]]
