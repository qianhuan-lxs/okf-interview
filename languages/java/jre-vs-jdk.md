---
type: question
id: languages/java/jre-vs-jdk
title: JRE 和 JDK 的区别
category: languages
subcategory: java
difficulty: easy
tags: [jre, jdk, java, basics]
languages: []
role: [ai-app, sde, backend]
companies: [海颐]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# JRE 和 JDK 的区别

## 解答
- **JRE (Java Runtime Environment)** = JVM + 核心类库（rt.jar / java.base 模块）。能**运行** Java 程序，不能编译。
- **JDK (Java Development Kit)** = JRE + 开发工具（javac / java / jdb / jstack / jmap / jar ...）。能**开发 + 运行**。

关系：`JDK ⊃ JRE ⊃ JVM`。

JDK 11+ 起不再单独提供 JRE 发行包（模块化后用 `jlink` 按需裁出运行时）。

## 延伸

## 延伸

- 关联题：[[languages/java/jdk17-new-features]]
