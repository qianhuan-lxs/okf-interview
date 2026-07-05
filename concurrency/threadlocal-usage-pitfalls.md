---
type: question
id: concurrency/threadlocal-usage-pitfalls
title: ThreadLocal 用法陷阱 (内存泄漏 / 弱引用 key / 回收)
category: concurrency
subcategory: concurrency
difficulty: hard
tags: [threadlocal, memory-leak, weak-reference, concurrency]
languages: [java]
role: [sde, backend]
companies: [安克创新, 有赞]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# ThreadLocal 用法陷阱 (内存泄漏 / 弱引用 key / 回收)

## 问题描述

ThreadLocal 为什么会内存泄漏？key 是弱引用为什么还会泄漏？怎么解决？为什么要用 `remove()`？

## 解答

### 结构
- **每个 `Thread` 持有 `ThreadLocalMap`**（不是 ThreadLocal 自己持有 Map，方向反了）。
- `ThreadLocalMap` 的 entry 是 `WeakReference<ThreadLocal>` 当 key，value 是强引用。
- 每个 ThreadLocal 实例的 `threadLocalHashCode` 决定其在数组中的槽位（开放定址法，非 HashMap 的链表法）。

### 为什么 key 用弱引用
- 防止 ThreadLocal 对象本身泄漏：当外部 ThreadLocal 引用消失（如方法栈出栈），GC 能回收 key。
- 但 **value 是强引用**——这是泄漏根源。

### 泄漏场景（核心面试点）
- 线程池场景：**线程长期存活**，ThreadLocalMap 也长期存活。
- ThreadLocal 外部引用消失 → key 被 GC 回收 → entry 变成 `(null, value)`（stale entry）。
- **value 强引用链**：`Thread → ThreadLocalMap → Entry.value → 大对象`。只要线程不死，value 永远不被回收 → 泄漏。
- 弱引用 key 只防"ThreadLocal 对象本身"泄漏，**不防 value 泄漏**。

### 为什么 set/get/cleanStaleEntry 不够
- ThreadLocal 源码在 `set`/`get`/`remove` 时会扫到 key==null 的 stale entry 做 `value=null` 清理（`expungeStaleEntry` / `replaceStaleEntry`）。
- **但**：只在访问到那个槽位时才清理，不访问就一直堆着。线程池长任务可能长期不触发清理。

### 解法（必答）
1. **`finally { threadLocal.remove(); }`**——最根本，显式断 value 引用。用完即清。
2. **线程池场景务必 remove**——线程复用，ThreadLocalMap 跟着复用，上轮残留污染下一轮。
3. 不要用 `static ThreadLocal` 长期持有大 value（生命周期被拉到类级）。
4. 谨慎用 `InheritableThreadLocal`——子线程继承父线程的 value，线程池下父子关系混乱。

### 阿里规约
- ThreadLocal 必须在 `finally` 中 `remove()`，尤其线程池场景。

### 真实应用场景
- **Spring `RequestContextHolder`**：HTTP 请求线程绑定 RequestContext，请求结束清理。
- **`TransactionSynchronizationManager`**：事务资源绑定到当前线程（Connection）。
- **`SimpleDateFormat` 线程安全**：SimpleDateFormat 非线程安全，用 `ThreadLocal<SimpleDateFormat>` 每线程一份。
- **MDC（日志链路追踪）**：`MDC.put(traceId)` 存链路 ID，日志输出时取。

## 易错点
- 以为弱引用 key 就不泄漏了 → value 是强引用，照样漏。
- 忘 `remove()`，尤其线程池 → 下一轮任务读到上一轮残留。
- 用 `ThreadLocal` 当全局变量缓存大对象且不清理 → 线程池 OOM。

## 延伸

## 延伸

- 关联题：[[concurrency/threadlocal-threadpool-problems]]
- 关联题：[[concurrency/thread-pool-principles]]
- 关联题：[[concurrency/volatile-principle]]
