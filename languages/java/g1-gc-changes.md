---
type: question
id: languages/java/g1-gc-changes
title: G1 相对之前回收器的改变
category: languages
subcategory: java
difficulty: medium
tags: [g1, gc, jvm, java]
languages: []
role: [ai-app, sde, backend]
companies: [恩士讯]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# G1 相对之前回收器的改变

## 问题描述
G1 相对之前的回收器有什么改变？

## 解答

### 之前：CMS / Parallel
- 物理分代（新生代/老年代是连续内存段）。
- CMS：并发标记清除，低停顿但**有碎片**、Concurrent Mode Failure 退化为 Serial Old。

### G1（Garbage First）
- **Region 化堆**：堆分成 2048 个左右等大 Region（1~32MB），逻辑分代不物理连续。每个 Region 可动态充当 Eden/Survivor/Old/Humongous。
- **Garbage First**：优先回收垃圾最多的 Region，停顿可控。
- **可预测停顿**：用户设 `-XX:MaxGCPauseMillis`，G1 用历史数据估算能在停顿时间内回收多少 Region。
- **混合回收**：不再严格分新生代/老年代 GC，一次回收可同时含新生代 Region + 部分老年代 Region。
- **RSet（Remembered Set）**：每个 Region 记录"谁引用了我"，避免全堆扫描；用写屏障维护。
- **SATB（Snapshot-At-The-Beginning）**：并发标记阶段，引用变更通过写屏障记录，保证标记正确性。
- 无碎片（Region 整体回收，复制算法）。

### 代价
- 内存开销：RSet + Collection Set 卡表约占堆 5%~10%。
- 写屏障开销。

### JDK 9+ 默认 G1；JDK 17+ ZGC 成熟，超低延迟场景可换 ZGC。

## 延伸

## 延伸

- 关联题：[[languages/java/jvm-garbage-collection]]
- 关联题：[[languages/java/jdk17-new-features]]
