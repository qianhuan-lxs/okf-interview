---
type: question
id: languages/java/hashmap-vs-concurrenthashmap
title: HashMap vs ConcurrentHashMap (CHM 1.8 源码: CAS+synchronized 桶锁/CounterCell/forwarding)
category: languages
subcategory: java
difficulty: hard
tags: [hashmap, concurrenthashmap, juc, cas, synchronized, counter-cell, forwarding-node, java, source]
languages: [java]
role: [sde, backend]
companies: [有赞]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-07-05
---

# HashMap vs ConcurrentHashMap (CHM 1.8 源码: CAS+synchronized 桶锁/CounterCell/forwarding)

## 问题描述

HashMap 和 ConcurrentHashMap 区别？CHM 1.7/1.8 实现细节？为什么不允许 null？size 怎么算的？扩容怎么并发做？迭代弱一致性是什么？

## 解答

## 一、对比总览

| 维度 | HashMap | ConcurrentHashMap |
| --- | --- | --- |
| 线程安全 | 否 | 是 |
| null key/value | 允许 1 null key / 多 null value | **都不允许**（NPE） |
| 1.7 实现 | 数组+链表，头插法 | **Segment 分段锁**（默认 16 段） |
| 1.8 实现 | 数组+链表+红黑树，尾插法 | 数组+链表+红黑树，**CAS + synchronized 锁桶头节点** |
| 失败 | fail-fast（迭代） | 弱一致性（迭代允许旧数据） |
| 迭代器 | `modCount` 校验，结构性修改抛 CME | 不抛 CME，迭代不保证看到最新 |
| size | `size` 字段精确 | `LongAdder` 思路（baseCount + CounterCell）近似 |
| 扩容 | 单线程 resize | **多线程并发扩容**（forwarding + 任务分配） |

## 二、ConcurrentHashMap 1.7：Segment 分段锁

```
ConcurrentHashMap
  └── Segment[] (extends ReentrantLock)，默认 16 段
        └── HashEntry[] (桶数组)
              └── HashEntry 链表
```
- 每个 Segment 是一个 ReentrantLock，put 时锁住对应段。
- 并发度 = Segment 数（默认 16，构造时可配）。
- **缺点**：锁粒度粗（一段多个桶共用一把锁），并发度受限；二次 hash（先定位 Segment 再定位桶）开销。

## 三、ConcurrentHashMap 1.8：CAS + synchronized 桶锁

### 数据结构
```
Node[] table                    // 桶数组
Node: { hash, key, value, next }   // val 和 next 都是 volatile
TreeNode / TreeBin              // 红黑树（TreeBin 包装 TreeNode，锁 TreeBin）
ForwardingNode                  // 扩容时的占位节点，hash = MOVED (-1)
ReservationNode                 // computeIfAbsent 占位（暂时）
```

### put 流程（源码核心 casTabAt / synchronized）
```java
final V putVal(K key, V value, boolean onlyIfAbsent) {
    if (key == null || value == null) throw new NullPointerException();  // ★ 不允 null
    int hash = spread(key.hashCode());     // ★扰动： (h ^ (h >>> 16)) & HASH_BITS，保证非负
    for (Node<K,V>[] tab = table;;) {
        Node<K,V> f; int n, i, fh;
        if (tab == null || (n = tab.length) == 0)
            tab = initTable();                                        // ① 表未建 → CAS 初始化
        else if ((f = tabAt(tab, i = (n - 1) & hash)) == null) {
            if (casTabAt(tab, i, null, new Node<>(hash, key, value))) // ② 桶空 → CAS 无锁插入
                break;
        } else if ((fh = f.hash) == MOVED)                             // ③ 桶头是 ForwardingNode → 帮忙扩容
            tab = helpTransfer(tab, f);
        else {                                                         // ④ 桶非空 → synchronized 锁桶头
            synchronized (f) {
                if (tabAt(tab, i) == f) {                              // double-check 桶头未变
                    if (fh >= 0) { /* 链表遍历插入/覆盖 */ }
                    else if (f instanceof TreeBin) { /* 红黑树插入 */ }
                }
            }
            if (binCount != 0) {
                if (binCount >= TREEIFY_THRESHOLD - 1) treeifyBin(tab, i);
                break;
            }
        }
    }
    addCount(1L, binCount);    // ★ size++ 用 CounterCell 分散竞争
    return null;
}
```

**关键点**：
- **空桶 → CAS 无锁插入**（`casTabAt` 用 `Unsafe.compareAndSwapObject`）。
- **非空桶 → `synchronized(桶头节点)`**，锁粒度从 Segment（段）降到**单个桶**，并发度 = 桶数（远高于 1.7 的 16）。
- **桶头是 ForwardingNode → 当前在扩容 → 当前线程 `helpTransfer` 帮忙扩容**（多线程协作扩容）。
- `tabAt` 用 `Unsafe.getObjectVolatile` 保证可见性（数组元素没有 volatile 修饰，靠 volatile 读）。

## 四、initTable 并发初始化

```java
private final Node<K,V>[] initTable() {
    Node<K,V>[] tab; int sc;
    while ((tab = table) == null || tab.length == 0) {
        if ((sc = sizeCtl) < 0)                       // sizeCtl < 0 表示别的线程在初始化或扩容
            Thread.yield();                            // 让出 CPU 等
        else if (U.compareAndSwapInt(this, SIZECTL, sc, -1)) {  // CAS 抢到初始化权
            try {
                if ((tab = table) == null || tab.length == 0) {
                    int n = (sc > 0) ? sc : DEFAULT_CAPACITY;
                    Node<K,V>[] nt = new Node[n];
                    table = tab = nt;
                    sc = n - (n >>> 2);                // threshold = n * 0.75
                }
            } finally { sizeCtl = sc; }
            break;
        }
    }
    return tab;
}
```
- `sizeCtl` 是核心控制变量：-1 = 初始化中、负数 -N = N-1 个线程在扩容、正数 = threshold 或下次扩容容量。
- 第一个 CAS 成功的线程建表，其他线程 `yield` 等。

## 五、size 用 LongAdder 思路（addCount）

```java
private final void addCount(long x, int check) {
    CounterCell[] as; long b, s;
    if ((as = counterCells) != null ||
        !U.compareAndSwapLong(this, BASECOUNT, b = baseCount, s = b + x)) {
        // CAS baseCount 失败 → 分散到 CounterCell
        CounterCell a; long v; int m;
        if (as == null || (m = as.length) < 1) {
            striped64Init(...);    // 初始化 CounterCell 数组
        } else if ((a = as[ThreadLocalRandom.getProbe() & m]) == null) {
            ... // 创建 CounterCell
        } else if (U.compareAndSwapLong(a, CELLVALUE, v = a.value, v + x)) {
            ... // CAS 当前线程的 CounterCell
        }
        s = sumCount();            // baseCount + 所有 CounterCell.value
    }
    if (check >= 0) {
        // 检查是否需要扩容
        while (s >= (long)(sc = sizeCtl) && sc < 0) {
            // 触发 transfer
        }
    }
}
```
- `baseCount` 是基础值，无竞争时直接 CAS。
- 有竞争时分散到 `CounterCell[]`（每线程按 probe hash 到一个 cell）——**和 `LongAdder` 一模一样的分段累加**。
- `size()` = `sumCount()` = `baseCount + Σ CounterCell.value` → **非精确瞬时值**（统计期间仍在变）。

## 六、并发扩容（transfer + ForwardingNode）

- 触发：`size > sizeCtl` 时调 `transfer`。
- **多线程协作**：把旧 table 分成多个**任务段**（每段 `stride` 个桶），每个线程用 CAS 抢一段迁移。
- 迁移中的桶在旧 table 上放 **`ForwardingNode`**（`hash = MOVED`）：`get` 时转发到新表查；`put` 时发现 Forwarding 调 `helpTransfer` 帮忙扩容。
- 迁移完一段抢下一段，全部迁完后线程退出。
- `sizeCtl` 用低位记录参与扩容的线程数，高位记录扩容戳（容量戳），协调多线程。

**ForwardingNode 的作用**：
- **读不阻塞**：扩容中 `get` 走到 Forwarding 节点 → 转发到新表查。
- **写协作**：`put` 走到 Forwarding → 当前线程帮扩容而不是阻塞。
- **标记**：旧表对应桶已迁移完。

## 七、为什么 CHM 不允许 null key/value

- **二义性问题**：`get(key) == null` 既可能是"不存在"，也可能是"存在但 value 是 null"——HashMap 用 `containsKey` 区分，但 CHM 并发场景下两个调用之间状态可能变，**无法可靠区分**。
- JSR 团队（Doug Lea）明确表态：并发场景下 null value 引入歧义，不如直接禁。

## 八、迭代弱一致性

- CHM 迭代器**不抛 `ConcurrentModificationException`**。
- 迭代器创建时遍历当时的 table，**不保证看到迭代期间的新增/删除**（弱一致性）。
- `size()` 也不是精确瞬时值。
- 这是允许并发读写的代价——换来了不阻塞读写。

## 九、HashMap 1.7/1.8 与 CHM 1.7/1.8 演进

| 维度 | HashMap 1.7 | HashMap 1.8 | CHM 1.7 | CHM 1.8 |
| --- | --- | --- | --- | --- |
| 结构 | 数组+链表 | 数组+链表+树 | Segment+HashEntry 链表 | 数组+链表+树 |
| 插入 | 头插 | 尾插 | 段内 | 桶内 |
| 锁 | 无 | 无 | Segment（ReentrantLock） | 桶头（synchronized）+ CAS |
| 并发度 | 不安全 | 不安全 | 16（段数） | 桶数（远高于 16） |
| 扩容 | 单线程 | 单线程 | 段内单线程 | **多线程协作** |

## 十、HashMap resize 为什么危险（详见 [resize 专篇](languages/java/hashmap-resize-jdk17-jdk18)）
- 1.7 头插法 + 并发扩容 → **链表环 → get 死循环 100% CPU**（经典面试题）。
- 1.8 尾插法消除环，但 HashMap 仍非线程安全：丢数据、size 不准、扩容期 get null。
- 任何并发场景都必须用 CHM 或外置锁。

## 易错点
- 以为 CHM 完全无锁 → 桶空 CAS 无锁，桶非空 synchronized 锁桶头。
- 以为 CHM `size()` 精确 → 是 baseCount + CounterCell 近似值。
- 以为 CHM 允许 null → 不允许（key 和 value 都不能 null）。
- 以为 CHM 1.8 锁 Segment → 锁的是桶头节点，并发度更高。
- 以为 CHM 迭代会 CME → 不会，弱一致性允许旧数据。
- 以为 ForwardingNode 是数据 → 是扩容占位符，转发用。
- 以为扩容单线程做 → CHM 1.8 多线程协作（helpTransfer）。

## 延伸

## 延伸

- 关联题：[[languages/java/hashmap-deep-dive]]
- 关联题：[[languages/java/hashmap-resize-jdk17-jdk18]]
- 关联题：[[concurrency/longadder-vs-atomiclong]]
- 关联题：[[concurrency/cas-mechanism]]
