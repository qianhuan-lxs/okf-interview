---
type: question
id: languages/java/jdk-version-optimization-survey
title: JDK 各版本优化总览 (8→25, JVM/GC/性能)
category: languages
subcategory: java
difficulty: hard
tags: [jdk, version, gc, jvm, optimization, lts, zgc, compact-headers, java]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-07-05
---

# JDK 各版本优化总览 (8→25, JVM/GC/性能)

## 问题描述

每个 JDK 版本（8 到 25）优化了什么？哪些是 LTS？JVM/GC 层的关键演进？

## 解答

按版本顺序，**重点标注 JVM/GC/性能优化**（语法/API 仅列关键）。**LTS**：8 / 11 / 17 / 21 / 25。

## JDK 8（2014，LTS）
- **PermGen 移除 → Metaspace**（堆外）：解决永久代 OOM 调优难。
- Lambda / Stream / Optional / default methods / 新日期 API。
- Nashorn JS 引擎；Compact Profiles（`compact1/2/3`）。
- **Parallel Scavenge + Parallel Old 默认**（重吞吐）。

## JDK 9（2017）
- **JPMS 模块系统**（Project Jigsaw）：`module-info.java`，封装 JDK 内部。
- **G1 还不是默认**（JDK9 才默认）——本版 G1 成为默认（替换 Parallel）。
- **JEP 254 Compact Strings**：`String` 内部 `char[]` → `byte[]` + coder 标记，**字符串内存减半**（ASCII 场景）。
- **JEP 158 统一日志**：`-Xlog:gc*` 替代各 GC 各自的日志格式。
- **AOT 编译器 jaotc**（实验）。
- jshell / jlink（自包含运行时镜像）。

## JDK 10（2018）
- **var 局部变量类型推断**。
- **JEP 307 G1 Full GC 并行化**：Full GC 不再单线程（Serial Old），大幅降低 Full GC STW。
- **JEP 304 Heap on Alternative Memory Devices**：堆可放 NVMe/DRAM。
- **JEP 310 AppCDS**：应用类数据共享，加速启动。
- **JEP 312 Thread-Local Handshakes**：在非 safepoint 点回调线程，降低某些操作 STW。

## JDK 11（2018，LTS）
- **JEP 333 ZGC 实验性引入**：低延迟并发 GC，TB 级堆，<10ms STW。
- **JEP 318 Epsilon GC**：no-op GC（不回收，纯分配），用于性能测试/短生命周期 job。
- **JEP 328 Flight Recorder 开源**：JFR 低开销持续 profiling（之前 Oracle 商业）。
- **JEP 181 Nest-Based Access Control**：嵌套成员访问（编译器生成的访问桥接优化）。
- HTTP Client（标准）/ var 用于 lambda 参数。

## JDK 12（2019）
- **G1 Abortable Mixed Collections**（JEP 344）：混合回收可中止，避免超停顿目标。
- **G1 及时归还未用堆内存**（JEP 346）：空闲堆还给 OS（容器友好）。
- Switch 表达式预览。

## JDK 13（2019）
- **ZGC 归还未用内存**（JEP 351）。
- Socket API 重写（NIO 实现）。
- Text Blocks 预览。

## JDK 14（2020）
- **JEP 363 CMS 移除**：结束 CMS 时代。
- **JEP 375 G1 NUMA 感知**：多 NUMA 节点 Region 分配提升本地性。
- **JEP 379 ZGC macOS/Windows 支持**。
- Records / Pattern Matching instanceof 预览；Switch 表达式正式。

## JDK 15（2020）
- **JEP 377 ZGC Production-Ready**：ZGC 转正（生产可用）。
- **JEP 379 Shenandoah Production-Ready**：Shenandoah 转正。
- **JEP 384 偏向锁默认禁用**（JEP 374）：现代多核收益递减，撤销的 safepoint 开销反而拖累。
- Text Blocks 正式；Sealed Classes 预览；Nashorn 移除。

## JDK 16（2021）
- **JEP 376 ZGC 并发线程栈扫描**：进一步降低 ZGC STW。
- Records / Pattern Matching instanceof / Sealed Classes 正式。
- jpackage（原生安装包）正式；Alpine Linux 移植。

## JDK 17（2021，LTS）
- **JEP 396 强封装 JDK 内部**：默认封锁 `--add-opens`，反射访问 JDK 私有 API 受限（影响 Lombok/ReflectASM/早期 Spring AOP）。
- **JEP 411 Security Manager 弃用**：逐步废弃，未来用 module。
- **Foreign Function & Memory API 孵化**（替代 JNI）。
- ZGC 进一步稳定（支持 16GB~16TB 堆）。
- Pattern Matching for instanceof 正式（16 已正式）+ Sealed 正式。
- Spring Boot 3 要求 17+。

## JDK 18（2022）
- **JEP 400 默认 UTF-8**：`Charset.defaultCharset()` 不再依赖平台编码。
- Simple Web Server（`jwebserver`）；Code Snippets in Javadoc。
- Vector API 孵化；Internet-Address 重写序列化。

## JDK 19（2022）
- **JEP 425 Virtual Threads 预览**：协程式轻量线程，百万并发。
- Structured Concurrency 孵化；Pattern Matching for Switch 预览。

## JDK 20（2023）
- Virtual Threads 二次预览；Scoped Values 孵化；Record Patterns 预览。

## JDK 21（2023，LTS）—— 重大
- **JEP 444 Virtual Threads 正式**：百万并发线程，IO 密集场景革命。
- **JEP 439 Generational ZGC**：ZGC 加分代（需 `-XX:+ZGenerational` 显式开），吞吐/尾延迟显著优于单代。
- **JEP 451 Generational Shenandoah**（实验，后续 JEP 404 在 JDK24）。
- Pattern Matching for Switch 正式；Record Patterns 正式；Sequenced Collections。
- String Templates 预览（后撤回）。

## JDK 22（2024）
- **JEP 456 Unnamed Variables & Patterns**（`_`）。
- **JEP 454 Foreign Function & Memory API 正式**：替代 JNI。
- Unnamed Classes & Instance Main Methods 预览（简化入门）。

## JDK 23（2024）
- **JEP 474 Generational ZGC 默认**：`-XX:+UseZGC` 默认走分代，非代际废弃待移除。
- **JEP 477 Compact Source Files & Instance Main Methods**（预览）。
- Markdown Javadoc；Primitive Patterns 预览；Vector API。

## JDK 24（2025）
- **JEP 490 ZGC 移除非代际模式**：ZGC 只有分代一种。
- **JEP 450 Compact Object Headers 实验**：MarkWord + KlassPtr 合并到 64 bit（96→64），堆降 10%~20%。
- **JEP 404 Generational Shenandoah 实验**：Shenandoah 加分代。
- AOT 探索继续。

## JDK 25（2025-09，LTS）—— 最新 LTS
- **JEP 519 Compact Object Headers 转产品**（`-XX:+UseCompactObjectHeaders`，默认关，JEP 534 计划 JDK27 默认开）。
- **JEP 521 Generational Shenandoah 转产品**（仍非默认）。
- **JEP 503 移除 32 位 x86 端口**。
- **JEP 514/515 AOT 命令行 + AOT 方法 profiling**：AOT 复活，目标改善启动（函数计算/Spring Boot）。
- **JEP 509 JFR CPU-Time Profiling**（实验）/ **JEP 518 JFR Cooperative Sampling**：JFR 增强。
- **JEP 506 Scoped Values 正式**；Structured Concurrency 第五次预览；Primitive Patterns 第三次预览。
- Module Import Declarations；Compact Source Files & Instance Main Methods 正式。

## GC 选型总览
| 场景 | 推荐 |
| --- | --- |
| 通用默认 | G1（JDK9+ 默认） |
| 超大堆 + 极低延迟 | ZGC（JDK25 默认分代，<1ms） |
| 低延迟备选 | Shenandoah（JDK25 可分代） |
| 高吞吐小堆 | Parallel（JDK8 默认） |
| 测试/短 job | Epsilon |

## 升级路径建议
- 8 → 17：最大收益（ sealed/records/ZGC/强封装 ），Spring Boot 3 要求 17。
- 17 → 21：Virtual Threads + Generational ZGC，IO 密集受益大。
- 21 → 25：Compact Object Headers（省内存）+ Generational ZGC 默认 + AOT 启动优化。

## 易错点
- 以为 ZGC 一定更快 → 吞吐低于 G1，CPU bound 慎用。
- 以为 JDK25 Compact Headers 默认开 → 默认关，需显式开。
- 堆设 32GB 关压缩反而更费 → 31GB 可能比 32GB 可用空间大。
- 升 JDK17 老 Lombok/Spring AOP 报反射错 → 强封装，加 `--add-opens` 或升级库。

## 延伸

## 延伸

- 关联题：[[languages/java/jvm-garbage-collection]]
- 关联题：[[languages/java/g1-gc-changes]]
- 关联题：[[languages/java/jvm-object-layout-jit]]
- 关联题：[[languages/java/jvm-oom-analysis]]
- 关联题：[[languages/java/jdk17-new-features]]
