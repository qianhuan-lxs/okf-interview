#!/usr/bin/env python3
"""JVM deep docs: rewrite 3 shallow + add 4 (memory structure, class loading,
object layout/JIT, per-JDK optimization survey)."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from ikf_writer import q

DATE = "2026-07-05"
SRC = "_interviews/2026-05-louis-ai-java"

# =========================================================================== #
# REWRITES
# =========================================================================== #

q("languages/java/jvm-garbage-collection.md",
  "JVM 垃圾回收 (判活 / 算法 / 收集器 / GC roots)",
  "languages", "java", "hard",
  ["jvm", "gc", "reachability", "g1", "zgc", "shenandoah", "java"],
  ["恩士讯", "海颐"],
  """# JVM 垃圾回收 (判活 / 算法 / 收集器 / GC roots)

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
""",
  languages=["java"], role=["sde", "backend"],
  source=SRC, status="reviewed", timestamp=DATE,
  links=["languages/java/g1-gc-changes",
         "languages/java/jvm-oom-analysis",
         "languages/java/jvm-memory-structure",
         "languages/java/jdk-version-optimization-survey"])

q("languages/java/jvm-oom-analysis.md",
  "OOM 分析 (7 种类型 / 排查流程 / 工具 / 容器)",
  "languages", "java", "hard",
  ["oom", "jvm", "heap-dump", "mat", "arthas", "java", "troubleshooting"],
  ["恩士讯"],
  """# OOM 分析 (7 种类型 / 排查流程 / 工具 / 容器)

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
""",
  languages=["java"], role=["sde", "backend"],
  source=SRC, status="reviewed", timestamp=DATE,
  links=["languages/java/jvm-garbage-collection",
         "languages/java/jvm-memory-structure",
         "concurrency/threadlocal-usage-pitfalls",
         "concurrency/thread-pool-principles"])

q("languages/java/g1-gc-changes.md",
  "G1 回收器 (Region/RSet/SATB/混合回收/演进)",
  "languages", "java", "hard",
  ["g1", "gc", "jvm", "region", "rset", "satb", "java"],
  ["恩士讯"],
  """# G1 回收器 (Region/RSet/SATB/混合回收/演进)

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
""",
  languages=["java"], role=["sde", "backend"],
  source=SRC, status="reviewed", timestamp=DATE,
  links=["languages/java/jvm-garbage-collection",
         "languages/java/jdk-version-optimization-survey",
         "languages/java/jvm-oom-analysis"])

# =========================================================================== #
# NEW
# =========================================================================== #

q("languages/java/jvm-memory-structure.md",
  "JVM 内存结构 (堆/元空间/栈/直接内存 + JDK8 永久代消失)",
  "languages", "java", "medium",
  ["jvm", "memory-model", "metaspace", "permgen", "direct-memory", "java"],
  [],
  """# JVM 内存结构 (堆/元空间/栈/直接内存 + JDK8 永久代消失)

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
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["languages/java/jvm-garbage-collection",
         "languages/java/jvm-oom-analysis",
         "concurrency/jmm-happens-before"])

q("languages/java/jvm-class-loading.md",
  "JVM 类加载 (5 阶段 / 双亲委派 / 破坏双亲委派)",
  "languages", "java", "medium",
  ["jvm", "class-loading", "classloader", "parent-delegation", "java"],
  [],
  """# JVM 类加载 (5 阶段 / 双亲委派 / 破坏双亲委派)

## 问题描述

JVM 类加载过程？双亲委派是什么？为什么有破坏双亲委派？哪些场景破坏？

## 解答

## 一、类加载 5 阶段（加载→验证→准备→解析→初始化）

### 1. 加载
- 通过类的全限定名获取定义此类的二进制字节流（从 jar/class/网络/动态生成）。
- 转为方法区的运行时数据结构；在堆生成 `java.lang.Class` 对象作为方法区数据访问入口。

### 2. 验证
- 文件格式、元数据、字节码、符号引用验证——确保 class 文件安全合规。

### 3. 准备
- **为类静态变量分配内存并设零值**（`static int v = 123` 此刻 v=0，赋值在初始化阶段；`static final` 常量在此阶段就赋值）。

### 4. 解析
- 常量池内的符号引用替换为直接引用（指针/偏移量）。可发生在初始化前（解析）或延迟到首次使用（懒解析）。

### 5. 初始化
- 执行 `<clinit>` 类构造器：按源码顺序执行 `static` 变量赋值 + `static` 块。**线程安全**（JVM 加锁保证一个类只初始化一次）。
- 触发时机：new 实例 / 调静态方法 / 访问静态字段（非 final 常量）/ 反射 / 子类初始化触发父类 / main 类。

## 二、类加载器与双亲委派

### 三层类加载器（JDK 9 前）
| 加载器 | 加载范围 | 实现 |
| --- | --- | --- |
| **Bootstrap ClassLoader**（启动） | `rt.jar`/核心库 | C++ 实现，JVM 一部分，无 Java 对象 |
| **Extension ClassLoader**（扩展） | `ext` 目录 | Java，`ExtClassLoader` |
| **Application ClassLoader**（应用） | classpath | Java，`AppClassLoader` |
- JDK 9 模块化后改为 Bootstrap → Platform ClassLoader → Application。

### 双亲委派模型
- 加载类时**先委托父加载器**加载，父加载不了才自己加载。
- 流程：`AppClassLoader` → 委托 `ExtClassLoader` → 委托 `Bootstrap`；Bootstrap 找不到 → ExtClassLoader 找 → AppClassLoader 找。
- **目的**：
  1. **安全**：防止用户伪造核心类（如自己写 `java.lang.String`，会被 Bootstrap 加载的官方 String 覆盖）。
  2. **唯一性**：同一个类只会被同一个加载器加载一次，保证类型一致（不同加载器加载的同名类是不同 Class）。

## 三、破坏双亲委派（重点面试题）

### 为什么需要破坏
- 双亲委派是"父优先"，但有些场景需要"子优先"或自定义加载顺序。

### 经典破坏场景

#### 1. JDBC（SPI 机制）
- `DriverManager` 在 Bootstrap 加载的核心类里，要用 `Class.forName("com.mysql.cj.jdbc.Driver")` 加载第三方驱动，但第三方驱动在 classpath，Bootstrap 加载不到。
- 解法：**Thread Context ClassLoader**（线程上下文加载器，默认 AppClassLoader）——父加载器反向用子加载器加载 SPI 实现。`ServiceLoader.load(Driver.class)` 用 TCCL。
- 这是"父加载器请求子加载器加载"——经典破坏。

#### 2. Tomcat（Web 应用隔离）
- 一个 Tomcat 跑多个 webapp，它们各自有 `lib`，类要互相隔离（webapp A 的 Spring 4 不影响 webapp B 的 Spring 5）。
- Tomcat 自定义 `WebappClassLoader`，**每个 webapp 一个**，**先自己加载（webapp WEB-INF/classes 和 lib）再委托父**——破坏双亲委派。
- 但核心类（`java.lang.*`）仍走双亲委派，避免被覆盖。

#### 3. OSGi（模块化）
- OSGi 用网状类加载器，每个 bundle 一个，可指定导入导出——彻底打破双亲委派的树状结构。

#### 4. 热部署 / 热加载
- 修改 class 后新建 ClassLoader 重新加载类——旧 ClassLoader 不可复用（已加载类不可卸载，除非加载器卸载）。
- JRebel / arthas redefine / Spring DevTools 用此机制。

## 四、类初始化顺序（高频）
1. 父类静态变量 + 静态块（按源码顺序）。
2. 子类静态变量 + 静态块。
3. 父类实例变量 + 实例块。
4. 父类构造函数。
5. 子类实例变量 + 实例块。
6. 子类构造函数。

## 易错点
- 以为 `static int v = 123` 在准备阶段赋值 → 准备阶段设零值，赋值在初始化。
- 以为双亲委派绝对安全 → SPI/Tomcat/OSGi 都要破坏。
- 不同加载器加载同名类当同一个 → 是不同 Class，`instanceof` 不通过。
- 以为类能卸载 → 只有加载该类的 ClassLoader 卸载时类才卸载（连同其 Class 对象）。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["languages/java/jvm-memory-structure",
         "languages/java/jvm-object-layout-jit",
         "languages/java/jvm-garbage-collection"])

q("languages/java/jvm-object-layout-jit.md",
  "对象内存布局 + JIT 执行引擎 (MarkWord/指针压缩/C1C2/逃逸分析)",
  "languages", "java", "hard",
  ["jvm", "object-layout", "markword", "jit", "escape-analysis", "java", "compact-headers"],
  [],
  """# 对象内存布局 + JIT 执行引擎 (MarkWord/指针压缩/C1C2/逃逸分析)

## 问题描述

JVM 对象在内存里长什么样？指针压缩怎么省内存？JIT 怎么执行字节码？C1/C2/Graal 区别？逃逸分析能优化什么？

## 解答

## 一、对象内存布局（64 位 JVM）

一个对象 = **对象头（Header）+ 实例数据（Instance Data）+ 对齐填充（Padding）**。

### 对象头（HotSpot）
- **Mark Word**（64 bit）：存 hashCode / GC 分代年龄 / 锁状态（无锁/偏向/轻量/重量，详见 [synchronized 锁升级](concurrency/synchronized-lock-escalation)）。
- **Klass Pointer**（类元数据指针）：指向方法区该类的元数据。
  - 开指针压缩（`-XX:+UseCompressedOops`，默认开且堆 <32GB）→ 32 bit；否则 64 bit。
- 数组对象额外 4 字节存数组长度。

### 实例数据
- 字段值，按类型宽度排（long/double 8B、int 4B...）。
- **字段重排序**：HotSpot 按字段类型宽度降序 + 父类字段在前，减少 padding。
- `-XX:-UseCompressedOops` 关闭指针压缩，引用字段 8B；开启 4B。

### 对齐填充
- 对象大小必须 8 字节整数倍（`-XX:ObjectAlignmentInBytes=8`），不足补齐。

### 一个空对象多大
- 普通对象：MarkWord(8) + KlassPtr(4 压缩) = 12B → 对齐到 **16B**。
- 关压缩：MarkWord(8) + KlassPtr(8) = 16B。
- 数组：16B 头 + 元素。

### JDK 24/25 Compact Object Headers（重要新优化）
- **JEP 450（JDK24 实验）/ JEP 519（JDK25 产品）**：把 MarkWord + KlassPtr **合并压缩到 64 bit**（96→64 bit），最小对象头从 12B 降到 8B。
- 堆大小降 10%~20%，GC 压力随之降（扫的对象头小了）。
- JDK25 用 `-XX:+UseCompactObjectHeaders` 开启（默认关，JDK 27 计划默认开，JEP 534）。
- 对 MarkWord 锁状态、GC 年龄做了重新编码，与 Project Valhalla（值类型）兼容。

## 二、指针压缩（UseCompressedOops）
- 64 位指针 8 字节，引用密集时浪费。堆 <32GB 时用 32 位指针 + 8 字节对齐偏移寻址，覆盖 32GB。
- `-XX:+UseCompressedOops`（默认开，堆 ≥32GB 自动关）。
- 节省堆 30%~50%（引用字段多时）。
- 堆 ≥32GB 关压缩 → 引用变 8B → 堆反而可能更费（"32GB 陷阱"：32GB 堆可用空间可能不如 31GB）。

## 三、JIT 执行引擎

JVM 字节码先**解释执行**（启动快），热点代码由 **JIT 编译为本地机器码**（跑得快）。

### 分层编译（Tiered Compilation，JDK 8 默认）
- **解释器** → C1 → C2，按热度升级。
- **C1（Client Compiler）**：快速编译，简单优化（方法内联、少数优化），适合短生命周期应用/启动敏感。
- **C2（Server Compiler）**：慢编译，激进优化（逃逸分析、标量替换、循环展开、锁消除、分支预测），适合长期运行。
- `-XX:TieredStopAtLevel=1` 只用 C1（启动敏感）；`-XX:-TieredCompilation` 关分层。

### Graal（JDK 10+）
- 用 Java 写的 JIT（C2 的替代/补充），`-XX:+UseJVMCICompiler`。
- 更激进的优化，但启动慢、稳定性仍演进。GraalVM 原生镜像基于它做 AOT。

### 触发编译
- **热点探测**：方法调用计数器 + 回边计数器，超阈值 `-XX:CompileThreshold`（C2 默认 10000）触发编译。
- 方法栈上替换（OSR）：长循环中途编译切换。

## 四、JIT 经典优化

### 1. 方法内联（最重要的优化）
- 把被调方法体直接嵌入调用处，消除调用开销 + 扩大优化范围。
- 受 `-XX:MaxInlineSize`（小方法直接内联）和 `-XX:FreqInlineSize`（热点方法）限制。
- 为什么 `private`/`final`/`static` 方法更易内联 → 无虚方法分派，编译期确定。

### 2. 逃逸分析（Escape Analysis）
- 分析对象是否逃逸出方法/线程。三种逃逸：不逃逸 / 方法逃逸 / 线程逃逸。
- 不逃逸对象可：
  - **栈上分配**（标量替换）：拆成字段放栈，随栈帧回收，不进堆、不 GC。
  - **同步消除**（锁消除）：对象不逃逸出线程，对它的 `synchronized` 可去掉。
  - **标量替换**：对象字段拆成局部变量。

### 3. 循环展开、分支预测、常量折叠、死代码消除。

## 五、AOT 编译（JDK 9+ 实验 / JDK 25 复活）
- **jaotc**（JDK9 实验，JDK17 弃用）：提前编译为本地代码。
- **JDK 25 JEP 514/515**：AOT 命令行 + AOT 方法 profiling 复活，目标是改善启动（Spring Boot/函数计算场景）。
- **GraalVM Native Image**：闭世界分析 AOT 编译成原生可执行，启动 ms 级、内存小，但牺牲动态性（反射需配置）。

## 易错点
- 算对象大小忘对齐 → 必须 8B 倍数。
- 堆设 32GB 关了压缩反而更费 → 31GB 可能比 32GB 可用空间大。
- 以为 `private` 一定快 → 是更易内联，不是绝对快。
- 以为逃逸分析所有对象都栈上分配 → 只有不逃逸的才标量替换，且不是所有 JVM 都做栈上分配（HotSpot 用标量替换代替）。
- Compact Object Headers 当默认开 → JDK25 默认关，要显式开。

## 延伸
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["concurrency/synchronized-lock-escalation",
         "languages/java/jvm-memory-structure",
         "languages/java/jvm-class-loading",
         "languages/java/jdk-version-optimization-survey"])

q("languages/java/jdk-version-optimization-survey.md",
  "JDK 各版本优化总览 (8→25, JVM/GC/性能)",
  "languages", "java", "hard",
  ["jdk", "version", "gc", "jvm", "optimization", "lts", "zgc", "compact-headers", "java"],
  [],
  """# JDK 各版本优化总览 (8→25, JVM/GC/性能)

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
""",
  languages=["java"], role=["sde", "backend"],
  source="", status="reviewed", timestamp=DATE,
  links=["languages/java/jvm-garbage-collection",
         "languages/java/g1-gc-changes",
         "languages/java/jvm-object-layout-jit",
         "languages/java/jvm-oom-analysis",
         "languages/java/jdk17-new-features"])

print("\nDone: JVM deep docs (3 rewrites + 4 new)")
