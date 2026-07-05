# Index — concurrency

## 题目

| 标题 | 难度 | 标签 |
| --- | --- | --- |
| [AQS 原理 (从直觉到源码)](concurrency/aqs-principle.md) | hard | aqs, clh-queue, juc, condition, concurrency |
| [CAS 机制 (从直觉到 cmpxchg 底层)](concurrency/cas-mechanism.md) | hard | cas, compare-and-swap, atomic, aba, unsafe, varhandle |
| [CompletableFuture 异步编排](concurrency/completablefuture-async-orchestration.md) | medium | completablefuture, async, juc, concurrency, future |
| [ConcurrentHashMap 原理 (1.7 vs 1.8 / sizeCtl / 转移节点)](concurrency/concurrenthashmap-principle.md) | hard | concurrenthashmap, juc, cas, synchronized, concurrency |
| [CountDownLatch / CyclicBarrier / Semaphore 区别](concurrency/countdownlatch-cyclicbarrier-semaphore.md) | medium | countdownlatch, cyclicbarrier, semaphore, juc, concurrency |
| [DCL 单例为什么必须 volatile](concurrency/dcl-singleton-volatile-why.md) | medium | dcl, singleton, volatile, instruction-reorder, concurrency |
| [Executors 内置线程池设计 (Fixed/Cached/Single/Scheduled/WorkStealing)](concurrency/executors-built-in-pools.md) | hard | executors, thread-pool, fixed, cached, scheduled, workstealing, juc |
| [ForkJoinPool 工作窃取 + parallelStream 坑](concurrency/forkjoinpool-parallelstream.md) | medium | forkjoinpool, work-stealing, parallelstream, juc, concurrency |
| [JMM 与 happens-before 八大原则](concurrency/jmm-happens-before.md) | hard | jmm, happens-before, memory-model, concurrency, java |
| [LockSupport.park / unpark 原理 (vs wait/notify)](concurrency/locksupport-park-unpark.md) | medium | locksupport, park, unpark, concurrency, juc |
| [LongAdder vs AtomicLong (分段累加 Cell)](concurrency/longadder-vs-atomiclong.md) | medium | longadder, atomiclong, cas, juc, concurrency |
| [ReentrantReadWriteLock / StampedLock (读写锁 + 乐观读)](concurrency/readwritelock-stampedlock.md) | hard | readwritelock, stampedlock, aqs, optimistic-read, concurrency |
| [ThreadLocal 在线程池中的问题 (闭环追问)](concurrency/threadlocal-threadpool-problems.md) | hard | threadlocal, thread-pool, inheritable-threadlocal, transmittable-threadlocal |
| [ThreadLocal 用法陷阱 (内存泄漏 / 弱引用 key / 回收)](concurrency/threadlocal-usage-pitfalls.md) | hard | threadlocal, memory-leak, weak-reference, concurrency |
| [ThreadPoolExecutor 源码解析 (ctl / execute / Worker / transfer)](concurrency/threadpool-source-analysis.md) | hard | thread-pool, threadpoolexecutor, source, juc, concurrency |
| [synchronized vs ReentrantLock 区别 (含锁升级与选型)](concurrency/synchronized-vs-reentrantlock.md) | hard | synchronized, reentrantlock, lock, aqs, juc, lock-escalation |
| [synchronized 锁升级 (偏向/轻量/重量 + MarkWord)](concurrency/synchronized-lock-escalation.md) | hard | synchronized, lock-escalation, markword, jvm, concurrency |
| [volatile 原理 (JMM / happens-before / 内存屏障 / DCL)](concurrency/volatile-principle.md) | hard | volatile, jmm, memory-barrier, happens-before, concurrency |
| [乐观锁 vs 悲观锁](concurrency/optimistic-vs-pessimistic-lock.md) | easy | optimistic-lock, pessimistic-lock, cas, version |
| [伪共享 false sharing 与 @Contended](concurrency/false-sharing-contended.md) | medium | false-sharing, contended, cache-line, concurrency, performance |
| [死锁四条件 + 排查 + 避免](concurrency/deadlock-detection-prevention.md) | medium | deadlock, jstack, lock-ordering, concurrency |
| [线程池运行原理 (ctl 高低位 / execute 流程 / Worker / 钩子)](concurrency/thread-pool-principles.md) | hard | thread-pool, juc, threadpoolexecutor, concurrency |

## 被引用 (cited by)

- [[backend/microservices/microservice-user-context-propagation]] — 微服务跨服务用户上下文传递 (设计题)
- [[distributed-systems/distributed-lock-redis-vs-zk]] — 分布式锁 (Redis vs ZK)
- [[languages/java/hashmap-vs-concurrenthashmap]] — HashMap vs ConcurrentHashMap
- [[languages/java/jvm-oom-analysis]] — OOM 分析过程

<!-- 由 `tools/okf.py gen-index` 自动生成，请勿手动编辑正文。 -->
