# Interview Knowledge Catalog (IKC)

一个面向 **面试题** 的、参考 [Open Knowledge Format (OKF)](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) 设计思想整理的知识目录。

> 一道题 = 一个 markdown 文件（带 YAML frontmatter）。
> 目录层级做主题分类，frontmatter 做 Agent 可查询维度，`index.md` 做 progressive disclosure，markdown 链接做知识图谱。

## 为什么这样组织

OKF 的核心思想是把知识做成 **人能读、Agent 也能读、可 diff、可移植** 的纯文本资产。本仓库把它落到面试题场景：

- **人可读** — 直接 `cat` 一道题，问题 / 思路 / 解答 / 复杂度全在一页。
- **Agent 可查询** — 统一的 frontmatter schema 让 Agent 通过 `grep`/`rg` 按 `category`、`difficulty`、`tags`、`companies`、`role` 等任意维度过滤，无需 SDK。
- **版本可控** — 每道题一个文件，PR review、行级 diff、blame 全部天然可用。
- **Progressive disclosure** — 每个目录有 `index.md`，Agent 先读 index 再决定下钻，避免一次性把整库塞进上下文。
- **图谱化** — 题目之间用 markdown 链接互引，表达"同题型变体""考点前置""延伸阅读"等关系，不止树形父子。
- **最小约束、自由扩展** — 必填字段保证互操作，任意额外 frontmatter 键都不会破坏消费者。

## 目录结构

```
interview/
├── README.md            # 本文件
├── SPEC.md              # 格式规范（必读）
├── index.md             # 根导航（自动生成）
├── _templates/          # 题目模板
├── tools/               # 管理 CLI（add / gen-index / search）
└── <category>/          # 一级主题
    ├── index.md
    └── <subcategory>/
        ├── index.md
        └── <slug>.md    # 一道题
```

一级主题（按 Agent 查询职责切分，正交不重叠）：

| 目录 | 覆盖范围 |
| --- | --- |
| `algorithms/` | 算法与数据结构（按子题型细分） |
| `system-design/` | 系统设计 / 架构题 |
| `databases/` | SQL、索引、事务、范式、分库分表、NoSQL |
| `operating-systems/` | 进程线程、内存、IO、文件系统 |
| `networks/` | TCP/IP、HTTP、DNS、TLS、应用层协议 |
| `distributed-systems/` | CAP、一致性、共识、消息队列、缓存 |
| `concurrency/` | 并发编程、锁、内存模型（跨语言） |
| `languages/<lang>/` | 各语言特性题（Python/Java/Go/JS/CPP/Rust …） |
| `frontend/` | 浏览器、框架、性能、可访问性 |
| `backend/` | API 设计、鉴权、中间件、可观测性 |
| `devops/` | CI/CD、容器、K8s、IaC、监控 |
| `ml-ai/` | 机器学习 / 深度学习 / LLM 工程题 |
| `behavioral/` | 行为面试题（BQ / STAR） |

## 快速上手

```bash
# 添加一道题（交互式生成 frontmatter + 模板正文）
python tools/okf.py add

# 重新生成所有 index.md
python tools/okf.py gen-index

# 按 frontmatter 维度检索
python tools/okf.py search --difficulty hard --tags kafka --role backend
```

## Agent 查询速查

```bash
# 所有 hard 难度的后端题
rg -l '^difficulty: hard' --type md | xargs rg -l '^role:.*backend'

# 所有带 "kafka" 标签的题
rg -l '^tags:.*kafka'

# 某家公司最近问过的题
rg -l '^companies:.*[<]Google[>]' --type md
```

详见 [SPEC.md](./SPEC.md)。
