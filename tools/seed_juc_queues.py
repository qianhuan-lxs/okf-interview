#!/usr/bin/env python3
"""Add JUC concurrent queue/deque family catalog doc."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from ikf_writer import q

DATE = "2026-07-05"

q("concurrency/juc-concurrent-queues.md",
  "JUC 并发队列族 (BlockingQueue / BlockingDeque / 无锁队列设计)",
  "concurrency", "concurrency", "hard",
  ["blockingqueue", "linkedblockingdeque", "concurrentlinkedqueue",
   "juc", "data-structure", "concurrency"],
  [],
  """# JUC 并发队列族 (BlockingQueue / BlockingDeque / 无锁队列设计)

## 问题描述

Java JUC 有哪些经典并发队列/双端队列？各自的数据结构、锁机制、特性、适用场景？双端阻塞队列是哪个？

## 解答

JUC 的并发队列分两大类：**阻塞（Blocking）** 用于生产者-消费者，**无锁（Concurrent）** 用于高并发无阻塞。下表是全族速览，再逐一拆设计。

| 实现 | 接口 | 底层结构 | 同步机制 | 有界 |
| --- | --- | --- | --- | --- |
| ArrayBlockingQueue | BlockingQueue | 数组+索引头尾 | 单 ReentrantLock + 2 Condition | ✅ |
| LinkedBlockingQueue | BlockingQueue | 链表+head/tail | **两把锁** takeLock/putLock | 可有界默认无界 |
| SynchronousQueue | BlockingQueue | 无容量 | TransferStack/TransferQueue + CAS | — |
| PriorityBlockingQueue | BlockingQueue | 堆数组 | 单 ReentrantLock | 无界 |
| DelayQueue | BlockingQueue | PriorityQueue | 单 ReentrantLock + Leader-Follower | 无界 |
| LinkedTransferQueue | TransferQueue/BlockingQueue | 链表 | 无锁 CAS | 无界 |
| **LinkedBlockingDeque** | **BlockingDeque** | 双向链表 | 单 ReentrantLock + 1 Condition | 可有界默认无界 |
| ConcurrentLinkedQueue | Queue | 单向链表 | 无锁 CAS（Michael-Scott） | 无界 |
| ConcurrentLinkedDeque | Deque | 双向链表 | 无锁 CAS | 无界 |

---

## 一、BlockingQueue 接口——四组操作语义

BlockingQueue 把"满/空时的处理"分成四组，记牢这四组就懂了所有阻塞队列的 API：

| | 抛异常 | 返回特殊值 | 阻塞 | 超时 |
| --- | --- | --- | --- | --- |
| 入队 | `add`（满抛 `IllegalStateException`） | `offer`（满返 false） | `put`（满阻塞） | `offer(e, timeout)` |
| 出队 | `remove`（空抛 `NoSuchElementException`） | `poll`（空返 null） | `take`（空阻塞） | `poll(timeout)` |
| 查看队首 | `element`（空抛异常） | `peek`（空返 null） | — | — |

---

## 二、ArrayBlockingQueue——数组 + 单锁 + 两 Condition

- **结构**：固定大小数组，`int takeIndex`/`putIndex`/`count`，环形复用（不搬移元素，索引回绕）。
- **锁**：一把 `ReentrantLock`，两个 `Condition`（`notEmpty`/`notFull`）。
- `put`：`lock.lock()` → `while (count == items.length) notFull.await()` → 写数组 → `count++` → `notEmpty.signal()`。
- `take`：对称，`while (count == 0) notEmpty.await()` → 读 → `notFull.signal()`。
- **有界**（构造必须指定容量），适合**有背压**的生产者-消费者。
- **为什么一把锁**：数组头尾索引耦合在同一数组，分开锁会复杂且收益有限。

---

## 三、LinkedBlockingQueue——链表 + 两把锁（设计亮点）

- **结构**：链表 + dummy head 节点 + `AtomicInteger count` + `head`/`last`。
- **锁**：**两把分离的锁** `ReentrantLock takeLock` + `putLock`，各配一个 Condition（`notEmpty`/`notFull`）。
- `put`：`putLock.lock()` → `while (count.get() == capacity) notFull.await()` → 链尾追加 → `count.getAndIncrement()` → `if (count.get() < capacity) notFull.signal()` → 释放 putLock → **`signalNotEmpty()`**（若 count 从 0→1，要拿 takeLock 唤醒消费者）。
- `take`：对称。

### 为什么能两把锁（重点）
- 链表头尾是**不同节点**，put 操作尾节点、take 操作头节点，物理上不冲突。
- `count` 用 `AtomicInteger` 让两把锁都能原子读写计数。
- **收益**：put 和 take 可真正并发——吞吐高于 ArrayBlockingQueue 的单锁。
- **代价**：`size()` 用 AtomicInteger，非精确瞬时；两把锁的交互（signalNotEmpty 要跨锁）增加复杂度。
- **默认容量 `Integer.MAX_VALUE`** → 无界 → OOM 隐患（这是 `Executors.newFixedThreadPool` 用它的根因）。

---

## 四、SynchronousQueue——无容量、直接交接

- **没有元素存储**——每个 `put` 必须等一个 `take` 同时在场才完成（hand-off）。
- 内部两个实现：
  - **公平模式**：`TransferQueue`（FIFO 队列存等待的 take/put）。
  - **非公平模式**（默认）：`TransferStack`（LIFO 栈，让最近等待的优先配对，减少 park 开销）。
- `put` 线程把"我有个元素"压栈/入队，等一个 `take` 线程来配对；配对后两者都完成。超时或中断则取消。
- **`CachedThreadPool` 用它**：来任务必须有线程正在 `take` 才交接成功，否则新建线程——这就是"无界线程+无容量队列"实现即时 hand-off 的原理。
- **坑**：`size()`/`peek()` 永远返回 0/null（没有驻留元素）；`iterator()` 空迭代。
- 适合：直接传递（线程间交接数据，不缓存）。

---

## 五、PriorityBlockingQueue——堆 + 单锁 + 无界

- **结构**：二叉小顶堆数组（`queue[]`），`Comparator` 决定优先级。
- **锁**：一把 `ReentrantLock` + `Condition notEmpty`（**没有 notFull**——无界，put 不阻塞）。
- `put`：`lock()` → 扩容（满则 grow）→ 上浮（`siftUp`）→ `notEmpty.signal()`。
- `take`：`lock()` → 弹堆顶 → 下沉（`siftDown`）→ 返回。
- **出队顺序按优先级**，不按入队顺序。
- **无界** → OOM 风险。
- 适合：任务有优先级的调度（如优先级任务池）。

---

## 六、DelayQueue——延迟出队的堆

- **结构**：基于 `PriorityQueue`（按 `getDelay` 排序，最近到期的在堆顶）+ `ReentrantLock`。
- 元素必须实现 `Delayed`（`getDelay(TimeUnit)` 返回剩余延迟）。
- `take`：`lock()` → 取堆顶 → `if (delay <= 0) 出队` 否则 **`available.awaitNanos(delay)`**（等到到期）。
- **Leader-Follower 模式**（设计亮点）：
  - 多个消费者等待时，**只有一个 leader** 等待堆顶到期（`awaitNanos`），其他 follower 无限 `await`。
  - leader 到期取走元素后 `signal()` 唤醒一个 follower 成为新 leader。
  - 收益：避免所有消费者都 `awaitNanos` 同一时间、到期时一起惊群竞争。
- `ScheduledThreadPoolExecutor` 内部用 `DelayedWorkQueue`（DelayQueue 的堆优化版，元素是 `ScheduledFutureTask`，索引可改）。
- 适合：定时任务、缓存过期、延迟消息。

---

## 七、LinkedTransferQueue——无锁 + transfer 语义（JDK 7）

- 实现 `TransferQueue`（扩展 `BlockingQueue`），**无锁 CAS**（基于 `LinkedBlockingQueue` 思想但去锁）。
- 核心 API：
  - `transfer(e)`：把元素直接交给一个正在等的消费者，**没有消费者就阻塞等**（不像 SynchronousQueue 那样必须同步在场——可以"我先在这等"）。
  - `tryTransfer(e)`：不阻塞，有消费者就交，没有返回 false。
  - `tryTransfer(e, timeout)`：限时等消费者。
- 数据结构：链表 + relaxed tail（tail 不总是最新，靠遍历修正，减少 CAS）+ `Node` 带 item/data 标记。
- 算法：Michael-Scott 队列变体 + 配对匹配（类似 SynchronousQueue 但支持暂存元素）。
- 适合：高吞吐的线程间交接，比 SynchronousQueue 更灵活（可暂存）。

---

## 八、LinkedBlockingDeque——双端阻塞队列（你想到的）

- **实现 `BlockingDeque`**（扩展 `BlockingQueue` + `Deque`），两端都能阻塞入/出。
- **结构**：双向链表 + `head`/`last`。
- **锁**：**一把 `ReentrantLock` + 一个 `Condition notEmpty`**（注意没有 notFull——容量满时也用 notEmpty？实际是 `Condition notFull` 也存在，两 Condition 共用一把锁）。
  - 准确：单 `lock`，两个 Condition（`notEmpty`/`notFull`）。
- 双端 API：`putFirst`/`putLast`/`takeFirst`/`takeLast`/`offerFirst`/`offerLast`/`pollFirst`/`pollLast` 等。
- **为什么单锁**：双向链表头尾操作都可能改相邻节点指针，分锁会互相阻塞且易死锁，单锁简单安全。
- **默认容量 `Integer.MAX_VALUE`** → 无界 OOM 风险。
- 适合：
  - **工作窃取**（`ForkJoinPool` 每个 worker 的 deque 就是双端——自己 LIFO 取尾，别人 FIFO 偷头）。
  - 生产者消费者两端都可入可出（如调度器两端插任务）。
- 坑：单锁吞吐低于 LinkedBlockingQueue 的双锁；无界 OOM。

### BlockingDeque 接口四组操作（两端各一套）
| | 抛异常 | 返回特殊值 | 阻塞 | 超时 |
| --- | --- | --- | --- | --- |
| 头入 | `addFirst` | `offerFirst` | `putFirst` | `offerFirst(e, t)` |
| 头出 | `removeFirst` | `pollFirst` | `takeFirst` | `pollFirst(t)` |
| 尾入 | `addLast` | `offerLast` | `putLast` | `offerLast(e, t)` |
| 尾出 | `removeLast` | `pollLast` | `takeLast` | `pollLast(t)` |

---

## 九、ConcurrentLinkedQueue / ConcurrentLinkedDeque——无锁（Michael-Scott）

- **不阻塞**——没有 `put`/`take`，用 `offer`/`poll`（立即返回，不等待）。
- **算法**：Michael & Scott 1996 经典无锁队列算法——`head`/`tail` 是 `AtomicReference<Node>`，`offer` 用 CAS 追加节点 + 修正 tail，`poll` 用 CAS 推进 head。
- **关键设计**：`tail` 不总是链表真正的尾（relaxed tail）——`offer` 时若发现 tail 落后，先 CAS 修正再追加。这是无锁算法的常见技巧：**允许中间状态不一致，靠后续操作自愈**，避免每次都强一致 CAS 的竞争。
- `ConcurrentLinkedDeque` 是双向版本，更复杂（双向指针的 CAS 更难，要用 CAS+unsafe）。
- `size()` 是 O(n) 遍历（不维护计数器，避免竞争）——**别在热路径调 `size()`**。
- 适合：高并发无阻塞场景，自己用阻塞逻辑包（如 `LinkedBlockingQueue` 太重时）。
- 坑：`poll` 在空时返回 null，无法区分"空"和"没数据"（阻塞队列用 `take` 解决）；无 `put` 阻塞，要自己实现背压。

---

## 十、选型决策

| 需求 | 选 |
| --- | --- |
| 有界 + 背压 + 简单 | ArrayBlockingQueue |
| 高吞吐生产者-消费者 + 可控容量 | LinkedBlockingQueue（设容量） |
| 线程间直接交接不缓存 | SynchronousQueue |
| 优先级任务 | PriorityBlockingQueue |
| 延迟/定时 | DelayQueue |
| 高吞吐 + transfer 语义 | LinkedTransferQueue |
| **双端阻塞（工作窃取、两端进出）** | **LinkedBlockingDeque** |
| 无阻塞高并发 + 自己管背压 | ConcurrentLinkedQueue/Deque |

---

## 十一、面试高频追问

| 问题 | 答 |
| --- | --- |
| LinkedBlockingQueue 为什么比 ArrayBlockingQueue 快？ | 两把锁分离 put/take，可并发；Array 单锁串行。 |
| SynchronousQueue 真的没存元素吗？ | 是，size 永远 0，put 必须等 take 配对。 |
| DelayQueue 怎么避免消费者惊群？ | Leader-Follower——只有一个 leader 等堆顶到期，其他无脑 await。 |
| ConcurrentLinkedQueue 的 tail 是真尾吗？ | 不总是，relaxed tail 允许落后，靠后续 offer 自愈。 |
| LinkedBlockingDeque 为什么单锁？ | 双向链表头尾指针互相关联，分锁易死锁。 |
| 哪些是无界队列？ | LinkedBlockingQueue(默认)/PriorityBlockingQueue/DelayQueue/LinkedTransferQueue/ConcurrentLinked*。无界要警惕 OOM。 |

## 易错点
- 用 `Executors.newFixedThreadPool` → LinkedBlockingQueue 无界 → OOM。
- ConcurrentLinkedQueue 当阻塞队列用 → 它不阻塞，poll 空返 null，要自己 wait。
- LinkedBlockingDeque 以为双锁 → 单锁，吞吐不如 LinkedBlockingQueue。
- DelayQueue 任务不实现 `Delayed` → 编译错。
- `size()` 在 ConcurrentLinkedQueue 是 O(n)，热路径别调。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["concurrency/thread-pool-principles",
         "concurrency/threadpool-source-analysis",
         "concurrency/executors-built-in-pools",
         "concurrency/forkjoinpool-parallelstream",
         "concurrency/aqs-principle"])

print("\nDone: JUC concurrent queue family catalog")
