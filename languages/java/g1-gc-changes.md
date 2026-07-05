---
type: question
id: languages/java/g1-gc-changes
title: G1 回收器 (Region/RSet/SATB/混合回收/演进)
category: languages
subcategory: java
difficulty: hard
tags: [g1, gc, jvm, region, rset, satb, java]
languages: [java]
role: [sde, backend]
companies: [恩士讯]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-07-05
---

# G1 回收器 (Region/RSet/SATB/混合回收/演进)

## 问题描述

G1 相对之前回收器有什么改变？Region/RSet/SATB 怎么工作？G1 的回收流程？JDK 各版本 G1 优化了什么？

## 解答

## 一、G1 之前的回收器
- **Parallel Scavenge + Parallel Old**（JDK8 默认）：物理分代（新生代/老年代连续内存段），重吞吐，停顿不可控。
- **CMS**：并发标记清除，低停顿但**有碎片**、`Concurrent Mode Failure` 退化为 Serial Old（长 STW）、浮动垃圾。JDK 9 弃用、JDK 14 移除。

## 二、G1 核心设计：Region 化堆

- 堆分成 ~2048 个等大 Region（默认 1~32MB，`-XX:G1HeapRegionSize` 可配）。
- **逻辑分代不物理连续**：每个 Region 可动态充当 Eden / Survivor / Old / **Humongous**（大对象，≥50% Region 大小连续多 Region）。
- **Garbage First**：优先回收垃圾最多的 Region（存活少收益高），用户设 `-XX:MaxGCPauseMillis=200`，G1 用历史数据估算能在停顿时间内回收多少 Region。

## 三、RSet（Remembered Set）——避免全堆扫描
- 问题：并发标记/回收某 Region 时，别的 Region 可能引用它——要扫全堆找跨 Region 引用，开销大。
- 解法：每个 Region 维护一个 RSet，记录"**哪些 Region 的哪些 card 引用了我**"。
- **Card Table**：堆按 512 字节划 card，写引用时**写屏障**把对应 card 标脏，REFINE 线程异步更新 RSet。
- 代价：RSet + card table 约占堆 5%~10%（`-XX:G1RSetRegionCache` 可调）。

## 四、SATB（Snapshot-At-The-Beginning）——并发标记正确性
- 并发标记期间，应用线程可能改引用（如把 A→B 改成 A→C），导致 B 漏标（被回收却仍被引用）。
- **SATB**：标记开始时拍快照，并发期间通过**写屏障**记录"被覆盖的旧引用"（即可能漏标的对象），标记结束时把这些对象当存活处理（哪怕已死，下次再回收——浮动垃圾）。
- 对比 **CMS 的 incremental update**：记录新增引用，结尾重新标记。G1 用 SATB 更稳。

## 五、G1 回收流程

### Young GC（Stop-The-World，必然发生）
- Eden 满 → 选所有 Young Region（Eden+S0/S1）复制到新 Survivor Region，清原 Region。
- 全程 STW，但因只复制存活对象（朝生夕死，少）而快。

### Concurrent Marking（并发，触发混合回收的前提）
- 触发：`-XX:InitiatingHeapOccupancyPercent=45` 老年代占用超阈值。
- 阶段：
  1. **初始标记**（STW，搭一次 Young GC 顺车）——标 GC Roots 直接引用。
  2. **并发标记**——沿引用链标，应用线程继续跑。
  3. **最终标记**（STW）——处理 SATB 缓冲区。
  4. **筛选回收**（STW）——统计各 Region 存活率，按收益排序，选 CSet（Collection Set）。

### Mixed GC（G1 主力）
- 一次回收 = 全部 Young Region + **部分** Old Region（按收益和停顿目标选）。
- 复制存活对象到空 Region，清原 Region——**无碎片**。
- `-XX:G1MixedGCCountTarget=8` 混合回收分多次完成老年代清理。

### Full GC（兜底，要避免）
- Mixed GC 跟不上 / 担保失败 → 退化为单线程 Serial Old Full GC，**很长 STW**。
- JDK 10 起 Full GC 改为**并行**（JEP 307），缓解但还是要避免。

## 六、G1 vs CMS

| 维度 | CMS | G1 |
| --- | --- | --- |
| 堆布局 | 物理分代 | Region 化逻辑分代 |
| 算法 | 标记-清除（碎片） | 复制（无碎片） |
| 停顿可控 | 弱 | 强（`MaxGCPauseMillis`） |
| 漏标策略 | Incremental Update | SATB |
| 跨代引用 | Card Table 全扫 | RSet 精准 |
| Full GC 退化 | Serial Old（单线程） | JDK10+ 并行 |
| 适用 | 小堆低延迟 | 大堆可控停顿 |

## 七、JDK 各版本 G1 优化
- JDK 9：G1 成为默认。
- JDK 10（JEP 307）：**Full GC 并行化**（不再单线程）。
- JDK 11：实验性 Epsilon GC（不回收，测性能用）；G1 可归还未用堆内存给 OS。
- JDK 12：G1 中止混合回收（`Abortable Mixed Collections`）、归还空闲堆。
- JDK 14：**NUMA 感知**（G1 在多 NUMA 节点分配 Region 提升本地性）、CMS 移除。
- JDK 15+：进一步稳定性与性能。
- JDK 17 LTS：ZGC production-ready 后，G1 仍是默认，ZGC 用于超低延迟。

## 八、G1 调优要点
- `-XX:MaxGCPauseMillis=200`：停顿目标（软约束，非保证）。
- `-XX:G1HeapRegionSize`： Region 大小（1/2/4/8/16/32MB，默认按堆自动）。
- `-XX:InitiatingHeapOccupancyPercent=45`：触发并发标记的占用比。
- `-XX:G1ReservePercent=10`：保留空 Region 防担保失败。
- 大堆 + 需要可控停顿 → G1；超大堆 + 极低延迟 → ZGC。

## 易错点
- 以为 G1 没有分代 → 有逻辑分代，只是 Region 化。
- 设 `MaxGCPauseMillis` 太小 → G1 调小 CSet，回收跟不上反而 Full GC。
- 以为 G1 不 Full GC → 跟不上会退化为 Full GC（JDK10+ 并行但仍要避免）。
- 忘 RSet 占内存 → 5%~10% 额外开销。

## 延伸

## 延伸

- 关联题：[[languages/java/jvm-garbage-collection]]
- 关联题：[[languages/java/jdk-version-optimization-survey]]
- 关联题：[[languages/java/jvm-oom-analysis]]
