---
type: question
id: backend/microservices/spring-boot-autoconfig
title: Spring Boot 自动配置原理
category: backend
subcategory: microservices
difficulty: medium
tags: [spring-boot, autoconfig, spring, java]
languages: []
role: [ai-app, sde, backend]
companies: [恩士讯, 海颐]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# Spring Boot 自动配置原理

## 问题描述
Spring Boot 的自动配置原理是什么？

## 解答

### 入口：@SpringBootApplication
- = `@SpringBootConfiguration` + `@EnableAutoConfiguration` + `@ComponentScan`。

### 核心：@EnableAutoConfiguration
- 通过 `@Import(AutoConfigurationImportSelector.class)` 引入选择器。
- `AutoConfigurationImportSelector.selectImports()` 调 `SpringFactoriesLoader.loadFactoryNames(...)`，从所有 jar 的 `META-INF/spring.factories`（2.7+ 改用 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`）加载 `EnableAutoConfiguration` 配置的全限定名列表。
- 加载后逐个 `@Conditional` 过滤：
  - `@ConditionalOnClass` —— classpath 有指定类才生效（如引入 Redis starter 才有 RedisAutoConfig）。
  - `@ConditionalOnMissingBean` —— 用户没自定义才生效（默认配置可被覆盖）。
  - `@ConditionalOnProperty` —— 配置项满足才生效。
  - `@ConditionalOnWebApplication` 等。

### 优势
- "约定大于配置"：引入 starter 即生效默认配置。
- 用户自定义 Bean 优先（@ConditionalOnMissingBean 兜底）。

### 自定义 starter
- 写 `XxxAutoConfiguration` + `@ConditionalOnClass` + `@ConditionalOnProperties`。
- 在 `META-INF/spring/...AutoConfiguration.imports` 注册。
- 配 `@ConfigurationProperties` 暴露配置项。

## 易错点
- 以为自动配置全量加载 —— 实际是按 Conditional 动态裁剪。
- 排查"为什么没生效"：开 `--debug` 看 `Conditions Evaluation Report`。

## 延伸

## 延伸

- 关联题：[[backend/microservices/spring-vs-spring-boot]]
- 关联题：[[backend/microservices/spring-ioc-di-injection]]
- 关联题：[[languages/java/template-method-pattern]]
