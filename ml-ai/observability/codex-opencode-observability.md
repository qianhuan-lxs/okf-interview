---
type: question
id: ml-ai/observability/codex-opencode-observability
title: Codex CLI / OpenCode 的可观测性与 hooks
category: ml-ai
subcategory: observability
difficulty: medium
tags: [codex, opencode, hooks, observability, otel, agent]
languages: [typescript, python]
role: [ai-app, sde, backend, devops]
companies: []
source: ""
status: reviewed
timestamp: 2026-05-26
---

# Codex CLI / OpenCode 的可观测性与 hooks

## 问题描述

OpenAI Codex CLI 和 OpenCode (SST) 怎么做可观测性？hooks 系统什么样？和 Claude Code 比有什么差异？

## 一、Codex CLI hooks（实验性，2026-03 v0.114 起步）

### 启用
在 `~/.codex/config.toml`：
```toml
[features]
codex_hooks = true   # 默认关，必须显式开
```
然后 `~/.codex/hooks.json` 或项目 `.codex/hooks.json` 定义 hook。**不开 flag hook 静默不触发**。

### 事件（PR #11067 + 文档）
| Event | 触发 | 能阻塞? |
| --- | --- | --- |
| `SessionStart` | session 开始/resume | ✅ `continue: false` |
| `PreToolUse` | 工具执行前 | ✅ deny |
| `PostToolUse` | 工具执行后 | ✅ `continue: false` |
| `UserPromptSubmit` | 用户提交 prompt | ✅ `continue: false` |
| `Stop` | agent turn 结束 | ✅ deny → 续问 |
| `SubagentStop` | 子 agent 结束 | — |
| `PreCompact` / `PostCompact` | 上下文压缩 | — |

### 协议
- JSON over stdio：stdin 收事件 JSON，stdout 返回 JSON 控制（`continue` / `systemMessage` / `hookSpecificOutput` / `permissionDecision: "deny"`）。
- exit 2 + stderr reason 也算 deny。
- 多个匹配 hook **并发跑，无顺序保证**。
- 默认 timeout 600s，可配 `timeout` / `timeoutSec`。

### ⚠️ 关键限制
- **PreToolUse/PostToolUse 目前只对 `Bash` 工具触发**——Read/Write/Edit/Apply Patch/web fetch/MCP 工具调用**不触发** hook。
- PreToolUse **只能 deny，不能 modify 工具输入**。
- 无 async hook 模式。
- 只支持 `"command"` handler 类型（不像 CC 多 handler）。
- `Stage::UnderDevelopment` 标记，API 可能变。
- 不像 CC 设 `CLAUDE_PROJECT_DIR` 环境变量；项目目录通过 stdin `cwd` 字段传。`CODEX_HOME`（默认 `~/.codex`）控配置/状态。

### 治理非 Bash 工具
hook 管 Bash，**MCP 工具走 MCP connector 路径**：`[mcp_servers.acp]` 把非 Bash 工具路由到治理 MCP 端点，统一进审计日志。

## 二、OpenCode (SST) 的可观测性

### 插件系统（TS/JS，比 shell hook 富得多）
插件是导出函数的 TS/JS 模块，返回 `Hooks` 对象：
```ts
export const MyPlugin = async ({ client, $ }) => {
  return {
    "tool.execute.before": async (input) => {
      // 可改 tool 参数
    },
    "tool.execute.after": async (input) => {
      await client.app.log({ body: { message: "Tool done", tool: input.tool } });
    },
    event: async ({ event }) => {
      if (event.type === "session.idle") { /* ... */ }
    },
  };
};
```
通过 `Service.trigger(name, input, output)` 分发，插件错误 → 发 `Session.Event.Error` 到全局 bus。

### Hooks 清单
| Hook | 用途 | 可改 |
| --- | --- | --- |
| `config` | 注入 commands/agents/MCP servers | config |
| `tool` | 注册自定义工具 | — |
| `auth` | 注册 auth provider | — |
| `event` | 订阅所有系统事件（观察者） | — |
| `chat.message` | 处理入站消息 | message/parts |
| `chat.params` | 改 LLM 参数 | temperature/topP/options |
| `permission.ask` | 处理权限请求 | ask/deny/allow |
| `tool.execute.before` | 工具执行前 | **tool arguments** |
| `tool.execute.after` | 工具执行后 | **tool output** |
| `experimental.text.complete` | 生成后修改 | generated text |
| `experimental.session.compacting` | 压缩前注入领域上下文 | — |

### event 子类型（`event` hook 收）
- Session：`session.created/compacted/deleted/diff/error/idle/status/updated`
- File：`file.edited/file.watcher.updated`
- LSP：`lsp.client.diagnostics/lsp.updated`
- Message：`message.part.removed/updated/removed/updated`
- Permission：`permission.replied/updated`
- Tool：`tool.execute.after/before`
- Command：`command.executed`
- TUI：`tui.prompt.append/tui.command.execute/tui.toast.show`
- Server：`server.connected`

### 结构化日志
用 `client.app.log()`（**不要** `console.log`）：
```ts
await client.app.log({ body: { service: "my-plugin", level: "info", message: "...", extra: { foo: "bar" } } });
```
level：`debug/info/warn/error`。日志 JSONL 存 `.opencode-autopilot/` 或 `~/.local/share/opencode/log/`。

### OTel 插件（opencode-otel-plugin）
第三方 `felixti/opencode-otel-plugin` 自动 trace 每次 session，OTLP/HTTP 导任意 OTel 后端。
**trace 树**：
```
session (root)
├── chat (LLM 调用, gen_ai.operation.name=chat)
├── execute_tool {name} (bash/edit/write/glob/...)
├── session_compaction
└── ...
```
**属性**：`gen_ai.operation.name` / `gen_ai.tool.name` 等（合 OTel GenAI semconv）。
**metrics**：`opencode.session.request.count` / `opencode.session.compaction.count` / `opencode.file.changes` / `opencode.tool.invocations` / `opencode.vcs.operations`。
**配置**：`OTEL_EXPORTER_OTLP_ENDPOINT` / `OTEL_EXPORTER_OTLP_HEADERS` / `OTEL_OPENCODE_FILTERED_TOOLS`（排除 tool 不建 span）。

## 三、三者对比

| 维度 | Claude Code | Codex CLI | OpenCode |
| --- | --- | --- | --- |
| hook 形态 | shell 命令 | shell 命令 | TS/JS 插件 |
| 事件数 | 32+ | ~7 | ~10 hook + 数十 event 子类型 |
| 工具覆盖 | 全工具（Bash/Write/Edit/MCP/...） | **仅 Bash** | 全工具（tool.execute.before/after） |
| 能改 tool input | ✅ PreToolUse `updatedInput` | ❌ 只能 deny | ✅ `tool.execute.before` |
| 原生 OTel | `CLAUDE_CODE_ENABLE_TELEMETRY=1` | 无（靠 hook + MCP） | 第三方 `opencode-otel-plugin` |
| 成熟度 | 生产级 | 实验性 (Stage::UnderDevelopment) | 生产级（插件生态） |
| 异步 | `background_tasks` | 无 | 插件 async |
| 配置位置 | `.claude/settings.json` | `~/.codex/hooks.json` + `config.toml` flag | TS 插件模块 |

## 四、选型观察

- **可观测覆盖全工具 + 原生 OTel** → Claude Code（开 telemetry + PostToolUse hook 叠业务维度）。
- **Codex** → hook 只能管 Bash，要全工具可观测得叠 MCP connector 路径，或等官方扩 tool 覆盖。
- **OpenCode** → 插件系统能改 tool input/output、event 子类型最细、有现成 OTel 插件，TS 团队上手最快。

## 易错点

- Codex hook 不触发 → 没开 `codex_hooks=true` flag。
- Codex 想拦截 Write/Edit → hook 不支持，要走 MCP。
- OpenCode 用 `console.log` → 不进结构化日志，要用 `client.app.log()`。
- 以为 Codex hook 能 modify input → 只能 deny。

## 延伸

## 延伸

- 关联题：[[ml-ai/observability/claude-code-hooks-observability]]
- 关联题：[[ml-ai/observability/langfuse-observability-design]]
- 关联题：[[ml-ai/observability/opentelemetry-genai-semantic-conventions]]
