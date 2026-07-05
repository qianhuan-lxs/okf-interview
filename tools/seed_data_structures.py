#!/usr/bin/env python3
"""Classic data structures: heap, skip-list, red-black-tree, b-tree/b+,
trie, lru-cache, union-find, bloom-filter+bitmap."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from ikf_writer import q

DATE = "2026-07-05"

# =========================================================================== #
# 1. 堆
# =========================================================================== #
q("algorithms/heap/heap-data-structure.md",
  "二叉堆 (堆化/堆排序/Top-K/Java PriorityQueue)",
  "algorithms", "heap", "medium",
  ["heap", "binary-heap", "priority-queue", "top-k", "heap-sort", "java",
   "data-structure"],
  [],
  """# 二叉堆 (堆化/堆排序/Top-K/Java PriorityQueue)

## 问题描述

堆是什么？堆化怎么做？堆排序复杂度？Top-K 经典解法？Java PriorityQueue 怎么实现？

## 解答

## 一、堆是什么

**完全二叉树** + 父子大小关系：
- **最大堆**：每个节点 ≥ 子节点。根 = 最大值。
- **最小堆**：每个节点 ≤ 子节点。根 = 最小值。
- **不要求左右子节点之间有序**——只父>子（或父<子）。

## 二、数组表示（关键）

完全二叉树用数组存，下标关系（0-indexed）：
- 节点 `i` 的父 = `(i-1)/2`。
- 左子 = `2i+1`，右子 = `2i+2`。
- 不需要指针，节省内存 + 缓存友好。

```
数组: [9, 7, 8, 4, 5, 6, 3, 1, 2]
树:
            9(0)
          /     \\
        7(1)     8(2)
       /  \\    /  \\
      4(3) 5(4) 6(5) 3(6)
     / \\
    1(7) 2(8)
```

## 三、堆化（Heapify）—— 两个方向

### `siftUp`（向上调整，插入用）
插入新元素到数组末尾，与父比较，违反堆性质就交换，递归向上。
```
insert(x): arr[n++] = x; siftUp(n-1);
siftUp(i): while i>0 && arr[i] > arr[parent(i)]: swap(arr[i], arr[parent]); i = parent;
```
- 复杂度 O(log n)。

### `siftDown`（向下调整，删堆顶/建堆用）
取出堆顶后，把末尾元素放堆顶，与较大子比较，违反就交换，递归向下。
```
extractMax(): root = arr[0]; arr[0] = arr[--n]; siftDown(0); return root;
siftDown(i):
  while hasLeft(i):
    max = largerChild(i)
    if arr[i] >= arr[max]: break
    swap(arr[i], arr[max]); i = max;
```
- 复杂度 O(log n)。

## 四、建堆 O(n)（不是 O(n log n)！）

从**最后一个非叶节点**（下标 `n/2-1`）到根，依次 `siftDown`。
- 直觉：叶子节点本就满足堆，从底层往上调整。
- 严格证明：`Σ h(i)` 求和后总工作量为 O(n)（不是每个节点都 O(log n)）。
- Java `PriorityQueue.heapify()` 用这个。

## 五、堆排序

1. 建最大堆 O(n)。
2. 交换堆顶（最大）与末尾，缩小堆 size 1，`siftDown(0)` 调整。
3. 重复 n-1 次。
- 时间：O(n) + n × O(log n) = **O(n log n)**。
- 空间：O(1) 原地排序。
- **不稳定**（交换可能打乱相等元素的相对顺序）。
- 比快排慢（常数大、缓存不友好），但最坏 O(n log n) 优于快排 O(n²)。

## 六、Top-K 问题（堆的杀手锏）

求前 K 大的元素（流式数据/海量数据）：
- **最小堆 size K**：堆顶是当前 K 中的最小。
  - 来一个新元素 x：若 x > 堆顶 → 替换堆顶 + siftDown；否则丢。
  - 最后堆里就是 Top-K。
- 时间：n × O(log K) = **O(n log K)**。
- 空间：O(K)。
- 优势：**流式可处理**（不用全部加载），内存可控。

对比：
| 方法 | 时间 | 空间 | 流式支持 |
| --- | --- | --- | --- |
| 全排序取前 K | O(n log n) | O(n) | 否 |
| 快排 partition | O(n) 平均 | O(n) | 否 |
| **最小堆 size K** | O(n log K) | O(K) | **是** |

## 七、Java `PriorityQueue`

- 默认**最小堆**（自然序）；要最大堆传 `Collections.reverseOrder()` 或自定义 `Comparator`。
- 内部用数组 + siftUp/siftDown。
- `add/offer` → siftUp，O(log n)。
- `poll`（取堆顶）→ siftDown，O(log n)。
- `peek` → O(1)。
- **非线程安全**；并发用 `PriorityBlockingQueue`。
- 不允许 null。

### 经典用法
```java
// Top-K 大
PriorityQueue<Integer> minHeap = new PriorityQueue<>(k);
for (int x : nums) {
    if (minHeap.size() < k) minHeap.offer(x);
    else if (x > minHeap.peek()) { minHeap.poll(); minHeap.offer(x); }
}
```

## 八、变种

- **d 叉堆**（d-ary heap）：每个节点 d 个子，堆更浅，siftDown 比较多但缓存更友好。Go runtime 用 4 叉堆做定时器。
- **斐波那契堆**： Decrease-key O(1) 均摊，理论优，实际常数大少用。
- **索引堆**：堆元素带索引，能 O(log n) 修改任意位置元素，Dijkstra 优化用。

## 九、应用

| 场景 | 用什么 |
| --- | --- |
| Top-K | 最小堆 size K |
| 任务调度（优先级） | PriorityQueue |
| Dijkstra 最短路 | 最小堆取当前最近点 |
| 合并 K 个有序链表 | 最小堆 |
| 求中位数 | 大顶堆 + 小顶堆（左大顶装前半，右小顶装后半） |
| Java Timer / ScheduledExecutor | 堆定时任务 |
| Go runtime timer | 4 叉堆 |

## 易错点
- 建堆当 O(n log n) → 是 O(n)（siftDown 自底向上）。
- Top-K 用最大堆 → 应该用 size K 的**最小堆**（堆顶是 K 中最小，新的比它大才替换）。
- 堆当完全有序 → 只保证父子关系，中序遍历不是排序的。
- 堆排序当稳定 → 不稳定。
- `PriorityQueue` 当线程安全 → 否，用 `PriorityBlockingQueue`。
- 取中位数用单堆 → 要两个堆平衡。

""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["algorithms/sorting-searching/sorting-algorithms-comparison.md",
         "algorithms/trees-graphs/red-black-tree.md",
         "concurrency/thread-pool-principles"])

# =========================================================================== #
# 2. 跳表
# =========================================================================== #
q("algorithms/linked-lists/skip-list.md",
  "跳表 (Skip List) (结构/概率平衡/Redis Zset/为什么不用红黑树)",
  "algorithms", "linked-lists", "medium",
  ["skip-list", "redis", "zset", "data-structure", "probabilistic",
   "ordered-set"],
  [],
  """# 跳表 (Skip List) (结构/概率平衡/Redis Zset/为什么不用红黑树)

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

""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["algorithms/trees-graphs/red-black-tree.md",
         "algorithms/heap/heap-data-structure.md",
         "databases/redis/redis-data-structures.md",
         "concurrency/concurrenthashmap-principle.md"])

# =========================================================================== #
# 3. 红黑树
# =========================================================================== #
q("algorithms/trees-graphs/red-black-tree.md",
  "红黑树 (5 性质/旋转着色/为什么不用 AVL/HashMap 树化)",
  "algorithms", "trees-graphs", "hard",
  ["red-black-tree", "balanced-tree", "rotation", "tree-map", "hashmap",
   "data-structure", "java"],
  [],
  """# 红黑树 (5 性质/旋转着色/为什么不用 AVL/HashMap 树化)

## 问题描述

红黑树是什么？5 条性质？为什么不用 AVL？旋转和着色怎么工作？哪些地方用到？

## 解答

## 一、红黑树是什么

**自平衡二叉搜索树**，通过"节点染色 + 旋转"保证：任意节点到叶子的最长路径不超过最短路径的 2 倍 → 高度 O(log n)。

## 二、5 条性质（必背）

1. 每个节点**非红即黑**。
2. **根是黑**。
3. **每个叶子（NIL 空节点）是黑**。
4. **红节点的子节点必须黑**（不能连续两个红）。
5. **任意节点到其所有叶子节点的路径包含相同数量的黑节点**（黑高相同）。

由 4 和 5 推出：最长路径（红黑相间）≤ 2 × 最短路径（全黑）→ 树高 ≤ 2 log(n+1)。

## 三、为什么不用 AVL

| 维度 | AVL | 红黑树 |
| --- | --- | --- |
| 平衡严格度 | 严格（左右子树高度差 ≤1） | 弱平衡（最长 ≤ 2×最短） |
| 查询 | 略快（树更矮） | 略慢 |
| 插入/删除旋转 | 多（最多 2 次） | 少（插入最多 2 旋转，删除最多 3 旋转） |
| 适用 | **读多写少** | **写多读少 / 通用** |

红黑树**牺牲一点查询性能换更少的旋转**——通用场景（既有读又有写）更合适。AVL 严格平衡查询最优但写操作旋转代价高。

## 四、旋转与着色

### 左旋 / 右旋
```
    Y                X
   / \\              / \\
  X   C    →       A   Y
 / \\                  / \\
A   B                B   C
```
- 旋转不改中序遍历顺序（BST 性质保持）。
- 旋转是 O(1) 局部操作。

### 插入调整
- 新插入节点默认**红**（不影响黑高）。
- 若父是黑 → 直接结束。
- 若父是红（违反性质 4）：
  - 叔也是红 → 父和叔改黑，祖父改红，递归处理祖父。
  - 叔是黑 → 旋转 + 着色（4 种情况：LL/LR/RL/RR，类似 AVL）。
- 最多 2 次旋转 + O(log n) 次着色。

### 删除调整
- 更复杂，涉及"双重黑"节点的修复。
- 最多 3 次旋转。

## 五、复杂度

| 操作 | 时间 |
| --- | --- |
| 查询 | O(log n) |
| 插入 | O(log n) |
| 删除 | O(log n) |
| 旋转次数（插入） | ≤ 2 |
| 旋转次数（删除） | ≤ 3 |

## 六、应用（高频追问）

| 场景 | 用 |
| --- | --- |
| **Java `TreeMap` / `TreeSet`** | 红黑树 |
| **Java 8+ `HashMap` 链表树化** | 链表 ≥8 且容量 ≥64 → 红黑树 |
| **C++ `std::map` / `std::set`** | 红黑树 |
| **Linux 内核 CFS 调度器** | 红黑树管理进程（按 vruntime 排序） |
| **Linux epoll** | 红黑树管理监听 fd |
| **Nginx timer** | 红黑树 |
| **EXT3/EXT4 文件系统** | 红黑树管理目录项 |

## 七、为什么 HashMap 树化用红黑树

- 链表 O(n) → 树 O(log n)，防哈希冲突攻击（恶意 key 全冲突 → 链表超长 → 查找退化）。
- 用红黑树不用 AVL：HashMap 写多（put/remove 频繁），红黑树旋转少更适合。
- 树化是兜底（链表 ≥8 概率千万分之一，见 [HashMap 深讲](languages/java/hashmap-deep-dive)），不是常态。

## 八、TreeMap 源码要点

- `Entry<K,V>`：`key, value, left, right, parent, color`。
- `put`：BST 插入 + 调平衡（`fixAfterInsertion`）。
- `remove`：BST 删除 + `fixAfterDeletion`。
- `get`：BST 查找 O(log n)。
- 支持 `firstKey`/`lastKey`/`subMap`/`headMap`/`tailMap` 等有序操作——这是 TreeMap 比 HashMap 强的地方。
- **非线程安全**；并发用 `ConcurrentSkipListMap`（注意是跳表，不是红黑树并发版）。

## 易错点
- 红黑树当完全平衡 → 是弱平衡，最长 ≤ 2×最短。
- 以为根是红 → 根必须黑。
- 以为红节点不能有红子节点就够 → 还要黑高相同。
- 以为 AVL 总比红黑树好 → 写多场景红黑树优。
- TreeMap 当线程安全 → 否，并发用 ConcurrentSkipListMap。
- 以为 HashMap 链表 ≥8 必树化 → 还要 capacity ≥64。

""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["languages/java/hashmap-deep-dive",
         "algorithms/linked-lists/skip-list.md",
         "databases/mysql/btree-vs-binary-tree.md"])

# =========================================================================== #
# 4. B 树 vs B+ 树
# =========================================================================== #
q("algorithms/trees-graphs/b-tree-vs-bplus-tree.md",
  "B 树 vs B+ 树 (高扇出/磁盘 IO/为什么数据库用 B+ 树)",
  "algorithms", "trees-graphs", "hard",
  ["b-tree", "bplus-tree", "database-index", "disk-io", "data-structure",
   "mysql", "fanout"],
  [],
  """# B 树 vs B+ 树 (高扇出/磁盘 IO/为什么数据库用 B+ 树)

## 问题描述

B 树和 B+ 树什么区别？为什么数据库索引用 B+ 树不用 B 树或红黑树？高扇出为什么重要？

## 解答

## 一、B 树（B-Tree，不是二叉树）

**多路平衡查找树**，每个节点可以有多个子（m 叉）。
- 节点存：**键 + 值 + 子指针**。
- **数据存在所有节点**（内部节点也存数据）。
- 子节点数 m 满足：`⌈m/2⌉ ≤ 子数 ≤ m`（根除外）。
- 高度 O(log_m n)。

```
              [10 | 20 | 30]              ← 内部节点也存数据
            /      |      |      \\
       [5|8]   [12|15] [22|25] [35|40]
```

## 二、B+ 树

B 树变种：
- **内部节点只存键和子指针，不存数据**（更紧凑 → 扇出更大）。
- **所有数据在叶子节点**，叶子按顺序**用链表相连**。
- 叶子是数据的"全集"。

```
              [10 | 20 | 30]              ← 只有键
            /      |      |      \\
       [5|8|10] [12|15|20] [22|25|30] [35|40|...]  ← 叶子存数据，互相链表
           ↔         ↔         ↔          ↔
```

## 三、B 树 vs B+ 树对比

| 维度 | B 树 | B+ 树 |
| --- | --- | --- |
| 数据存储位置 | 所有节点 | **只在叶子** |
| 单节点能放多少键 | 少（要存数据） | 多（只存键） |
| 扇出 | 小 | **大** |
| 树高 | 高 | **低** |
| 单点查询 | 任何层都可能命中 | 必须到叶子 |
| **范围查询** | 中序遍历回溯 | **叶子链表顺序扫**（杀手锏） |
| 磁盘 IO 次数 | 多 | **少** |

## 四、为什么数据库用 B+ 树（核心）

### 1. 磁盘瓶颈是 IO，不是 CPU
- 磁盘一次 IO 读一个 page（如 16KB）。
- 树越矮，IO 次数越少。
- B+ 树内部节点不存数据 → 单 page 能放更多键 → 扇出更大 → 树更矮。

### 2. 实际数字
- 假设键+指针 12 字节，page 16KB。
- B 树节点要存数据（假设 1KB/条）→ 单 page 放 ~16 条 → 扇出 16。
- B+ 树内部节点只存键+指针 → 单 page 放 ~1300 条 → 扇出 1300。
- 百万数据：
  - B 树：`log_16(1e6)` ≈ 5 层 → 5 次 IO。
  - B+ 树：`log_1300(1e6)` ≈ **3 层 → 3 次 IO**（且根常驻内存 → 实际 2 次）。
- **层数差 1，IO 差一倍**——磁盘 IO 是 ms 级，差别巨大。

### 3. 范围查询
- 数据库 90%+ 查询是范围查询（`WHERE id BETWEEN` / `ORDER BY` / `JOIN`）。
- B+ 树叶子链表顺序扫，找到起点后顺着 next 指针走，O(log n + m)。
- B 树要中序遍历多次回溯父节点，IO 多。

### 4. 数据稳定
- B+ 树插入/删除只动叶子（除非分裂/合并传到内部），内部节点键变化少 → 缓存友好。

## 五、为什么不用红黑树/AVL

- 红黑树是**二叉树**，扇出 2。
- 百万数据：`log_2(1e6)` ≈ 20 层 → **20 次 IO**。
- B+ 树 3 层完胜。
- 红黑树适合**内存**（比较是 CPU 操作，二叉平衡查询最优），不适合磁盘（IO 才是瓶颈）。

详见 [B+ 树 vs 二叉树](databases/mysql/btree-vs-binary-tree)。

## 六、B+ 树在 MySQL InnoDB

- 节点大小 = page = 16KB（默认）。
- **聚簇索引**：叶子存完整行数据（数据本身按主键构成 B+ 树）。
- **二级索引**：叶子存主键值 → 回表到聚簇索引查行。
- 非叶子节点常驻 buffer pool → 实际 IO 通常 1~2 次。
- 三层 B+ 树可存 ~2000 万行（每行 1KB）。

## 七、B+ 树的分裂与合并

- 插入到叶子满 → **分裂**：把一半挪到新节点，父节点加一个键。
- 删除使节点 < 半满 → **合并**或从兄弟借。
- 分裂/合并可能传到根 → 树长高/变矮。
- 复杂度 O(log_m n)。

## 八、其他变种

- **B* 树**：节点满时先从兄弟借再分裂，空间利用率更高。
- **LSM 树**（LSM-Tree）：写优化，写内存 + 顺序写磁盘 + 后台合并。LevelDB/RocksDB/Cassandra/HBase 用。
  - 写远多于读、海量数据场景。
  - 代价：读放大（要查多层 SSTable）+ compaction IO。

## 易错点
- B 树当二叉树 → 是多路（m 叉）平衡树，"B" 不代表 Binary。
- B+ 树当 B 树 → 数据只在叶子，叶子链表相连。
- 以为 B 树范围查询快 → 不如 B+ 树（叶子链表）。
- 以为红黑树查询快就适合数据库 → 内存里快，磁盘 IO 拖死。
- 以为 B+ 树层数和 B 树一样 → B+ 扇出大得多，层数更少。
- 把 B+ 树和 LSM 混 → LSM 是写优化的不同结构。

""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["databases/mysql/btree-vs-binary-tree.md",
         "databases/mysql/mysql-btree-index.md",
         "databases/mysql/clustered-vs-secondary-index.md",
         "algorithms/trees-graphs/red-black-tree.md"])

# =========================================================================== #
# 5. 字典树
# =========================================================================== #
q("algorithms/trees-graphs/trie-prefix-tree.md",
  "字典树 Trie (前缀匹配/复杂度/应用: 补全/敏感词/IP 路由)",
  "algorithms", "trees-graphs", "medium",
  ["trie", "prefix-tree", "data-structure", "autocomplete", "word-filter",
   "ip-routing"],
  [],
  """# 字典树 Trie (前缀匹配/复杂度/应用: 补全/敏感词/IP 路由)

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
        /    \\
       c      d
      / \\    / \\
     a   a?  o   o?
    / \\      |    |
   t   r     g    o
                / \\
               r   o
                  / \\
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

""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["algorithms/trees-graphs/red-black-tree.md",
         "algorithms/linked-lists/skip-list.md",
         "algorithms/heap/heap-data-structure.md"])

# =========================================================================== #
# 6. LRU 缓存
# =========================================================================== #
q("algorithms/linked-lists/lru-cache-implementation.md",
  "LRU 缓存 (HashMap+双向链表/Java LinkedHashMap/LFU 对比)",
  "algorithms", "linked-lists", "medium",
  ["lru", "lfu", "cache", "linked-hash-map", "data-structure", "java",
   "redis"],
  [],
  """# LRU 缓存 (HashMap+双向链表/Java LinkedHashMap/LFU 对比)

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

""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["algorithms/linked-lists/skip-list.md",
         "databases/redis/redis-data-structures.md",
         "concurrency/concurrenthashmap-principle.md"])

# =========================================================================== #
# 7. 并查集
# =========================================================================== #
q("algorithms/trees-graphs/union-find.md",
  "并查集 Union-Find (路径压缩/按秩合并/Kruskal/连通性)",
  "algorithms", "trees-graphs", "medium",
  ["union-find", "disjoint-set", "kruskal", "data-structure",
   "connectivity", "path-compression"],
  [],
  """# 并查集 Union-Find (路径压缩/按秩合并/Kruskal/连通性)

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
      /|\\                      /
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

""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["algorithms/trees-graphs/red-black-tree.md",
         "algorithms/trees-graphs/trie-prefix-tree.md"])

# =========================================================================== #
# 8. 布隆过滤器 + 位图
# =========================================================================== #
q("algorithms/hashing/bloom-filter-bitmap.md",
  "布隆过滤器 + 位图 (概率判断/HyperLogLog/缓存穿透)",
  "algorithms", "hashing", "medium",
  ["bloom-filter", "bitmap", "hyperloglog", "probabilistic",
   "cache-penetration", "data-structure"],
  [],
  """# 布隆过滤器 + 位图 (概率判断/HyperLogLog/缓存穿透)

## 问题描述

布隆过滤器是什么？为什么有假阳性没假阴性？位图能做什么？HyperLogLog 怎么计数？

## 解答

## 一、位图（Bitmap）

**用每一位（bit）表示一个元素是否存在**。N 个元素 → N bit。
- 例：10 亿整数是否存在 → 10^9 bit ≈ 125 MB（远小于 HashSet 的几 GB）。
- 操作：`set(i)` → `arr[i/64] |= 1<<(i%64)`；`get(i)` → `(arr[i/64]>>(i%64))&1`。
- 适合**稠密整数集合**（如 ID 范围 0~10^9）。
- Java `BitSet`、Redis `SETBIT`/`GETBIT`。

### 应用
- 用户签到（按天 1 bit）。
- UV 去重（粗粒度）。
- 布隆过滤器底层。
- 大整数排序/去重（10 亿手机号排序用位图最省）。

## 二、布隆过滤器（Bloom Filter）

**概率型数据结构**，判断"元素是否在集合里"：
- **一定准确说"不在"**（无假阴性）。
- **可能误判说"在"**（假阳性，false positive）。

### 结构
- 一个 m 位的位数组（初始全 0）。
- k 个独立哈希函数。

### 插入
```
add(x):
  for i in 1..k:
    pos = h_i(x) % m
    bit[pos] = 1
```

### 查询
```
contains(x):
  for i in 1..k:
    pos = h_i(x) % m
    if bit[pos] == 0: return false   // 任一位为 0 → 一定不在
  return true                          // 全为 1 → 可能在（或假阳性）
```

### 为什么有假阳性没假阴性
- **没假阴性**：插入时所有 h_i(x) 对应位都置 1，查询时这些位必然都 1。
- **有假阳性**：别的元素可能恰好把 x 的所有位都置了 1 → 误判在。

### 假阳性率
- 公式（近似）：`p ≈ (1 - e^(-kn/m))^k`，n = 已插元素数，m = 位数，k = 哈希数。
- 实际配置：m、k 按"预期元素数 n + 目标假阳性率 p"算。
- 例：n=1亿、p=1% → m≈958M bit（~114MB），k=7。
- p 调小 → m 增大；n 超预期 → p 上升。

### 优缺点
- 优点：**空间极省**（1 亿元素 100+ MB vs HashSet 几 GB）、O(k) 查询、保密（不存原值）。
- 缺点：**假阳性**、**不支持删除**（标准版，多位被多个元素共享；Counting Bloom Filter 可删）。

## 三、Counting Bloom Filter（可删）

- 每位用计数器（4 bit/8 bit）代替 1 bit，插入 +1 删除 -1。
- 代价：内存翻几倍。
- 注意计数器溢出。

## 四、应用

### 1. 缓存穿透防护（最经典）
- 缓存穿透：查一个 DB 没有的 key，每次都打到 DB。
- 用布隆过滤器先判：说"不在" → 直接返回，不查 DB。
- 说"在" → 再查缓存/DB（可能是假阳性，但概率低）。
- 配合：DB 写入时同步 `add` 到布隆过滤器。

### 2. 邮箱/用户名重复检测
- 海量用户，判重用 HashSet 内存吃紧 → 布隆过滤器，假阳性时再回查 DB 确认。

### 3. 黑名单过滤
- URL 黑名单、IP 黑名单 → 布隆过滤器快速判。

### 4. 爬虫 URL 去重
- 已爬 URL 进布隆过滤器，新 URL 查 → 说"不在"才爬。

### 5. HBase/LevelDB SSTable 查询加速
- 每个 SSTable 配一个布隆过滤器 → 查 key 时先过滤，避免无谓磁盘读。

## 五、HyperLogLog（基数估计）

**估算集合去重后元素数（基数）**，误差 ~0.81%，内存固定（Redis 实现 12KB）。
- 例：UV 统计，10 亿访问去重计数。
- 比 HashSet（存所有元素）省几个数量级。
- Redis `PFADD`/`PFCOUNT`/`PFMERGE`。
- 不存元素本身，只估数。

## 六、对比

| 结构 | 空间 | 精确 | 支持 | 适合 |
| --- | --- | --- | --- | --- |
| **HashSet** | O(n) | 精确 | 增删查 | 通用去重 |
| **Bitmap** | O(max_value) | 精确 | 增删查 | 稠密整数 |
| **Bloom Filter** | O(n) 但常数小 | **有假阳性** | 增查（删要 Counting） | 海量存在性判断 |
| **HyperLogLog** | 固定 12KB | **~0.81% 误差** | 增+估数（不查单元素） | 基数估计（UV） |

## 易错点
- 布隆过滤器当精确 → 有假阳性，业务要容忍。
- 以为布隆过滤器能删 → 标准版不能，要用 Counting Bloom Filter。
- 元素数超预期 → 假阳性率飙升，要按预期 n 留余量配 m。
- 位图当万能 → 仅适合稠密整数，稀疏（如 UUID）不划算。
- HyperLogLog 当精确计数 → 是估算，误差 ~0.81%。
- 缓存穿透布隆过滤器忘记同步 → DB 写入后要 `add` 到布隆过滤器，否则永远说"不在"。

""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["algorithms/heap/heap-data-structure.md",
         "algorithms/linked-lists/lru-cache-implementation.md",
         "databases/redis/redis-data-structures.md"])

print("\nDone: 8 classic data structure docs")
