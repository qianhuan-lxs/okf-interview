---
type: question
id: languages/java/jvm-memory-structure
title: JVM 内存结构 (堆/元空间/栈/直接内存 + JDK8 永久代消失)
category: languages
subcategory: java
difficulty: medium
tags: [jvm, memory-model, metaspace, permgen, direct-memory, java]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-07-05
---

# JVM 内存结构 (堆/元空间/栈/直接内存 + JDK8 永久代消失)

## 问题描述

JVM 内存结构有哪些区域？各存什么？哪个区域对应哪种 OOM？JDK8 永久代为什么去掉？

## 解答

## 一、JVM 运行时数据区（JVM 规范）

| 区域 | 线程共享 | 存什么 | OOM 类型 |
| --- | --- | --- | --- |
| **堆 Heap** | ✅ 共享 | 对象实例、数组 | `Java heap space` / `GC overhead` |
| **方法区 Method Area** | ✅ 共享 | 类元信息、常量池、静态变量 | JDK7- `PermGen space`；JDK8+ `Metaspace` |
| **虚拟机栈 VM Stack** | ❌ 线程私有 | 栈帧（局部变量、操作数栈、动态链接、返回地址） | `StackOverflowError` / OOM |
| **本地方法栈 Native Stack** | ❌ 线程私有 | native 方法栈帧 | 同上 |
| **程序计数器 PC** | ❌ 线程私有 | 当前线程执行字节码地址 | 唯一不会 OOM |
| **直接内存 Direct Memory** | ❌（NIO 堆外） | `ByteBuffer.allocateDirect` | `Direct buffer memory` |

## 二、堆（Heap）
- 所有对象实例、数组（不含栈上分配优化的逃逸对象）。
- 分新生代（Eden+S0+S1）+ 老年代。
- `-Xms` 初始堆、`-Xmx` 最大堆（生产建议 `Xms==Xmx` 避免动态扩缩开销）。
- `-Xmn` 新生代大小（或 `-XX:NewRatio=2` 老:新=2:1）。

## 三、方法区 / 元空间（重点变化）
- 存：**类元信息**（类的字段/方法/字节码）、**运行时常量池**（String 常量池、Class 常量池解析后）、**静态变量**（JDK7 移到堆）、JIT 编译的本地代码（CodeCache 另算）。
- **JDK 7 及之前**：方法区实现 = **永久代 PermGen**（在堆中，`-XX:MaxPermSize` 固定上限）。
- **JDK 8+**：永久代移除，方法区实现 = **元空间 Metaspace**（**在本地内存/堆外**，`-XX:MaxMetaspaceSize` 默认无上限，受物理内存限制）。
- **为什么去掉永久代**：
  1. 永久代固定大小易 OOM（`PermGen space`），调优难。
  2. 元空间用本地内存，上限大，难溢出（仍可能，动态类生成）。
  3. 与 JRockit 合并的产物（JRockit 没 PermGen）。
- **String 常量池**：JDK7 从永久代移到堆（永久代 GC 频率低，String intern 易泄漏）。

## 四、虚拟机栈
- 每个方法调用 = 压一个**栈帧**：局部变量表 + 操作数栈 + 动态链接 + 方法返回地址。
- `-Xss` 栈大小（默认 512KB~1MB）。
- 递归过深 → `StackOverflowError`；栈太小或线程太多 → OOM（unable to create native thread）。

## 五、程序计数器（PC）
- 唯一不会 OOM 的区域——每线程一小块存当前字节码地址。

## 六、直接内存（Direct Memory）
- 不归 JVM 堆管，NIO `ByteBuffer.allocateDirect` 分配的堆外内存，**零拷贝**（绕过堆→native 复制）。
- 受 `-XX:MaxDirectMemorySize` 限制（默认约等于 `Xmx`）。
- 通过 `Cleaner`（虚引用 + ReferenceQueue）回收，**不立即释放**，泄漏难发现。
- Netty / Kafka / RPC 框架大量用。

## 七、对象在堆 vs 栈（逃逸分析优化）
- JIT 逃逸分析若判定对象不逃逸出方法 → **栈上分配**（标量替换）+ **同步消除**。
- 栈上分配的对象随栈帧出栈自动回收，不进堆、不 GC——降低 GC 压力。

## 八、容器场景
- `-Xmx` + Metaspace + DirectMemory + 线程栈 + JIT CodeCache + JVM 自身 < 容器 memory limit。
- JDK 8u191+ / JDK10+ 默认感知 cgroup；老 JDK8 不感知，`Xmx` 不设按宿主机算。

## 易错点
- 以为静态变量在方法区 → JDK7 起移到堆。
- 以为元空间在堆 → 在本地内存（堆外）。
- 把"JVM 内存结构"和"JMM 主内存/工作内存"混 → 前者是运行时数据区，后者是并发可见性模型，两回事。
- `Xmx` 设满容器内存 → OOM Killer。

## 延伸

## 延伸

- 关联题：[[languages/java/jvm-garbage-collection]]
- 关联题：[[languages/java/jvm-oom-analysis]]
- 关联题：[[concurrency/jmm-happens-before]]
