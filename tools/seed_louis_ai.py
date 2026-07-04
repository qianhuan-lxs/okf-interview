#!/usr/bin/env python3
"""One-off seeder: ingest the AI-topic questions from the 2026-05 Louis面经
into ml-ai/agent, ml-ai/rag, ml-ai/mcp. Idempotent: overwrites existing files.

Re-run after editing data. Followed by `python tools/okf.py gen-index`.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = "_interviews/2026-05-louis-ai-java"
DATE = "2026-05-26"
COMPANIES_ALL = ["华大制造", "广州大娱", "OPPO", "中泓一线", "北京用友", "有赞", "安克创新", "探迹", "拼多多", "恩士讯", "海颐"]


def write(rel_path: str, fm: dict, body: str) -> None:
    p = ROOT / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    fm_lines = ["---"]
    for k, v in fm.items():
        if isinstance(v, list):
            # Emit YAML flow list without per-item quotes; all our list values are
            # simple kebab-case identifiers or company names that don't need quoting.
            fm_lines.append(f"{k}: [{', '.join(str(x) for x in v)}]")
        elif v == "":
            fm_lines.append(f'{k}: ""')
        else:
            fm_lines.append(f"{k}: {v}")
    fm_lines.append("---")
    p.write_text("\n".join(fm_lines) + "\n\n" + body.lstrip("\n"), encoding="utf-8")
    print(f"[w] {rel_path}")


def q(rel, title, category, subcategory, difficulty, tags, companies, body,
      languages=None, role=None, links=None, source=SRC, status="reviewed"):
    fm = {
        "type": "question",
        "id": rel[:-3] if rel.endswith(".md") else rel,
        "title": title,
        "category": category,
        "subcategory": subcategory,
        "difficulty": difficulty,
        "tags": tags,
        "languages": languages or [],
        "role": role or ["ai-app", "sde", "backend"],
        "companies": companies,
        "source": source,
        "status": status,
        "timestamp": DATE,
    }
    if links:
        body = body.rstrip() + "\n\n## 延伸\n\n" + "\n".join(f"- 关联题：[[{l}]]" for l in links) + "\n"
    write(rel, fm, body)


# =========================================================================== #
# ml-ai/agent
# =========================================================================== #

q("ml-ai/agent/multi-agent-orchestration-architecture.md",
  "Multi-Agent 编排架构设计",
  "ml-ai", "agent", "hard",
  ["multi-agent", "orchestration", "adk", "langgraph", "architecture"],
  ["华大制造", "广州大娱", "OPPO", "中泓一线", "北京用友", "有赞"],
  """# Multi-Agent 编排架构设计

## 问题描述

面试官要求描述多 Agent 协作架构是怎么设计、怎么开发的：agent 之间如何交接、串行/并行/分支如何编排、上下文与文件如何在 agent 间流转。

> 来源：华大制造、广州大娱、OPPO、中泓一线、北京用友、有赞均深挖此题。

## 思路

先区分三种经典编排模式，再讲状态/上下文流转，最后讲工程落地。

**编排模式（业界共识的三种）：**

1. **Sequential（串行 / Pipeline）** — 上一个 agent 的输出作为下一个的输入。适合线性工序，如「抽取 → 校验 → 生成」。
2. **Parallel（并行 / Fan-out & Fan-in）** — 多个无依赖子 agent 同时跑，聚合结果。适合多视角分析、多源检索。
3. **Hierarchical / Supervisor（层级 / 路由）** — 一个 supervisor agent 决定把任务路由给哪些 worker agent，可多轮调度。适合开放式任务、工具选择。

**状态与上下文流转：**
- **共享 State**：一个全局 state 对象（dict / dataclass / TypedDict），各 agent 读写。LangGraph 的 `State` + reducer 是典型实现。
- **消息传递**：agent 间通过 message list 交接，保留历史。
- **文件 / 大对象**：不宜放进 LLM context，应落盘到沙箱或对象存储，agent 之间只传**引用（路径 / 句柄）**，由沙箱内的代码 agent 真正消费。

**工程落地要点：**
- 每个子 agent 是独立 `Agent` 实例，有自己的 system prompt、tools、model 配置。
- 编排层负责调度、超时、重试、失败聚合、可观测（trace 每一步的 input/output/token）。
- agent 间交接的数据格式用 **schema 约束**（Pydantic / JSON Schema），让上游输出可被下游解析。

## 解答（以 LangGraph + Google ADK 思路）

```python
# LangGraph: supervisor 路由 + parallel workers
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal

class State(TypedDict):
    query: str
    docs: list[str]
    answer: str

def retriever(state): ...      # 写 state["docs"]
def writer(state): ...         # 读 docs，写 state["answer"]

g = StateGraph(State)
g.add_node("retriever", retriever)
g.add_node("writer", writer)
g.add_edge("retriever", "writer")
g.add_edge("writer", END)
app = g.compile()
```

Google ADK 的 `SequentialAgent / ParallelAgent / LoopAgent` 是声明式封装，对应上述三种模式；底层仍是 state 在 agent 间流转。

## 易错点

- **把文件塞进 context** 而不是传引用——上下文爆炸且不可复用。
- **并行模式不处理失败聚合**——一个子 agent 失败就整体崩，缺少 partial-success 策略（见 [[ml-ai/agent/parallel-agent-failure-handling]]）。
- **状态 schema 不固定**——下游 agent 解析上游输出时频繁报错。

## 延伸
""",
  links=["ml-ai/agent/parallel-agent-failure-handling",
         "ml-ai/agent/agent-framework-selection",
         "ml-ai/agent/multi-agent-common-architectures"])

q("ml-ai/agent/multi-agent-common-architectures.md",
  "多 Agent 常见架构有哪些",
  "ml-ai", "agent", "medium",
  ["multi-agent", "architecture", "taxonomy"],
  ["中泓一线", "华大制造"],
  """# 多 Agent 常见架构有哪些

## 问题描述

"多 agent 的架构一般常见的架构有哪些？"（中泓一线）

## 解答

业界常见四类：

| 架构 | 别名 | 特征 | 适用 |
| --- | --- | --- | --- |
| **Sequential** | Pipeline / Waterfall | 串行接力 | 线性工序、确定性流程 |
| **Parallel** | Fan-out / Map-Reduce | 并行 + 聚合 | 无依赖子任务、多源召回 |
| **Supervisor / Router** | Hierarchical / Orchestrator-Worker | 中心调度者路由 | 开放任务、动态选工具 |
| **Network / Conversational** | Peer-to-Peer / Debate | agent 间自由对话、可辩论 | 复杂推理、辩论/反思 |

补充模式：
- **Reflection（反思）** — agent A 生成，agent B 批判，A 修订，迭代。
- **ReAct** — 单 agent 内的 Thought-Action-Observation 循环（不算 multi-agent，但是 multi-agent 的基本积木）。
- **Plan-and-Execute** — Planner 拆解 → Executor 执行。

## 易错点

- 把 ReAct 当成 multi-agent 架构——ReAct 是单 agent 内的循环。
- 认为 Network 架构一定更好——它最难控制 token 成本和终止条件。

## 延伸
""",
  links=["ml-ai/agent/multi-agent-orchestration-architecture"])

q("ml-ai/agent/agent-framework-selection.md",
  "Agent 框架选型 (ADK / LangChain / LangGraph / Spring AI)",
  "ml-ai", "agent", "medium",
  ["agent-framework", "langchain", "langgraph", "google-adk", "spring-ai", "selection"],
  ["华大制造", "广州大娱", "OPPO", "安克创新", "北京用友"],
  """# Agent 框架选型 (ADK / LangChain / LangGraph / Spring AI)

## 问题描述

你熟悉的标准 Agent 框架有哪些？整个架构是什么？LangChain 和 Google ADK 是同时用吗？ADK 的优缺点？能实现三种编排功能吗？

## 思路：按"控制粒度 vs 开箱即用"光谱定位

| 框架 | 语言 | 定位 | 控制粒度 | 优势 | 劣势 |
| --- | --- | --- | --- | --- | --- |
| **LangChain** | Py/JS | 工具/集成大杂烩 | 中 | 集成最全、社区大 | 抽象反复 break change、黑盒 |
| **LangGraph** | Py/JS | 状态图编排 | 高 | 显式状态机、可观测、可控 | 学习曲线、样板代码 |
| **Google ADK** | Py | 声明式多 agent | 中高 | `Sequential/Parallel/LoopAgent` 开箱、与 Gemini/Vertex 深度集成 | 绑定 Google 生态、灵活性弱于 LangGraph |
| **Spring AI** | Java | Spring 风格 AI | 中 | 与 Spring Boot 无缝、Java 团队友好 | 生态新、复杂编排能力弱 |
| **Coze/Dify/n8n** | 低代码 | 可视化 | 低 | 快速搭 demo | 难定制、难版本控制 |

**选型建议：**
- 要 **细粒度状态机 + 可观测** → LangGraph
- 要 **快速搭多 agent + 用 Gemini** → Google ADK
- 要 **Java 后端无缝集成** → Spring AI
- 要 **原型快速验证** → Coze/Dify
- 生产严肃编排不建议只用裸 LangChain（太黑盒）

## 易错点

- 同时混用 LangChain 和 ADK 仅为了"功能拼凑"——会引入两套抽象、两套依赖，维护成本翻倍。混用应只在边界（如 LangChain 做 retriever，ADK 做编排）。

## 延伸
""",
  links=["ml-ai/agent/multi-agent-orchestration-architecture",
         "ml-ai/mcp/mcp-protocol-understanding"])

q("ml-ai/agent/agent-function-call-mechanism.md",
  "Agent 工具调用机制 (Function Call 原理)",
  "ml-ai", "agent", "medium",
  ["function-call", "tool-calling", "llm", "json-schema"],
  ["华大制造", "广州大娱", "中泓一线"],
  """# Agent 工具调用机制 (Function Call 原理)

## 问题描述

大模型输出都是文字，它是怎么有能力去调用一个接口的？谁去调的 MCP 工具？是大模型调的吗？Function Call 内部机制是什么？

## 思路

**关键澄清：大模型本身不"执行"任何东西，它只产出结构化指令；执行的是 agent runtime（你的代码）。**

## 解答

完整流程：

1. **注册阶段**：你把工具的 JSON Schema（name / description / parameters）放进 system prompt 或 `tools` 字段一起送给模型。
2. **决策阶段**：模型根据用户问题，决定是否需要调工具。若需要，它在响应里产出一段 **结构化 JSON**（`tool_calls` 字段），内容是 `{"name": "search", "arguments": {...}}`——注意这是**文字输出**，不是动作。
3. **解析阶段**：agent runtime（LangChain / ADK / 你的代码）解析这段 JSON，校验 schema。
4. **执行阶段**：runtime 用反射/分发调用真正的函数（本地函数 / HTTP 接口 / MCP tool）。
5. **回填阶段**：把函数返回值作为 `tool` role message 拼回对话历史，再次送给模型。
6. **生成阶段**：模型基于工具结果生成最终自然语言回答。

训练侧支撑：现代模型（GPT-4/Claude/Gemini）经过了 **function-calling fine-tuning**，学会在合适时机产出符合 schema 的 JSON，而不是自由文本。

```
User ──→ LLM ──→ tool_calls(JSON) ──→ Runtime 执行 ──→ tool result ──→ LLM ──→ Answer
```

## 易错点

- 以为"模型直接调用了接口"——是 runtime 调的，模型只产出意图。
- 不做 schema 校验——模型偶尔产出非法 JSON 会导致 runtime 崩。
- 工具 description 写得含糊——模型选错工具或根本不调（见 [[ml-ai/mcp/mcp-vs-skill-difference]]）。

## 延伸
""",
  links=["ml-ai/mcp/mcp-protocol-understanding",
         "ml-ai/agent/skill-meaning-loading-evolution"])

q("ml-ai/agent/skill-meaning-loading-evolution.md",
  "Skill 的含义 / 加载机制 / 自进化",
  "ml-ai", "agent", "medium",
  ["skill", "prompt-engineering", "loading", "self-evolution"],
  ["华大制造", "广州大娱", "安克创新", "OPPO", "北京用友", "有赞"],
  """# Skill 的含义 / 加载机制 / 自进化

## 问题描述

你怎么理解 skill？skill 怎么知道什么时候应该调用哪个 skill？skills 加载机制是自己写的还是框架自带？Skill 的自净化？Skill 的优点？Skill 为什么不能只是 prompt？

## 思路

**Skill = 一份"给模型看的工作说明书"**，比裸 prompt 更结构化、可组合、可按需加载。

## 解答

### Skill 通常包含什么

1. **Description（入口描述）** — 渐进式披露的关键：模型先看到所有 skill 的 description，决定加载哪个。
2. **System prompt / Instructions** — 该 skill 的工作方式、约束、输出格式。
3. **Tools** — 这个 skill 可调用的工具集合。
4. **Examples / Few-shot** — 示例输入输出。
5. **Guardrails** — 边界条件、禁止行为。

### 何时调用哪个 skill

不是"自动知道"，而是 **two-stage**：
- **Stage 1（路由）**：把所有 skill 的 **description** 拼进 context，让模型选一个 skill（或由 router agent 选）。
- **Stage 2（加载执行）**：选中后，**才把该 skill 的完整 prompt + tools 加载进 context**（渐进式披露，省 token）。

这正是 Claude Skills / Cursor Skills / Agent Skills 的共同设计：description 是"门牌"，加载是"进屋"。

### 加载机制：自写 vs 框架自带

- **Claude Code / Cursor Skills**：框架自带——扫 `.cursor/skills/*/SKILL.md`，按 description 注入。
- **Google ADK**：通过 `Agent` 的 `tools` + `sub_agents` 声明，框架调度。
- **自研框架**：常见做法是 skill registry（YAML/MD 文件目录）+ router prompt + 动态拼装。

### 自进化 / 自净化

指 skill 库随使用反馈迭代：失败 case 自动回流、评测、改写 description 或 prompt。OPPO/有赞问的"自净化"通常指自动剔除低效 skill 或修正其 description。

### 为什么不能只是 system prompt

- **Token 成本**：所有 skill 全塞 system prompt 会爆炸；渐进式披露按需加载才省。
- **可组合性**：skill 是模块化单元，可跨 agent 复用；裸 prompt 难复用。
- **可观测 / 可版本化**：skill 是独立文件，可 diff、可评测、可回滚。

## 易错点

- description 写成给人看的标签，而不是给模型看的"何时调用我"判断依据。
- 把所有 skill 全量注入——丢失渐进式披露的核心收益。

## 延伸
""",
  links=["ml-ai/mcp/mcp-vs-skill-difference",
         "ml-ai/agent/agent-function-call-mechanism"])

q("ml-ai/agent/agent-memory-management.md",
  "Agent 上下文记忆管理 (Memory)",
  "ml-ai", "agent", "medium",
  ["memory", "short-term", "long-term", "context-management"],
  ["中泓一线", "有赞"],
  """# Agent 上下文记忆管理 (Memory)

## 问题描述

Spring AI 用什么实现 memory？基于 mysql？记忆分几个部分？哪几种记忆？每个存储在哪、以什么方式？OpenClaw 核心定位？

## 解答

### 记忆的三层划分

| 类型 | 别名 | 存储位置 | 实现 |
| --- | --- | --- | --- |
| **Short-term / Working** | 会话内 | 进程内 / 内存 / Redis | 对话历史 message list，window 截断 |
| **Long-term / Episodic** | 跨会话事实 | 向量库 / 关系库 | 用户画像、偏好、过往事件，召回注入 |
| **Semantic / Knowledge** | 共享知识 | 向量库 / 知识图谱 | RAG 知识库 |

### Spring AI 的 Memory

- `ChatMemory` 接口，默认 `InMemoryChatMemory`，可换 `RedisChatMemory` / `JdbcChatMemory`（MySQL/Postgres）。
- 按 `conversationId` 维度存 message 列表，注入时取最近 N 条。

### OpenClaw（OpenClaudeMemory 类）

核心定位：**跨会话的个人长期记忆层**。把对话中提取的事实（"用户喜欢用 Go"、"用户在准备面试"）结构化存到向量库 / KV，下次会话开始时召回相关记忆注入 system prompt，实现"记得你"。

### 工程要点

- **窗口策略**：token 超限时，要么滑窗截断、要么摘要压缩、要么向量化旧消息再召回。
- **事实提取**：用一个轻量 model 在每轮结束后抽取"值得长期记住的事实"。
- **隐私 / 衰减**：长期记忆要有 TTL 和用户可删除。

## 延伸
""",
  links=["ml-ai/rag/rag-full-pipeline",
         "ml-ai/agent/agent-function-call-mechanism"])

q("ml-ai/agent/chatbot-to-agent-leap.md",
  "Chatbot → Agent 的核心跨越",
  "ml-ai", "agent", "easy",
  ["chatbot", "agent", "concept"],
  ["广州大娱"],
  """# Chatbot → Agent 的核心跨越

## 问题描述

从一个 chatbot 到智能体，核心要解决的问题是什么？怎么从这步跨到这步？

## 解答

chatbot 是 **"输入文本 → 输出文本"** 的单轮映射；agent 是 **"目标 → 感知-决策-行动循环 → 状态变更"** 的闭环。核心跨越有三：

1. **行动能力（Actuation）** — chatbot 只能说话，agent 能调工具、改世界状态。技术上是 Function Call / Tool Use / MCP。
2. **自主决策循环（Autonomy Loop）** — chatbot 一问一答；agent 有 ReAct / Plan-Execute 循环：感知（读 observation）→ 思考（thought）→ 行动（action）→ 观察（observation）→ 继续，直到任务完成。
3. **状态与记忆（State & Memory）** — chatbot 无状态靠 prompt 拼历史；agent 维护持久 state、可跨轮跨会话记忆。

一句话：**chatbot 是"嘴"，agent 是"嘴+手+脑循环+记忆"**。

## 延伸
""",
  links=["ml-ai/agent/agent-function-call-mechanism",
         "ml-ai/agent/multi-agent-orchestration-architecture"])

q("ml-ai/agent/parallel-agent-failure-handling.md",
  "并行 Agent 失败处理 (部分成功 vs 整体失败)",
  "ml-ai", "agent", "medium",
  ["multi-agent", "parallel", "failure-handling", "resilience"],
  ["北京用友"],
  """# 并行 Agent 失败处理 (部分成功 vs 整体失败)

## 问题描述

Luna-AI 框架并行模式多个子 Agent 并发执行机制是什么？聚合结果时如果其中一个 Agent 失败了，Parallel 模式是部分成功还是整体失败？

## 思路

不是二选一，而是 **策略可配置**，默认应是"部分成功 + 标记降级"。

## 解答

### 并发执行机制

- 用 `asyncio.gather` / `ThreadPoolExecutor` / `concurrent.futures` 并发拉起子 agent。
- 每个子 agent 独立调用 LLM、独立超时、独立重试。
- 主流程 `gather(return_exceptions=True)` 收集，避免一个失败导致全崩。

### 失败策略（应支持可配）

| 策略 | 行为 | 适用 |
| --- | --- | --- |
| **Fail-Fast（整体失败）** | 任一失败即抛出、取消其余 | 强一致性任务（如金融汇总） |
| **Partial Success（部分成功）** | 成功的结果照常聚合，失败的位标记 null/降级 | 容忍缺失（多源召回、多视角分析） |
| **Retry-then-Skip** | 单 agent 内重试 N 次仍失败才 skip | 抖动场景 |
| **Quorum** | 成功数 ≥ 阈值才整体成功 | 投票/共识类 |

### 聚合

聚合器根据策略处理：填充默认值、记录失败原因到 trace、给下游 agent 一个"哪些子任务缺了"的元信息，让下游能降级处理。

## 易错点

- 用 `gather()` 不带 `return_exceptions=True`——一个失败全崩，丢失已成功的结果。
- 失败信息不进 trace——后续无法排查为什么聚合结果"少了一块"。

## 延伸
""",
  links=["ml-ai/agent/multi-agent-orchestration-architecture"])


# =========================================================================== #
# ml-ai/rag
# =========================================================================== #

q("ml-ai/rag/rag-full-pipeline.md",
  "RAG 完整流程 (切分 → Embedding → 检索 → 生成)",
  "ml-ai", "rag", "medium",
  ["rag", "embedding", "retrieval", "generation"],
  ["中泓一线"],
  """# RAG 完整流程 (切分 → Embedding → 检索 → 生成)

## 问题描述

说一下 RAG 的整个过程。（中泓一线总监面深挖）

## 解答

RAG = Retrieval-Augmented Generation，分 **离线索引** + **在线检索生成** 两大阶段。

### 离线索引（Indexing）

1. **Load** — 加载源文档（PDF/HTML/Markdown/DB）。
2. **Clean / Parse** — 去噪、提正文、OCR、表格识别。
3. **Chunk（切分）** — 按语义切块。策略：
   - 固定长度 + overlap（最简单）
   - 按结构（段落/标题/Markdown header）
   - 语义切分（SemanticChunker，按 embedding 相似度断句）
   - 父子切分（小粒度检索、大粒度返回）
4. **Embed** — 每个 chunk 过 embedding 模型得向量。
5. **Store** — 向量 + 原文 + 元数据写入向量库。

### 在线检索生成（Query）

1. **Query Transform** — 改写 / HyDE / 多 query 扩展，提升召回。
2. **Embed Query** — 用同一 embedding 模型向量化问题。
3. **Retrieve** — 向量库 top-k（余弦/KNN）+ 可选 BM25 混合检索。
4. **Rerank** — Cross-encoder reranker 重排，提精度。
5. **Context Assembly** — 拼 Prompt：system + 检索片段 + 问题。
6. **Generate** — LLM 基于片段生成答案，附引用。
7. **Cite / Grounding check** — 标注来源，必要时做幻觉检测。

## 易错点

- 切分粒度一刀切——短问题要小 chunk，长摘要要大 chunk，应父子分层。
- 检索只靠向量——关键词/精确匹配场景要加 BM25 混合。
- 不做 rerank——向量召回 recall 高但 precision 低，rerank 提精度。

## 延伸
""",
  links=["ml-ai/rag/embedding-model-selection",
         "ml-ai/rag/rag-recall-algorithms",
         "ml-ai/rag/vector-database-selection"])

q("ml-ai/rag/embedding-model-selection.md",
  "Embedding 模型选型 (bge / OpenAI / m3e)",
  "ml-ai", "rag", "easy",
  ["embedding", "bge", "openai", "m3e", "model-selection"],
  ["中泓一线"],
  """# Embedding 模型选型 (bge / OpenAI / m3e)

## 问题描述

Embedding 用的什么模型？

## 解答

| 模型 | 维度 | 语言 | 部署 | 特点 |
| --- | --- | --- | --- | --- |
| **OpenAI text-embedding-3-small/large** | 1536 / 3072（可降维） | 多语 | 闭源 API | 效果稳、贵、需出境 |
| **bge-large-zh / bge-m3**（智源） | 1024 / 1024 | 中/多语 | 可本地 | 中文 SOTA、开源、可私有化 |
| **m3e-base/large** | 768 / 1024 | 中文 | 可本地 | 中文老牌开源，效果略逊 bge |
| **Cohere embed-v3** | 1024 | 多语 | 闭源 API | 英文强 |
| **GTE（阿里）** | 768/1024 | 中英 | 可本地 | 开源、长文本友好 |

**选型建议（中文场景）：**
- 私有化 + 中文 SOTA → **bge-m3**（支持稀疏+稠密+多向量，长文本好）
- 不愿出境 + 快速验证 → m3e
- 英文为主 / 接受 API → OpenAI 3-small

## 易错点

- 中英文混用却选了纯中文模型——英文召回差。
- embedding 模型和 LLM 混为一谈——embedding 只做向量化，不生成文本。

## 延伸
""",
  links=["ml-ai/rag/rag-full-pipeline",
         "ml-ai/rag/vector-dimension-tradeoff"])

q("ml-ai/rag/vector-database-selection.md",
  "向量数据库选型 (PG Vector / Milvus / ...)",
  "ml-ai", "rag", "easy",
  ["vector-database", "pgvector", "milvus", "qdrant", "selection"],
  ["中泓一线"],
  """# 向量数据库选型 (PG Vector / Milvus / ...)

## 问题描述

熟悉的向量数据库有哪些？PG Vector 怎么样？

## 解答

| 方案 | 类型 | 适合规模 | 优势 | 劣势 |
| --- | --- | --- | --- | --- |
| **pgvector** | Postgres 扩展 | <10M | 复用 PG 生态、事务、SQL 混合查询 | 规模上限低、ANN 算法少 |
| **Milvus** | 专用 | 1B+ | 分布式、多索引、高性能 | 部署重（etcd+minio+pv） |
| **Qdrant** | 专用 | 中大 | Rust 实现、轻、filter 强 | 生态略小 |
| **Chroma** | 嵌入式 | 小/原型 | 零部署 | 不适合生产 |
| **Weaviate** | 专用 | 中大 | 内置混合检索、schema 灵活 | 资源占用高 |
| **Elasticsearch** | 搜索引擎 | 大 | BM25+vector 混合天然 | 向量性能弱于专用 |

**选型经验：**
- 已有 PG + 数据量 < 千万 → **pgvector**（运维零增量）
- 亿级以上 + 严肃生产 → **Milvus**
- 中等规模 + 重过滤 → **Qdrant**

## 延伸
""",
  links=["ml-ai/rag/pgvector-index-types",
         "ml-ai/rag/rag-full-pipeline"])

q("ml-ai/rag/pgvector-index-types.md",
  "PG Vector 索引类型 (IVFFlat / HNSW)",
  "ml-ai", "rag", "medium",
  ["pgvector", "ivfflat", "hnsw", "ann-index"],
  ["中泓一线"],
  """# PG Vector 索引类型 (IVFFlat / HNSW)

## 问题描述

PG Vector 对应有哪些索引类型、存储类型？

## 解答

pgvector 支持两种 ANN 索引（默认精确扫描，无索引时复杂度 O(n)）：

### IVFFlat（倒排文件 + 扁平量化）
- 把向量聚成 `lists` 个簇，查询时只扫 `probes` 个最相近簇。
- 建索引快、内存占用小。
- 召回率依赖 `probes` 调参，精度低于 HNSW。
- SQL：`CREATE INDEX ON t USING ivfflat (vec vector_cosine_ops) WITH (lists = 100);`

### HNSW（分层可导航小世界图）
- 多层图结构，查询沿图贪心走。
- 召回率高、查询快，**但建索引慢、内存占用大**。
- 参数：`m`（邻居数）、`ef_construction`、`ef_search`。
- SQL：`CREATE INDEX ON t USING hnsw (vec vector_cosine_ops) WITH (m = 16, ef_construction = 64);`

### 存储类型
- `vector(n)` 固定维度，存储为 float4 数组。
- `halfvec(n)` — pgvector 0.7+，半精度，**省一半空间**，精度损失可接受，生产推荐。

### ops 算子（必须匹配距离度量）
- `vector_cosine_ops`（余弦）/ `vector_l2_ops`（欧式）/ `vector_ip_ops`（内积）
- **索引的 ops 必须和查询用的距离函数一致**，否则索引失效。

## 易错点

- 用 `vector_cosine_ops` 建索引却用 `<->`（L2）查询——索引不走。
- 入库向量未归一化却用 cosine——结果对但浪费内积优化（见 [[ml-ai/rag/vector-normalization]]）。

## 延伸
""",
  links=["ml-ai/rag/vector-normalization",
         "ml-ai/rag/vector-database-selection"])

q("ml-ai/rag/vector-normalization.md",
  "向量归一化 (L2 / 余弦相似度)",
  "ml-ai", "rag", "medium",
  ["normalization", "l2", "cosine", "similarity"],
  ["中泓一线"],
  """# 向量归一化 (L2 / 余弦相似度)

## 问题描述

放到数据库里面之前，要不要归一化？

## 解答

**视距离度量而定，但生产实践强烈建议归一化。**

### 数学关系

- **余弦相似度** = `(A·B) / (||A||·||B||)`
- 若 A、B 都已 L2 归一化（||A||=||B||=1），则 **余弦 = 内积 A·B**。
- 此时可用 `vector_ip_ops`（内积）替代 `vector_cosine_ops`，**查询更快**（少两次范数计算）。

### 是否归一化

| 度量 | 是否需归一化 | 说明 |
| --- | --- | --- |
| 余弦 | 建议但非必须 | 归一化后可走内积索引加速 |
| 内积 (IP) | **必须** | 否则结果受向量模长污染 |
| L2 | 不需要 | L2 本身就含模长信息 |

### 工程做法

- 入库前统一 `vec = vec / np.linalg.norm(vec)`。
- 用 OpenAI / bge 模型时，部分模型默认输出已归一化（OpenAI text-embedding-3 已归一化；bge 需手动）。

## 易错点

- 模型输出未归一化却用内积检索——结果受向量模长影响，召回错乱。

## 延伸
""",
  links=["ml-ai/rag/pgvector-index-types",
         "ml-ai/rag/rag-recall-algorithms"])

q("ml-ai/rag/vector-dimension-tradeoff.md",
  "向量维度 trade-off (1024 vs 3072 vs 128)",
  "ml-ai", "rag", "medium",
  ["vector-dimension", "storage", "recall", "tradeoff"],
  ["中泓一线"],
  """# 向量维度 trade-off (1024 vs 3072 vs 128)

## 问题描述

向量字段一般设置多长？1024 设的长还是短？对我们有什么影响？可以设两万多吗？128 可以吗？

## 解答

维度 d 是 **召回精度 / 存储 / 计算成本** 的三角 trade-off：

| 维度 | 存储（每向量） | 召回精度 | 查询耗时 | 适用 |
| --- | --- | --- | --- | --- |
| 128 | 0.5 KB | 低 | 极快 | 原型、粗排、人脸/图像 |
| 768 | 3 KB | 中 | 快 | m3e/GTE-base |
| 1024 | 4 KB | 中高 | 中 | bge-m3、主流选择 |
| 1536 | 6 KB | 高 | 较慢 | OpenAI 3-small |
| 3072 | 12 KB | 很高 | 慢 | OpenAI 3-large、长尾精度 |

### 经验

- **1024 是当前主流甜点**——精度够、成本可控。
- **3072 一般不值**——精度边际收益小，存储/索引/查询成本翻倍。OpenAI 3-large 支持 **Matryoshka 降维**：直接取前 1536/768 维即可降维（损失很小）。
- **128 对中文文本检索太短**——语义信息丢太多，召回差。
- **两万多**（如一些大模型 hidden）几乎没人用全量，会降维或蒸馏。

### 影响

- 存储：`N × d × 4 bytes`，1M 条 3072 维 = 12GB。
- 索引构建时间随 d 近似线性增长。
- HNSW 内存占用 ≈ 向量本体 × 1.5。

## 延伸
""",
  links=["ml-ai/rag/embedding-model-selection",
         "ml-ai/rag/vector-database-selection"])

q("ml-ai/rag/rag-recall-algorithms.md",
  "召回算法 (余弦 / KNN / Reranker / 混合检索)",
  "ml-ai", "rag", "medium",
  ["recall", "cosine", "knn", "rerank", "hybrid-search"],
  ["中泓一线"],
  """# 召回算法 (余弦 / KNN / Reranker / 混合检索)

## 问题描述

用户提问的时候，召回算法有哪些种？匹配算法？

## 解答

### 一阶段：召回（Recall，求快求全）

| 算法 | 类型 | 说明 |
| --- | --- | --- |
| **余弦相似度 (Cosine)** | 稠密向量 | 文本语义最常用，归一化后等价内积 |
| **L2 / 欧式距离** | 稠密向量 | 对模长敏感，图像场景多 |
| **内积 (IP)** | 稠密向量 | 归一化向量等价 cosine，更快 |
| **KNN（精确）** | 暴力扫描 | O(n)，小数据或 ground truth |
| **ANN（近似 KNN）** | 索引加速 | HNSW / IVF / PQ，牺牲少量精度换速度 |
| **BM25** | 稀疏关键词 | 精确匹配、专有名词、ID 类强 |

### 二阶段：重排（Rerank，求准）

- **Cross-encoder Reranker**（bge-reranker / Cohere rerank）：把 (query, doc) 一起送模型打分，精度远高于向量相似度，但慢——只对 top-50 重排。

### 三阶段：混合检索（Hybrid）

- **向量 + BM25 并联召回** → **RRF（Reciprocal Rank Fusion）融合** → reranker 重排。
- 解决"语义召回好但专名漏"和"关键词召回好但语义漏"的互补问题。

### 流水线

```
Query → [Dense ANN top-100] + [BM25 top-100] → RRF 融合 top-50 → Reranker top-5 → LLM
```

## 易错点

- 只用向量召回——专有名词、代码、ID 召回差。
- 不做 rerank——top-1 常不是最相关。

## 延伸
""",
  links=["ml-ai/rag/rag-full-pipeline",
         "ml-ai/rag/vector-normalization"])

q("ml-ai/rag/heterogeneous-data-vectorization.md",
  "异构数据向量化 (文本 / 语音 / 视频)",
  "ml-ai", "rag", "medium",
  ["multimodal", "embedding", "audio", "video", "image"],
  ["中泓一线"],
  """# 异构数据向量化 (文本 / 语音 / 视频)

## 问题描述

不同文件类型（文本/语音/视频）转成向量后，怎么存储这个字段？维度长度是多少？

## 解答

### 各模态向量化路径

| 模态 | 路径 | 典型模型 |
| --- | --- | --- |
| **文本** | text → embedding | bge-m3 / OpenAI |
| **图像** | image → embedding | CLIP / SigLIP（图文共用空间） |
| **语音** | audio → ASR 转文本 → 文本 embedding；或 audio → CLAP 音频 embedding | Whisper + bge / CLAP |
| **视频** | 抽关键帧 → 图像 embedding；或 ASR 字幕 + 视觉特征融合 | CLIP + Whisper |

### 存储策略

1. **统一向量空间**：用 CLIP 类多模态模型，文/图/音在**同一向量空间**，可跨模态检索（用文本搜图）。存同一张向量表的 `vec` 列。
2. **分模态向量空间**：各模态各用各的 embedding 模型，分表存。检索时按模态分别召回再融合。
3. **向量 + 原始引用**：向量库只存 embedding + `modality` + `source_uri`，原始媒体落对象存储。

### 维度

- 不强制统一——文本 1024、图像 512（CLIP）、音频 1024（CLAP）可各不相同。
- 若要同一空间（CLIP 系），各模态维度一致（如 512/768）。

### 字段 schema（pgvector 示例）

```sql
CREATE TABLE chunks (
  id bigint primary key,
  modality text,          -- text/image/audio/video
  source_uri text,
  embedding vector(1024), -- 文本
  -- 或分列：text_vec vector(1024), img_vec vector(512)
  payload jsonb
);
```

## 易错点

- 强行把不同模态向量塞同一空间却用了不同模型——跨模态检索结果无意义。
- 把原始音视频也塞向量库——应只存引用。

## 延伸
""",
  links=["ml-ai/rag/vector-dimension-tradeoff",
         "ml-ai/rag/vector-database-selection"])

q("ml-ai/rag/llm-finetuning-methods.md",
  "大模型微调训练方式 (LoRA / QLoRA / SFT / RLHF)",
  "ml-ai", "rag", "medium",
  ["finetuning", "lora", "qlora", "sft", "rlhf", "dpo"],
  ["中泓一线"],
  """# 大模型微调训练方式 (LoRA / QLoRA / SFT / RLHF)

## 问题描述

大模型微调训练部署怎么训练？训练方式有哪些种？

## 解答

训练方式分两个正交维度：**训练目标** 和 **参数效率**。

### 按训练目标

| 方式 | 目标 | 数据 | 用途 |
| --- | --- | --- | --- |
| **Pretrain** | 自回归下一个 token | 海量无标注 | 从零训基座（一般不做） |
| **SFT (Supervised Fine-Tuning)** | 模仿标注样本 | (instruction, response) 对 | 教模型按指令回答 |
| **RLHF** | 人类偏好强化学习 | 偏好对 + reward model | 对齐人类偏好 |
| **DPO** | 直接偏好优化 | 偏好对（chosen/rejected） | RLHF 的简化，无需 reward model |
| **Continued Pretrain** | 领域语料继续预训练 | 领域无标注 | 注入领域知识 |

### 按参数效率（PEFT）

| 方式 | 可训参数 | 显存 | 适用 |
| --- | --- | --- | --- |
| **Full FT** | 100% | 极高 | 资源充足、效果上限最高 |
| **LoRA** | 低秩矩阵 A·B，<1% | 中 | 主流，性价比最高 |
| **QLoRA** | LoRA + 基座 4bit 量化 | 低 | 单卡可训大模型 |
| **Adapter / Prefix Tuning** | 插入小模块 | 中 | 老牌 PEFT，渐被 LoRA 替代 |

### 典型组合

- **领域注入**：Continued Pretrain + SFT
- **指令对齐**：SFT + DPO
- **资源紧张 + 7B/13B**：QLoRA + SFT

### 部署

合并 LoRA 权重回基座 → 量化（GPTQ/AWQ/GGUF）→ vLLM / TGI / Ollama 服务化。

## 易错点

- 把 SFT 当成预训练——SFT 不会注入大量新知识，只是改变行为风格。
- RLHF/DPO 想在 RAG 场景直接用——通常应先 SFT 让模型学会用检索片段再 DPO。

## 延伸
""",
  links=["ml-ai/rag/rag-full-pipeline"])


# =========================================================================== #
# ml-ai/mcp
# =========================================================================== #

q("ml-ai/mcp/mcp-protocol-understanding.md",
  "MCP 协议理解 (解决什么问题)",
  "ml-ai", "mcp", "easy",
  ["mcp", "protocol", "tool-calling", "standardization"],
  ["华大制造", "北京用友", "安克创新", "中泓一线"],
  """# MCP 协议理解 (解决什么问题)

## 问题描述

MCP 主要解决什么问题？MCP 的工具到工具调用这一套技术流程大概怎样？

## 解答

**MCP (Model Context Protocol)** 是 Anthropic 2024 年底开源的**开放协议**，把"模型 ↔ 外部工具/数据源"的接入标准化。类比：**USB-C 之于硬件，MCP 之于 LLM 工具接入**。

### 解决什么问题

- **N×M → N+M**：以前每个 Agent 框架 × 每个工具都要单独写适配；MCP 之后，工具写一份 MCP server，任何支持 MCP 的 client（Claude/Cursor/Cline/自研 agent）都能用。
- **协议统一**：tool 列表发现、调用、参数校验、结果回传都有标准 JSON-RPC 格式。
- **解耦**：工具方和 agent 方独立演进。

### 核心概念

- **MCP Server**：暴露 `tools` / `resources` / `prompts` 三类能力。
- **MCP Client**：agent 侧，连接 server，发现工具，把 tool schema 暴露给 LLM。
- **Transport**：stdio（本地）/ SSE / HTTP。

### 流程

1. Client 启动时连 server，调 `tools/list` 拿到工具 schema 列表。
2. Client 把 schema 转成 LLM 的 `tools` 字段。
3. LLM 决定调工具 → 产出 `tool_call`。
4. Client 调 server 的 `tools/call`，拿结果。
5. 结果回填 LLM。

## 易错点

- 把 MCP 等同于 Function Call——Function Call 是 **模型能力**，MCP 是 **接入协议**，MCP 之上仍走 Function Call。
- 以为 MCP server 必须本地——可远程 HTTP/SSE，正是网关场景的来源（见 [[ml-ai/mcp/mcp-gateway-architecture]]）。

## 延伸
""",
  links=["ml-ai/mcp/mcp-gateway-architecture",
         "ml-ai/agent/agent-function-call-mechanism",
         "ml-ai/mcp/mcp-vs-a2a-difference"])

q("ml-ai/mcp/mcp-vs-skill-difference.md",
  "MCP vs Skill 区别",
  "ml-ai", "mcp", "medium",
  ["mcp", "skill", "comparison", "prompt-engineering"],
  ["安克创新", "有赞"],
  """# MCP vs Skill 区别

## 问题描述

MCP 跟 skill 什么区别？MCP 和 Skill 就是约束和 model 吧？各自用在什么场景？如果 Skill 只是约束+prompt，直接在 System Prompt 里写不行吗？

## 解答

**一句话：MCP 管"能调什么工具"，Skill 管"怎么干活的方法论"。**

| 维度 | MCP | Skill |
| --- | --- | --- |
| 本质 | 协议（接入层） | 工作流封装（认知层） |
| 内容 | tool schema + 调用接口 | description + prompt + tools + examples + guardrails |
| 解决 | "工具怎么被发现、被调用" | "任务该怎么想、怎么做" |
| 粒度 | 单个工具/资源 | 一类任务的方法论 |
| 复用 | 工具跨 agent 复用 | 工作流跨场景复用 |
| 类比 | API 网关 | 一份 SOP 手册 |

### 关系（不是替代）

Skill **可以包含** 一组 MCP tools。即 Skill 在 description 里声明"我这个活儿要用这几个 MCP 工具"，加载 skill 时把对应 MCP tools 一起挂上。

### "Skill 只是 prompt 行不行"

不行（见 [[ml-ai/agent/skill-meaning-loading-evolution]]）：
1. **渐进式披露** — 全塞 system prompt 会 token 爆炸；skill 按需加载。
2. **可组合** — skill 是模块，可跨 agent 复用、可 diff、可版本化。
3. **绑定工具** — skill 不只是文字，还绑 tools/guardrails，纯 prompt 没有这层。

### 场景选择

- 要让 agent 调外部系统（数据库/API/文件） → **MCP**
- 要把一类任务的最佳实践固化（如"做代码评审的标准流程"） → **Skill**
- 严肃 agent 通常 **两者都用**：Skill 定义"怎么做"，MCP 提供"用什么"。

## 延伸
""",
  links=["ml-ai/agent/skill-meaning-loading-evolution",
         "ml-ai/mcp/mcp-protocol-understanding"])

q("ml-ai/mcp/mcp-gateway-architecture.md",
  "MCP 网关架构 (鉴权 / 限流 / 降级 / 缓存 / Tool 注册)",
  "ml-ai", "mcp", "hard",
  ["mcp", "gateway", "auth", "rate-limiting", "circuit-breaker", "cache", "tool-registry"],
  ["华大制造", "OPPO", "探迹", "中泓一线", "北京用友"],
  """# MCP 网关架构 (鉴权 / 限流 / 降级 / 缓存 / Tool 注册)

## 问题描述

MCP 网关做了什么事？用户端只配网关地址，网关再连具体 MCP 工具？网关鉴权限流细节？Tool 注册流程？流量大怎么解决？除了限流还有别的方式？

## 思路

MCP 网关 = **企业级 MCP 中间件**，把 N 个分散的 MCP server 收口，对 agent 暴露统一入口，叠加治理能力。类比 API Gateway（Kong/APISIX）之于 REST。

## 解答

### 核心职责

1. **统一入口** — agent 只配网关地址，网关后端连多个 MCP server。
2. **Tool Registry（注册中心）** — 维护 tool 元数据（schema、所属 server、owner、版本、SLA）。注册方式：
   - **手工录入**（运营后台填 schema）
   - **自动发现**（拉取下游 server 的 `tools/list`）
   - **OpenAPI 自动转换**（见 [[ml-ai/mcp/openapi-to-mcp-auto-conversion]]）
3. **鉴权 Auth** — 双向：
   - 入向：校 agent / tenant 的 token（JWT / mTLS）。
   - 出向：维护下游 MCP server 的凭证库（密钥/OAuth），按需注入。
4. **限流 Rate Limiting** — 多维度：tenant / tool / 全局。
5. **降级 / 熔断** — 下游 MCP 异常时返回兜底响应或短路。
6. **缓存** — 相同 (tool, args) 短 TTL 缓存，省下游调用与 token 成本。
7. **可观测** — 每次调用 trace、token 计费、成功率监控。

### 限流方案（华大/探迹追问"还有别的方式吗"）

| 方案 | 粒度 | 实现 |
| --- | --- | --- |
| **令牌桶** | 平滑限流 | Redis + Lua 原子扣 token |
| **漏桶** | 强制匀速 | 队列 + 固定速率消费 |
| **滑动窗口** | 精确窗口 | Redis ZSET 按时间戳计数 |
| **固定窗口** | 简单 | Redis INCR + EXPIRE |
| **自适应限流** | 根据延迟/错误率 | Sentinel / BBR 思路 |
| **排队 + 削峰** | 突发吸收 | MQ 异步化 |

**单机 vs 分布式**：网关多副本时，限流必须用 Redis 等共享存储做**分布式限流**，否则单机配额会被突破。

### 高并发流量打法（华大）

1. **水平扩容** — 网关无状态，多副本 + LB。
2. **分布式限流** — Redis 令牌桶，按 tenant/tool 维度。
3. **缓存** — 读多写少的 tool 结果缓存。
4. **异步化** — 长耗时 tool 改异步（提交任务 → webhook 回调）。
5. **降级** — 下游故障时返回兜底，避免雪崩。
6. **连接复用** — 对下游 MCP server 用连接池/长连接。

## 易错点

- 单机限流配多副本网关——总 QPS 超预期。
- 缓存对带副作用（写类）tool 也开——脏写。
- Tool 注册只走自动发现，没有 owner/SLA 治理——出问题无人认领。

## 延伸
""",
  links=["ml-ai/mcp/openapi-to-mcp-auto-conversion",
         "ml-ai/mcp/mcp-protocol-understanding",
         "distributed-systems/rate-limiting-redis-token-bucket"])

q("ml-ai/mcp/mcp-vs-a2a-difference.md",
  "MCP vs A2A 区别",
  "ml-ai", "mcp", "medium",
  ["mcp", "a2a", "agent2agent", "protocol", "comparison"],
  ["北京用友"],
  """# MCP vs A2A 区别

## 问题描述

MCP 跟 ATA（A2A）有什么差别？

## 解答

| 维度 | MCP | A2A (Agent2Agent) |
| --- | --- | --- |
| 全称 | Model Context Protocol | Agent2Agent Protocol |
| 提出方 | Anthropic (2024.11) | Google (2025.04) |
| 解决 | Agent ↔ **工具/数据源** | Agent ↔ **Agent** |
| 通信方 | LLM client ↔ tool server | agent ↔ agent |
| 暴露 | tools / resources / prompts | agent card（能力声明 + 任务接口） |
| 范例 | Cursor 调本地文件工具 | 两个 agent 互相委派任务 |

**一句话区别：MCP 给 agent 装"手"（调工具），A2A 让 agent 之间"对话协作"。**

### 互补关系

- A2A 协作过程中，单个 agent 仍可用 MCP 调工具。
- 例：agent A 收到任务 → 通过 A2A 委派给 agent B → B 用 MCP 调数据库 → 结果沿 A2A 回 A。

## 易错点

- 把 A2A 当成 MCP 的替代——它们解决不同层问题，常常共存。

## 延伸
""",
  links=["ml-ai/mcp/mcp-protocol-understanding",
         "ml-ai/agent/multi-agent-orchestration-architecture"])

q("ml-ai/mcp/openapi-to-mcp-auto-conversion.md",
  "OpenAPI → MCP Tool 自动转换",
  "ml-ai", "mcp", "hard",
  ["mcp", "openapi", "conversion", "tool-registry", "automation"],
  ["华大制造", "有赞"],
  """# OpenAPI → MCP Tool 自动转换

## 问题描述

简历提到把 OpenAPI 自动转换为 MCP Tool 定义。最难处理的点是什么？接口文档里没有描述怎么办？

## 解答

### 转换映射

| OpenAPI | MCP Tool |
| --- | --- |
| `operationId` (或 path+method) | tool name |
| `summary` / `description` | tool description（关键，模型靠它选工具） |
| `parameters` + `requestBody` | `inputSchema` (JSON Schema) |
| `servers` + `path` | 调用入口 |
| `responses` | 输出格式（MCP 通常返回 text，自行渲染） |

### 最难的点

1. **description 缺失或低质** — OpenAPI 里很多接口没 description 或只有"创建订单"这种给人看的标签。模型选工具靠 description，质量差就调错或漏调。
   - 解法：用 LLM **基于 path/params/schema 生成 description**，再人工 review；或拉接口文档/示例代码再生成。
2. **复杂参数 schema** — 嵌套 object、oneOf、$ref、文件上传、formData。MCP inputSchema 是扁平 JSON Schema，需要递归展开 + 去环。
3. **鉴权多样性** — Bearer / API Key / OAuth / 签名。要在网关层屏蔽，注入凭证。
4. **大响应裁剪** — 接口返回几 MB JSON，超过 LLM context。要按 schema 抽关键字段或摘要。
5. **副作用识别** — GET 安全可缓存，POST/PUT 有副作用，不能盲目缓存。
6. **跨团队推动** — 业务方 OpenAPI 文档质量参差，需要协作规范（这本身是工程难点）。

### description 生成最佳实践

- 风格：**"做什么 + 何时该用 + 输入要点 + 边界条件"**，给模型判断依据，不是给人看的标签。
- 例：`"按订单号查询订单详情。当用户问'我的订单''订单状态'时使用。输入 order_id（32位字符串）。仅返回最近 90 天订单。"`

## 易错点

- 直接用 `summary` 当 description——给模型看的判断信息严重不足。
- 不裁剪大响应——context 爆炸且成本高。

## 延伸
""",
  links=["ml-ai/mcp/mcp-gateway-architecture",
         "ml-ai/agent/skill-meaning-loading-evolution"])

q("ml-ai/mcp/mcp-tool-registration-flow.md",
  "MCP Tool 注册流程",
  "ml-ai", "mcp", "medium",
  ["mcp", "tool-registry", "registration", "governance"],
  ["OPPO", "华大制造"],
  """# MCP Tool 注册流程

## 问题描述

手工把 MCP 工具录进来？Tool 注册流程是怎样的？

## 解答

注册三种模式，生产通常**三者结合**：

### 1. 自动发现（Pull）
网关启动/定时拉取下游 MCP server 的 `tools/list`，把返回的 tool schema 写入 registry。
- 优点：零人工、新工具自动上架。
- 缺点：没有 owner/SLA/分类等治理元数据。

### 2. 手工录入（Push）
运营后台填表：name / description / 所属 server / owner / 分类 / 鉴权策略 / SLA。
- 优点：治理信息完整、可控。
- 缺点：慢、易和实际 schema 漂移。

### 3. 自动转换（Transform）
OpenAPI / GraphQL schema 自动转 MCP tool（见 [[ml-ai/mcp/openapi-to-mcp-auto-conversion]]）。

### 典型流程（生产）

```
[新工具接入]
  1. 工具方提供 OpenAPI 或 MCP server 地址
  2. 网关 pull 自动发现 / transform 生成 registry 草稿
  3. 工具方在后台补全 owner / 分类 / description（必要时 LLM 辅助生成）
  4. review 通过 → 发布到 production registry
  5. 灰度对 agent 可见，监控调用量/错误率
  6. 下线：标记 deprecated → 灰度摘流量 → 删除
```

### Registry 字段建议

`name` / `description` / `server_id` / `owner` / `category` / `auth_policy` / `rate_limit` / `sla` / `version` / `status` / `created_at` / `deprecated_at`。

## 易错点

- 只走自动发现、没人工 review——description 质量差导致模型乱选工具。
- 没有灰度/下线流程——工具方改动直接打挂线上 agent。

## 延伸
""",
  links=["ml-ai/mcp/mcp-gateway-architecture",
         "ml-ai/mcp/openapi-to-mcp-auto-conversion"])

q("ml-ai/mcp/sandbox-vs-normal-container.md",
  "容器化沙箱 vs 普通容器",
  "ml-ai", "mcp", "medium",
  ["sandbox", "container", "security", "code-execution"],
  ["华大制造", "北京用友"],
  """# 容器化沙箱 vs 普通容器

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
""",
  links=["ml-ai/agent/multi-agent-orchestration-architecture",
         "ml-ai/mcp/mcp-gateway-architecture"])

print("\nDone. Now run: python tools/okf.py gen-index && python tools/okf.py validate")
