---
type: question
id: devops/devops-direction-understanding
title: 对 DevOps 方向的了解
category: devops
subcategory: devops
difficulty: easy
tags: [devops, concept, culture]
languages: []
role: [ai-app, sde, backend]
companies: [OPPO]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 对 DevOps 方向的了解

## 问题描述
你对 DevOps 这个方向了解吗？

## 解答

### DevOps = Development + Operations
不是某个工具，而是**文化 + 实践 + 工具**，目标：缩短从代码到生产的周期、提升交付质量与频率。

### 核心实践
1. **CI/CD**：自动化构建、测试、部署。
2. **IaC（基础设施即代码）**：Terraform / Pulumi / Ansible，环境可版本化可复现。
3. **容器化 + 编排**：Docker / Kubernetes。
4. **可观测性**：Metrics（Prometheus）+ Logs（Loki/ELK）+ Traces（OpenTelemetry/SkyWalking）。
5. **GitOps**：ArgoCD/Flux，Git 作为唯一真相源。
6. **SRE 实践**：SLI/SLO/Error Budget、错误预算驱动发布节奏。
7. **安全左移（DevSecOps）**：镜像扫描、依赖扫描、密钥扫描进流水线。

### 岗位技能栈
- Linux/网络基础。
- 至少一门脚本语言（Python/Go/Shell）。
- Docker/K8s 实操。
- CI/CD 工具（Jenkins/GitLab CI/Argo）。
- 监控告警体系。
- IaC。

### 与"开发"的关系
DevOps 不只是运维的事，是让开发能自助发布、自助运维，强调**共同责任**。

## 延伸

## 延伸

- 关联题：[[devops/cicd-pipeline-jenkins]]
- 关联题：[[devops/k8s-environment-labels-resource-management]]
