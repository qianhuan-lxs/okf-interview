---
type: question
id: languages/java/jvm-oom-analysis
title: OOM 分析 (7 种类型 / 排查流程 / 工具 / 容器)
category: languages
subcategory: java
difficulty: hard
tags: [oom, jvm, heap-dump, mat, arthas, java, troubleshooting]
languages: [java]
role: [sde, backend]
companies: [恩士讯]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-07-05
---

# OOM 分析 (7 种类型 / 排查流程 / 工具 / 容器)

## 问题描述

OOM 有哪些类型？怎么排查？具体流程？线上怎么处理？容器场景要注意什么？

## 解答

## 一、保留现场（第一步，最关键）

JVM 启动参数：
```
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/data/oom-${date}.hprof
-XX:OnOutOfMemoryError="kill -9 %p"   # 可选：OOM 后杀进程触发重启
```
- **容器场景**：dump 路径要挂 PV（emptyDir 会随 Pod 销毁）；dump 文件可能等于堆大小，磁盘要够。
- 自动 dump + 告警 + 拉日志，是生产标配。

## 二、7 种 OOM 类型（必背）

| OOM 信息 | 触发区域 | 常见原因 |
| --- | --- | --- |
| `Java heap space` | 堆 | 大对象、内存泄漏、堆太小、大结果集 |
| `GC overhead limit exceeded` | 堆 | GC 回收 <2% 但耗时 >98%，泄漏濒临 OOM |
| `Metaspace` | 元空间 | 动态类生成（CGLIB/反射/动态代理）、类不卸载 |
| `Direct buffer memory` | 堆外 | NIO `ByteBuffer.allocateDirect` 泄漏、未释放 |
| `unable to create new native thread` | native | 线程数超系统上限（`ulimit -u` / `max user processes`）、线程泄漏 |
| `Requested array size exceeds VM limit` | 堆 | `new byte[Integer.MAX_VALUE]` 超数组上限 |
| `Out of swap space` / `Out of memory: kill process` | OS | 物理内存+swap 耗尽，OOM Killer 杀进程 |

## 三、排查流程（5 步）

### 1. 看 OOM 信息，定位类型
日志第一行 `java.lang.OutOfMemoryError: <类型>` 决定方向。堆/元空间/堆外/线程，排查手段不同。

### 2. 拿 dump
- 自动 dump（已配 `HeapDumpOnOutOfMemoryError`）。
- 手动：`jcmd <pid> GC.heap_dump /path/dump.hprof` 或 `jmap -dump:format=b,file=... <pid>`。
- 线程 OOM：`jstack <pid>` 看线程数 + 状态。

### 3. 分析 dump（堆/元空间类型）
- **MAT**（首选）：
  - **Leak Suspects** 报告 → 自动找嫌疑。
  - **Dominator Tree** → 按对象支配的内存大小排序，找最大的。
  - **Histogram** → 按类统计实例数和大小，TopN 异常类。
  - **Path to GC Roots** → 看大对象到 GC Root 的引用链，定位泄漏源。
  - **OQL** → SQL 查询对象。
- **Arthas**（线上热查，不开 dump）：`dashboard` / `heapdump` / `vmtool --action getInstances --className ...` / `jad` 反编译。
- **jhat**（老，慢）。
- **JProfiler / YourKit**（商业，好用）。

### 4. 常见根因模式
| 模式 | 表现 | 定位 |
| --- | --- | --- |
| 静态集合无限增长 | HashMap 越来越大 | Histogram 找 Map/Entry 实例爆炸 |
| ThreadLocal 线程池泄漏 | 线程长生 + value 强引用 | 看 `ThreadLocalMap$Entry` 数 |
| 连接/Statement 未关闭 | Connection/PreparedStatement 堆积 | 看驱动类实例 |
| 大结果集一次查回 | byte[] / String 巨大 | Dominator Tree 看大对象 |
| 动态类生成不卸载 | Metaspace 涨，ClassLoader 多 | `jcmd class_stats`/MAT 看 ClassLoader 实例 |
| NIO DirectBuffer 泄漏 | 堆外涨、堆里 DirectByteBuffer 增 | `jcmd VM.native_memory` |
| 缓存无淘汰 | 自建 cache 涨 | 用 Caffeine 加 LRU/TTL |
| 第三方库 bug | 特定版本 | 升级 / 二分定位 |

### 5. 验证
- 修复后压测 + 监控堆/元空间/堆外增长曲线 + GC 日志。
- 加阈值告警：老年代占用 > 85% / Metaspace > 80% / DirectBuffer 增长。

## 四、各类 OOM 的针对性排查

### 堆 OOM
- 看是不是堆太小（`-Xmx`）→ 先调大验证。
- 看是不是瞬时大对象（大 SQL/大文件全读）→ 分页/流式。
- 看是不是泄漏 → MAT Path to GC Roots。

### GC overhead
- 通常堆快满了但还能挣扎，是堆 OOM 的前兆。同堆 OOM 排查。
- 可临时 `-XX:-UseGCOverheadLimit` 关掉它，但治标不治本。

### Metaspace
- `-XX:MaxMetaspaceSize` 设小了 → 调大。
- 动态类生成（CGLIB/AspectJ/反射）→ 看是否类不卸载（ClassLoader 泄漏）。
- `jcmd <pid> GC.class_stats` 看类和 ClassLoader 分布（需 unlock commercial）。

### Direct buffer
- `jcmd <pid> VM.native_memory summary` 看 Native Memory Tracking（需 `-XX:NativeMemoryTracking=summary`）。
- 检查 NIO `ByteBuffer.allocateDirect` 是否在 try-with-resources / Cleaner 释放。
- `-XX:MaxDirectMemorySize` 限制。

### Native thread
- `ulimit -u` 看用户进程/线程上限；`/proc/<pid>/status` 看 Threads。
- 线程泄漏：`jstack` 连续打几次，看线程数是否单调增。
- 线程池 max 配置过大或没拒绝策略 → 任务堆积建线程。

## 五、容器场景特别注意

- **cgroup 内存限制**：`-Xmx` 必须 < 容器 memory limit（留余量给元空间/线程栈/直接内存/JVM 自身）。
  - 推荐：`-Xmx` ≤ 容器内存的 75%；剩余给 Metaspace + DirectBuffer + 线程栈 + JIT + native。
- **JDK 8u191+ / JDK 10+**：JVM 默认感知 cgroup（`+UseContainerSupport`），`-Xmx` 不设会按 cgroup 算。老 JDK 8 不感知 cgroup，`-Xmx` 不设会按宿主机算 → 容器 OOM Killer 杀进程。
- **OOM Killer**：Linux 内核杀进程（`dmesg | grep -i kill`），日志无 Java 堆栈 → 是 `Out of memory: kill process`。
- **dump 挂载**：`HeapDumpPath` 必须挂 PV，否则 Pod 重启 dump 丢失。

## 六、预防

- 上线加 `-XX:+HeapDumpOnOutOfMemoryError` + PV dump 路径 + 告警。
- 监控：堆/元空间/堆外/线程数/GC 停顿/频率。
- 代码规范：缓存用 Caffeine（LRU+TTL）、连接用 try-with-resources、ThreadLocal `finally remove`、分页查 SQL。
- 压测找上限。
- `-XX:NativeMemoryTracking=summary` 开 NMT（约 5%~10% 开销，按需开）。

## 易错点
- dump 随容器销毁 → 挂 PV。
- `-Xmx` 设满容器内存 → OOM Killer 杀（没留余量给非堆）。
- 老 JDK 8 不感知 cgroup → `Xmx` 不设按宿主机算。
- 只看堆不看 DirectBuffer/Metaspace → 漏诊。
- Native thread OOM 当堆 OOM 排查 → 方向错。

## 延伸

## 延伸

- 关联题：[[languages/java/jvm-garbage-collection]]
- 关联题：[[languages/java/jvm-memory-structure]]
- 关联题：[[concurrency/threadlocal-usage-pitfalls]]
- 关联题：[[concurrency/thread-pool-principles]]
