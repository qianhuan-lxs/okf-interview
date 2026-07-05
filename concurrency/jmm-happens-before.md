---
type: question
id: concurrency/jmm-happens-before
title: JMM 与 happens-before 八大原则
category: concurrency
subcategory: concurrency
difficulty: hard
tags: [jmm, happens-before, memory-model, concurrency, java]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-05-26
---

# JMM 与 happens-before 八大原则

## 问题描述

什么是 Java 内存模型 (JMM)？happens-before 是什么？有哪些规则？为什么需要它？

## 解答

### 为什么需要 JMM
- 真实硬件：CPU 多级缓存 + 寄存器 + 指令重排 + 写缓冲区 → 每个线程"看到"的内存视图不一致。
- 没有内存模型，多线程程序行为不可预测（不同 CPU 架构结果不同）。
- **JSR-133 (JMM)** 定义了一套抽象规则，规定在什么条件下一个线程的写对另一个线程可见，以及编译器/CPU 能怎么重排。

### JMM 抽象结构
- **主内存** vs **工作内存**（抽象，对应 CPU 缓存/寄存器）。
- 线程不能直接读写主内存，必须经过工作内存：`read`/`load`/`use`/`assign`/`store`/`write`/`lock`/`unlock` 八大原子操作。
- 这套操作描述太底层，JSR-133 用 **happens-before** 替代表达。

### happens-before 八大规则（必背）
如果一个操作 A happens-before B，则 A 的结果对 B 可见，且 A 的执行顺序先于 B（**语义顺序，不是实际指令顺序**——只要不改变结果，CPU/编译器可重排）。

1. **程序顺序规则**：同一线程内，前面的操作 happens-before 后面的操作（as-if-serial）。
2. **volatile 变量规则**：volatile 写 happens-before 后续对该变量的读。
3. **锁规则（monitor lock）**：unlock happens-before 后续对同一把锁的 lock。
4. **线程启动规则**：`Thread.start()` happens-before 该线程的所有操作（所以启动前赋值的变量对新线程可见）。
5. **线程终止规则**：线程所有操作 happens-before `Thread.join()` 返回（所以 join 后能读到子线程结果）。
7. **线程中断规则**：`Thread.interrupt()` happens-before 被中断线程检测到中断。
7. **对象终结规则**：构造函数执行结束 happens-before `finalize()`。
8. **传递性**：A happens-before B，B happens-before C → A happens-before C。

> 注：编号按 JSR-133 通行表述，实际是 8 条（程序顺序/volatile/锁/启动/终止/中断/终结/传递性）。

### happens-before 不是"执行时序"
- 不是说 A 一定先执行完再执行 B，而是说 **A 的效果对 B 可见，且 A 不被重排到 B 之后**。
- 编译器/CPU 仍可重排，只要不违反 happens-before 关系（结果一致）。

### 实战推导
- 双重检查锁（DCL）：构造函数初始化 `happens-before` 把引用赋给 `instance`（程序顺序规则）→ 加 volatile 后赋值 `happens-before` 外部读（volatile 规则）→ 传递性 → 外部读到完全初始化的对象。

## 易错点
- 把 happens-before 当"执行先后" → 是可见性 + 重排约束，不是时序。
- 忘了传递性 → 无法跨多条规则推导可见性。
- 以为线程 start 前的赋值不可见 → 启动规则保证可见。

## 延伸

## 延伸

- 关联题：[[concurrency/volatile-principle]]
- 关联题：[[concurrency/synchronized-vs-reentrantlock]]
- 关联题：[[concurrency/dcl-singleton-volatile-why]]
