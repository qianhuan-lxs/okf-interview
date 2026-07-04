---
type: question
id: languages/java/jdk17-new-features
title: JDK 17 新特性
category: languages
subcategory: java
difficulty: medium
tags: [jdk17, jvm, java, features, lts]
languages: []
role: [ai-app, sde, backend]
companies: [中泓一线]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# JDK 17 新特性

## 问题描述
JDK 17 有什么新特性？抛开语法不说，JDK 层面有什么新的？

## 解答

JDK 17 是 LTS（2021.09），从 8/11 升级主要收益。

### 语法/API
- **Records**（14 预览，16 正式）：`record Point(int x, int y) {}` 自动生成 equals/hashCode/toString。
- **Sealed Classes**（17 正式）：`sealed interface Shape permits Circle, Square;` 限制继承。
- **Pattern Matching for instanceof**（16 正式）：`if (o instanceof String s) ...`。
- **Switch 表达式**（14 正式）：`case "a" -> 1;`。
- **Text Blocks**（15 正式）：三引号 `"""..."""` 多行字符串。
- **Helpful NullPointerExceptions**：NPE 指明哪个变量为 null。

### JDK/JVM 层面（面试官追问重点）
- **ZGC**：低延迟垃圾回收器，亚毫秒停顿（17 时正式 production-ready，支持 16GB~16TB 堆）。
- **G1** 进一步优化（NUMA 感知、堆 Region 更灵活）。
- **Deprecated Security Manager**：逐步废弃，未来用 module + JEP 411。
- **Strongly Encapsulate JDK Internals**：默认封锁 `--add-opens`，反射访问 JDK 私有 API 受限（影响很多老库如 Lombok、ReflectASM、Spring AOP 早期版本）。
- **Packaging Tool**（jpackage，16 正式）：原生可执行包，无需 JVM。
- **Foreign Function & Memory API**（孵化）：替代 JNI 访问本地代码/堆外内存。

### 生态
- Spring Boot 3 要求 JDK 17+。
- GC 选型：低延迟用 ZGC/Shenandoah；吞吐用 G1（默认）。

## 延伸

## 延伸

- 关联题：[[languages/java/jvm-garbage-collection]]
- 关联题：[[languages/java/g1-gc-changes]]
