---
type: question
id: databases/mysql/transaction-annotation-failure
title: 事务注解失效 / 代理层面失效解决
category: databases
subcategory: mysql
difficulty: medium
tags: [spring, transaction, aop, proxy, database]
languages: []
role: [ai-app, sde, backend]
companies: [恩士讯]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 事务注解失效 / 代理层面失效解决

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

## 延伸

- 关联题：[[databases/mysql/mysql-transaction-usage]]
- 关联题：[[backend/microservices/spring-ioc-di-injection]]
