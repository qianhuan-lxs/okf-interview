---
type: question
id: concurrency/volatile-principle
title: volatile 原理 (JMM / happens-before / 内存屏障 / DCL)
category: concurrency
subcategory: concurrency
difficulty: hard
tags: [volatile, jmm, memory-barrier, happens-before, concurrency]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-05-26
---

# volatile 原理 (JMM / happens-before / 内存屏障 / DCL)

## 问题描述

volatile 的原理？能保证什么不能保证什么？为什么 DCL 单例的实例字段要 volatile？volatile 和 synchronized 区别？

## 解答

### volatile 两大语义
1. **可见性**：写 volatile 变量 → 刷新到主内存；读 volatile 变量 → 从主内存重新加载，不缓存到工作内存（CPU 缓存/寄存器）。一写多读立即可见。
2. **禁止指令重排**：在 volatile 读/写前后插入**内存屏障**，阻止编译器与 CPU 重排跨 volatile 的指令。

### volatile 不能保证什么
- **不保证原子性**。`i++` 是读-改-写三步，volatile 只保证每步可见，但三步之间可被打断 → 多线程下仍丢更新。要原子用 `AtomicInteger` 或 `synchronized`。
- 只能用在"一写多读"的标志位/状态发布场景。

### 内存屏障（底层）
- JSR-133 规范的屏障规则：
  - volatile 写前插入 `StoreStore`（禁止前面普通写与 volatile 写重排）。
  - volatile 写后插入 `StoreLoad`（禁止 volatile 写与后面 volatile 读/写重排，最重）。
  - volatile 读后插入 `LoadLoad` + `LoadStore`（禁止后面普通读/写与 volatile 读重排）。
- x86 上 volatile 写实际生成 `lock addl $0,0,(%rsp)` 或 `lock cmpxchg`——`lock` 前缀既保证原子又充当全屏障。所以 x86 上 volatile 写较便宜，volatile 读几乎免费（TSO 内存模型）。

### happens-before（详见 [JMM 专篇](concurrency/jmm-happens-before)）
- volatile 写 happens-before 后续 volatile 读。这是 volatile 可见性的 JMM 层保证。
- volatile 写前的所有普通写，对 volatile 读后的所有普通读可见（因为 StoreStore + LoadLoad 屏障）。

### DCL 单例为什么必须 volatile（高频）
```java
class Singleton {
    private static volatile Singleton instance;  // 必须 volatile
    public static Singleton getInstance() {
        if (instance == null) {
            synchronized (Singleton.class) {
                if (instance == null) {
                    instance = new Singleton();  // 非原子
                }
            }
        }
        return instance;
    }
}
```
- `instance = new Singleton()` 在字节码层是三步：
  1. 分配内存
  2. 调构造器初始化对象
  3. 把引用指向内存地址
- **没有 volatile 时，2 和 3 可能被重排**（JIT 优化），变成 1→3→2。
- 线程 A 执行到 3（已赋值但未初始化），线程 B 第一次 `if (instance == null)` 看到**非 null 但未初始化的对象**，直接 return → 用到半个对象 → NPE 或脏值。
- volatile 禁止 2、3 重排，保证对象完全构造好后才发布。

### volatile 与 synchronized 区别
| 维度 | volatile | synchronized |
| --- | --- | --- |
| 原子性 | ❌（单次读/写原子，复合操作不原子） | ✅ |
| 可见性 | ✅ | ✅ |
| 有序性 | ✅（禁止重排） | ✅（临界区串行） |
| 阻塞 | 不阻塞 | 阻塞 |
| 粒度 | 变量级 | 块/方法级 |
| 适用 | 一写多读标志位、安全发布 | 复合操作临界区 |

## 易错点
- volatile 当原子计数器用 → 多线程 `i++` 丢更新。
- DCL 单例不加 volatile → 偶发拿到半初始化对象。
- 以为 volatile 写一定贵 → x86 上 `lock` 前缀成本可接受，读几乎免费。

## 延伸

## 延伸

- 关联题：[[concurrency/jmm-happens-before]]
- 关联题：[[concurrency/dcl-singleton-volatile-why]]
- 关联题：[[concurrency/synchronized-vs-reentrantlock]]
- 关联题：[[concurrency/cas-mechanism]]
