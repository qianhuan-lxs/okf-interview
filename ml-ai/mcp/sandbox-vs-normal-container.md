---
type: question
id: ml-ai/mcp/sandbox-vs-normal-container
title: 容器化沙箱 vs 普通容器
category: ml-ai
subcategory: mcp
difficulty: medium
tags: [sandbox, container, security, code-execution]
languages: []
role: [ai-app, sde, backend]
companies: [华大制造, 北京用友]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 容器化沙箱 vs 普通容器

## 问题描述

容器化沙箱跟普通容器比有什么特殊？沙箱里起服务、执行什么任务？

## 解答

普通容器解决**隔离与部署**，AI 沙箱在此基础上叠加 **"执行不可信代码 / agent 产出的操作"** 的安全与生命周期治理。

| 维度 | 普通容器 | AI 沙箱 |
| --- | --- | --- |
| 信任假设 | 镜像可信 | 内部跑 **LLM 生成代码 / 工具产出**，不可信 |
| 网络 | 通常开放 | 严格出网白名单 / 全禁 |
| 文件系统 | 持久卷 | 临时 + 配额 + 投毒防护 |
| 资源 | 静态 limit | CPU/内存/时间/进程数硬限 + OOM kill |
| 权限 | 视情况 | 去 capability、rootless、seccomp 严控 |
| 生命周期 | 长驻 | **每会话/每任务起一个**，结束即销毁 |
| 可观测 | metrics | 完整 syscall/IO 录制，便于回放评测 |
| API | 无 | 提供"提交代码 / 装包 / 取结果"REST 接口 |

### 典型用途（华大场景）

- agent 把生成的 Python/SQL 丢进沙箱跑，拿结果回填。
- 多 agent 间传 excel，下游 agent 在沙箱里用 pandas 处理。
- 工具产出不可信结果，沙箱内二次校验。

### 强化手段

- **gVisor / Kata** — 用户态内核 / VM 级隔离，比 runc 更强。
- **Firejail / nsjail** — 轻量沙箱。
- **rootless + seccomp + AppArmor** — 多层降权。
- **eBPF 监控** — 录制异常 syscall。

## 易错点

- 直接用 docker 跑 LLM 生成代码而不去网/不限时——任意代码执行 RCE 风险。
- 沙箱复用跨会话——状态泄漏。

## 延伸

## 延伸

- 关联题：[[ml-ai/agent/multi-agent-orchestration-architecture]]
- 关联题：[[ml-ai/mcp/mcp-gateway-architecture]]
