---
type: question
id: languages/java/template-method-pattern
title: 模板方法模式
category: languages
subcategory: java
difficulty: easy
tags: [design-pattern, template-method, java, oop]
languages: []
role: [ai-app, sde, backend]
companies: [中泓一线]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 模板方法模式

## 问题描述
模板方法模式简单介绍一下？

## 解答
**模板方法模式**：在父类定义算法骨架（一个 `final` 的 templateMethod 串联步骤），把可变步骤声明为抽象方法由子类实现。即"骨架不变，步骤可换"。

```java
abstract class AsyncTask {
    public final void run() {       // 模板方法，final 防止子类改骨架
        prepare();
        doExecute();                // 抽象步骤
        cleanup();
    }
    protected void prepare() { /* 默认实现 */ }
    protected abstract void doExecute();
    protected void cleanup() { /* 默认实现 */ }
}

class DownloadTask extends AsyncTask {
    @Override protected void doExecute() { /* 下载逻辑 */ }
}
```

### 优点
- 复用骨架，避免子类重复编排。
- 钩子方法（hook）提供默认实现，子类按需覆盖。

### 经典应用
- Spring `JdbcTemplate / RestTemplate / RedisTemplate` —— 都是模板方法 + Callback。
- `AbstractApplicationContext.refresh()` 是模板方法，子类 refreshBeanFactory 等步骤可定制。
- HttpServlet `service()` 调 doGet/doPost。

### 与策略模式区别
- 模板方法：用**继承**，子类覆盖个别步骤；骨架固定。
- 策略：用**组合**，整个算法可替换；上下文不变。

## 延伸

## 延伸

- 关联题：[[backend/microservices/spring-boot-autoconfig]]
