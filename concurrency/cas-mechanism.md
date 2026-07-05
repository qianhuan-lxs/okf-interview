---
type: question
id: concurrency/cas-mechanism
title: CAS 机制 (从直觉到 cmpxchg 底层)
category: concurrency
subcategory: concurrency
difficulty: hard
tags: [cas, compare-and-swap, atomic, aba, unsafe, varhandle]
languages: [java]
role: [sde, backend]
companies: [有赞, 探迹, 北京用友]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-07-05
---

# CAS 机制 (从直觉到 cmpxchg 底层)

## 问题描述

CAS 是什么？为什么需要它？底层怎么保证原子？ABA 真有那么严重？高并发下 CAS 为什么反而差？

## 一、先建直觉：CAS 在解决什么

多线程改一个共享变量，最朴素是加锁：
```java
synchronized (lock) { i++; }   // 串行化，慢
```
锁太重——要系统调用、上下文切换。**CAS 给了一种"不加锁"的乐观做法**：

> "我觉得现在 i 是 5，如果是 5 就把它改成 6；如果不是 5，那说明被别人改过了，我重试。"

这就是 **Compare-And-Swap**：三参数 `(内存位置 V, 期望值 A, 新值 B)`，仅当 `V==A` 时把 V 改成 B，否则返回当前值。**比较和替换是 CPU 一条指令完成的**，中间不会被别的线程插足。

类比：你改 git 文件前先 `git pull`，发现远程比你新就 rebase 重来，不冲突就 push。乐观、不阻塞、冲突才重试。

## 二、为什么需要 CAS（而非只用锁）
- 锁（synchronized/ReentrantLock）阻塞 → 系统调用 + 上下文切换，高并发低竞争时开销占大头。
- CAS 无锁自旋 → 竞争不剧烈时几乎零开销，性能远超锁。
- 是无锁数据结构（ConcurrentHashMap 空槽插入、AtomicInteger 自增、AQS 改 state）的基石。

## 三、底层怎么保证原子（重点）

CAS 在 Java 层是 `Unsafe.compareAndSwapXxx` / JDK 9+ `VarHandle.compareAndSet`，最终走 JNI 到 CPU 指令：

- **x86**：`lock cmpxchg`。`cmpxchg` 本身是"读-比较-写"三步，**不是原子的**；但加 **`lock` 前缀** → 锁缓存行（MESI 协议）或锁总线，保证整条指令原子。
- **ARM/PowerPC**：LL-SC（Load-Linked / Store-Conditional）循环——硬件层"乐观"：若加载后该缓存行被改，SC 失败，重试。

> 新手理解到这层就够：**CAS 原子性靠 CPU 硬件指令，不是 Java 自己实现的**。

## 四、Java 里的 CAS 封装

| API | 用途 |
| --- | --- |
| `AtomicInteger / AtomicLong / AtomicReference` | 基本原子类，封装 volatile 字段 + CAS |
| `AtomicStampedReference` | 带 int 版本号的引用（防 ABA） |
| `AtomicMarkableReference` | 带 boolean 标记的引用（防 ABA 简化版） |
| `Unsafe.compareAndSwapXxx` | JDK 9 前的底层 native API（内部用） |
| `VarHandle.compareAndSet` | JDK 9+ 标准替代 Unsafe，支持内存序 |

AQS 的 `state` 修改、`ConcurrentHashMap` 空槽插入、`LongAdder` 的 Cell 累加都用 CAS。

## 五、ABA 问题（新手最难理解，用例子讲）

### 现象
线程 1 读到值 A，准备 CAS A→C。被抢占期间，线程 2 把 A→B→A（值"回到"A 但中间变过）。线程 1 恢复，CAS A→C 仍成功——值"看起来"没变，但中间状态丢失了。

### 真实危害场景（无锁栈）
- 栈顶是 A，A 的 next 指向 B。
- 线程 1 要 pop：记下 top=A、next=B，准备 CAS top A→B。被抢占。
- 线程 2：pop A、pop B、又 push A（A 的 next 现在变了，可能指向 null 或别的）。
- 线程 1 恢复：CAS top A→B 成功——**但此时 A 的 next 早已不是 B**，栈结构破坏，B 可能丢失或重复。

### 解法
- `AtomicStampedReference`：每次改动带版本号，CAS 必须匹配 `(值, 版本)`。A→B→A 时版本也变了，线程 1 的旧版本 CAS 失败。
- `AtomicMarkableReference`：boolean 标记，更轻（仅二态）。
- GC 隐式缓解对象引用场景，但**不解决同一对象被复用**。

> 新手要点：**ABA 不是值错了，是"中间过程"丢了**。值类的计数器 ABA 通常无害（值对就行），但**指针/引用型的数据结构**会真出问题。

## 六、高并发下 CAS 为什么反而差 + "重试有没有上限"

### 现象
CAS 失败就自旋重试 → 高竞争下大量线程同时 CAS 同一字段，只有一个成功，其余空转耗 CPU。极端情况吞吐比 synchronized 还差（锁至少排队不空转）。

### 那 `AtomicInteger.incrementAndGet` 重试有没有上限？
**没有**。看源码就是无限 `do-while`：
```java
public final int incrementAndGet() {
    int cur, next;
    do {
        cur = get();
        next = cur + 1;
    } while (!compareAndSet(cur, next));   // 失败就重来，无次数上限
    return next;
}
```
**理论上一根线程可能一直输**——每轮都被别人抢先。但这引出两个正式概念：

| 概念 | 定义 | `AtomicInteger` 是吗 |
| --- | --- | --- |
| **lock-free（无锁）** | 系统整体总在前进——每轮至少有一个线程 CAS 成功 | ✅ 是 |
| **wait-free（无等待）** | 每个线程都在**有界步**内完成——单线程不饿死 | ❌ 不是 |

所以精确回答"会不会一直失败"：
- **系统层面不会停**：每轮必有 1 个线程赢，系统前进。
- **单线程可能持续失败**：lock-free **不保证**单线程有界完成，理论上某线程可被饿死。实际中赢的线程退出后竞争减少，很难真持续，但**JVM 不给你这个保证**。

### 工程上怎么"限"重试（关键）

| 做法 | 谁用 | 说明 |
| --- | --- | --- |
| **纯自旋无上限** | `AtomicInteger/Long/Reference` 的 `getAndAdd` 等 | 极简，赌低竞争 |
| **自旋 + park 阻塞** | **AQS**（`acquireQueued`）、`ReentrantLock`、`Semaphore` | CAS 改 state 失败 → 入 CLH 队 → `LockSupport.park` 挂起，**不空转**。这是"自旋有限"的关键模式 |
| **分散热点** | **`LongAdder`**（base + Cell[]）、`Striped64` | 不让 N 线程 CAS 同一字段，hash 到不同 Cell |
| **退避 backoff** | 手写代码：失败 N 次后 `Thread.yield()` / 短 sleep / 指数退避 | 无内置 API，需自己加 |
| **`Thread.onSpinWait()`** (JDK9+) | 提示 CPU 发 `PAUSE` 指令 | ⚠️ **只是功耗/乱序提示，不是次数限制**——常被误解 |
| **CAS 失败退化为锁** | `ConcurrentHashMap` 1.8 链表头插入 / `computeIfAbsent` | CAS 抢 bin 头失败 → `synchronized` 锁该 bin |

### 高竞争的正确姿势不是"重试更狠"，是换策略
- **计数器** → `LongAdder`（分散热点，吞吐数倍于 `AtomicLong`，代价 `sum()` 非精确瞬时值）。
- **复合状态竞争** → AQS / 锁（自旋一阵就 park，不空转耗 CPU）。
- **极端兜底** → synchronized 重量锁（park 阻塞，吞吐未必差）。
- 想限重试 → 自己在 CAS 循环外加计数器 + `Thread.yield()`/退避。

## 七、CAS 和 volatile 的关系（易混）
- `AtomicInteger.value` 是 **volatile** → 保证读的可见性。
- **CAS** → 保证写的原子性。
- 两者结合才完整：volatile 管"看得见"，CAS 管"改得对"。
- 所以 `AtomicInteger` 不是"只靠 CAS"，是 volatile + CAS。

## 八、面试高频追问速答

| 问题 | 答 |
| --- | --- |
| CAS 原子性谁保证？ | CPU 硬件指令（x86 `lock cmpxchg`，ARM LL-SC）。 |
| CAS 能替代锁吗？ | 低竞争可以（原子类）；复合操作（先读再判断再写多步）不行。 |
| ABA 何时真有害？ | 引用/指针型数据结构（无锁栈、链表）；纯计数器通常无害。 |
| `i++` 加 volatile 行吗？ | 不行，volatile 不保证原子；用 `AtomicInteger` 或锁。 |
| 高并发计数器选什么？ | `LongAdder`（远优于 `AtomicLong`）。 |
| CAS 重试有上限吗？ | 纯 `Atomic*` 无上限（无限 do-while）；AQS 是自旋后 park；想限要自己加 backoff。 |
| `AtomicInteger` 是 wait-free 吗？ | 不是，是 lock-free。系统前进但单线程理论可饿死。 |

## 易错点
- 把 CAS 当万能 → 高竞争退化为自旋空耗。
- 以为 `AtomicReference` 防 ABA → 不能，要用 `AtomicStampedReference`。
- `i++` 用 volatile 想原子 → 不行，复合操作。
- `LongAdder.sum()` 当精确快照 → 它是估算求和，期间 Cell 仍在变。

## 延伸

- 关联题：[[concurrency/aqs-principle]]
- 关联题：[[concurrency/synchronized-vs-reentrantlock]]
- 关联题：[[concurrency/longadder-vs-atomiclong]]
- 关联题：[[concurrency/volatile-principle]]
