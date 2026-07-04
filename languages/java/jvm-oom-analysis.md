---
type: question
id: languages/java/jvm-oom-analysis
title: OOM 分析过程
category: languages
subcategory: java
difficulty: medium
tags: [oom, jvm, heap-dump, java, troubleshooting]
languages: []
role: [ai-app, sde, backend]
companies: [恩士讯]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# OOM 分析过程

## 问题描述
怎么分析 OOM 的？具体过程？

## 解答

### 第一步：保留现场
- JVM 启动参数加 `-XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/var/log/oom.hprof`，OOM 时自动 dump。
- 容器场景挂 PV，避免 dump 随容器销毁。

### 第二步：定位 OOM 类型
| 类型 | 触发 | 常见原因 |
| --- | --- | --- |
| `Java heap space` | 堆满 | 大对象、内存泄漏、堆太小 |
| `GC overhead limit` | GC 回收 <2% 但耗时 >98% | 内存泄漏 |
| `Metaspace` | 元空间满 | 动态类生成（CGLIB/反射） |
| `Direct buffer memory` | 堆外内存满 | NIO ByteBuffer 泄漏 |
| `unable to create new native thread` | 线程数超限 | 线程泄漏 |

### 第三步：分析 hprof
- **MAT (Memory Analyzer)**：打开 hprof → 看 Dominator Tree 找最大对象 → Leak Suspects 报告 → 查 GC Root 引用链。
- **Arthas**（线上热查）：`dashboard / heapdump / vmtool`。
- **jmap -histo:live | head`**：快速看对象 TopN。

### 第四步：常见根因
- 静态集合无限增长（缓存无淘汰）。
- ThreadLocal 线程池泄漏。
- 连接/Statement 未关闭。
- 大结果集一次查回。
- 第三方库内存泄漏（如 fastjson 某版本）。

### 第五步：验证
- 修复后压测 + 监控堆增长曲线 + 配 G1/ZGC 日志 `-Xlog:gc*`。

## 延伸

## 延伸

- 关联题：[[languages/java/jvm-garbage-collection]]
- 关联题：[[concurrency/threadlocal-usage-pitfalls]]
