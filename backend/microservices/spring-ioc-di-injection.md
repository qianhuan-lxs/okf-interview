---
type: question
id: backend/microservices/spring-ioc-di-injection
title: Spring IOC / DI 注入方式
category: backend
subcategory: microservices
difficulty: easy
tags: [spring, ioc, di, java, injection]
languages: []
role: [ai-app, sde, backend]
companies: [海颐]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# Spring IOC / DI 注入方式

## 问题描述
说一下 Spring 的注入方式有哪一些？再说一下你对 IOC 的理解。

## 解答

### IOC（Inversion of Control）
- 对象创建和依赖关系**由容器管理**，而非对象自己 new。
- "控制"指对象创建控制权，反转 = 从对象转移到容器。
- 好处：解耦、易测试（mock）、生命周期统一。

### DI（Dependency Injection）—— IOC 的实现方式
- 容器主动把依赖"注入"对象，对象被动接收。

### 注入方式（3 种）
1. **构造器注入**（推荐）：`@Autowired` 在构造方法。不可变、强制依赖、易测、避免循环依赖（启动期暴露）。
2. **Setter 注入**：可选依赖，可重新注入。
3. **字段注入** `@Autowired private X x;`：最简洁但**不推荐**——不能 final、无法脱离容器测试、隐藏依赖。

### @Resource vs @Autowired
- `@Autowired` byType，可选 `@Qualifier` byName。
- `@Resource`（JSR-250）默认 byName，找不到再 byType。

### 循环依赖
- Spring 用三级缓存解决单例 setter/字段循环依赖：singletonObjects / earlySingletonObjects / singletonFactories。
- **构造器循环依赖无法解决**（对象都还没建出来）。
- Spring Boot 2.6+ 默认 `spring.main.allow-circular-references=false`。

## 易错点
- 字段注入 + 循环依赖能跑但埋雷；新代码强制构造器注入。

## 延伸

## 延伸

- 关联题：[[backend/microservices/spring-vs-spring-boot]]
- 关联题：[[backend/microservices/spring-boot-autoconfig]]
