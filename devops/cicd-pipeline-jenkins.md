---
type: question
id: devops/cicd-pipeline-jenkins
title: CI/CD 流水线 (Jenkins → 构建 → 镜像 → 部署)
category: devops
subcategory: devops
difficulty: medium
tags: [ci-cd, jenkins, docker, pipeline, devops]
languages: []
role: [ai-app, sde, backend]
companies: [OPPO]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# CI/CD 流水线 (Jenkins → 构建 → 镜像 → 部署)

## 问题描述
容器化部署负责的两个功能点？具体流水线打包流程？用过 Jenkins 吗？

## 解答

### 典型流水线
```
1. Code Commit  → Git push 触发 webhook
2. CI 阶段
   - Checkout / 拉代码
   - 静态检查（lint、SonarQube）
   - 单元测试 + 覆盖率
   - 构建（Maven/Gradle/Go build）
   - 构建 Docker 镜像 → 推 Harbor
   - 镜像扫描（Trivy/Clair）
3. CD 阶段
   - 改 K8s 部署镜像 tag
   - kubectl apply / Helm upgrade
   - 滚动更新
   - 健康检查 / 灰度
4. 验证：smoke test、监控告警
```

### Jenkinsfile（声明式）
```groovy
pipeline {
  agent any
  stages {
    stage("Build")   { steps { sh "mvn -B clean package" } }
    stage("Image")   { steps { sh "docker build -t reg/app:${env.BUILD_NUMBER} ." } }
    stage("Push")    { steps { sh "docker push reg/app:${env.BUILD_NUMBER}" } }
    stage("Deploy")  { steps { sh "kubectl set image deploy/app app=reg/app:${env.BUILD_NUMBER}" } }
  }
}
```

### 工具栈
- 流水线：Jenkins / GitLab CI / GitHub Actions / ArgoCD（GitOps）。
- 镜像仓库：Harbor。
- 部署：Helm / Kustomize / ArgoCD。

### OPPO 场景追问：状态机 & 资源泄露
- **状态机**：流水线任务有 pending/running/success/failed/canceled，状态机驱动 UI 与重试。
- **资源泄露**：构建 pod 没清理、Docker layer 堆积、临时 volume 没回收 → 定期 GC + 配额。

## 延伸

## 延伸

- 关联题：[[devops/k8s-rolling-update-health-probe]]
- 关联题：[[devops/offline-deployment]]
