---
type: question
id: ml-ai/observability/claude-code-hooks-observability
title: Claude Code hooks 做可观测性 (事件 / 协议 / 管道模式)
category: ml-ai
subcategory: observability
difficulty: hard
tags: [claude-code, hooks, observability, telemetry, otel, agent]
languages: []
role: [ai-app, sde, backend, devops]
companies: []
source: ""
status: reviewed
timestamp: 2026-05-26
---

# Claude Code hooks 做可观测性 (事件 / 协议 / 管道模式)

## 问题描述

Claude Code 怎么做可观测性？hooks 在其中起什么作用？有哪些事件？怎么把 hook 事件喂给 Langfuse/OTel？

## 一、Hooks 是 CC 的"确定性控制层"

**Hook = 在 agent 生命周期特定点触发的 shell 命令。** 不是模型决定要不要跑——是确定性的，框架保证跑。这让可观测性、安全、合规**不依赖模型记得**。

配置在 `.claude/settings.json` 或 SDK：
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Bash|Write|Edit",
      "hooks": [{ "type": "command", "command": "./scripts/trace.sh" }]
    }]
  }
}
```

## 二、协议

- **stdin**：hook 脚本收一个 JSON 对象（事件 + 上下文：tool name / input / output / session id / cwd 等）。
- **stdout**：返回 JSON 控制行为（`permissionDecision` / `additionalContext` / `updatedToolOutput` 等）。
- **exit code 2**：阻塞（PreToolUse）或拒绝（UserPromptSubmit）。
- hook 失败**永不阻塞 session**（graceful）。

## 三、事件清单（2026，32+ events）

按用途分四组，**可观测性相关加粗**。

### Tool 生命周期
| Event | 触发 | 能阻塞? | 可观测用法 |
| --- | --- | --- | --- |
| `PreToolUse` | 工具调用前 | ✅ exit 2 | **记录 agent 意图** |
| `PostToolUse` | 工具成功后 | ❌（已执行） | **记录工具结果 / 自动格式化 / 推 CI** |
| `PostToolUseFailure` | 工具失败后 | ❌ | **记录失败 + 错误归因** |
| `PostToolBatch` | 一批并行工具调用结束 | ✅ 停 loop | **批量提交 trace** |
| `PermissionRequest` | 权限对话框 | ✅ deny | **审计权限决策** |
| `PermissionDenied` | auto classifier 拒绝 | ❌ | **记录被拒原因** |

### Session 生命周期
| Event | 触发 | 用法 |
| --- | --- | --- |
| `SessionStart` | session 开始/resume | **初始化 trace、注入项目上下文** |
| `SessionEnd` | session 结束 | **flush trace、写 summary、清理** |
| `Setup` | `--init/--maintenance` 模式 | 初始化 |
| `ConfigChange` | 配置变更 | **审计配置改动** |
| `InstructionsLoaded` | instructions 加载 | 追踪上下文来源 |

### 对话 / 上下文
| Event | 触发 | 用法 |
| --- | --- | --- |
| `UserPromptSubmit` | 用户提交 prompt | **审计 prompt、敏感词检测** |
| `Notification` | 通知 | **镜像到 Slack / 观测栈** |
| `PreCompact` / `PostCompact` | 上下文压缩前后 | **记录被压缩丢了什么** |
| `FileChanged` | `.env` 等文件变 | 安全告警 |

### Agent / 子 agent
| Event | 触发 | 用法 |
| --- | --- | --- |
| `SubagentStart` / `SubagentStop` | 子 agent 起/停 | **追踪 team 组成 + 子任务结果** |
| `Stop` / `StopFailure` | 顶层 turn 结束 / 失败 | **结束 root span、记录 stopReason** |
| `InstructionsLoaded` | nested 遍历 | 上下文溯源 |

### Matcher（事件子过滤）
- Tool 类：`Bash` / `Edit|Write` / `mcp__.*`
- SessionStart：`startup` / `resume` / `clear` / `compact`
- Subagent：`general-purpose` / `Explore` / `Plan`
- 等。

## 四、可观测性管道模式（Pattern 3）

每个事件都喂给监控系统：
```
SessionStart  → 起 root trace + 注入 user/session
PreToolUse    → 起 execute_tool span（记录意图/参数）
PostToolUse   → 结束 span（记录结果/latency）→ 自动格式化/推 CI
PreCompact    → 记录被压缩的上下文
SubagentStart/Stop → 子 agent span
Stop          → 结束 root trace + 写 summary
```

实现：每个 hook 是 shell 脚本，`cat stdin | jq` 提取字段，`curl` POST 到 OTel collector / Langfuse ingestion API。

## 五、原生 OTel（不用自己写 hook）

设 `CLAUDE_CODE_ENABLE_TELEMETRY=1`，CC 直接发 OTLP trace 到配置的 collector，无需 hook。适合零侵入基础可观测；hook 用于叠加自定义维度（业务关联、合规审计、自动后处理）。

## 六、PreToolUse vs PostToolUse 的可观测语义

- **PreToolUse**：记录 agent **意图**（要干什么），可阻塞。可观测 + 安全双职责。
- **PostToolUse**：记录工具**结果**，**observability-only**——已经发生了，不能撤销，但能反应（格式化文件、跑测试、推 CI、redact diff、注入 `additionalContext` 让 Claude 看到反馈）。

## 七、最小可观测 hook 示例

```bash
#!/usr/bin/env bash
# ./scripts/trace.sh — PostToolUse hook → Langfuse
input=$(cat)
tool=$(echo "$input" | jq -r .tool_name)
latency=$(echo "$input" | jq -r .latency_ms)
session=$(echo "$input" | jq -r .session_id)
curl -s -X POST https://cloud.langfuse.com/api/public/observations   -H "Authorization: Basic $LANGFUSE_AUTH"   -d "{"name":"$tool","type":"span","traceId":"$session","metadata":$input}"
```

## 易错点

- PostToolUse 想"撤销"工具 → 不可能，已经执行。改成 PreToolUse 阻塞 + 校验。
- hook 脚本阻塞（同步等慢服务）→ 拖慢 agent。用 `background_tasks` 异步发，或加 timeout。
- 不设 graceful → hook 挂了拖垮 session（CC 默认 graceful，但自己写脚本别忘超时）。
- matcher 写错（如 `Bash` 写成 `bash`）→ hook 不触发。

## 延伸

## 延伸

- 关联题：[[ml-ai/observability/langfuse-observability-design]]
- 关联题：[[ml-ai/observability/codex-opencode-observability]]
- 关联题：[[ml-ai/observability/opentelemetry-genai-semantic-conventions]]
- 关联题：[[ml-ai/agent/skill-meaning-loading-evolution]]
