---
type: question
id: concurrency/threadlocal-usage-pitfalls
title: ThreadLocal 使用场景与内存泄漏
category: concurrency
subcategory: concurrency
difficulty: medium
tags: [threadlocal, memory-leak, context, juc]
languages: []
role: [ai-app, sde, backend]
companies: [中泓一线, 有赞]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# ThreadLocal 使用场景与内存泄漏

## 问题描述
ThreadLocal 是什么？用在什么场景？使用注意的点？为什么会脏掉？

## 解答
**ThreadLocal** = 线程本地变量，每个线程一份独立副本，线程间隔离。

### 实现原理
- 每个 `Thread` 持有 `ThreadLocalMap threadLocals`。
- Map 的 **key 是 ThreadLocal 的弱引用**，**value 是强引用**。
- `ThreadLocal.get()` → 取当前线程的 map → 按 this 查 Entry。

### 典型场景
1. **用户上下文传递**：HTTP 请求进网关，在 filter 把 userId 放 ThreadLocal，整个调用链免传参。
2. **数据库连接 / 事务绑定**：Spring 的 `TransactionSynchronizationManager`。
3. **SimpleDateFormat 隔离**（非线程安全）。
4. **MDC 日志 traceId**。

### 内存泄漏机制
- key 是弱引用，ThreadLocal 实例若无外部强引用会被 GC，Entry 变成 `(null, value)`。
- value 是强引用，**只要线程活着**就回收不掉。
- 线程池里线程长生不死 → value 永久泄漏。

### 注意点
- **用完必须 `remove()`**，尤其在线程池场景（finally 块）。
- 不要把大对象塞进去。
- 不要用 `static ThreadLocal` 滥用，会造成全局隐式状态。

### 为什么会"脏"
线程池复用线程，上一个任务没 `remove()`，下一个任务 `get()` 拿到上一个任务的残留。见 [[concurrency/threadlocal-threadpool-problems]]。

## 延伸

## 延伸

- 关联题：[[concurrency/threadlocal-threadpool-problems]]
- 关联题：[[concurrency/thread-pool-principles]]
- 关联题：[[backend/microservices/microservice-user-context-propagation]]
