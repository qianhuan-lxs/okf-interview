---
type: question
id: behavioral/八股-attitude-and-disliked-java
title: 八股态度 / Java 最讨厌的地方 / 设计模式偏好
category: behavioral
subcategory: behavioral
difficulty: easy
tags: [behavioral, java, design-pattern, opinion, soft]
languages: []
role: [ai-app, sde, backend]
companies: [安克创新]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 八股态度 / Java 最讨厌的地方 / 设计模式偏好

## 问题描述
八股重要吗？高中生背得应该比你快吧？Java 最讨厌的地方？最常用/最优雅的设计模式？

## 应对要点

### 八股重要吗
- 重要但不该是全部：八股是**地基**（并发/JVM/网络/数据库），决定能不能答上来；项目深挖和系统设计决定上限。
- "高中生背得比你快"——反驳点：八股不是纯背诵，要能解释原理 + 联系项目取舍，这是经验优势。

### Java 最讨厌的地方
给**真实但有建设性**的回答，避免纯吐槽：
- **啰嗦**：getter/setter/equals/hashCode/toString 样板（Lombok / Records 缓解）。
- **类型系统偏弱**：擦除泛型、数组协变坑。
- **JVM 启动慢、内存大**：云原生时代对微服务不友好（GraalVM Native Image 缓解）。
- **历史包袱**：Date/Calendar 设计糟糕（java.time 才修复）。

### 最常用 / 最优雅的设计模式
- 常用：模板方法（Spring XxxTemplate）、策略（消除 if-else）、建造者（链式构造）、责任链（Filter/Interceptor）。
- 最优雅示例：**策略 + 工厂** 消除长 if-else；或 **观察者 / 事件总线** 解耦。

## 延伸

## 延伸

- 关联题：[[languages/java/template-method-pattern]]
- 关联题：[[behavioral/career-planning-engineering-vs-pm]]
