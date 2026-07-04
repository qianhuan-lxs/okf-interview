---
type: question
id: backend/microservices/spring-cloud-microservice-ecosystem
title: Spring Cloud 微服务生态
category: backend
subcategory: microservices
difficulty: medium
tags: [spring-cloud, microservices, service-discovery, gateway, config]
languages: []
role: [ai-app, sde, backend]
companies: [中泓一线]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# Spring Cloud 微服务生态

## 问题描述
Spring Cloud 有吗？微服务的这些生态应该是不是？

## 解答

Spring Cloud 是微服务治理全家桶，分两套主流栈：**Netflix（停更）** 和 **Alibaba**。

| 治理能力 | Spring Cloud Netflix | Spring Cloud Alibaba |
| --- | --- | --- |
| 注册中心 | Eureka | Nacos / Eureka |
| 配置中心 | Config + Bus | Nacos Config |
| 网关 | Zuul（1 停更）/ Spring Cloud Gateway | Gateway / Higress |
| 负载均衡 | Ribbon（停更）→ LoadBalancer | LoadBalancer / Dubbo 内置 |
| 声明式调用 | Feign / OpenFeign | OpenFeign / Dubbo RPC |
| 熔断限流 | Hystrix（停更）→ Resilience4j | Sentinel |
| 链路追踪 | Sleuth + Zipkin | SkyWalking / Zipkin |
| 分布式事务 | — | Seata |

### 核心组件职责
- **注册中心**：服务上下线发现，心跳保活。
- **配置中心**：动态配置，热刷新（`@RefreshScope`）。
- **网关**：统一入口、路由、鉴权、限流、跨域。
- **熔断器**：下游故障时快速失败、降级，防雪崩。
- **RPC**：服务间调用。

### 选型建议（2026）
- 新项目：Nacos + Gateway + OpenFeign + Sentinel + Seata。
- 监控：SkyWalking / OpenTelemetry + Prometheus + Grafana + Loki。

## 延伸

## 延伸

- 关联题：[[backend/microservices/spring-boot-autoconfig]]
- 关联题：[[distributed-systems/cap-theory]]
- 关联题：[[backend/microservices/microservice-user-context-propagation]]
