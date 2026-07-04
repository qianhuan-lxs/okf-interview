---
type: question
id: devops/offline-deployment
title: 离线部署经验
category: devops
subcategory: devops
difficulty: medium
tags: [offline-deployment, air-gapped, kubernetes, devops]
languages: []
role: [ai-app, sde, backend]
companies: [OPPO]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 离线部署经验

## 问题描述
离线部署经验？

## 解答

### 场景
内网/隔离环境（政企、制造业、工厂产线）无法拉公网镜像和包，需"打包—搬运—离线安装"。

### 流程
1. **公网侧准备**
   - 把镜像导出：`docker save -o app.tar reg/app:v1`。
   - 把依赖镜像（K8s 组件、网络插件 CNI、CSI、Helm chart 资源）一起 save。
   - 把二进制（kubeadm/kubelet/kubectl/etcd）、rpm/deb 包下载归档。
   - 离线 chart：`helm template` 渲染好，或 chart + 依赖打包。
2. **搬运**：U 盘 / 内网 FTP / jumpbox 中转。
3. **内网侧安装**
   - 私有镜像仓库：Harbor（离线装）或临时 `docker load < app.tar`。
   - K8s 离线初始化：`kubeadm init --image-repository=内网仓库`。
   - `helm install` 用本地 chart。
4. **验证**：smoke test、监控自检。

### 工具
- **sealos**：一键离线装 K8s 集群。
- **KubeKey**（KubeSphere）：离线包制作。
- **rainbond**：离线一体化。

### 坑
- CPU 架构差异（x86 打包到 ARM 跑）→ 多架构镜像或分开打。
- 镜像 layer 重复 → 合并 save 减体积。
- 版本一致性：K8s 组件、CNI、CSI 版本兼容矩阵。
- 配置里的公网域名/registry 改成内网。

## 延伸

## 延伸

- 关联题：[[devops/cicd-pipeline-jenkins]]
