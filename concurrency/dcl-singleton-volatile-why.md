---
type: question
id: concurrency/dcl-singleton-volatile-why
title: DCL 单例为什么必须 volatile
category: concurrency
subcategory: concurrency
difficulty: medium
tags: [dcl, singleton, volatile, instruction-reorder, concurrency]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-05-26
---

# DCL 单例为什么必须 volatile

## 问题描述

双重检查锁 (DCL) 单例的 instance 字段为什么要加 volatile？不加会出什么问题？

## 解答

### DCL 写法
```java
class Singleton {
    private static volatile Singleton instance;   // volatile 必须
    public static Singleton getInstance() {
        if (instance == null) {                    // 第一次检查，无锁
            synchronized (Singleton.class) {
                if (instance == null) {            // 第二次检查，防重复创建
                    instance = new Singleton();
                }
            }
        }
        return instance;
    }
}
```

### 为什么需要 volatile（核心）
`instance = new Singleton()` 在字节码/JIT 层不是原子的，分三步：
1. 分配对象内存
2. 调用构造器，初始化对象字段
3. 把 `instance` 引用指向内存地址

**没有 volatile 时，JIT 可能重排 2 和 3**（1→3→2），因为单线程内重排不影响结果。

### 不加 volatile 的故障
- 线程 A 执行到 1→3（已赋值，但对象未初始化完）。
- 线程 B 第一次 `if (instance == null)`：**`instance != null`**（看到非 null），直接 `return instance`。
- 线程 B 拿到的是**半初始化对象**（字段是默认值/null），使用时 NPE 或脏值。
- 这个 bug 是**偶发**的，难复现，压测或生产偶现崩溃。

### volatile 怎么解决
- volatile 写前插 `StoreStore` 屏障 → 禁止 2（普通写/构造器写）与 3（volatile 写）重排。
- volatile 写后插 `StoreLoad` 屏障 → 保证写对后续读可见。
- 结果：1→2→3 顺序固定，对象完全初始化后才发布，其他线程要么看到 null，要么看到完整对象。

### DCL 的其他要点
- **两次检查都必要**：第一次避免已创建对象每次都进同步块（性能）；第二次防多线程同时通过第一次检查后重复创建。
- **锁用 class 对象**（`Singleton.class`），静态字段属于 Class。
- 1.5 之后 volatile 语义完善（JSR-133），DCL 才真正可靠；1.4 之前 volatile 语义弱，DCL 仍不安全。

### 更好的替代
- **静态内部类持有**（推荐，无 volatile）：
  ```java
  class Singleton {
      private Singleton() {}
      private static class Holder { static final Singleton INSTANCE = new Singleton(); }
      public static Singleton getInstance() { return Holder.INSTANCE; }
  }
  ```
  类加载时初始化，JVM 保证类初始化线程安全（`<clinit>` 加锁），且延迟到首次 `getInstance` 才加载 Holder。
- **枚举单例**（Effective Java 推荐）：天然线程安全、防反射、防序列化。

## 易错点
- 不加 volatile → 偶发半初始化对象，难复现。
- 以为 synchronized 就够了 → synchronized 保证原子与可见性，但不禁止重排（2 和 3 在锁内仍可重排）。
- 第一次检查不在锁内读 instance → 没 volatile 时连可见性都不保证，更危险。

## 延伸

## 延伸

- 关联题：[[concurrency/volatile-principle]]
- 关联题：[[concurrency/jmm-happens-before]]
- 关联题：[[concurrency/synchronized-vs-reentrantlock]]
