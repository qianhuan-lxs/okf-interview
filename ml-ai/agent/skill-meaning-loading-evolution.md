---
type: question
id: ml-ai/agent/skill-meaning-loading-evolution
title: Skill 的含义 / 加载机制 / 自进化 (以 Claude Code 为参照)
category: ml-ai
subcategory: agent
difficulty: hard
tags: [skill, claude-code, progressive-disclosure, filesystem-watcher, hot-reload, prompt-engineering, self-evolution]
languages: []
role: [ai-app, sde, backend]
companies: [华大制造, 广州大娱, 安克创新, OPPO, 北京用友, 有赞]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-07-05
---

# Skill 的含义 / 加载机制 / 自进化 (以 Claude Code 为参照)

## 问题描述

你怎么理解 skill？skill 怎么知道什么时候应该调用哪个 skill？skills 加载机制是自己写的还是框架自带？Skill 的自净化？Skill 的优点？Skill 为什么不能只是 prompt？（安克创新 / 有赞 7 层深问）

> 本文以 **Claude Code** 的真实实现为参照（官方文档 + 反编译分析 + issue #31559），把"渐进式披露"落到工程级别。Cursor / Cline 等机制类似但细节不同。

## 一、Skill 是什么

**Skill = 一份"给模型看的工作说明书"，被框架发现、按需注入、可在对话中执行。** 比裸 prompt 更结构化、可组合、可按需加载、可被框架统一治理。

一个 skill 物理上是一个目录 + 一个 `SKILL.md` 文件（无 manifest、无注册中心、无类型声明）。`SKILL.md` 的 frontmatter（name / description / 可选 `paths`）是元数据，正文是给模型看的指令。

### Skill 通常包含
1. **Description（入口描述）** — 渐进式披露的关键：模型先看到所有 skill 的 description，决定加载哪个。
2. **Instructions / 正文** — 该 skill 的工作方式、约束、输出格式。
3. **`$ARGUMENTS` / `${CLAUDE_SKILL_DIR}` 占位符** — 调用时被框架替换，让 skill 接参数、引用自身目录下资源。
4. **`paths` 字段（可选）** — gitignore 语法的文件匹配模式，用于"按文件路径激活"。
5. 可附带 `hooks/` / `.mcp.json` / `agents/` / `output-styles/`（属于 plugin 层，不归 skill watcher 管）。

## 二、加载机制：两阶段 + 单次缓存（核心，回答"是不是每次都读文件"）

**不是每轮都读。** Claude Code 是**启动发现 + 调用加载 + 单次注入不重读**的三段式。

### 阶段 1：启动 Discovery（只读 frontmatter）
- session 启动扫描 `~/.claude/skills/`、项目 `.claude/skills/`、`--add-dir` 下的 `.claude/skills/`。
- 对每个 `SKILL.md` **只解析 frontmatter**（name / description / paths），构造 `Skill` 元数据对象。
- **只有 description 列表注入 system prompt**，让模型知道"有哪些 skill 可用"——正文不进 system prompt。
- **inode 去重**：同一 `SKILL.md` 通过 symlink 同时出现在 `~/.claude/skills/` 和项目目录时，loader 记 inode 到 `Map<number, SkillSource>`，重复跳过，避免双倍加载。
- **`paths` 字段的"休眠池"**：声明了 `paths` 的 skill **不进 system prompt**，进"休眠池"。当用户碰到匹配文件时才激活并注入——比 description 路由更细粒度的条件激活。

### 阶段 2：调用 Loading（读一次完整正文）
- 模型决定用某 skill 时调用 `SkillTool({skill: "xxx"})`。
- 工具读取**完整 `SKILL.md`**，做 `$ARGUMENTS` / `${CLAUDE_SKILL_DIR}` 变量替换，可选执行内联 shell 命令。
- **完整正文作为一条 message 注入对话**。
- 在 session 级 set 里登记该 skill 名，**同 session 内不再重复发送**。

### 阶段 3：后续轮次不重读
- 官方文档原话：**"Claude Code does not re-read the skill file on later turns."**
- 正文进入对话历史后就留在那儿，后续轮次模型直接引用历史里的内容，**零文件系统访问**。

### 性能特征
| 时机 | 文件 IO |
| --- | --- |
| session 启动 | O(skills) 次 frontmatter 解析（只读几行 YAML） |
| 调用某 skill | 1 次完整 read |
| 其他轮次 | 0 次 skill 文件 IO |

**无压缩**：完整 `SKILL.md` 内容逐字注入，无摘要无压缩。长 skill 一次触发吃几千 token，这是保真 vs 省 context 的明确 trade-off——所以 skill 正文要精炼，别写废话。

## 三、何时调用哪个 skill

不是"自动知道"，是**两阶段路由**：
- **Stage 1（路由）**：所有 skill 的 **description** 在 system prompt 里，模型据此选一个（或由 `paths` 休眠池按文件路径激活）。
- **Stage 2（加载执行）**：选中后**才把该 skill 的完整 prompt 加载进 context**（渐进式披露，省 token）。

这正是 Claude Skills / Cursor Skills / Agent Skills 的共同设计：**description 是"门牌"，加载是"进屋"**。

## 四、如何感知人工更新 / 卸载 / 新增（v2.1.0+ 热重载）

三层机制，**且有一个已知 bug**。

### a) 文件 watcher（自动）
- 用 `fs.watchFile()` 监听**会话启动时已知的那些 `SKILL.md` 文件**。
- **编辑现有 `SKILL.md` 文本** → 自动检测，当前 session 内生效，无需重启。
- 监听范围**仅文件本身，不监听目录**。

### b) `/reload-skills` 命令（v2.1.152+，2026-05-27 引入）
- 手动重新扫描 skill 目录，**保留对话上下文不变**，只替换可用 skill 集合。
- 场景：手改/装了 `SKILL.md` 想立刻生效。
- 还有 `SessionStart` hook 返回 `reloadSkills: true`，给"hook 程序化装 skill"用。
- 解耦了"能力发现（cheap、可重跑的目录扫描）"与"上下文积累（expensive、重启即丢）"。

### c) 重启 session
- 兜底：丢失对话上下文，但完整重扫。

### 各操作感知行为表

| 操作 | 自动感知 | 处理 |
| --- | --- | --- |
| 改现有 `SKILL.md` 正文 | ✅ watcher | 无需操作 |
| 改 frontmatter description | ✅ watcher 检测文本变化 | 无需操作（system prompt 旧 description 是否实时刷新文档未明说，体感有延迟） |
| 删 `SKILL.md`（卸载） | ⚠️ watcher 检测到 → 从可用集合移除，**但已注入对话历史的正文无法撤回** | 后续轮次不再可调用，旧内容残留在上下文 |
| **新建 skill 目录 + `SKILL.md`** | ❌ **不感知**（已知 bug） | 跑 `/reload-skills`；若是新建**顶层目录**（会话启动时不存在），`/reload-skills` 也不行，必须重启 |
| 改 plugin 层（`hooks/` / `.mcp.json` / `agents/` / `output-styles/`） | ❌ watcher 只管 `SKILL.md` 文本 | 跑 `/reload-plugins` |

### 已知 limitation（GitHub issue #31559）
`fs.watchFile()` 只监听**会话启动时已知的单个 `SKILL.md` 文件**，没对 skill 目录用 `fs.watch()` 监听子目录创建。所以**会话中途新建的 skill 目录不会被发现**。社区修法：给目录加 `fs.watch()` + debounce 触发已有的重扫函数，但官方未合并。这是为什么需要 `/reload-skills` 兜底。

## 五、加载机制是自己写的还是框架自带

- **Claude Code / Cursor**：框架自带——扫 `.claude/skills/*/SKILL.md`，按 description 注入 system prompt，watcher 热重载。
- **Google ADK**：通过 `Agent` 的 `tools` + `sub_agents` 声明，框架调度。
- **自研框架**：常见做法是 skill registry（YAML/MD 目录）+ router prompt + 动态拼装，**这套机制本身不难写**——核心就是"启动扫 frontmatter + 调用时读正文 + 单次缓存"，加上可选的 watcher。

## 六、自进化 / 自净化

指 skill 库随使用反馈迭代：失败 case 自动回流 → 评测 → 改写 description 或 prompt。OPPO / 有赞问的"自净化"通常指自动剔除低效 skill 或修正其 description。工程做法：
- 每次 skill 调用记录 trace（input/output/是否成功/耗时/token）。
- 评测器（LLM-as-Judge 或规则）打分，低分 skill 进待优化队列。
- 人或 agent 改写 description（让路由更准）或正文（让执行更稳）。
- 改完靠 watcher / `/reload-skills` 热生效，无需重启。

## 七、为什么不能只是 system prompt（回答有赞 7 层追问）

1. **Token 成本** — 所有 skill 全塞 system prompt 会爆炸；渐进式披露按需加载才省。
2. **可组合** — skill 是模块化单元，可跨 agent 复用；裸 prompt 难复用。
3. **可观测 / 可版本化** — skill 是独立文件，可 diff、可评测、可回滚。
4. **绑定执行能力** — skill 不只是文字，还可绑 `paths` 条件激活、`$ARGUMENTS` 接参数、内联 shell、附 plugin 层（hooks/MCP），纯 system prompt 没这层。

## 易错点

- description 写成给人看的标签（"代码评审"），而不是给模型看的"何时调用我"判断依据（"当用户要求 review 代码变更时使用，会检查风格/bug/安全…"）。
- 把所有 skill 全量注入 system prompt —— 丢失渐进式披露的核心收益。
- 以为新建 skill 目录会自动被发现 —— 不会，要 `/reload-skills` 或重启。
- 长正文逐字注入无压缩 —— skill 写太长会持续吃 token，正文要精炼。

## 延伸

- 关联题：[[ml-ai/mcp/mcp-vs-skill-difference]]
- 关联题：[[ml-ai/agent/agent-function-call-mechanism]]
- 关联题：[[ml-ai/mcp/mcp-gateway-architecture]]

## Citations

- [1] [Extend Claude with skills — 官方文档](https://code.claude.com/docs/en/skills.md)
- [2] [Skill hot-reload doesn't detect new skill directories — issue #31559](https://github.com/anthropics/claude-code/issues/31559)
- [3] [Reloading Skills Mid-Session — AgentPatterns](https://agentpatterns.ai/tools/claude/reload-skills-mid-session/)
- [4] [Inside Claude Code Skills: five-layer loading mechanism — BestHub](https://www.besthub.dev/articles/inside-claude-code-skills-how-a-single-markdown-file-powers-a-five-layer-loading-mechanism-03ae41163a90)
- [5] [Agent Skills in the SDK — 官方文档](https://code.claude.com/docs/en/agent-sdk/skills)
