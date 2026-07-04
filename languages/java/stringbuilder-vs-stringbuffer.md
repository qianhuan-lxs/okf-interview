---
type: question
id: languages/java/stringbuilder-vs-stringbuffer
title: StringBuilder 和 StringBuffer 的区别
category: languages
subcategory: java
difficulty: easy
tags: [stringbuilder, stringbuffer, java, basics]
languages: []
role: [ai-app, sde, backend]
companies: [海颐]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# StringBuilder 和 StringBuffer 的区别

## 解答

| 维度 | StringBuilder | StringBuffer |
| --- | --- | --- |
| 线程安全 | 否 | 是（synchronized） |
| 性能 | 高（无锁） | 低（锁开销） |
| 引入版本 | JDK 5 | JDK 1.0 |
| 适用 | 单线程拼接 | 多线程共享拼接 |

- 都继承 `AbstractStringBuilder`，底层是可变 char[]/byte[]，扩容 `原容量*2 + 2`。
- **单线程拼接优先 StringBuilder**；多线程共享才用 StringBuffer（实际极少见，更推荐用 `StringJoiner` 或不可变 + 锁外部控制）。
- 编译器会把 `+` 拼接优化成 StringBuilder.append（循环内 `+` 除外，循环内每次 new StringBuilder，应手动用 builder）。

## 延伸
