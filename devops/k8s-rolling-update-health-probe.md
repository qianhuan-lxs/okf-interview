---
type: question
id: devops/k8s-rolling-update-health-probe
title: K8S 滚动更新 / 健康检查探针
category: devops
subcategory: devops
difficulty: medium
tags: [kubernetes, rolling-update, liveness, readiness, probe, devops]
languages: []
role: [ai-app, sde, backend]
companies: [OPPO]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# K8S 滚动更新 / 健康检查探针

## 问题描述
K8S 滚动更新 / 健康检查探针（OPPO 主管面预测题）。

## 解答

### 三种探针
| 探针 | 作用 | 失败后果 |
| --- | --- | --- |
| **livenessProbe** | 容器是否"活着" | 重启容器 |
| **readinessProbe** | 容器是否"就绪接流量" | 从 Service Endpoints 摘除，不重启 |
| **startupProbe**（1.16+） | 启动是否完成 | 启动前禁用 liveness/readiness，避免慢启动被杀 |

探针机制：HTTP GET / TCP socket / exec command。

### 滚动更新（RollingUpdate）
- `strategy.type=RollingUpdate`，`maxSurge`（最多多出多少副本）、`maxUnavailable`（最多不可用多少）。
- 流程：新 pod 起 → readiness 通过 → 旧 pod 摘流量并终止。
- 始终保持 `replicas - maxUnavailable` 个可用，零停机。

### 配合探针
- 启动慢的应用配 startupProbe + 较大 failureThreshold。
- readiness 探针保证新 pod 健康才接流量。
- liveness 探针检测死锁等假死，重启恢复。

### 常见坑
- liveness 探针过严 → 临时抖动导致雪崩重启。
- readiness 与 liveness 用同一接口 → 就绪失败也重启。
- 滚动更新时 maxUnavailable=0 但 readiness 没配 → 旧 pod 等不到新 pod ready，超时卡死。

## 延伸

## 延伸

- 关联题：[[devops/cicd-pipeline-jenkins]]
- 关联题：[[devops/k8s-environment-labels-resource-management]]
