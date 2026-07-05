---
type: question
id: concurrency/readwritelock-stampedlock
title: ReentrantReadWriteLock / StampedLock (读写锁 + 乐观读)
category: concurrency
subcategory: concurrency
difficulty: hard
tags: [readwritelock, stampedlock, aqs, optimistic-read, concurrency]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-05-26
---

# ReentrantReadWriteLock / StampedLock (读写锁 + 乐观读)

## 问题描述

读写锁怎么实现？读写锁有什么问题？StampedLock 的乐观读怎么解决？什么时候用 StampedLock？

## 解答

### ReentrantReadWriteLock（基于 AQS）
- **state 高低位复用**：高 16 位 = 共享读次数（多个读者），低 16 位 = 独占写重入数（最多一个写者）。
- 读锁 `tryAcquireShared`：写锁未被持（低 16 位=0）且读者数未超上限 → CAS 高 16 位 +1。
- 写锁 `tryAcquire`：state==0 或 owner==当前线程（重入）→ CAS 低 16 位 +1。
- **支持重入**：读者可再读，写者可重入写、也可"锁降级"（持写锁时再获取读锁，再释放写锁）。
- **不支持锁升级**：持读锁时不能直接拿写锁（会死锁——写锁等所有读者释放，而自己就是读者）。

### 读写锁的问题
1. **写饥饿**：读多写少场景，读者源源不断，写者永远等不到所有读者释放 → 写饿死。
   - 解法：公平模式（写者优先排队）或写锁设超时。
2. **读不可并发升级**。
3. 高并发读时 CAS 改高 16 位竞争激烈（同一 state 字段）。

### StampedLock（JDK 8，乐观读）
- 三种模式：**写锁 / 悲观读锁 / 乐观读**。
- **乐观读（核心）**：
  ```java
  long stamp = lock.tryOptimisticRead();   // 读一个 stamp，不加锁
  // ... 读数据到本地变量 ...
  if (!lock.validate(stamp)) {             // 期间有写？
      stamp = lock.readLock();             // 升级悲观读锁
      try { /* 重新读 */ } finally { lock.unlockRead(stamp); }
  }
  ```
- `validate` 是**轻量级**：仅检查 stamp 对应的版本是否变化（volatile 读 + 屏障），不加锁不阻塞。
- 乐观读期间若无写，**全程零开销**（无 CAS、无队列）；有写才升级悲观读重试。
- **不可重入**：同一线程重复 `readLock` 会死锁。所以**不用在嵌套场景**。
- 写锁、悲观读锁用法类似 ReentrantReadWriteLock。

### 三者对比
| 维度 | synchronized | ReentrantReadWriteLock | StampedLock |
| --- | --- | --- | --- |
| 读写分离 | ❌ | ✅ | ✅ |
| 乐观读 | ❌ | ❌ | ✅ |
| 可重入 | ✅ | ✅ | ❌ |
| 写饥饿缓解 | — | 公平模式 | 乐观读不阻塞写 |
| 适用 | 简单临界 | 读多写少、需重入 | 读多写少、不重入、极致性能 |

### 何时用 StampedLock
- 读远多于写、且不重入、不需 Condition → StampedLock 乐观读性能最优。
- 需要重入 / Condition / 普遍场景 → ReentrantReadWriteLock 更安全。
- 简单同步 → synchronized。

## 易错点
- StampedLock 当可重入用 → 同线程重复 readLock 死锁。
- 持读锁尝试升级写锁 → 死锁（锁升级不支持）。
- 乐观读不 validate 直接用 → 读到中间态脏数据。
- 乐观读升级悲观读后忘 unlock → 锁泄漏。

## 延伸

## 延伸

- 关联题：[[concurrency/aqs-principle]]
- 关联题：[[concurrency/synchronized-vs-reentrantlock]]
- 关联题：[[concurrency/cas-mechanism]]
