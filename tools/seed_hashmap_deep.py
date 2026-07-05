#!/usr/bin/env python3
"""HashMap deep dive + rewrite two shallow docs."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from ikf_writer import q

DATE = "2026-07-05"
SRC = "_interviews/2026-05-louis-ai-java"

# =========================================================================== #
# NEW: 全景深文
# =========================================================================== #
q("languages/java/hashmap-deep-dive.md",
  "HashMap 全景深讲 (hash/桶定位/put/resize/树化/0.75/2幂/扰动)",
  "languages", "java", "hard",
  ["hashmap", "hash", "resize", "red-black-tree", "load-factor",
   "treeify", "java", "source", "jdk18"],
  ["有赞"],
  """# HashMap 全景深讲 (hash/桶定位/put/resize/树化/0.75/2幂/扰动)

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
""",
  languages=["java"], role=["sde", "backend"],
  source=SRC, status="reviewed", timestamp=DATE,
  links=["languages/java/hashmap-vs-concurrenthashmap",
         "languages/java/hashmap-resize-jdk17-jdk18",
         "concurrency/concurrenthashmap-principle"])

# =========================================================================== #
# REWRITE: HashMap vs ConcurrentHashMap
# =========================================================================== #
q("languages/java/hashmap-vs-concurrenthashmap.md",
  "HashMap vs ConcurrentHashMap (CHM 1.8 源码: CAS+synchronized 桶锁/CounterCell/forwarding)",
  "languages", "java", "hard",
  ["hashmap", "concurrenthashmap", "juc", "cas", "synchronized",
   "counter-cell", "forwarding-node", "java", "source"],
  ["有赞"],
  """# HashMap vs ConcurrentHashMap (CHM 1.8 源码: CAS+synchronized 桶锁/CounterCell/forwarding)

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
""",
  languages=["java"], role=["sde", "backend"],
  source=SRC, status="reviewed", timestamp=DATE,
  links=["languages/java/hashmap-deep-dive",
         "languages/java/hashmap-resize-jdk17-jdk18",
         "concurrency/longadder-vs-atomiclong",
         "concurrency/cas-mechanism"])

# =========================================================================== #
# REWRITE: HashMap resize 1.7 vs 1.8
# =========================================================================== #
q("languages/java/hashmap-resize-jdk17-jdk18.md",
  "HashMap resize (1.7 头插法死循环源码 / 1.8 尾插法+高位 bit rehash 优化)",
  "languages", "java", "hard",
  ["hashmap", "resize", "jdk17", "jdk18", "concurrent-modification",
   "head-insertion", "tail-insertion", "java", "source"],
  ["有赞"],
  """# HashMap resize (1.7 头插法死循环源码 / 1.8 尾插法+高位 bit rehash 优化)

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
""",
  languages=["java"], role=["sde", "backend"],
  source=SRC, status="reviewed", timestamp=DATE,
  links=["languages/java/hashmap-deep-dive",
         "languages/java/hashmap-vs-concurrenthashmap",
         "concurrency/concurrenthashmap-principle",
         "concurrency/synchronized-lock-escalation"])

print("\nDone: 1 new + 2 rewritten HashMap docs")
