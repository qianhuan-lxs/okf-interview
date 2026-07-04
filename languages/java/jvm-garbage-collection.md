---
type: question
id: languages/java/jvm-garbage-collection
title: JVM 垃圾回收 (可达性分析 / GC)
category: languages
subcategory: java
difficulty: medium
tags: [jvm, gc, reachability, garbage-collection, java]
languages: []
role: [ai-app, sde, backend]
companies: [恩士讯, 海颐]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# JVM 垃圾回收 (可达性分析 / GC)

## 问题描述
JVM 是怎么把对象判定为垃圾的？了解过垃圾回收吗？大概讲一下。

## 解答

### 判活：可达性分析（替代引用计数）
- 通过一系列 **GC Roots** 作为起点，沿引用链遍历，可达 = 活，不可达 = 垃圾。
- 引用计数有循环引用问题，JVM 不用。
- **GC Roots**：
  1. 虚拟机栈帧中的局部变量、操作数栈引用
  2. 方法区中类静态变量、常量引用
  3. 本地方法栈 JNI 引用
  4. 同步锁持有的对象
  5. JVM 内部引用（如基本类型异常对象）

### 回收算法
- **标记-清除**：碎片多。
- **复制**：新生代用， eden + 2 survivor，空间换时间。
- **标记-整理**：老年代用，无碎片但慢。
- **分代**：新生代（朝生夕死，复制算法）+ 老年代（标记整理/G1）。

### 引用强度
强 → 软（内存不足才回收，适合缓存）→ 弱（下次 GC 必回收，WeakHashMap）→ 虚（跟踪回收时机）。

### 垃圾回收器演进
Serial → ParNew → Parallel Scavenge → CMS（并发标记清除，已废弃）→ **G1**（JDK9 默认）→ ZGC / Shenandoah（低延迟）。

## 延伸

## 延伸

- 关联题：[[languages/java/g1-gc-changes]]
- 关联题：[[languages/java/jvm-oom-analysis]]
