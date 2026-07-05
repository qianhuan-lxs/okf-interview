---
type: question
id: algorithms/hashing/bloom-filter-bitmap
title: 布隆过滤器 + 位图 (概率判断/HyperLogLog/缓存穿透)
category: algorithms
subcategory: hashing
difficulty: medium
tags: [bloom-filter, bitmap, hyperloglog, probabilistic, cache-penetration, data-structure]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-07-05
---

# 布隆过滤器 + 位图 (概率判断/HyperLogLog/缓存穿透)

## 问题描述

布隆过滤器是什么？为什么有假阳性没假阴性？位图能做什么？HyperLogLog 怎么计数？

## 解答

## 一、位图（Bitmap）

**用每一位（bit）表示一个元素是否存在**。N 个元素 → N bit。
- 例：10 亿整数是否存在 → 10^9 bit ≈ 125 MB（远小于 HashSet 的几 GB）。
- 操作：`set(i)` → `arr[i/64] |= 1<<(i%64)`；`get(i)` → `(arr[i/64]>>(i%64))&1`。
- 适合**稠密整数集合**（如 ID 范围 0~10^9）。
- Java `BitSet`、Redis `SETBIT`/`GETBIT`。

### 应用
- 用户签到（按天 1 bit）。
- UV 去重（粗粒度）。
- 布隆过滤器底层。
- 大整数排序/去重（10 亿手机号排序用位图最省）。

## 二、布隆过滤器（Bloom Filter）

**概率型数据结构**，判断"元素是否在集合里"：
- **一定准确说"不在"**（无假阴性）。
- **可能误判说"在"**（假阳性，false positive）。

### 结构
- 一个 m 位的位数组（初始全 0）。
- k 个独立哈希函数。

### 插入
```
add(x):
  for i in 1..k:
    pos = h_i(x) % m
    bit[pos] = 1
```

### 查询
```
contains(x):
  for i in 1..k:
    pos = h_i(x) % m
    if bit[pos] == 0: return false   // 任一位为 0 → 一定不在
  return true                          // 全为 1 → 可能在（或假阳性）
```

### 为什么有假阳性没假阴性
- **没假阴性**：插入时所有 h_i(x) 对应位都置 1，查询时这些位必然都 1。
- **有假阳性**：别的元素可能恰好把 x 的所有位都置了 1 → 误判在。

### 假阳性率
- 公式（近似）：`p ≈ (1 - e^(-kn/m))^k`，n = 已插元素数，m = 位数，k = 哈希数。
- 实际配置：m、k 按"预期元素数 n + 目标假阳性率 p"算。
- 例：n=1亿、p=1% → m≈958M bit（~114MB），k=7。
- p 调小 → m 增大；n 超预期 → p 上升。

### 优缺点
- 优点：**空间极省**（1 亿元素 100+ MB vs HashSet 几 GB）、O(k) 查询、保密（不存原值）。
- 缺点：**假阳性**、**不支持删除**（标准版，多位被多个元素共享；Counting Bloom Filter 可删）。

## 三、Counting Bloom Filter（可删）

- 每位用计数器（4 bit/8 bit）代替 1 bit，插入 +1 删除 -1。
- 代价：内存翻几倍。
- 注意计数器溢出。

## 四、应用

### 1. 缓存穿透防护（最经典）
- 缓存穿透：查一个 DB 没有的 key，每次都打到 DB。
- 用布隆过滤器先判：说"不在" → 直接返回，不查 DB。
- 说"在" → 再查缓存/DB（可能是假阳性，但概率低）。
- 配合：DB 写入时同步 `add` 到布隆过滤器。

### 2. 邮箱/用户名重复检测
- 海量用户，判重用 HashSet 内存吃紧 → 布隆过滤器，假阳性时再回查 DB 确认。

### 3. 黑名单过滤
- URL 黑名单、IP 黑名单 → 布隆过滤器快速判。

### 4. 爬虫 URL 去重
- 已爬 URL 进布隆过滤器，新 URL 查 → 说"不在"才爬。

### 5. HBase/LevelDB SSTable 查询加速
- 每个 SSTable 配一个布隆过滤器 → 查 key 时先过滤，避免无谓磁盘读。

## 五、HyperLogLog（基数估计）

**估算集合去重后元素数（基数）**，误差 ~0.81%，内存固定（Redis 实现 12KB）。
- 例：UV 统计，10 亿访问去重计数。
- 比 HashSet（存所有元素）省几个数量级。
- Redis `PFADD`/`PFCOUNT`/`PFMERGE`。
- 不存元素本身，只估数。

## 六、对比

| 结构 | 空间 | 精确 | 支持 | 适合 |
| --- | --- | --- | --- | --- |
| **HashSet** | O(n) | 精确 | 增删查 | 通用去重 |
| **Bitmap** | O(max_value) | 精确 | 增删查 | 稠密整数 |
| **Bloom Filter** | O(n) 但常数小 | **有假阳性** | 增查（删要 Counting） | 海量存在性判断 |
| **HyperLogLog** | 固定 12KB | **~0.81% 误差** | 增+估数（不查单元素） | 基数估计（UV） |

## 易错点
- 布隆过滤器当精确 → 有假阳性，业务要容忍。
- 以为布隆过滤器能删 → 标准版不能，要用 Counting Bloom Filter。
- 元素数超预期 → 假阳性率飙升，要按预期 n 留余量配 m。
- 位图当万能 → 仅适合稠密整数，稀疏（如 UUID）不划算。
- HyperLogLog 当精确计数 → 是估算，误差 ~0.81%。
- 缓存穿透布隆过滤器忘记同步 → DB 写入后要 `add` 到布隆过滤器，否则永远说"不在"。

## 延伸

- 关联题：[[algorithms/heap/heap-data-structure.md]]
- 关联题：[[algorithms/linked-lists/lru-cache-implementation.md]]
- 关联题：[[databases/redis/redis-data-structures.md]]
