---
type: question
id: languages/java/hashmap-deep-dive
title: HashMap 全景深讲 (hash/桶定位/put/resize/树化/0.75/2幂/扰动)
category: languages
subcategory: java
difficulty: hard
tags: [hashmap, hash, resize, red-black-tree, load-factor, treeify, java, source, jdk18]
languages: [java]
role: [sde, backend]
companies: [有赞]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-07-05
---

# HashMap 全景深讲 (hash/桶定位/put/resize/树化/0.75/2幂/扰动)

## 问题描述

HashMap 数据结构？hash 算法为什么扰动？桶定位为什么 `(n-1) & hash`？put/resize 源码流程？树化条件？为什么 loadFactor 0.75？为什么容量必须 2 的幂？1.7 vs 1.8 区别？

## 解答

## 一、数据结构（1.8+）

```
table: Node<K,V>[]            // 桶数组，长度始终 2 的幂
Node: { hash, key, value, next }    // 链表节点
TreeNode extends Node: { parent, left, right, prev, red }   // 红黑树节点
```
- **数组 + 链表 + 红黑树**。一个桶里：≤8 节点用链表，≥8 且 `capacity ≥ 64` 转红黑树；≤6 退链表。
- 1.7 只有数组 + 链表，无树。

## 二、hash 扰动函数（高频追问）

```java
static final int hash(Object key) {
    int h;
    return (key == null) ? 0 : (h = key.hashCode()) ^ (h >>> 16);
}
```
- **hashCode 高 16 位与低 16 位异或**，让高位也参与桶定位。
- 原因：桶定位用 `(n-1) & hash`，n 通常很小（16、32…），`(n-1)` 只有低位几位是 1，**高位 bit 完全不参与运算** → 哈希冲突集中在低位。
- 扰动后高位也影响低位 → **分散冲突**。
- `null` key 的 hash 固定 0 → 永远落在桶 0。

## 三、桶定位 `(n - 1) & hash`

- 等价 `hash % n`（n 是 2 的幂时），但**位运算比取模快**。
- 这就是为什么容量必须 2 的幂——`(n-1) & hash` 才等价 mod。
- 扩容 2 倍后，`(n*2 - 1)` 比 `(n-1)` 多一位 1，原 hash 不变也能正确分配新桶。

## 四、容量、loadFactor、threshold

| 概念 | 默认 | 含义 |
| --- | --- | --- |
| `initial capacity` | 16 | 初始桶数 |
| `load factor` | 0.75 | 负载因子 |
| `threshold` | `capacity * loadFactor` = 12 | 触发扩容的 size 阈值 |
| `TREEIFY_THRESHOLD` | 8 | 链表转树阈值 |
| `UNTREEIFY_THRESHOLD` | 6 | 树退链表阈值 |
| `MIN_TREEIFY_CAPACITY` | 64 | 树化要求的最低容量 |
| `MAXIMUM_CAPACITY` | 1<<30 | 最大容量 |

- `size > threshold` 触发 `resize()`。
- 构造时传的 `initialCapacity` 不是 2 的幂也无所谓——`tableSizeFor(int cap)` 找到 ≥ cap 的最小 2 的幂（如传 17 → 32）。

## 五、tableSizeFor 找最小 2 的幂

```java
static final int tableSizeFor(int cap) {
    int n = -1 >>> Integer.numberOfLeadingZeros(cap - 1);
    return (n < 0) ? 1 : (n >= MAXIMUM_CAPACITY) ? MAXIMUM_CAPACITY : n + 1;
}
```
- 把 cap-1 的最高位以下的位全填 1，再 +1 → 得到 2 的幂。
- 例：cap=17 → cap-1=16=`10000` → 填成 `11111`=31 → +1=32。
- 保证 capacity 始终 2 的幂。

## 六、put 流程源码（核心）

```java
final V putVal(int hash, K key, V value, boolean onlyIfAbsent, boolean evict) {
    Node<K,V>[] tab; Node<K,V> p; int n, i;
    if ((tab = table) == null || (n = tab.length) == 0)
        n = (tab = resize()).length;                          // ① 首次 put 触发 resize 建表
    if ((p = tab[i = (n - 1) & hash]) == null)
        tab[i] = newNode(hash, key, value, null);             // ② 桶空 → 直接放
    else {                                                     // ③ 桶非空
        Node<K,V> e; K k;
        if (p.hash == hash &&
            ((k = p.key) == key || (key != null && key.equals(k))))
            e = p;                                             // ③a 桶头就是要找的 key
        else if (p instanceof TreeNode)
            e = ((TreeNode<K,V>)p).putTreeVal(this, tab, hash, key, value);  // ③b 红黑树插入
        else {
            for (int binCount = 0; ; ++binCount) {             // ③c 链表遍历
                if ((e = p.next) == null) {
                    p.next = newNode(hash, key, value, null);  // 尾插
                    if (binCount >= TREEIFY_THRESHOLD - 1)
                        treeifyBin(tab, hash);                 // 链表 ≥8 → 尝试树化
                    break;
                }
                if (e.hash == hash &&
                    ((k = e.key) == key || (key != null && key.equals(k))))
                    break;                                     // 找到相同 key，跳出覆盖
                p = e;
            }
        }
        if (e != null) {                                       // ④ 已存在 key → 覆盖 value
            V oldValue = e.value;
            if (!onlyIfAbsent || oldValue == null) e.value = value;
            afterNodeAccess(e);
            return oldValue;
        }
    }
    ++modCount;
    if (++size > threshold) resize();                          // ⑤ 超 threshold → 扩容
    afterNodeInsertion(evict);
    return null;
}
```

**5 步要点**：建表 → 桶空直接放 → 桶非空分桶头/树/链表 → key 存在则覆盖 → size++ 超阈值扩容。

## 七、get 流程

```java
final Node<K,V> getNode(int hash, Object key) {
    Node<K,V>[] tab; Node<K,V> first, e; int n; K k;
    if ((tab = table) != null && (n = tab.length) > 0 &&
        (first = tab[(n - 1) & hash]) != null) {
        if (first.hash == hash &&
            ((k = first.key) == key || (key != null && key.equals(k))))
            return first;                                       // 桶头即命中
        if ((e = first.next) != null) {
            if (first instanceof TreeNode)
                return ((TreeNode<K,V>)first).getTreeNode(hash, key);  // 树查找 O(log n)
            do {                                                 // 链表遍历 O(n)
                if (e.hash == hash &&
                    ((k = e.key) == key || (key != null && key.equals(k))))
                    return e;
            } while ((e = e.next) != null);
        }
    }
    return null;
}
```

## 八、resize 扩容（源码核心）

- 新容量 = 旧容量 × 2（不超过 `MAXIMUM_CAPACITY`）。
- 新 threshold = 新容量 × loadFactor。
- **rehash 优化（1.8 关键改进）**：不需要重新算每个元素的 `hash & (newCap-1)`，只看 hash 的**高位 bit**：

```java
// 拆分原桶 j 的链表到新桶 j（低位）和 j+oldCap（高位）
Node<K,V> loHead = null, loTail = null;
Node<K,V> hiHead = null, hiTail = null;
for (Node<K,V> e = oldTab[j]; e != null; ) {
    Node<K,V> next = e.next;
    if ((e.hash & oldCap) == 0) {       // 高位 bit = 0 → 留新桶 j
        if (loTail == null) loHead = e; else loTail.next = e;
        loTail = e;
    } else {                            // 高位 bit = 1 → 新桶 j + oldCap
        if (hiTail == null) hiHead = e; else hiTail.next = e;
        hiTail = e;
    }
    e = next;
}
if (loTail != null) { loTail.next = null; newTab[j] = loHead; }
if (hiTail != null) { hiTail.next = null; newTab[j + oldCap] = hiHead; }
```

**为什么 `(e.hash & oldCap) == 0` 判断正确？**
- 旧 cap 是 2 的幂，二进制只有一个 1（如 `10000`=16）。
- 扩容 2 倍后 `(newCap-1)` 比 `(oldCap-1)` 多一位 1（高位）。
- 新桶下标 = `hash & (newCap-1)`，比旧下标 = `hash & (oldCap-1)` 多看这一位。
- 这一位 = 0 → 新下标 = 旧下标（留 j）。
- 这位 = 1 → 新下标 = 旧下标 + oldCap（去 j + oldCap）。
- `e.hash & oldCap` 就是取这一位的值——**避免重新 hash 整个数组**，O(1) 决定每个元素去向。

**尾插法**：1.8 用 `loTail`/`hiTail` 维护尾部追加，**保留链表原顺序**（1.7 头插法倒序）。

## 九、树化与退树

### 树化条件（两个都要满足）
1. 链表长度 ≥ `TREEIFY_THRESHOLD`（8）。
2. **数组容量 ≥ `MIN_TREEIFY_CAPACITY`（64）**。

```java
final void treeifyBin(Node<K,V>[] tab, int hash) {
    int n, index; Node<K,V> e;
    if (tab == null || (n = tab.length) < MIN_TREEIFY_CAPACITY)
        resize();              // 容量 < 64 → 不树化，先扩容
    else if ((e = tab[index = (n - 1) & hash]) != null) {
        // 链表转 TreeNode 红黑树
    }
}
```
- 容量 < 64 时链表长 8 → **先扩容**（让桶变多分散冲突），而不是树化。
- 容量 ≥ 64 后才真正转红黑树。

### 退树条件
- resize 或 remove 时，**树节点数 ≤ `UNTREEIFY_THRESHOLD`（6）** → 退回链表。
- 8 和 6 之间留缓冲区防"频繁树化/退树"震荡。

## 十、为什么红黑树而不是 AVL

- 链表 O(n) 查找；红黑树 O(log n)。
- 红黑树插入/删除旋转次数比 AVL 少（AVL 更严格平衡），适合写多于读的场景。
- HashMap 的树化是兜底防哈希冲突攻击（恶意 key 全冲突 → 链表变长 → 查找退化），不是常态。

## 十一、为什么 loadFactor 默认 0.75

- 太低（如 0.5）→ 频繁扩容，空间浪费。
- 太高（如 1.0）→ 桶冲突多，链表/树长，查找慢。
- **0.75 是时间与空间的折中**，JDK 注释提到桶节点数近似**泊松分布** λ≈0.5：单个桶里 ≥8 个节点的概率 ≈ 0.00000006（千万分之一），所以树化是极罕见的兜底，0.75 让常态下链表平均长度很低。
- 也可显式 `new HashMap<>(cap, 0.5)` 或 `0.9`，但 0.75 是经验最优。

## 十二、为什么容量必须 2 的幂

1. **`(n-1) & hash` 等价 `hash % n`**，位运算更快。
2. **扩容 2 倍后 `(newCap-1)` 比 `(oldCap-1)` 多一位 1**，让"高位 bit 判断" rehash 优化成立（见第八节）。
3. `tableSizeFor` 把任意 initialCapacity 向上取 2 的幂保证这点。

## 十三、1.7 vs 1.8

| 维度 | 1.7 | 1.8 |
| --- | --- | --- |
| 数据结构 | 数组 + 链表 | 数组 + 链表 + 红黑树 |
| 插入法 | **头插法**（扩容倒序） | **尾插法**（保序） |
| 扩容 rehash | 重新 `hash & (newCap-1)` | 高位 bit 判断（O(1) 决定） |
| 并发扩容 | **链表环 → get 死循环 100% CPU** | 消除环，但仍非线程安全 |
| hash 扰动 | 多次位运算扰动 | `h ^ (h >>> 16)` 一次扰动 |

## 十四、线程不安全的具体表现（1.8 仍存在）

| 问题 | 表现 |
| --- | --- |
| 并发 put 丢数据 | 两个线程同时判桶空 → 一个覆盖另一个 |
| size 不准 | `size++` 非原子 |
| 扩容期 get 到 null | resize 中 table 在切换，旧数据还没搬完 |
| fail-fast | 迭代期间结构性修改抛 `ConcurrentModificationException`（modCount 校验） |
| 1.7 死循环 | 头插法并发扩容成环 → get 死循环 100% CPU（1.8 已消除） |

并发场景一律用 `ConcurrentHashMap`（详见 [CHM 对比](languages/java/hashmap-vs-concurrenthashmap)）。

## 十五、面试高频追问速答

| 问 | 答 |
| --- | --- |
| 默认初始容量 | 16 |
| 默认 loadFactor | 0.75 |
| 链表转树阈值 | 8（且 capacity ≥ 64） |
| 树退链表阈值 | 6 |
| 容量为什么 2 的幂 | `(n-1) & hash` 等价 mod 且扩容 rehash 优化 |
| 扰动函数作用 | 高低位异或让高位也参与桶定位，分散冲突 |
| null key 放哪 | 桶 0（hash 固定 0） |
| 1.8 put 是头插还是尾插 | 尾插，保序 |
| 1.7 并发死循环原因 | 头插法扩容成链表环 |
| 为什么 0.75 | 时间空间折中 + 泊松分布下树化罕见 |
| HashMap 能存 null key/value 吗 | 能（1 个 null key、多个 null value） |
| 为什么红黑树不用 AVL | 写多于读，旋转次数少 |

## 易错点
- 以为链表 ≥8 就树化 → 还要 capacity ≥64，否则只扩容。
- 以为容量是任意值 → 必 2 的幂（tableSizeFor 保证）。
- 以为 1.8 HashMap 线程安全 → 只消除了死循环，丢数据仍在。
- 以为 `hash % n` 等价 `(n-1) & hash` 任何时候成立 → 必须 n 是 2 的幂。
- 以为扩容全 rehash → 1.8 用高位 bit 判断 O(1) 决定每个元素去向。
- 以为 0.75 是性能"最优" → 是经验折中，可调。
- null key 当 NPE → null key 允许且固定桶 0。

## 延伸

## 延伸

- 关联题：[[languages/java/hashmap-vs-concurrenthashmap]]
- 关联题：[[languages/java/hashmap-resize-jdk17-jdk18]]
- 关联题：[[concurrency/concurrenthashmap-principle]]
