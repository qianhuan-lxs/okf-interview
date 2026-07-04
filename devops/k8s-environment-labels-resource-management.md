---
type: question
id: devops/k8s-environment-labels-resource-management
title: K8S 环境标签 / 资源管理
category: devops
subcategory: devops
difficulty: medium
tags: [kubernetes, labels, resource-quota, devops]
languages: []
role: [ai-app, sde, backend]
companies: [有赞, 探迹]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# K8S 环境标签 / 资源管理

## 问题描述
K8S 资源为什么要统一打环境标签？环境标签打好之后的作用？资源不足时清理的优先级？

## 解答

### 统一打环境标签
- 给所有资源打 `env=dev/test/prod`、`team=xxx`、`tier=frontend/backend`。
- 作用：
  1. **Selector 路由**：Service 用 `selector` 选同标签 Pod。
  2. **NetworkPolicy**：按标签限定网络可达。
  3. **ResourceQuota / LimitRange**：按 namespace/标签分资源配额。
  4. **监控/告警/成本分摊**：按标签聚合 Prometheus 指标、计算团队成本。
  5. **清理策略**：dev 资源夜间回收，prod 长驻。

### 资源管理
- **requests**（调度依据，保证量）/ **limits**（上限，超则 throttle/kill）。
- CPU limit 超则 throttle（cgroup）；memory limit 超则 OOMKilled。
- **ResourceQuota** 限 namespace 总量；**LimitRange** 限单个 pod 默认/范围。

### 资源不足清理优先级
- **PriorityClass**：低优先级 pod（如批处理）先被驱逐。
- **QoS 等级**：Guaranteed（req=limit）> Burstable（req<limit）> BestEffort（无 req/limit）。节点压力时 BestEffort 先杀。
- **节点压力驱逐**：kubelet 在内存/磁盘压力时按 QoS + Priority 驱逐。
- **dev 环境定时清理**：CronJob 夜间 scale 0 或删非关键 deployment。

## 易错点
- 不设 requests → 调度器不知道需求，节点超卖。
- memory limit 设小于 JVM 堆 + 元空间 + 堆外 → OOMKilled（Java 应用 Xmx 应 < limit - headroom）。

## 延伸

## 延伸

- 关联题：[[devops/k8s-rolling-update-health-probe]]
- 关联题：[[ml-ai/mcp/sandbox-vs-normal-container]]
