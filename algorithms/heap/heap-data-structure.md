---
type: question
id: algorithms/heap/heap-data-structure
title: 二叉堆 (堆化/堆排序/Top-K/Java PriorityQueue)
category: algorithms
subcategory: heap
difficulty: medium
tags: [heap, binary-heap, priority-queue, top-k, heap-sort, java, data-structure]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-07-05
---

# 二叉堆 (堆化/堆排序/Top-K/Java PriorityQueue)

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
          /     \
        7(1)     8(2)
       /  \    /  \
      4(3) 5(4) 6(5) 3(6)
     / \
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

## 延伸

- 关联题：[[algorithms/sorting-searching/sorting-algorithms-comparison.md]]
- 关联题：[[algorithms/trees-graphs/red-black-tree.md]]
- 关联题：[[concurrency/thread-pool-principles]]
