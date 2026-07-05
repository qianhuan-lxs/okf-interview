---
type: question
id: languages/java/jvm-garbage-collection
title: JVM 垃圾回收 (判活 / 算法 / 收集器 / GC roots)
category: languages
subcategory: java
difficulty: hard
tags: [jvm, gc, reachability, g1, zgc, shenandoah, java]
languages: [java]
role: [sde, backend]
companies: [恩士讯, 海颐]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-07-05
---

# JVM 垃圾回收 (判活 / 算法 / 收集器 / GC roots)

## 问题描述

JVM 怎么判定对象为垃圾？GC 算法有哪些？各垃圾收集器区别？G1/ZGC 怎么工作？

## 解答

## 一、判活：可达性分析（不用引用计数）

引用计数有循环引用问题（A↔B 互引但都该回收），JVM 不用。**可达性分析**：从 GC Roots 沿引用链遍历，可达=活，不可达=垃圾。

### GC Roots（必背完整版）
1. **虚拟机栈帧**中的局部变量、操作数栈引用（方法运行时的对象）。
2. **方法区**中类静态变量、常量引用（`static` 字段、`String` 常量池）。
3. **本地方法栈** JNI 引用（Java 调 native 持有的对象）。
4. **同步锁**持有的对象（`synchronized` 持锁对象）。
5. **JVM 内部引用**（基本类型异常对象、类加载器、UUID 等）。
6. JFR/Agent 等 JVMTI 工具临时 root。

### 引用强度（决定回收时机）
| 类型 | 回收时机 | 用途 |
| --- | --- | --- |
| 强引用 | 永不（除非置 null） | 普通引用 `Object o = new ...` |
| 软引用 SoftReference | 内存不足时 | 缓存（可被回收换内存） |
| 弱引用 WeakReference | 下次 GC 必回收 | WeakHashMap、ThreadLocal 的 key |
| 虚引用 PhantomReference | 随时（get 永远 null） | 跟踪对象被回收的时机，配合 ReferenceQueue |

## 二、分代内存布局（HotSpot）

```
堆 (Heap)
├── 新生代 (Young) = Eden : S0 : S1 = 8 : 1 : 1  (-XX:SurvivorRatio=8)
│   └── 朝生夕死，复制算法
└── 老年代 (Old)
    └── 长期存活对象，标记-整理 / G1 region
```
- 新对象 → Eden（大对象直接进老年代 `-XX:PretenureSizeThreshold`）。
- Minor GC：Eden 满 → 存活进 S0/S1，年龄 +1。**Survivor 区其中一个始终空**（复制算法用）。
- 晋升老年代：`-XX:MaxTenuringThreshold=15`（默认 15），年龄达标进老年代；或 Survivor 空间不足**动态年龄计算**（同龄对象超 Survivor 一半则该龄以上全晋升）。
- Major GC / Full GC：老年代 / 元空间触发，STW 久。

## 三、GC 算法

| 算法 | 过程 | 优缺 | 用在哪 |
| --- | --- | --- | --- |
| 标记-清除 | 标记存活→清除未标记 | 碎片多、效率低 | CMS 老年代 |
| 复制 | 存活对象复制到另一半→清原区 | 无碎片、快、费空间（要空一半） | 新生代 |
| 标记-整理 | 标记→存活向一端移动→清边界外 | 无碎片、慢（要移动） | 老年代 |
| 分代 | 新生代复制 + 老年代标记整理 | 综合最优 | HotSpot 默认布局 |
| Region 化 (G1) | 堆分 Region，回收垃圾最多的 | 可控停顿、无碎片 | G1 |

## 四、垃圾收集器演进与对比

| 收集器 | 作用域 | 算法 | 并发 | STW | 适用 |
| --- | --- | --- | --- | --- | --- |
| Serial / Serial Old | 新/老 | 复制/整理 | 单线程 | 长 | 客户端、小堆 |
| ParNew | 新 | 复制 | 多线程并行 | 中 | 配 CMS |
| Parallel Scavenge / Parallel Old | 新/老 | 复制/整理 | 多线程并行 | 中 | JDK8 默认，重吞吐 |
| CMS | 老 | 标记-清除 | **并发标记** | 短但有碎片、Concurrent Mode Failure | 已废弃（JDK14 移除） |
| **G1** | 整堆 | Region + SATB + 复制 | 并发标记 + 并行回收 | 可控停顿 | **JDK9+ 默认** |
| **ZGC** | 整堆 | Region + **染色指针** + 读屏障 | 全并发 | **<1ms** | 大堆低延迟 |
| **Shenandoah** | 整堆 | Brooks 转发指针 + 并发整理 | 全并发 | <10ms | 低延迟 |

## 五、G1 工作机制（详见 [G1 专篇](languages/java/g1-gc-changes)）
- 堆分 ~2048 个 Region（1~32MB），逻辑分代不物理连续，每个 Region 可动态当 Eden/Survivor/Old/Humongous。
- **Garbage First**：优先回收垃圾最多的 Region，用历史数据估算能在 `-XX:MaxGCPauseMillis` 内回收多少。
- **RSet（Remembered Set）**：每个 Region 记录"谁引用了我"，避免全堆扫描；写屏障维护。
- **SATB**：并发标记快照，引用变更通过写屏障记录，保证标记正确性。
- **混合回收**：一次可回收新生代 + 部分老年代 Region。
- 代价：RSet + 卡表约占堆 5%~10%。

## 六、ZGC（染色指针 + 读屏障，重点）
- **染色指针**：在 64 位指针的高位 bit 编码 GC 状态（Marked0/Marked1/Remapped/Finalizable），利用 CPU 硬件位掩码。
- **读屏障**：每次读对象引用时检查指针颜色，若需重定位则修正指针（并发移动对象）。
- 全并发（标记、转移、重定位都并发），STW 仅几次初始标记/再标记，<1ms。
- 支持 TB 级堆。
- **JDK 21 引入 Generational ZGC**（JEP 439，需 `-XX:+ZGenerational`）；**JDK 23 默认**（JEP 474）；**JDK 24 移除非代际**（JEP 490）。

## 七、Shenandoah（Brooks 转发指针）
- 每个对象头多一个转发指针，指向自己或新副本；并发整理时建副本、转发指针指向新副本。
- 与 ZGC 区别：ZGC 用染色指针+读屏障，Shenandoah 用 Brooks 转发指针（每个对象多 8 字节）。
- **JDK 24 引入 Generational Shenandoah 实验**（JEP 404）；**JDK 25 转产品**（JEP 521，仍非默认）。

## 八、GC 触发条件
- Young GC：Eden 满。
- Full GC：老年代满 / 元空间满 / `System.gc()` / 担保失败（Promotion Failure）/ Concurrent Mode Failure (CMS)。
- G1 混合 GC：`-XX:InitiatingHeapOccupancyPercent`（默认 45%）老年代占用超阈值触发并发标记。

## 九、GC 日志与监控
- JDK9+ 统一日志：`-Xlog:gc*:file=gc.log:time,uptime,level,tags`。
- JFR（Flight Recorder）：低开销持续监控。
- 关键指标：停顿时间、GC 频率、回收量、吞吐（应用时间占比）。

## 易错点
- 把"Minor GC"当无 STW → 都有 STW，只是短。
- 以为引用计数能判活 → 循环引用问题，JVM 不用。
- CMS 还能用 → JDK 14 已移除。
- ZGC 一定更快 → 吞吐低于 G1，CPU bound 场景慎用。

## 延伸

## 延伸

- 关联题：[[languages/java/g1-gc-changes]]
- 关联题：[[languages/java/jvm-oom-analysis]]
- 关联题：[[languages/java/jvm-memory-structure]]
- 关联题：[[languages/java/jdk-version-optimization-survey]]
