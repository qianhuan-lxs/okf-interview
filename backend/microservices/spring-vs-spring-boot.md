---
type: question
id: backend/microservices/spring-vs-spring-boot
title: Spring 和 Spring Boot 的区别
category: backend
subcategory: microservices
difficulty: easy
tags: [spring, spring-boot, java]
languages: []
role: [ai-app, sde, backend]
companies: [海颐]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# Spring 和 Spring Boot 的区别

## 解答

| 维度 | Spring | Spring Boot |
| --- | --- | --- |
| 定位 | 框架（IoC/AOP 容器 + 生态） | 之上做的"约定配置 + 起步依赖"封装 |
| 配置 | 大量 XML / 注解，需手动配 | 自动配置 + application.yml，零 XML |
| 依赖 | 手动管 jar 版本 | starter 聚合版本，开箱即用 |
| 内嵌容器 | 需部署 war 到 Tomcat | 内嵌 Tomcat/Jetty/Undertow，jar 直接跑 |
| 监控 | 自建 | actuator 开箱（/health /metrics） |
| 生产 | 配一堆才能跑 | `java -jar` 即跑 |

一句话：Spring 是引擎，Spring Boot 是装好引擎+座椅+方向盘的整车，开箱即开。

## 延伸

## 延伸

- 关联题：[[backend/microservices/spring-boot-autoconfig]]
- 关联题：[[backend/microservices/spring-ioc-di-injection]]
