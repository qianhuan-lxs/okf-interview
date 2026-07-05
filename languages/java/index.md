# Index — languages/java

## 题目

| 标题 | 难度 | 标签 |
| --- | --- | --- |
| [G1 回收器 (Region/RSet/SATB/混合回收/演进)](languages/java/g1-gc-changes.md) | hard | g1, gc, jvm, region, rset, satb, java |
| [HashMap resize (1.7 头插法死循环源码 / 1.8 尾插法+高位 bit rehash 优化)](languages/java/hashmap-resize-jdk17-jdk18.md) | hard | hashmap, resize, jdk17, jdk18, concurrent-modification, head-insertion, tail-insertion, java, source |
| [HashMap vs ConcurrentHashMap (CHM 1.8 源码: CAS+synchronized 桶锁/CounterCell/forwarding)](languages/java/hashmap-vs-concurrenthashmap.md) | hard | hashmap, concurrenthashmap, juc, cas, synchronized, counter-cell, forwarding-node, java, source |
| [HashMap 全景深讲 (hash/桶定位/put/resize/树化/0.75/2幂/扰动)](languages/java/hashmap-deep-dive.md) | hard | hashmap, hash, resize, red-black-tree, load-factor, treeify, java, source, jdk18 |
| [JDK 17 新特性](languages/java/jdk17-new-features.md) | medium | jdk17, jvm, java, features, lts |
| [JDK 各版本优化总览 (8→25, JVM/GC/性能)](languages/java/jdk-version-optimization-survey.md) | hard | jdk, version, gc, jvm, optimization, lts, zgc, compact-headers, java |
| [JRE 和 JDK 的区别](languages/java/jre-vs-jdk.md) | easy | jre, jdk, java, basics |
| [JVM 内存结构 (堆/元空间/栈/直接内存 + JDK8 永久代消失)](languages/java/jvm-memory-structure.md) | medium | jvm, memory-model, metaspace, permgen, direct-memory, java |
| [JVM 垃圾回收 (判活 / 算法 / 收集器 / GC roots)](languages/java/jvm-garbage-collection.md) | hard | jvm, gc, reachability, g1, zgc, shenandoah, java |
| [JVM 类加载 (5 阶段 / 双亲委派 / 破坏双亲委派)](languages/java/jvm-class-loading.md) | medium | jvm, class-loading, classloader, parent-delegation, java |
| [Java IO 流的种类](languages/java/java-io-stream-types.md) | easy | io, stream, nio, java, basics |
| [OOM 分析 (7 种类型 / 排查流程 / 工具 / 容器)](languages/java/jvm-oom-analysis.md) | hard | oom, jvm, heap-dump, mat, arthas, java, troubleshooting |
| [StringBuilder 和 StringBuffer 的区别](languages/java/stringbuilder-vs-stringbuffer.md) | easy | stringbuilder, stringbuffer, java, basics |
| [对象内存布局 + JIT 执行引擎 (MarkWord/指针压缩/C1C2/逃逸分析)](languages/java/jvm-object-layout-jit.md) | hard | jvm, object-layout, markword, jit, escape-analysis, java, compact-headers |
| [模板方法模式](languages/java/template-method-pattern.md) | easy | design-pattern, template-method, java, oop |

## 被引用 (cited by)

- [[algorithms/trees-graphs/red-black-tree]] — 红黑树 (5 性质/旋转着色/为什么不用 AVL/HashMap 树化)
- [[backend/microservices/spring-boot-autoconfig]] — Spring Boot 自动配置原理
- [[backend/microservices/spring-webflux]] — Spring WebFlux (Reactor/Mono/Flux/Netty/背压 + 2026 vs 虚拟线程)
- [[backend/microservices/tomcat-servlet-thread-pool]] — Tomcat Servlet 线程池 (acceptCount/maxConnections/maxThreads/TaskQueue/NIO)
- [[behavioral/八股-attitude-and-disliked-java]] — 八股态度 / Java 最讨厌的地方 / 设计模式偏好
- [[concurrency/coroutine-virtual-thread-principle]] — 协程原理 (Java VT/Kotlin/Go/Python 对比 + mount-unmount + pinning)
- [[concurrency/virtual-thread-pool-antipattern]] — 协程池 / 虚拟线程池 (该不该用 + 限流 + 与线程池配合)

<!-- 由 `tools/okf.py gen-index` 自动生成，请勿手动编辑正文。 -->
