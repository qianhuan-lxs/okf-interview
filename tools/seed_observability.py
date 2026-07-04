#!/usr/bin/env python3
"""Seeder: Agent observability knowledge docs (user-requested, research-backed).

Topics: OpenTelemetry GenAI semantic conventions, Langfuse v4 design,
agent trace span model, Claude Code hooks for observability,
Codex/OpenCode observability mechanisms.

Sources are general research (citations inline), not tied to a specific面经 question.
Where探迹's可观测性/评测体系 question is directly relevant.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from seed_louis_ai import q

DATE = "2026-07-05"

# =========================================================================== #
# ml-ai/observability/
# =========================================================================== #

q("ml-ai/observability/opentelemetry-genai-semantic-conventions.md",
  "OpenTelemetry GenAI 语义约定 (Agent 可观测的通用语)",
  "ml-ai", "observability", "hard",
  ["opentelemetry", "genai", "semantic-conventions", "openinference", "openllmetry", "tracing"],
  ["探迹"],
  """# OpenTelemetry GenAI 语义约定 (Agent 可观测的通用语)

## 问题描述

Agent 可观测性的"通用语"是什么？OpenTelemetry GenAI 约定、OpenInference、OpenLLMetry 三者什么关系？为什么应该收敛到 OTel GenAI？

## 一、为什么 Agent 可观测性需要"通用语"

早期 LLM tracer 各自发明字段名（Langfuse / Arize Phoenix / OpenLLMetry / LangSmith 各一套）。后果：

- 换后端 = 重写 instrumentation。
- 跨框架无法建统一 dashboard、无法算 per-agent 指标、无法关联 trace。

**OpenTelemetry GenAI 语义约定**（`gen_ai.*` 命名空间）就是来解决这个的：一套共享的 span 名 + 属性词表，让任何库产出的 trace 在任何后端都能读。**Langfuse / Phoenix / OpenLLMetry / Laminar 已全部收敛到它**——按标准 instrumentation 是不锁定的做法。

## 二、OTel GenAI 约定的核心

### Operation（span 名）
| Span | operation | 含义 |
| --- | --- | --- |
| 模型调用 | `chat` | 一次 LLM 调用 |
| Agent / 子 agent | `invoke_agent` | 一次 agent 运行 |
| 工具调用 | `execute_tool` | 一次 tool 执行 |
| Embedding | `embeddings` | 向量化调用 |
| Agent 构造 | `create_agent` | agent 实例化 |

### 关键属性（挂在对应 span 上）
| Span | 属性 |
| --- | --- |
| 模型调用 | `gen_ai.request.model` / `gen_ai.usage.input_tokens` / `gen_ai.usage.output_tokens` / `gen_ai.response.finish_reasons` / `gen_ai.provider.name` |
| Agent | `gen_ai.agent.name` / `gen_ai.agent.id` / `gen_ai.conversation.id` |
| 工具 | `gen_ai.tool.name` / `gen_ai.tool.call.id` + arguments + result |

`finish_reasons` 是数组（`["stop"]` / `["tool_calls"]`），区分"答完"还是"要调工具"——agent 调试的关键。

## 三、三大约定对比

| 维度 | OTel GenAI SemConv | OpenInference (Arize) | OpenLLMetry (Traceloop) |
| --- | --- | --- | --- |
| 定位 | OTel 官方标准 | 专为 LLM/agent 设计的约定 | 自动 instrumentation 库 + 约定 |
| 命名空间 | `gen_ai.*` | `llm.*` / `retriever.*` / `tool.*` | `llm.*` |
| Span 类型粒度 | operation 维度 | span kind: LLM/TOOL/AGENT/CHAIN/RETREVER | 类似 OpenInference |
| 自动 instrumentation 覆盖 | 官方 ~7 库 | 30+ 库（LangChain/LlamaIndex/OpenAI/ADK/Mastra/Strands/CrewAI） | 30+ 库（OpenAI/Anthropic/LangChain/向量库） |
| Retrieval/Rerank 一等公民 | 较弱 | ✅ 一等公民 | ✅ |
| 治理 | OTel 社区（慢但稳） | Arize 主导（迭代快） | Traceloop 主导 |

### 选型
- **生产 agent + RAG 重 + 现在就要可调试细节** → OpenInference（full prompt/completion 捕获、retrieval 一等公民、span 类型粒度细、自动 instrumentation 覆盖广）。
- **要厂商中立、不锁定、面向未来** → 直接 OTel GenAI SemConv。
- **现实最佳路径** → 用 OpenInference/OpenLLMetry 自动 instrumentation **产出**，再用 **genainormalizer** 归一化到 OTel GenAI，后端收到的就是 canonical 数据。

## 四、genainormalizer（桥接器）

OTel Collector 的 processor（PR #48062，target semconv v1.41.0），把 OpenInference / OpenLLMetry 属性映射到 OTel GenAI：

```yaml
processors:
  genainormalizer:
    profiles: [openinference, openllmetry]
    remove_originals: true
service:
  pipelines:
    traces:
      processors: [genainormalizer]
```

映射示例：
- `llm.usage.prompt_tokens` (OpenLLMetry) → `gen_ai.usage.input_tokens`
- `llm.token_count.prompt` (OpenInference) → `gen_ai.usage.input_tokens`
- `openinference.span.kind: "LLM"` → `gen_ai.operation.name: "chat"`
- `llm.response.finish_reason: "stop"` → `gen_ai.response.finish_reasons: ["stop"]`（含类型转换 string → string[]）

34 个属性映射跨 2 个 profile，已对 OTel GenAI SemConv registry 验证。

## 五、Agent 一次 turn 的标准 trace 树

```
invoke_agent (root)
├── chat (LLM 调用，决定要调工具)
│   └── finish_reasons: ["tool_calls"]
├── execute_tool (search)
│   └── gen_ai.tool.name=search, args, result
├── chat (基于工具结果再调 LLM)
└── chat (最终回答，finish_reasons: ["stop"])
```

实践中 OpenLLMetry 自动给 OpenAI/Anthropic/LangChain/向量库 instrumentation，OpenAI Agents SDK 默认开 tracing 就发这棵树。

## 易错点

- 自己造字段名 → 后端不认识，dashboard 空。
- `finish_reason` 写成 string 而非 string[] → 不合 semconv。
- 用 OpenInference 又不归一化 → 换后端要重写。

## 延伸
""",
  languages=[], role=["ai-app", "sde", "backend", "devops", "ml-engineer"],
  source="", status="reviewed",
  links=["ml-ai/observability/agent-trace-span-model",
         "ml-ai/observability/langfuse-observability-design",
         "system-design/vertical-observation-pipeline"])

q("ml-ai/observability/langfuse-observability-design.md",
  "Langfuse 可观测性设计 (v4 observation-centric)",
  "ml-ai", "observability", "hard",
  ["langfuse", "observability", "clickhouse", "otel", "trace-model", "llmops"],
  ["探迹"],
  """# Langfuse 可观测性设计 (v4 observation-centric)

## 问题描述

Langfuse 的可观测设计是怎样的？trace / observation / session 模型？存储架构？SDK 怎么用？为什么 v4 改成 observation-centric？

## 一、数据模型：v4 observation-centric（2026-03）

Langfuse v4 把"trace 和 observation 两张表"合并成**单张不可变 observations 宽表**。

| 维度 | Classic 模型 | v4 observation-centric |
| --- | --- | --- |
| 存储 | 独立可变 Traces 表 + Observations 表 | 单张不可变 Observations 表 |
| 上下文属性 | 存在 trace 上，查询时 join | SDK 侧 propagate 到每个 observation |
| Trace input/output | 直接设在 trace 上 | 移除，用 observation IO（旧 LLM-as-judge 依赖 trace IO 的可用 deprecated `set_trace_io`） |
| 可变性 | trace 和 observation 都可变 | observation 不可变（写一次） |

### 关键转变：trace_id 从"顶层实体"降为"关联句柄"

> "The `trace_id` becomes a correlation handle—like `session_id` or `user_id`—rather than its own top-level entity."

一次 agentic trace 现在能含**数千个 operation**，有意思的很少在顶层。把 trace_id 当过滤列（同 session_id / user_id / score）来 group 相关 observation，比"按 trace 浏览"更有力。

## 二、为什么这么改（动机）

1. **agentic trace 太大**：单 trace 含上千 operation，trace 顶层浏览找不到重点。
2. **join 贵**：trace 属性 + observation 分两表，查询要 join，ClickHouse 不擅长。
3. **可变 + 多事件/span**：旧 SDK 一次 span 发多条事件（先发 model+input，后发 output+cost），逼着 Langfuse 用可变表 + 频繁 dedup。不可变宽表消除这个。
4. **实时性**：旧模型 trace 元数据存 S3，慢；AggregatingMergeTree 在 ClickHouse 原生聚合，快。

## 三、存储架构

```
SDK / OTel endpoint
   │  (events)
   ▼
Redis queues → S3 → async workers
   │
   ▼
ClickHouse (analytical engine)
   ├─ observations 宽表 (AggregatingMergeTree, 不可变)
   └─ staging 表 + 微批 job (每 3min + 5min 延迟，把 trace 元数据 join 到 observation)
Postgres (metadata: users/sessions/scores 元信息)
```

- 2024-12 (v3)：trace 数据从 Postgres 迁到 ClickHouse，查询延迟从分钟级降到近实时。
- v4：再进一步，宽表 + 不可变 + AggregatingMergeTree，内存降 3x、分析查询快 20x。
- 兼容老 SDK：后台 job 回填 legacy 数据到新 schema，新 SDK 直接写不可变表。

## 四、SDK v4 用法

### propagate_attributes()（替代 update_current_trace()）
```python
from langfuse import Langfuse
langfuse = Langfuse()

with langfuse.propagate_attributes(user_id="u123", session_id="s456", tags=["prod"]):
    # 在此作用域内创建的所有 observation 自动继承这些属性
    with langfuse.start_as_current_observation(name="agent_run", as_type="span") as obs:
        gen = obs.start_observation(name="llm_call", as_type="generation", model="gpt-4")
        # ... 调模型 ...
        gen.end(output=result)
```

属性通过 **OTel Context + Baggage** 传播到子 observation，无需 join。

### 统一 start_observation(as_type=...)
| v3 | v4 |
| --- | --- |
| `langfuse.start_span(name="x")` | `langfuse.start_observation(name="x")` |
| `langfuse.start_generation(name="x", model="m")` | `langfuse.start_observation(name="x", as_type="generation", model="m")` |

`as_type` 取 `span` / `generation` / `event`，替代 v3 三个独立方法。

## 五、Observation API v2 + Metrics API v2

- 单表查询、强制时间过滤、细粒度字段选择、token 分页（配合 ClickHouse 数据剪枝）。
- **observation 级评测秒级执行**（不用再为每个评测查 ClickHouse）。

## 六、Saved Views（保存的视图）

| 视图 | 配置 |
| --- | --- |
| 关键操作 | 按 observation `name`/`type` 过滤 |
| 最贵 LLM 调用 | `type=generation`，按 `total_cost` 降序 |
| 某用户报错 | `user_id` + `level=ERROR` |
| 某会话慢操作 | `session_id`，按 `latency` 降序 |

## 七、与 OTel 的关系

Langfuse 用 **OTel 做数据 ingestion**（OTLP endpoint），自身 trace 模型是 OTel 兼容的。SDK 基于 OTel Context + Baggage 传播属性。所以 Langfuse 既是 OTel 后端，又在其上叠了 LLM 专属的查询/评测/Score 体系。

## 易错点

- v3 SDK 升 v4 没改 `update_current_trace()` → 属性不会 propagate，查询缺维度。
- 还依赖 trace input/output 做评测 → 用 `set_trace_io` deprecated 方法过渡，或改评测逻辑读 observation IO。
- 老 SDK 不升 → 后台回填有延迟，实时性差。

## 延伸
""",
  languages=["python", "typescript"], role=["ai-app", "sde", "backend", "devops", "ml-engineer"],
  source="", status="reviewed",
  links=["ml-ai/observability/opentelemetry-genai-semantic-conventions",
         "ml-ai/observability/agent-trace-span-model",
         "ml-ai/observability/claude-code-hooks-observability"])

q("ml-ai/observability/agent-trace-span-model.md",
  "Agent trace span 模型 (一棵标准 trace 长什么样)",
  "ml-ai", "observability", "medium",
  ["tracing", "span-model", "agent", "opentelemetry", "observability"],
  ["探迹"],
  """# Agent trace span 模型 (一棵标准 trace 长什么样)

## 问题描述

Agent 一次运行的 trace 该怎么结构化？span 树长什么样？每类 span 挂什么属性？

## 一、为什么需要标准 span 模型

Agent 不像普通服务"一个请求一个 span"。一次 agent run 包含：多次 LLM 调用、多次工具调用、可能的 RAG 检索、子 agent 嵌套。没有标准 span 模型，调试 agent 失败时无法定位"是哪次 LLM 调用选错工具"还是"工具返回错"还是"检索召回差"。

## 二、canonical span 树

```
invoke_agent (root span, agent 名/会话 id)
├── embeddings (query 向量化, RAG 入口)
├── retriever (向量/BM26 召回, recall@k)
│   └── reranker (cross-encoder 重排)
├── chat (LLM 调用 1: 决定调工具)
│   └── finish_reasons=["tool_calls"], input_tokens, output_tokens
├── execute_tool (search_tool)
│   └── gen_ai.tool.name, args, result, latency
├── execute_tool (db_query)
├── chat (LLM 调用 2: 基于工具结果)
├── invoke_agent (子 agent: code_reviewer)
│   ├── chat
│   └── execute_tool
└── chat (最终回答, finish_reasons=["stop"])
```

## 三、span 类型与属性

| Span 类型 | operation / kind | 关键属性 |
| --- | --- | --- |
| **Agent 根** | `invoke_agent` | `gen_ai.agent.name` / `gen_ai.agent.id` / `gen_ai.conversation.id` |
| **LLM 调用** | `chat` | `gen_ai.request.model` / `gen_ai.usage.input_tokens` / `gen_ai.usage.output_tokens` / `gen_ai.response.finish_reasons` / `gen_ai.provider.name` |
| **工具调用** | `execute_tool` | `gen_ai.tool.name` / `gen_ai.tool.call.id` / args / result |
| **检索** | `retriever` (OpenInference kind) | query / retrieved docs / scores |
| **重排** | `reranker` | input docs / output docs / model |
| **Embedding** | `embeddings` | model / vector dim / token count |
| **链/编排** | `chain` (OpenInference) | 编排步骤 |

## 四、为什么是嵌套树而非扁平列表

- **父 子关系表达因果**：LLM 调用产出的 tool_calls → 对应的 execute_tool span 作为子 span，能追溯"哪次 LLM 决定触发了哪次工具"。
- **子 agent 嵌套**：`invoke_agent` 套 `invoke_agent`，反映 multi-agent 编排结构。
- **代价归因**：子 span 的 token/cost 汇总到父 agent span，算出"这个子 agent 这次 run 花了多少"。
- **延迟分解**：父 span 总时长 = Σ 子 span + 编排开销，定位瓶颈。

## 五、对 agent 调试的价值

| 故障现象 | 看哪类 span |
| --- | --- |
| Agent 选错工具 | `chat` span 的 `finish_reasons` + tool_calls 字段 |
| 工具调用超时 | `execute_tool` span 的 latency |
| RAG 召回差 | `retriever` span 的 retrieved docs vs 期望 |
| 成本暴涨 | `chat` span 的 token usage 聚合 |
| 子 agent 死循环 | 嵌套 `invoke_agent` 深度 + 重复 `chat` |
| 幻觉 | 对比 `chat` 的 input context vs output claim |

## 六、自动 instrumentation

不要手写每个 span。用：
- **OpenInference** instrumentation（LangChain/LlamaIndex/ADK/CrewAI 自动埋点）
- **OpenLLMetry**（OpenAI/Anthropic/向量库自动埋点）
- **OpenAI Agents SDK** 默认开 tracing 就发这棵树
- 自研框架：在编排层包一层 `start_as_current_observation`，工具调用 wrapper 自动建 execute_tool span

## 易错点

- 把所有 LLM 调用平铺成兄弟 span 而非嵌套 → 丢失因果链。
- 不记 `finish_reasons` → 无法区分"答完"和"要调工具"。
- 检索 span 不记 retrieved docs 内容 → 召回差时无法回放。

## 延伸
""",
  languages=["python", "typescript"], role=["ai-app", "sde", "backend", "ml-engineer"],
  source="", status="reviewed",
  links=["ml-ai/observability/opentelemetry-genai-semantic-conventions",
         "ml-ai/observability/langfuse-observability-design",
         "ml-ai/agent/multi-agent-orchestration-architecture"])

q("ml-ai/observability/claude-code-hooks-observability.md",
  "Claude Code hooks 做可观测性 (事件 / 协议 / 管道模式)",
  "ml-ai", "observability", "hard",
  ["claude-code", "hooks", "observability", "telemetry", "otel", "agent"],
  [],
  """# Claude Code hooks 做可观测性 (事件 / 协议 / 管道模式)

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
curl -s -X POST https://cloud.langfuse.com/api/public/observations \
  -H "Authorization: Basic $LANGFUSE_AUTH" \
  -d "{\"name\":\"$tool\",\"type\":\"span\",\"traceId\":\"$session\",\"metadata\":$input}"
```

## 易错点

- PostToolUse 想"撤销"工具 → 不可能，已经执行。改成 PreToolUse 阻塞 + 校验。
- hook 脚本阻塞（同步等慢服务）→ 拖慢 agent。用 `background_tasks` 异步发，或加 timeout。
- 不设 graceful → hook 挂了拖垮 session（CC 默认 graceful，但自己写脚本别忘超时）。
- matcher 写错（如 `Bash` 写成 `bash`）→ hook 不触发。

## 延伸
""",
  languages=[], role=["ai-app", "sde", "backend", "devops"],
  source="", status="reviewed",
  links=["ml-ai/observability/langfuse-observability-design",
         "ml-ai/observability/codex-opencode-observability",
         "ml-ai/observability/opentelemetry-genai-semantic-conventions",
         "ml-ai/agent/skill-meaning-loading-evolution"])

q("ml-ai/observability/codex-opencode-observability.md",
  "Codex CLI / OpenCode 的可观测性与 hooks",
  "ml-ai", "observability", "medium",
  ["codex", "opencode", "hooks", "observability", "otel", "agent"],
  [],
  """# Codex CLI / OpenCode 的可观测性与 hooks

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
""",
  languages=["typescript", "python"], role=["ai-app", "sde", "backend", "devops"],
  source="", status="reviewed",
  links=["ml-ai/observability/claude-code-hooks-observability",
         "ml-ai/observability/langfuse-observability-design",
         "ml-ai/observability/opentelemetry-genai-semantic-conventions"])

print("\nDone: observability knowledge docs")
