#!/usr/bin/env python3
"""Seeder: MySQL / Redis / Kafka from 2026-05 Louis面经."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from seed_louis_ai import q

# --- databases/mysql/ ------------------------------------------------------ #

q("databases/mysql/mysql-btree-index.md",
  "MySQL 索引为什么用 B+ 树",
  "databases", "mysql", "medium",
  ["mysql", "b-tree", "index", "database"],
  ["拼多多"],
  '''# MySQL 索引为什么用 B+ 树

## 问题描述
你知道 MySQL 的索引是怎么实现的吗？为什么 B+ 树？B+ 树有什么好处？

## 解答

InnoDB 索引数据结构是 **B+ 树（B+ Tree）**。

### B+ 树结构
- 所有数据只存在**叶子节点**，内部节点只存索引（指针）。
- 叶子节点用**双向链表**串起来，便于范围扫描。
- 每个节点通常对应一个 InnoDB page（默认 16KB）。

### 为什么是 B+ 树而不是其他

| 候选 | 问题 |
| --- | --- |
| 二叉搜索树 | 退化为链表；层数太高，磁盘 IO 多 |
| AVL/红黑树 | 二叉 → 层数 h = log2 N，百万数据 ~20 层 = 20 次 IO |
| B 树 | 内部节点也存数据，单节点 key 数少 → 层更高；范围查询要中序遍历多次回溯 |
| Hash | O(1) 等值快，但**不支持范围/排序/最左前缀** |
| **B+ 树** | 内部节点不存数据 → 单节点可塞更多 key → **扇出大、层数低**；范围查询沿叶子链表扫 |

### B+ 树好处
1. **IO 少**：3 层 B+ 树可撑 2000 万行（每节点扇出 ~1200）。
2. **范围查询快**：叶子链表顺序扫。
3. **稳定**：所有数据都在叶子，查询路径长度恒定。

### InnoDB 聚簇索引
- 主键索引 = 聚簇索引，叶子节点存**整行数据**。
- 二级索引叶子存主键值（不是行指针），需**回表**到聚簇索引取行。

## 延伸
''',
  links=["databases/mysql/btree-vs-binary-tree",
         "databases/mysql/clustered-vs-secondary-index",
         "databases/mysql/index-failure-scenarios"])

q("databases/mysql/btree-vs-binary-tree.md",
  "B+ 树 vs 二叉树对比",
  "databases", "mysql", "easy",
  ["mysql", "b-tree", "binary-tree", "index", "database"],
  ["拼多多"],
  '''# B+ 树 vs 二叉树对比

## 问题描述
二叉树也是针对查询优化过的，跟 B+ 树相比呢？

## 解答

| 维度 | 二叉树（含 AVL/红黑） | B+ 树 |
| --- | --- | --- |
| 分支数 | 2 | 几百~上千（高扇出） |
| 层数 h | log2 N，百万数据 ~20 | log120 N，百万数据 ~3 |
| 单次 IO | 一层一次 IO | 一个节点一个 page（16KB） |
| 磁盘 IO 次数 | 多（~20） | 少（~3） |
| 范围查询 | 需中序遍历多次回溯 | 叶子链表顺序扫 |

### 核心结论
数据库瓶颈是**磁盘 IO**，不是 CPU 比较。二叉树层数高 → IO 次数多 → 慢。B+ 树靠高扇出把层数压到 3~4，IO 次数极小。

即便二叉树本身"平衡且查询 O(log N)"，在磁盘存储上仍然不如 B+ 树，因为它的"fan-out"太小。

## 延伸
''',
  links=["databases/mysql/mysql-btree-index"])

q("databases/mysql/clustered-vs-secondary-index.md",
  "聚簇索引 vs 二级索引",
  "databases", "mysql", "medium",
  ["mysql", "clustered-index", "secondary-index", "covering-index", "database"],
  ["北京用友"],
  '''# 聚簇索引 vs 二级索引

## 问题描述
什么是聚簇索引？什么是二级索引？

## 解答

### 聚簇索引 (Clustered Index)
- 索引与数据**一起存储**：B+ 树叶子节点 = 完整行数据。
- 一张表**只有一个**聚簇索引（InnoDB 默认主键）。
- 没有显式主键时：选第一个 NOT NULL 唯一索引；都没有则 InnoDB 隐式生成 6 字节 ROWID。
- 数据物理上按聚簇索引键顺序存（所以主键最好自增、单调，避免页分裂）。

### 二级索引 (Secondary / Non-clustered Index)
- 叶子节点存的是**主键值**（不是行指针），不是完整行。
- 查询走二级索引 → 拿到主键 → **回表**到聚簇索引取完整行（除非**覆盖索引**）。
- 一张表可有多个。

### 覆盖索引 (Covering Index)
- 查询列全部被索引覆盖 → 不需要回表，直接从索引返回。
- 优化技巧：把 `SELECT *` 改为只查索引列，或建联合索引覆盖热点查询。

### 回表代价
- 每次回表 = 多一次随机 IO。
- 高频查询应尽量覆盖索引，避免回表。

### 联合索引与最左前缀
- `(a, b, c)` 联合索引：能用于 `a` / `a,b` / `a,b,c`，不能跳过 `a` 直接用 `b,c`。
- 范围查询（> / BETWEEN / LIKE 'x%'）之后的列不再走索引。

## 延伸
''',
  links=["databases/mysql/mysql-btree-index",
         "databases/mysql/index-failure-scenarios",
         "databases/mysql/sql-tuning-deep-pagination"])

q("databases/mysql/inverted-index-es.md",
  "倒排索引原理 (ES)",
  "databases", "mysql", "medium",
  ["elasticsearch", "inverted-index", "search", "database"],
  ["恩士讯", "北京用友"],
  '''# 倒排索引原理 (ES)

## 问题描述
ES 倒排索引的原理？还有哪些组成部分？

## 解答

**倒排索引 (Inverted Index)**：从"词"反查"文档列表"，是搜索引擎的核心结构。

### 结构
- **Term Dictionary（词典）**：所有出现过的词项。
- **Term Index（词典索引）**：FST/前缀树，快速定位 Term 在 Dictionary 中的位置。
- **Posting List（倒排表）**：每个 Term 对应的文档 ID 列表 + 词频 + 位置 + 偏移。
- 词典通常放内存，倒排表放磁盘（FOR + RBM 压缩）。

### 工作流程
1. **写入**：文档分析（分词）→ 每个 term 建倒排表项。
2. **查询**：query 分词 → 在词典查 term → 取 posting list → 交集/并集 → 打分（TF-IDF/BM25）排序。

### ES 倒排组成部分（追问）
- Doc Values（正排）：用于排序、聚合（避免 fielddata 反解倒排）。
- Source：原始 JSON。
- _id 索引、_all（已废弃）、_type（已废弃）。
- **分片（shard）** = 一个 Lucene 索引；副本（replica）。

### 与 B+ 树对比
- B+ 树擅长**等值/范围/排序**，对全文模糊匹配（LIKE '%x%'）无效。
- 倒排擅长**全文检索**，能秒级匹配千万文档关键词。

## 延伸
''',
  links=["databases/mysql/mysql-btree-index"])

q("databases/mysql/index-failure-scenarios.md",
  "索引失效场景",
  "databases", "mysql", "easy",
  ["mysql", "index", "query-optimization", "database"],
  ["海颐"],
  '''# 索引失效场景

## 问题描述
说一下索引失效的场景。

## 解答

1. **对索引列做函数/运算**：`WHERE YEAR(create_time)=2026` → 失效。改 `WHERE create_time >= '2026-01-01' AND < '2027-01-01'`。
2. **隐式类型转换**：phone 是 varchar，`WHERE phone=13800000000`（数字）→ 全表。改 `'13800000000'`。
3. **最左前缀缺失**：联合索引 `(a,b,c)`，查询只有 `b,c` → 不走索引。
4. **范围后列失效**：`WHERE a=? AND b>? AND c=?` → c 不走索引（b 的范围阻断）。
5. **LIKE 以 % 开头**：`LIKE '%abc'` 失效；`LIKE 'abc%'` 走索引。
6. **OR 两边不全有索引**：`WHERE a=1 OR b=2`，若 b 无索引 → 全表。
7. **NOT IN / NOT EXISTS / != / <>**：通常不走索引（视优化器与数据分布）。
8. **IS NULL / IS NOT NULL**：通常不走索引（取决于 null 比例）。
9. **优化器认为全表更快**：表小、索引列区分度低（如性别）→ 主动放弃索引。
10. **字符集/排序规则不一致**（JOIN 两表 charset 不同）：失效。

### 排查
`EXPLAIN` 看 `type` / `key` / `rows` / `Extra`（`Using filesort` / `Using temporary` 是告警）。

## 延伸
''',
  links=["databases/mysql/clustered-vs-secondary-index",
         "databases/mysql/sql-tuning-deep-pagination"])

q("databases/mysql/sql-tuning-deep-pagination.md",
  "SQL 调优 / 深分页优化",
  "databases", "mysql", "medium",
  ["mysql", "sql-tuning", "deep-pagination", "database", "optimization"],
  ["恩士讯", "海颐"],
  '''# SQL 调优 / 深分页优化

## 问题描述
具体怎么从十多秒优化到 2 秒的？数据量大分页越深越慢，有什么解决方案？

## 解答

### 深分页为什么慢
`SELECT * FROM t ORDER BY id LIMIT 1000000, 10`：
- MySQL 需要先扫前 100 万行 → 每行回表取 `*` → 丢掉 → 再取 10 行。
- 偏移越大，丢弃越多，IO 与 CPU 浪费越多。

### 优化方案

1. **延迟关联（Deferred Join）** —— 最常用
```sql
SELECT * FROM t
INNER JOIN (SELECT id FROM t ORDER BY id LIMIT 1000000, 10) x ON t.id = x.id;
```
子查询只走索引覆盖（`id` 是主键，索引覆盖），不用回表，扫完 100 万拿到 10 个 id 后才回表 10 次。

2. **游标 / Keyset 分页**（推荐）
```sql
SELECT * FROM t WHERE id > <last_id> ORDER BY id LIMIT 10;
```
不丢数据，每次只扫 10 行。要求按主键或唯一索引排序，且页面用"上一页最后 id"翻页（不能跳页）。

3. **覆盖索引 + 子查询**：同 1 思路。

4. **缓存热门页**：前几页缓存 Redis，深页才走 DB。

5. **产品层妥协**：限制最大翻页深度（如最多 100 页），或改无限滚动（游标分页）。

### 其他调优手段
- 加合适索引（覆盖索引避免回表）。
- 大表历史归档 / 冷热分离。
- `SELECT *` 改具体列。
- JOIN 用小表驱动大表、JOIN 字段建索引且同类型。

## 延伸
''',
  links=["databases/mysql/index-failure-scenarios",
         "databases/mysql/clustered-vs-secondary-index"])

q("databases/mysql/mvcc-principle.md",
  "MVCC 原理",
  "databases", "mysql", "hard",
  ["mysql", "mvcc", "transaction", "isolation", "database"],
  ["恩士讯"],
  '''# MVCC 原理

## 问题描述
说一下 MVCC 原理。

## 解答

**MVCC (Multi-Version Concurrency Control)**：通过维护数据多版本，让**读不阻塞写、写不阻塞读**，提升并发。InnoDB 在 RC/RR 隔离级别下用 MVCC。

### 三个组件

1. **隐藏列**：每行有 `DB_TRX_ID`（最近修改的事务 id）、`DB_ROLL_PTR`（回滚指针指向 undo log）。
2. **Undo Log**：每次修改前旧版本写入 undo log，形成版本链（旧 → 更旧）。
3. **Read View（读视图）**：事务在某次快照读时生成的"可见性判断快照"：
   - `m_ids`：生成时活跃未提交的事务 id 列表。
   - `min_trx_id` / `max_trx_id`：活跃事务最小/下一个分配 id。
   - `creator_trx_id`：当前事务 id。

### 可见性判断规则
对当前行的 `DB_TRX_ID`：
- `< min_trx_id` → 已提交，可见。
- `>= max_trx_id` → 未来事务，不可见。
- 在 `m_ids` 中 → 还活跃，不可见，沿 undo 链找下一版本再判。
- 不在 `m_ids` 中且在区间内 → 已提交，可见。

### RC vs RR 区别
- **RC (Read Committed)**：每次 SELECT 都生成新 Read View → 能看到新提交。
- **RR (Repeatable Read)**：事务内**只在第一次 SELECT 时生成一次** Read View → 后续都用同一份，可重复读。
- InnoDB 的 RR + MVCC 在大部分场景下已防幻读；严格防幻读用 `SELECT ... FOR UPDATE` 加间隙锁。

### 当前读 vs 快照读
- 快照读（普通 SELECT）走 MVCC。
- 当前读（`FOR UPDATE / LOCK IN SHARE MODE / UPDATE / DELETE`）读最新版本 + 加锁。

## 延伸
''',
  links=["databases/mysql/transaction-annotation-failure",
         "databases/mysql/mysql-transaction-usage"])

q("databases/mysql/mysql-transaction-usage.md",
  "MySQL 事务使用方式 / 注解事务",
  "databases", "mysql", "medium",
  ["mysql", "transaction", "spring", "isolation", "database"],
  ["恩士讯"],
  '''# MySQL 事务使用方式 / 注解事务

## 问题描述
MySQL 事务了解吗？代码上怎么使用事务？注解方式使用事务有哪些注意点？

## 解答

### MySQL 事务
- ACID：原子/一致/隔离/持久。
- 隔离级别：READ UNCOMMITTED → READ COMMITTED → REPEATABLE READ（InnoDB 默认）→ SERIALIZABLE。
- InnoDB 通过 redo log（持久性）+ undo log（原子性/回滚）+ MVCC（隔离性）+ 锁实现。

### 代码使用（Spring `@Transactional`）
```java
@Transactional(rollbackFor = Exception.class, isolation = Isolation.REPEATABLE_READ, propagation = Propagation.REQUIRED)
public void createOrder(...) { ... }
```

### 注意点
1. **rollbackFor**：默认只回滚 `RuntimeException` 和 `Error`；checked 异常不回滚。建议显式 `rollbackFor = Exception.class`。
2. **propagation（传播）**：REQUIRED / REQUIRES_NEW / NESTED / SUPPORTS / MANDATORY / NOT_SUPPORTED / NEVER。
3. **隔离级别**：根据场景选，默认 RR 在高并发写场景可能死锁/间隙锁，可降 RC。
4. **超时**：`timeout` 防止长事务占锁。
5. **只读**：`readOnly = true` 让优化器做读优化。

### @Transactional 失效场景（高频追问）
1. **方法非 public**：Spring AOP 默认只代理 public 方法。
2. **同类内部调用**：`this.method()` 不走代理 → 注解失效。解法：注入自身代理 `AopContext.currentProxy()` 或拆到另一个 Bean。
3. **rollbackFor 没配**：checked 异常不回滚。
4. **异常被 catch 吞掉**：事务感知不到异常，不回滚。
5. **传播行为不当**：内部方法 `REQUIRES_NEW` 但同类内部调用仍走原事务。
6. **数据库引擎不支持事务**：MyISAM 无事务。
7. **Bean 没被 Spring 管理**（new 出来的对象）。
8. **多线程跨连接**：事务绑定线程，跨线程不在同一事务。

## 延伸
''',
  links=["databases/mysql/mvcc-principle",
         "databases/mysql/transaction-annotation-failure"])

q("databases/mysql/transaction-annotation-failure.md",
  "事务注解失效 / 代理层面失效解决",
  "databases", "mysql", "medium",
  ["spring", "transaction", "aop", "proxy", "database"],
  ["恩士讯"],
  '''# 事务注解失效 / 代理层面失效解决

## 问题描述
代理层面事务失效有哪些解决方法？

## 解答

失效根因：`@Transactional` 通过 **Spring AOP 动态代理**生效，绕过代理就失效。

### 主要失效场景与解决

| 场景 | 原因 | 解决 |
| --- | --- | --- |
| 同类内部方法调用 `this.b()` | 不走代理 | 1) 注入自身 `@Autowired self` 调 `self.b()`；2) `AopContext.currentProxy()` 取代理（需 `@EnableAspectJAutoProxy(exposeProxy=true)`）；3) 拆到另一个 Bean |
| 方法非 public | AOP 默认只代理 public | 改 public，或用 AspectJ 编译/加载时织入 |
| 异常被 catch | 事务感知不到 | catch 后 `throw`，或手动 `TransactionAspectSupport.currentTransactionStatus().setRollbackOnly()` |
| rollbackFor 没配 | checked 异常不回滚 | `rollbackFor = Exception.class` |
| final / static 方法 | 不可被代理覆写 | 改可覆写 |
| Bean 未被 Spring 管理 | 没代理 | 注入而非 new |
| 多线程 | 跨线程跨连接 | 拆事务边界或用编程式事务 |

### 编程式事务（替代方案）
```java
transactionTemplate.execute(status -> { ... return ...; });
```
适合细粒度控制、内部调用场景。

### AspectJ 替代 CGLIB 代理
- 改用 AspectJ LTW（加载时织入）可解决 self-invocation，因为它是字节码级织入，不依赖代理对象。

## 延伸
''',
  links=["databases/mysql/mysql-transaction-usage",
         "backend/microservices/spring-ioc-di-injection"])

q("databases/mysql/mysql-query-optimization.md",
  "MySQL 查询优化经验",
  "databases", "mysql", "medium",
  ["mysql", "query-optimization", "explain", "database"],
  ["拼多多", "北京用友"],
  '''# MySQL 查询优化经验

## 问题描述
有一些查询优化经验吗？你说的游标跟跳跃具体是指什么？MySQL 优化？

## 解答

### 通用优化流程
1. **EXPLAIN** 看 `type`（const > eq_ref > ref > range > index > ALL）、`key`（实际用的索引）、`rows`（估算扫描行）、`Extra`（Using index = 覆盖索引好；Using filesort/Using temporary = 告警）。
2. 避免全表扫描：建合适索引、避免索引失效写法。
3. 减少回表：覆盖索引、避免 `SELECT *`。
4. 大结果集分页：游标/延迟关联（见 [[databases/mysql/sql-tuning-deep-pagination]]）。
5. 小表驱动大表：JOIN 时小结果集做驱动表。
6. 子查询改 JOIN（早期 MySQL 子查询优化差，新版改善）。

### "游标 vs 跳跃"澄清
- **游标分页（Keyset / Seek）**：`WHERE id > last_id LIMIT n`，每次定位到上次最大 id 之后，O(n) 不浪费。
- **跳跃分页（OFFSET）**：`LIMIT offset, n`，offset 即"跳跃"过的行数；深翻页时跳过大量行，越深越慢。
- 拼多多追问的"游标 vs 跳跃"指这两种分页策略的对比。

### 索引设计
- 高频查询列建索引，区分度低的（性别/状态）不单独建。
- 联合索引按"等值在前、范围在后、排序字段再后"排列。
- 别滥用索引：写多读少场景索引会拖慢写入。

### 监控
- 慢查询日志 `slow_query_log` + `pt-query-digest` 分析 TopN。
- `SHOW PROCESSLIST` / `sys.schema_index_statistics`。

## 延伸
''',
  links=["databases/mysql/index-failure-scenarios",
         "databases/mysql/sql-tuning-deep-pagination"])

q("databases/mysql/oracle-gaussdb.md",
  "Oracle / 高斯数据库了解",
  "databases", "mysql", "easy",
  ["oracle", "gaussdb", "database", "domestic-db"],
  ["海颐"],
  '''# Oracle / 高斯数据库了解

## 问题描述
Oracle 或者说华为的高斯数据库有没有了解过？

## 解答

### Oracle
- 商业闭源关系数据库龙头。
- 特性：RAC（集群）、Data Guard（主备）、表空间、PL/SQL、物化视图、分区表、强大优化器。
- 企业级 OLTP/OLAP 常见，金融/电信/制造业深使用。

### GaussDB（华为高斯）
- 华为自研分布式数据库，主打国产化/信创。
- 系列：
  - **GaussDB(for MySQL)** —— MySQL 兼容，云原生存算分离。
  - **GaussDB(for PostgreSQL)** / **GaussDB 200**（数仓）—— PG 兼容。
  - **openGauss** —— 2020 开源版本（基于 PG），国产化常用。
- 架构：分布式共享存储、一写多读、HTAP。

### 信创背景
国产化替代推进，金融/政企从 Oracle/MySQL 迁移到达梦/人大金仓/GaussDB/OceanBase/TiDB。

### 与 MySQL 差异点（迁移注意）
- SQL 方言、函数、自增主键写法、字符集、连接池驱动不同。
- 部分语法/索引行为差异（PG 系）。

## 延伸
''',
  links=["databases/mysql/mysql-btree-index"])

# --- databases/redis/ ------------------------------------------------------ #

q("databases/redis/redis-data-types.md",
  "Redis 数据类型",
  "databases", "redis", "easy",
  ["redis", "data-structure", "cache"],
  ["海颐", "北京用友"],
  '''# Redis 数据类型

## 问题描述
Redis 具体支持哪些数据类型？你知道它的这个数据结构吗？

## 解答

### 5 大基础类型
| 类型 | 底层结构 | 典型用途 |
| --- | --- | --- |
| **String** | SDS（简单动态字符串） | 计数器、缓存、分布式锁 |
| **List** | quicklist（ziplist + linkedlist，7.0 改 listpack） | 消息队列、最新列表 |
| **Hash** | ziplist / hashtable | 对象存储（用户信息） |
| **Set** | intset / hashtable | 去重、标签、共同好友 |
| **ZSet** | ziplist / skiplist + hashtable | 排行榜、延时队列、范围查 |

### 扩展类型（4+）
- **Stream**（5.0+）：持久化消息流，替代 List 做可靠 MQ。
- **Bitmap**：位图，签到、活跃统计、布隆过滤器。
- **HyperLogLog**：基数估算（UV），12KB 估 12 亿去重。
- **Geo**：基于 ZSet，经纬度范围查。
- **5 种新结构**：Stream / Listpack / BF/CF/...（RedisBloom 模块）。

### 底层编码选择
- 数据少用 ziplist/listpack（紧凑省内存），达到阈值切换 hashtable/skiplist（性能优先）。
- 阈值由 `hash-max-ziplist-entries` 等配置控制。

## 延伸
''',
  links=["databases/redis/redis-persistence",
         "databases/redis/redis-cache-avalanche"])

q("databases/redis/redis-persistence.md",
  "Redis 持久化 (RDB / AOF)",
  "databases", "redis", "medium",
  ["redis", "rdb", "aof", "persistence"],
  ["海颐"],
  '''# Redis 持久化 (RDB / AOF)

## 解答

### RDB (Redis Database)
- 全量快照，二进制 dump。
- 触发：`SAVE`/`BGSAVE`、配置 `save m n`、主从同步。
- 优点：体积小、恢复快、适合备份。
- 缺点：宕机丢最后一次快照后的数据；`BGSAVE` fork 大内存实例慢。

### AOF (Append Only File)
- 追加写命令日志。
- 刷盘策略：`always`（每条 fsync，最安全最慢）/ `everysec`（默认，每秒）/ `no`（OS 决定）。
- 重写（rewrite）：fork 子进程按当前内存状态生成最小等价 AOF，避免文件膨胀。
- 优点：丢数据少（everysec 最多丢 1 秒）。
- 缺点：体积大、恢复慢。

### Redis 4.0+ 混合持久化
- `aof-use-rdb-preamble yes`：AOF 重写时前半段写 RDB 快照 + 后半段追加 AOF 命令。
- 兼顾 RDB 恢复快 + AOF 丢数据少。

### 选型
- 纯缓存可关持久化。
- 允许丢几分钟 → RDB。
- 不允许丢 → AOF everysec + 混合持久化。
- 金融级不应只用 Redis 做主存。

## 延伸
''',
  links=["databases/redis/redis-data-types"])

q("databases/redis/redis-cache-avalanche.md",
  "缓存雪崩 / 穿透 / 击穿",
  "databases", "redis", "medium",
  ["redis", "cache-avalanche", "cache-breakdown", "cache-penetration", "cache"],
  ["海颐"],
  '''# 缓存雪崩 / 穿透 / 击穿

## 问题描述
你说一下缓存雪崩的理解。

## 解答

三种经典缓存故障，区分清楚是高频考点。

| 故障 | 现象 | 原因 | 解法 |
| --- | --- | --- | --- |
| **雪崩** | 大量 key 同时失效 / Redis 宕机，请求全打 DB | TTL 集中、Redis 挂 | TTL 加随机抖动；多级缓存；熔断限流；Redis 集群高可用 |
| **穿透** | 查不存在的 key，每次都打到 DB | 恶意攻击 / 业务 bug | 布隆过滤器拦截；缓存空值（短 TTL）；参数校验 |
| **击穿** | 单个热 key 过期瞬间，海量并发同时查 DB | 热 key 失效 | 互斥锁（SETNX）只让一个线程回源；热 key 永不过期 + 后台异步刷新 |

### 雪崩专项
- TTL 加 `random(60s)` 抖动避免同时过期。
- Redis 集群 + 哨兵/Cluster 高可用，避免整体宕机。
- 应用层 Hystrix/Sentinel 熔断限流，DB 不被压垮。
- 多级缓存：Caffeine 本地 + Redis + DB。

### 穿透专项
- 布隆过滤器前置：启动时把所有合法 id 加进 BF，请求先过 BF，不存在直接拒绝。
- 缓存空对象 `null` 短 TTL（30s），防同 key 反复打 DB。

### 击穿专项
- 互斥锁重建缓存：
```java
if (redis.get(key) == null) {
  if (setnx(lock, 1, 10s)) {
    val = db.query(); redis.set(key, val, ttl); del(lock);
  } else { sleep+retry; }
}
```
- 热 key 逻辑过期（不设 TTL，存过期时间戳，发现过期后异步刷新，期间返回旧值）。

## 延伸
''',
  links=["databases/redis/redis-data-types",
         "distributed-systems/distributed-lock-redis-vs-zk",
         "backend/microservices/microservice-user-context-propagation"])

q("databases/redis/redis-distributed-architecture.md",
  "Redis 分布式架构 (主从 / 哨兵 / Cluster)",
  "databases", "redis", "medium",
  ["redis", "replication", "sentinel", "cluster", "ha"],
  ["中泓一线"],
  '''# Redis 分布式架构 (主从 / 哨兵 / Cluster)

## 问题描述
Redis 有哪些分布式架构？Redis 搭过高可用？

## 解答

### 1. 主从复制
- 一主多从，写主读从，读写分离。
- 同步方式：全量（bgsync + RDB 传输）+ 增量（repl_backlog）。
- 异步复制 → 主从延迟、主挂丢数据。
- 不自动故障转移。

### 2. Sentinel（哨兵）
- Sentinel 集群（≥3 节点）监控主从。
- 主挂时哨兵**投票选新主**，应用通过 Sentinel 拿最新主地址。
- 适合**小规模、不需水平扩容**的高可用。
- 故障转移：主观下线 → 客观下线 → 选举 leader sentinel → 选新主 → 通知客户端。

### 3. Cluster
- **数据分片**：16384 个 slot，按 `CRC16(key) % 16384` 分配到节点。
- 每个节点负责一部分 slot，节点间 Gossip 通信。
- **去中心化**，无单独代理；客户端缓存 slot 路由表，MOVED 重定向。
- 每个主节点配一个从节点，主挂从提升（半自动）。
- 适合**大数据量 + 水平扩容**。
- 限制：跨 slot 操作需 hash tag（`{user}:1`）；事务/多键受限；不支持 select db（只用 db0）。

### 选型
- 数据量小、要 HA → Sentinel。
- 数据量大、要水平扩展 → Cluster。
- 极致性能 + HA → 代理层（Codis/Twemproxy，已渐少用）或自研。

## 延伸
''',
  links=["databases/redis/redis-persistence",
         "distributed-systems/distributed-lock-redis-vs-zk"])

# --- distributed-systems/ (MQ) -------------------------------------------- #

q("distributed-systems/redis-mq-vs-kafka-rocketmq.md",
  "Redis 做 MQ vs Kafka / RocketMQ",
  "distributed-systems", "distributed-systems", "medium",
  ["redis", "kafka", "rocketmq", "message-queue", "comparison"],
  ["恩士讯"],
  '''# Redis 做 MQ vs Kafka / RocketMQ

## 问题描述
项目上消息队列用的什么？Redis 做 MQ 比 Kafka/RocketMQ 有什么缺点？

## 解答

### Redis 做 MQ 的方式
- List + `BRPOP`：简单队列。
- Pub/Sub：广播，但**无持久化、离线订阅者丢消息**。
- Stream（5.0+）：接近 Kafka 的 consumer group + 持久化，最像 MQ。

### Redis 做 MQ 的缺点
| 维度 | Redis Stream | Kafka/RocketMQ |
| --- | --- | --- |
| 吞吐 | 万级 TPS | 百万级 TPS |
| 持久化 | 受限于 Redis 内存 + AOF/RDB | 专门顺序写磁盘 + 副本 |
| 堆积能力 | 内存限制，堆积会拖垮 | TB 级堆积无压力 |
| 顺序/分片 | 弱 | 分区强顺序 |
| 事务消息 | 无 | RocketMQ 支持 |
| 回溯 | 有限 | 按时间/offset 回溯 |
| 运维 | 简单 | 重（Kafka 需 ZK/KRaft） |
| 生态 | 弱 | 流计算、Connector、Schema Registry |

### 结论
- Redis MQ 适合**轻量、低吞吐、无严格堆积需求**的场景（如内部任务队列、限流提示）。
- 严肃 MQ 场景（订单、日志、流处理）选 Kafka（吞吐/流式）或 RocketMQ（事务消息/电商）。

## 延伸
''',
  links=["distributed-systems/kafka-offset-rebalance",
         "distributed-systems/kafka-vs-rocketmq-scenarios"])

q("distributed-systems/kafka-offset-rebalance.md",
  "Kafka 偏移量 / Rebalance",
  "distributed-systems", "distributed-systems", "medium",
  ["kafka", "offset", "consumer-group", "rebalance", "message-queue"],
  ["中泓一线", "拼多多"],
  '''# Kafka 偏移量 / Rebalance

## 问题描述
Kafka 偏移量有哪几种？常见设置偏移量有哪些？Topic 和 Group 哪个大？换 group 要重置偏移量吗？有没有了解过 Rebalance 概念？

## 解答

### 偏移量 (offset)
- 每个分区一个单调递增 offset，标识消费位置。
- 提交方式：
  - **自动提交**：`enable.auto.commit=true`，每 `auto.commit.interval.ms` 提交，可能**重复/丢失**。
  - **手动提交**：`commitSync()` / `commitAsync()`，业务处理完再提交，精确但需自己管。
- 初始位置 `auto.offset.reset`：`earliest` / `latest` / `none`。

### 常见设置
- 至少一次：手动提交 + 幂等消费。
- 至多一次：自动提交 + 处理前提交。
- 精确一次：事务/幂等生产 + 事务消费（Kafka 0.11+）。

### Topic vs Group
- **Topic 是数据维度**，**Group 是消费维度**，二者正交，没有"谁大"。
- 一个 Topic 可被多个 Group 独立消费（各自 offset），互不干扰。
- 一个 Group 内分区被瓜分：组内消费者数 ≤ 分区数才有意义，多了空闲。

### 换 group 要重置 offset 吗
- 新 group 第一次消费按 `auto.offset.reset` 决定（earliest/latest）。
- 不存在"重置"，因为是全新 group，没有历史 offset。
- 老群体改 `auto.offset.reset` 不影响已提交的 offset，要重置需用 `kafka-consumer-groups --reset-offsets` 工具。

### Rebalance
- 触发：消费者加入/退出、订阅变化、分区数变化、心跳超时。
- 过程：所有消费者暂停消费 → 协调器重新分配分区 → 消费者继续。
- 问题：**Stop-The-World**，期间全组不消费；频繁 rebalance 影响吞吐。
- 优化：
  - `session.timeout.ms` / `heartbeat.interval.ms` 调大避免误判。
  - `max.poll.interval.ms` 调大避免长处理被踢。
  - **Sticky Assignor / Cooperative Rebalance**（2.4+）：增量 rebalance，减少抖动。
  - 静态成员 `group.instance.id`：消费者重启不触发 rebalance。

## 延伸
''',
  links=["distributed-systems/kafka-duplicate-consumption-message-loss",
         "distributed-systems/kafka-vs-rocketmq-scenarios"])

q("distributed-systems/kafka-vs-rocketmq-scenarios.md",
  "Kafka vs RocketMQ 场景选择",
  "distributed-systems", "distributed-systems", "medium",
  ["kafka", "rocketmq", "message-queue", "comparison", "selection"],
  ["海颐"],
  '''# Kafka vs RocketMQ 场景选择

## 问题描述
Kafka 跟 RocketMQ 对比，各自适合什么场景？

## 解答

| 维度 | Kafka | RocketMQ |
| --- | --- | --- |
| 起源 | LinkedIn，流处理 | 阿里，电商场景 |
| 语言 | Scala/Java | Java |
| 事务消息 | 0.11+ 支持但弱 | 原生强支持（半消息 + 回查） |
| 顺序消息 | 分区内有序 | 分区内有序，且支持全局顺序 |
| 延时消息 | 需自己实现 | 原生支持（18 个级别） |
| 消息回溯 | 按 offset/时间 | 按时间 |
| 吞吐 | 极高（百万级） | 高（十万级） |
| 堆积 | TB 级 | 亿级（优化好） |
| 生态 | Kafka Streams / Connect / Schema Registry | 弱 |
| 运维 | 重（ZK/KRaft） | 中（NameServer） |

### 场景选型
- **日志/流式处理/大数据管道** → Kafka（生态成熟、吞吐极致）。
- **电商交易/订单/事务消息/延时任务** → RocketMQ（事务消息、延时、可靠投递）。
- **金融/严格不丢** → RocketMQ（双刷 + 同步刷盘 + 同步复制）。

## 延伸
''',
  links=["distributed-systems/kafka-offset-rebalance",
         "distributed-systems/kafka-duplicate-consumption-message-loss"])

q("distributed-systems/kafka-duplicate-consumption-message-loss.md",
  "Kafka 重复消费 / 丢消息",
  "distributed-systems", "distributed-systems", "medium",
  ["kafka", "duplicate-consumption", "message-loss", "idempotent", "message-queue"],
  ["拼多多", "海颐"],
  '''# Kafka 重复消费 / 丢消息

## 问题描述
怎么避免重复发送呢？Kafka 什么情况下会出现丢消息的情况？

## 解答

### 重复消费来源
1. 自动提交 offset 后业务才失败 → 重启后从已提交 offset 后消费，丢业务但 Kafka 认为已消费。
2. Rebalance 时部分消息已处理但未提交 offset → 新消费者重新消费。
3. 生产端重试（网络抖动）导致 broker 收到重复消息。

### 避免重复消费
- **手动提交**：业务处理成功后才 commit。
- **幂等消费**：用业务唯一键（订单号）去重，DB 唯一索引 / Redis SETNX 标记已处理。
- **事务**：消费 + 业务写 + 提交 offset 放同一事务。

### 丢消息场景
1. **生产端**：`acks=0`（不等任何确认）就丢； producer 异步 send 不处理回调。**解法**：`acks=all` + 重试 + `enable.idempotence=true`。
2. **Broker**：单副本 + 宕机；`min.insync.replicas` 设小。**解法**：副本 ≥3 + `min.insync.replicas=2` + 同步刷盘。
3. **消费端**：先提交 offset 再处理业务，处理失败就丢。**解法**：处理完再提交。
4. **缓冲区满**：buffer.memory 满且 block 超时丢。**解法**：调大 buffer 或处理背压。

### 精确一次（Exactly-Once）
- Kafka 0.11+：幂等 producer + 事务（producer 写 + consumer 提交 offset 同一事务）。
- 业务侧仍建议**幂等消费**做兜底，比依赖精确一次更稳。

## 延伸
''',
  links=["distributed-systems/kafka-offset-rebalance",
         "distributed-systems/kafka-vs-rocketmq-scenarios"])

# --- distributed-systems/ (rate limiting, referenced by mcp-gateway) ------- #

q("distributed-systems/rate-limiting-redis-token-bucket.md",
  "限流方案 (令牌桶 / 漏桶 / 滑动窗口 / Redis)",
  "distributed-systems", "distributed-systems", "medium",
  ["rate-limiting", "token-bucket", "sliding-window", "redis", "lua"],
  ["华大制造", "探迹", "恩士讯"],
  '''# 限流方案 (令牌桶 / 漏桶 / 滑动窗口 / Redis)

## 问题描述
限流除了这种方式还有别的方式？单机怎么考量？不会成为单点故障的隐患吗？

## 解答

### 算法对比

| 算法 | 特点 | 实现 |
| --- | --- | --- |
| **固定窗口** | 简单，窗口边界突刺 | Redis INCR + EXPIRE |
| **滑动窗口** | 精确，无边界突刺 | Redis ZSET（按时间戳计数，删过期） |
| **令牌桶** | 平滑限流，允许突发 | Redis + Lua 原子扣 token |
| **漏桶** | 强制匀速，拒绝突发 | 队列 + 固定速率消费 |
| **自适应** | 按延迟/错误率动态调整 | Sentinel / BBR |

### 单机 vs 分布式
- 单机：Guava `RateLimiter`（令牌桶）/ Bucket4j。
- 多机：必须**共享存储**限流，否则总 QPS = 单机配额 × 副本数，超预期。
- 共享存储选型：Redis（主流）/ Sentinel 集群 / 自研中心化限流服务。

### Redis 令牌桶 Lua 原子脚本
```lua
-- KEYS[1]=key  ARGV[1]=capacity  ARGV[2]=refill_rate  ARGV[3]=now  ARGV[4]=requested
local last = tonumber(redis.call("hget", KEYS[1], "ts")) or ARGV[3]
local tokens = tonumber(redis.call("hget", KEYS[1], "tk")) or ARGV[1]
local delta = math.max(0, ARGV[3] - last) * ARGV[2]
tokens = math.min(ARGV[1], tokens + delta)
if tokens >= ARGV[4] then
  redis.call("hmset", KEYS[1], "tk", tokens - ARGV[4], "ts", ARGV[3])
  return 1
else
  return 0
end
```

### 单点故障隐患
- 限流器本身是单点 → 限流器挂了，要么全放行（DB 被打爆）要么全拒绝（服务不可用）。
- 解法：
  - 限流服务高可用（Redis Cluster / Sentinel）。
  - 客户端**本地兜底**：连不上限流器时走本地令牌桶（保守值）。
  - 多级：网关粗限流 + 服务细限流。

### 集群限流（更精确）
- 中心化 token 服务（每节点定时拉额度）或 Redis 集群分散热点 key。

## 易错点
- 用 `INCR + EXPIRE` 做固定窗口 → 边界突刺（窗口切换瞬间双倍流量）。
- 单机限流配多副本网关 → 总 QPS 失控。

## 延伸
''',
  links=["ml-ai/mcp/mcp-gateway-architecture",
         "distributed-systems/distributed-lock-redis-vs-zk"])

print("\nDone: mysql + redis + kafka + rate-limiting")
