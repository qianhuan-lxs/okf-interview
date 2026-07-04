---
type: question
id: ml-ai/observability/claude-code-hooks-implementation
title: Claude Code hooks 的实现机制 (两层模型 / handler / exit code / matcher)
category: ml-ai
subcategory: observability
difficulty: hard
tags: [claude-code, hooks, implementation, sdk, exit-code, matcher, agent]
languages: [python, typescript]
role: [ai-app, sde, backend, devops]
companies: []
source: ""
status: reviewed
timestamp: 2026-05-26
---

# Claude Code hooks 的实现机制 (两层模型 / handler / exit code / matcher)

## 问题描述

Claude Code 的 hook 系统底层是怎么实现的？事件怎么分发、handler 怎么执行、exit code 怎么解读、matcher 怎么匹配、配置怎么加载和热重载？

## 一、为什么是 hooks 而不是 prompt

Prompt 指令合规率 70-90%——长会话/上下文压力/竞争优先级时会跳过。**Hooks 是系统级拦截器，在 LLM 推理链之外执行，100% 合规**。类比 Express 中间件：拦截 agent 的 tool call / session / permission 决策，而非 HTTP 请求。

## 二、两层实现模型

CC hook 有两种实现路径，SDK 把它们统一进同一个分发流程。

### 1. SDK 回调 hook（in-process）
直接在 SDK 里注册回调函数，同进程执行：

```python
# Python SDK
async def protect_env(input_data, tool_use_id, context):
    if input_data["tool_input"]["file_path"].endswith(".env"):
        return {"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "no .env writes"}}
    return {}

options = ClaudeSDKOptions(
    hooks={"PreToolUse": [HookMatcher(matcher="Write|Edit", hooks=[protect_env])]})
```

```typescript
// TypeScript SDK
const protectEnv: HookCallback = async (input, id, { signal }) => {
  if (input.tool_input.file_path.endsWith(".env")) {
    return { hookSpecificOutput: { hookEventName: "PreToolUse",
      permissionDecision: "deny", permissionDecisionReason: "no .env" } };
  }
  return {};
};
options = { hooks: { PreToolUse: [{ matcher: "Write|Edit", hooks: [protectEnv] }] } };
```

### 2. Shell 命令 hook（out-of-process，settings.json）
配在 `.claude/settings.json`，SDK 通过 `setting_sources`/`settingSources` 决定是否加载（默认 `query()` 开）：

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{ "type": "command", "command": "./scripts/guard.sh" }]
    }]
  }
}
```

**SessionStart / SessionEnd 在 Python SDK 没有 HookEvent 类型**——只能用 shell 命令 hook（settings.json）。TypeScript SDK 才有回调形式。

## 三、分发生命周期（一次事件怎么走完）

```
1. agent 执行中发生事件（PreToolUse / PostToolUse / Stop / ...）
2. SDK 检查该事件类型注册的 hook：
     - options.hooks 里的回调 hook
     - setting_sources 启用时，settings.json 里的 shell 命令 hook
3. 对每个 hook 做 matcher 测试（见第五节）→ 不匹配跳过
4. 执行匹配的 hook：
     - 回调 hook：直接 await 调用
     - command hook：spawn 子进程，stdin 管入 JSON，读 stdout/stderr
     - http/mcp_tool/prompt/agent handler：按各自协议
5. 解析输出 JSON（或 exit code）→ 提取 permissionDecision / updatedInput / additionalContext 等
6. 把决策应用到 agent 行为（阻塞 / 改输入 / 注入上下文 / 放行）
```

## 四、5 种 Handler 类型

| type | 机制 | 适用 | 阻塞可靠性 |
| --- | --- | --- | --- |
| `command` | spawn shell，pipe stdin JSON，读 stdout JSON/stderr | 结构化校验、lint、event 转发 | ✅ exit 2 阻塞 |
| `http` | POST JSON 到 endpoint；2xx 空=成功，2xx JSON=hook 输出，非 2xx=非阻塞错误 | 集中策略服务、Slack 通知 | ⚠️ 网络失败不阻塞 |
| `mcp_tool` | 转发给 MCP server 暴露的 tool；server 断开或 `isError:true` = 非阻塞错误 | 复用 MCP 工具能力 | ⚠️ 断连不阻塞，别用于强策略 |
| `prompt` | 单轮 Claude 决策，`$ARGUMENTS`=hook 输入 JSON，模型返 JSON | 轻量策略、自然语言判断 | 取决于模型输出 |
| `agent` | spawn 完整子 agent（有工具访问、多步推理）| 复杂审查门 | 最重 |

`command` 还有 shell form（无 `args`，支持 pipe/glob）vs exec form（有 `args`，逐字传入、路径占位符替换）；`async: true` 后台跑不阻塞 agent loop，`asyncRewake: true` 在 async 命令 exit 2 时唤醒。

## 五、Matcher 规则（容易踩坑）

matcher 不是统一正则，按字符集分两种语义：

| matcher 值 | 求值方式 | 例 |
| --- | --- | --- |
| `*` / `""` / 省略 | 全匹配 | 每次事件都 fire |
| 仅含字母/数字/`_`/`-`/空格/`,`/`\|` | **精确字符串**，`\|` 或 `,` 分隔备选 | `Write\|Edit`、`Write, Edit`、`code-reviewer` |
| 含其他字符 | **非锚定 JavaScript 正则** | `^mcp__`、`Edit.*`、`mcp__memory__.*` |

**坑**：`mcp__memory` 只含精确匹配字符 → 当字符串比较 → **匹配不到任何工具**。要匹配某 MCP server 全部工具必须写 `mcp__memory__.*`（带 `.` 触发正则模式）。需要全串匹配就 `^...$` 包起来。

工具类 hook 的 matcher 只按 **tool name** 过滤，不过滤文件路径——路径过滤在回调体里查 `tool_input.file_path`。

## 六、Exit Code 语义（最易错）

仅对 command handler：

| exit code | 含义 | 行为 |
| --- | --- | --- |
| 0 | 成功 | 解析 stdout JSON 取输出；JSON 没阻塞就放行 |
| 2 | **阻塞错误** | 忽略 stdout，stderr 当错误消息；对可阻塞事件阻塞动作 |
| 其他 | 非阻塞错误 | 忽略 stdout，stderr 第一行进 transcript，**继续执行** |

> **"exit 1 是常规 Unix 失败码，但 CC 把 exit 1 当非阻塞错误，动作照常进行。策略强制必须 `exit 2`。"**

这是坑掉一半 hook 实现的 gotcha：开发者本能 `exit 1`，hook 静默失败，危险动作照样跑。

## 七、输出 JSON Schema

通用字段 + 事件特有字段。关键：

| 字段 | 作用 | 适用事件 |
| --- | --- | --- |
| `permissionDecision` | `allow`/`deny`/`ask`/`defer` | PreToolUse（defer 结束查询留待后续 resume） |
| `permissionDecisionReason` | 原因 | PreToolUse |
| `updatedInput` | 改 tool 输入（必须在 `hookSpecificOutput` 内，**不能放顶层**） | PreToolUse |
| `additionalContext` | 追加到 tool 结果，Claude 能看到 | PostToolUse |
| `updatedToolOutput` | 改 tool 输出 | PostToolUse |
| `systemMessage` | 给用户看（不给模型）；要进消息流需 `includeHookEvents` | 通用 |
| `hookEventName` | 标识 hook 类型 | 必须在 `hookSpecificOutput` 内 |
| `async`/`asyncTimeout` | 异步模式 | 通用 |

**易错**：`updatedInput` 放顶层不生效，必须 `hookSpecificOutput.updatedInput`。

## 八、异步模式（side-effect 不阻塞）

默认 agent 等 hook 返回才继续。纯 side-effect（日志/webhook/metrics）可返异步立即放行：

```python
async def async_hook(input_data, tid, context):
    asyncio.create_task(send_to_logging_service(input_data))
    return {"async_": True, "asyncTimeout": 30000}   # Python 用 async_ 避关键字
```

```typescript
const asyncHook: HookCallback = async (input, id, { signal }) => {
  backgroundFireAndForget(input);  // 自己起后台任务
  return { async: true, asyncTimeout: 30000 };
};
```

**异步不能阻塞/改输入/注入上下文**——agent 已经走了。只用于日志、指标、通知。

## 九、Timeout 与取消

- 默认 `timeout=60` 秒（HookMatcher 可改）。
- 超时则 kill 子进程；TypeScript 回调收 `AbortSignal`，应把 `signal` 透传给 fetch/请求以便优雅取消。
- Python 用线程跑阻塞 HTTP 调用避免卡 event loop。
- 慢 hook 拖慢 agent——单文件 lint < 5s；重量分析放 `Stop` hook（只跑一次）而非 `PostToolUse`（每次工具都跑）。

## 十、配置来源与热重载

| 来源 | 作用域 | 提交到 git? |
| --- | --- | --- |
| `~/.claude/settings.json` | 所有项目 | 否，本地 |
| `.claude/settings.json` | 单项目 | ✅ |
| Skill/agent frontmatter | 组件生命周期 | ✅（在文件内） |

- `ConfigChange` 事件：配置文件变更时触发，**动态 reload settings**。
- **hook 可嵌入 agent / skill 定义**（不只是全局 settings.json）→ per-agent 校验。例：CSV agent 配 CSV 结构校验 hook，API agent 配 OpenAPI 校验 hook，互不干扰。

## 十一、子 agent 与循环防护

- **子 agent 不自动继承父 agent 权限**——每个子 agent 分别请求权限。避免反复弹窗：用 PreToolUse hook 自动批准特定工具，或配适用子 agent session 的权限规则。
- **UserPromptSubmit hook 若 spawn 子 agent 会触发同 hook → 无限循环**。防护：hook 输入里检查子 agent 标识再决定是否 spawn。

## 十二、可观测落点（接前一篇）

实现机制决定了可观测管道怎么搭：
- `SessionStart` shell hook → 起 root trace（注意 Python SDK 没这事件，得用 settings.json shell hook）。
- `PostToolUse` 回调 → 起/结 `execute_tool` span，async 模式发到 OTel collector 不阻塞 agent。
- `Stop` hook → 结 root trace、写 summary（只跑一次，适合重量操作）。
- `ConfigChange` → 审计配置变更。
- `PreCompact` → 记录被压缩丢的上下文。

## 易错点汇总

- `exit 1` 当阻塞 → 实际非阻塞，危险动作放行。策略必须 `exit 2`。
- `updatedInput` 放顶层 → 不生效，必须 `hookSpecificOutput.updatedInput`。
- matcher `mcp__memory` → 精确字符串匹配不到工具，要 `mcp__memory__.*`。
- Python SDK 注册 SessionStart/End 回调 → 没这 HookEvent，只能 settings.json shell hook。
- 慢 PostToolUse hook 每次工具都跑 → agent 卡。重活放 Stop hook。
- http/mcp_tool handler 网络失败不阻塞 → 别用于必须 hold 的强策略，用 command + exit 2。
- UserPromptSubmit hook spawn 子 agent → 无限循环，要检查子 agent 标识。

## 延伸

## 延伸

- 关联题：[[ml-ai/observability/claude-code-hooks-observability]]
- 关联题：[[ml-ai/observability/codex-opencode-observability]]
- 关联题：[[ml-ai/observability/opentelemetry-genai-semantic-conventions]]
- 关联题：[[ml-ai/agent/skill-meaning-loading-evolution]]
