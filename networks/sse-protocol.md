---
type: question
id: networks/sse-protocol
title: SSE 协议 (规范/AI 流式输出/OpenAI vs Anthropic/SSE vs WebSocket)
category: networks
subcategory: ""
difficulty: medium
tags: [sse, server-sent-events, eventsource, text-event-stream, streaming, openai, anthropic, websocket, http, ai]
languages: []
role: [sde, backend, ai-app]
companies: []
source: ""
status: reviewed
timestamp: 2026-07-05
---

# SSE 协议 (规范/AI 流式输出/OpenAI vs Anthropic/SSE vs WebSocket)

## 问题描述

SSE 是什么？有哪些规范？AI 流式输出用的是 SSE 吗？OpenAI 和 Anthropic 的 SSE 格式有什么区别？SSE 和 WebSocket 什么区别？什么时候用哪个？

## 解答

## 一、SSE 是什么

**Server-Sent Events（SSE）= 服务器单向推送给浏览器的 HTTP 流式协议**。基于 HTTP 长连接，服务器持续往响应里写事件，客户端通过 `EventSource` API 接收。

- 单向：**服务器 → 客户端**，客户端不能通过同一连接回推（要回数据另发 HTTP 请求）。
- 文本协议：纯文本，每事件 UTF-8 编码。
- 自动重连：浏览器断线后自动重连，并通过 `Last-Event-ID` 头告知服务器最后收到的事件 ID。
- 长连接：一条 HTTP 连接持续推送多个事件，避免轮询。

## 二、规范来源

SSE 不是独立 RFC，是 **HTML Living Standard（WHATWG）的一部分**：
- **EventSource 接口**：`EventSource` Web API 规范（WHATWG HTML 规范的"Server-sent events"章节）。
- **MIME 类型**：`text/event-stream`（IANA 注册）。
- **事件格式**：规范定义的 4 个字段 + `

` 分隔。
- 历史上 W3C 也发布过 EventSource 推荐，现已合并入 WHATWG HTML。

## 三、事件格式（4 个字段）

每条 SSE 消息由若干行字段组成，**用空行（`

`）分隔**：

| 字段 | 作用 | 示例 |
| --- | --- | --- |
| `data:` | 消息数据（可多行拼接） | `data: {"text":"hello"}` |
| `event:` | 事件类型（客户端可分别监听） | `event: message_stop` |
| `id:` | 事件 ID（重连时通过 `Last-Event-ID` 头回传） | `id: 12345` |
| `retry:` | 客户端重连等待时间（毫秒） | `retry: 3000` |
| `:`（冒号开头） | 注释/心跳，不发数据 | `: keep-alive` |

### 示例
```
event: ping
data: {"ts": 1700000000}

data: line1
data: line2
id: 42

data: [DONE]
```
- `data:` 多行 → 客户端 `event.data` 用 `
` 拼接。
- 浏览器 `EventSource` 自动按 `event` 字段分派到 `addEventListener(eventType, ...)`，没 `event` 字段的走 `onmessage`。

## 四、EventSource API（浏览器）

```javascript
const es = new EventSource('/api/stream');
es.onmessage = e => console.log('default:', e.data);
es.addEventListener('user_joined', e => console.log('user:', e.data));
es.onerror = e => console.log('error, browser will auto-reconnect');
es.close();   // 主动关
```
- 默认自动重连，重连间隔由 `retry:` 字段或浏览器默认（~3s）控制。
- 重连时带 `Last-Event-ID: 42` 请求头，服务器可据此续传。
- 只支持 GET（`EventSource` 构造只接 URL），不能带自定义 header / POST body——这是 SSE 在需要鉴权时的痛点。

## 五、AI 流式输出用的是 SSE 吗？

**是**。**OpenAI 和 Anthropic 的流式响应都基于 SSE**，请求 body 加 `"stream": true`，响应 `Content-Type: text/event-stream`，token 逐个 delta 推送。这是 ChatGPT/Claude 前端"打字机"效果的底层。

### OpenAI Chat Completions 格式（无 `event:` 字段）
```
data: {"id":"chatcmpl-...","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

data: {"id":"chatcmpl-...","choices":[{"index":0,"delta":{"content":" world"},"finish_reason":null}]}

data: {"id":"chatcmpl-...","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```
- 每行 `data:` + JSON，**无 `event:` 字段**，全部走默认 message。
- **终止信号**：`data: [DONE]`（字符串 sentinel，非 JSON）。
- 内容在 `choices[0].delta.content`。
- 想拿 token usage：请求加 `stream_options: {include_usage: true}`，最后一 chunk 带 `usage`。
- **OpenAI Responses API**（新）改为**语义化 typed 事件**（`response.created`、`response.output_text.delta`、`response.completed`），仍走 SSE 传输。

### Anthropic Messages API 格式（typed `event:` 字段）
```
event: message_start
data: {"type":"message_start","message":{"id":"msg_abc","role":"assistant","content":[],"usage":{"input_tokens":25,"output_tokens":1}}}

event: content_block_start
data: {"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"Hello"}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":" world"}}

event: content_block_stop
data: {"type":"content_block_stop","index":0}

event: message_delta
data: {"type":"message_delta","delta":{"stop_reason":"end_turn"},"usage":{"output_tokens":17}}

event: message_stop
data: {"type":"message_stop"}

event: ping
data: {"type":"ping"}
```
- 每条带 `event:` 类型，客户端按类型分别处理。
- 生命周期：`message_start` → 多个 `content_block_start/delta/stop`（每个 content block 一组，text/thinking/tool_use 都走这套）→ `message_delta`（顶层变更如 stop_reason/usage）→ `message_stop`。
- **终止信号**：`event: message_stop`（**不用** `[DONE]`）。
- `ping` 事件做 keep-alive 心跳。
- tool_use 流式参数通过 `input_json_delta` 增量推送。

### 两家关键差异速查
| 维度 | OpenAI Chat Completions | Anthropic Messages |
| --- | --- | --- |
| `event:` 字段 | 无 | 有（typed） |
| 内容字段 | `choices[0].delta.content` | `delta.text`（在 `content_block_delta` 内） |
| 终止信号 | `data: [DONE]` | `event: message_stop` |
| token usage | 需 `stream_options.include_usage` | `message_start` + `message_delta` 自带 |
| tool use 流式 | `delta.tool_calls[].function.arguments` 增量 | `input_json_delta` 增量 |
| 心跳 | 无标准（实现依赖） | `event: ping` |

### 为什么 AI 用 SSE 而不用 WebSocket
- **请求-响应模型**：LLM 推理是一次请求流式回包，本质 server→client 单向推送，不需要双向。
- **HTTP 生态友好**：SSE 走标准 HTTP，能过 CDN/网关/反向代理，鉴权用普通 HTTP header，负载均衡友好。
- **简单**：不需要 WebSocket 的握手/帧协议/状态机。
- **自动重连**：网络抖动浏览器自动续接（AI 场景一般重发，因为模型有状态难续）。
- 反向场景：OpenAI Responses API 提供 **WebSocket 模式**用于"持久会话+增量输入"（多轮流式输入输出），这是少数例外。

## 六、SSE vs WebSocket（核心对比）

| 维度 | SSE | WebSocket |
| --- | --- | --- |
| 通信方向 | **单向** server→client | **双向**全双工 |
| 协议 | HTTP（`text/event-stream`） | 自有协议（`ws://`，RFC 6455） |
| 端口 | 80/443（HTTP） | 80/443（升级握手后转 ws） |
| 数据格式 | 文本（UTF-8） | 文本 + 二进制 |
| 自动重连 | ✅ 浏览器自带 | ❌ 需自己实现 |
| 断点续传 | `Last-Event-ID` 头原生支持 | 自己设计消息 ID |
| 客户端 API | `EventSource`（仅 GET） | `WebSocket`（任意） |
| 自定义 header | ❌ `EventSource` 不支持 | ❌ 握手时可带，之后无 |
| 鉴权 | 走 cookie 或 query token（痛点） | 握手 header / 子协议 |
| 代理/CDN/防火墙 | 友好（标准 HTTP） | 部分代理不友好（升级握手被拦） |
| HTTP/2 连接数限制 | 同源 6 连接（HTTP/1.1）/ HTTP/2 无限 | 不限 |
| 开销 | 低（HTTP 长连接） | 中（帧协议开销 + 握手） |
| 背压 | 无原生（靠 TCP 背压 + 应用层 buffer 控制） | 无原生（同左） |
| 适合 | 服务器推送、AI 流式、SSE/股票行情、通知 | 聊天室、协作编辑、游戏、双向实时 |

### 选型决策
- **只需 server→client 推送** → SSE（更简单，HTTP 友好）。
- **需要 client→server 频繁双向** → WebSocket。
- **AI 流式输出** → SSE（业界事实标准）。
- **多端实时聊天/协作** → WebSocket。
- **需要二进制流** → WebSocket（SSE 只文本，base64 转换费带宽）。
- **穿透严格企业代理** → SSE 更稳（标准 HTTP）。

## 七、HTTP chunked vs SSE

- HTTP/1.1 `Transfer-Encoding: chunked` 是底层传输机制，**SSE 建立在它之上**（`text/event-stream` 响应通常 chunked 编码）。
- 两者都能"流式"传，但 SSE 多了：事件格式（`data:`/`event:`/`id:`）、`EventSource` API、自动重连、`Last-Event-ID`。
- 用 `fetch` + `ReadableStream` 自己解析 chunked 也行（OpenAI SDK 多数这么干，绕开 EventSource 只 GET 的限制）——但需自己实现 SSE 解析（按 `

` 分事件、按字段拆）。

## 八、SSE 实战要点

### 后端实现
- 响应头：`Content-Type: text/event-stream`、`Cache-Control: no-cache`、`Connection: keep-alive`。
- **Nginx 代理坑**：默认 buffer 响应，要加 `proxy_buffering off;` 或响应头 `X-Accel-Buffering: no`，否则前端收不到流。
- 每写一个事件 flush 一次（Servlet 用 `response.getWriter().flush()`；WebFlux `Flux` 自然流式）。
- 心跳：定期写 `: ping

`（注释行）保活，防代理/防火墙超时断连。

### Spring 实现（MVC `SseEmitter` vs WebFlux `Flux<ServerSentEvent>`）

两者底层栈完全不同，不只是 API 包装差别。

**底层栈与服务器**
| | MVC `SseEmitter` | WebFlux `Flux<ServerSentEvent>` |
| --- | --- | --- |
| 基础 | Servlet 3.0 异步（`AsyncContext`） | Reactive Streams / Reactor |
| 服务器 | Tomcat/Jetty/Servlet 容器 | Netty / reactive Tomcat / Undertow |
| 编码类 | `org.springframework.web.servlet.mvc.method.annotation.SseEmitter` | `org.springframework.http.codec.ServerSentEvent` + `ServerSentEventHttpMessageWriter` |

**MVC（命令式）** —— 手动 `send`/`complete`：
```java
@GetMapping(value="/stream", produces=MediaType.TEXT_EVENT_STREAM_VALUE)
public SseEmitter stream() {
    SseEmitter emitter = new SseEmitter(0L);   // 0 = 不超时
    executor.execute(() -> {
        try {
            for (Event e : source) {
                emitter.send(SseEmitter.event()
                    .id(String.valueOf(e.getId()))
                    .name("update")
                    .data(e, MediaType.APPLICATION_JSON));
            }
            emitter.complete();
        } catch (IOException ex) { emitter.completeWithError(ex); }
    });
    emitter.onTimeout(source::close);
    emitter.onError(ex -> source.close());
    return emitter;
}
```

**WebFlux（声明式）** —— 返回 `Flux`，框架订阅：
```java
@GetMapping(value="/stream", produces=MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<ServerSentEvent<Event>> stream() {
    return source.flux()
        .map(e -> ServerSentEvent.builder(e)
            .id(String.valueOf(e.getId()))
            .event("update")
            .build())
        .onErrorResume(ex -> Flux.empty());
}
// 也可直接返回 Flux<T>，框架自动包成 ServerSentEvent
```

**8 维对比**
| 维度 | MVC `SseEmitter` | WebFlux `Flux<ServerSentEvent>` |
| --- | --- | --- |
| 线程模型 | 每 connection 占一个 Servlet async slot；`send` 由任意线程调 | Netty event loop 几线程复用千万连接 |
| **背压** | ❌ **无原生**——`send` 到慢客户端 buffer 满则阻塞或超时，需自己检测断开 | ✅ **原生 Reactor 背压沿链传**——慢客户端不 `request(n)`，上游自动限速 |
| 取消传播 | `complete()`/`onCompletion` 手动清理 | 客户端断 → Flux `cancel` 自动传到上游（DB cursor/Kafka consumer 自动关） |
| 错误处理 | `onError`/`onTimeout`/`completeWithError` 回调 | `onErrorResume`/`onErrorMap`/`retry` 链式操作符 |
| 并发上限 | 受 Tomcat `maxThreads`/async slot（数百~数千） | event loop，万~十万级持久连接 |
| 编程 | 命令式，好写好调，栈清楚 | 声明式，调试难（响应式栈跨线程） |
| 慢客户端 | 内存风险（buffer 堆积），要自己监控断开 | 背压自然限速，无内存爆 |
| 适合 | 已 MVC 项目、简单推送、量不大 | 高并发流式、需背压、SSE 推送网关、已 WebFlux |

**2026 虚拟线程时代**
- MVC `SseEmitter` + `spring.threads.virtual.enabled=true` → 每连接一 VT，并发上限大幅提高，但**仍无原生背压**——慢客户端问题没解决。
- WebFlux `Flux` 的背压是协议级保证，VT 出现后仍是流式推送场景的更优解（这正是 [WebFlux 文档](backend/microservices/spring-webflux) 里说的"WebFlux 留给流式/背压"）。

**选型**
- 简单推送、已 MVC 项目、连接数不多 → `SseEmitter`。
- 高并发流式、需要背压、SSE 推送网关、已 WebFlux → `Flux<ServerSentEvent>`。
- AI token 流式（单请求一次响应，量不大）→ `SseEmitter` 够用；多用户聚合推送/慢客户端防护 → WebFlux。

### 鉴权痛点
- `EventSource` 不支持自定义 header → 用 cookie（同域）或 query token（`?token=...`，有泄露风险，需短时效 + 限定路径）。
- 复杂鉴权用 `fetch` + `ReadableStream` 自己解析 SSE，能带任意 header。

## 九、连接数限制（坑）

- **HTTP/1.1 同源最多 6 个 SSE 连接/浏览器**——多标签页/多 EventSource 会撞墙。
- **HTTP/2 无此限制**（多路复用）——升 HTTP/2 解决。
- 服务端用 HTTP/2 + 单连接多事件流（用 `event:` 字段分派）能省连接。

## 十、背压

SSE **无原生背压**（不像 WebFlux `Flux` 的 `request(n)`）。慢客户端时：
- 底层靠 **TCP 背压**（发送 buffer 满则 write 阻塞）。
- 应用层要主动控制：检测写阻塞/超时 → 断开慢客户端，避免内存堆积。
- WebFlux `Flux<Event>` SSE 是例外——Reactor 背压沿链传到上游（限速生产）。

## 十一、AI 流式常见坑

### 0. 选型建议（高频追问：流式调 LLM 该用 SseEmitter 还是 Flux）

**默认推荐：Spring MVC + `SseEmitter` + 虚拟线程**（2026 大多数场景最优）。理由：
- LLM 流式是请求-响应模型（一次请求一次流式回包，连接活几秒~几分钟），不是持久多事件订阅——`SseEmitter` 命令式 `send`/`complete` 完美匹配。
- 浏览器几乎不是慢客户端（LLM 是慢生产者，token 速度 < 渲染速度）→ WebFlux 的原生背压**用不上**（背压从下游往上游传，下游是浏览器，它不慢）。
- 真正瓶颈在上游 LLM API rate limit，与 SseEmitter/Flux 选型无关。
- 代码简单可调试，VT 解决并发（`spring.threads.virtual.enabled=true` 每请求一 VT）。

**改用 WebFlux `Flux<ServerSentEvent>` 的场景**：
1. 服务本质是 **LLM 网关**（10k+ 并发流式代理）→ WebFlux + WebClient 透传 SSE（不解码不重编码）最省资源，Netty event loop 比 Tomcat async slot 更省线程。
2. **已全栈 WebFlux** → 保持栈一致。
3. 需要**端到端 Reactor 背压**（慢客户端防护，但 LLM 场景浏览器很少是慢客户端，此理由多数 LLM 场景不成立）。

### ⚠️ 澄清常见误解：用 Spring AI 不需要换 WebFlux

Spring AI 的 `stream()` 返回 `Flux<ChatResponse>`，**MVC 和 WebFlux 都能直接返回 `Flux<ServerSentEvent>`**——**不需要为 Spring AI 单独换栈**。

- **Spring MVC 从 5.0 起支持响应式返回类型**：`ReactiveTypeHandler` 检测到控制器返回 `Flux`/`Mono` 时，自动用**异步 Servlet**（`AsyncContext`）订阅，逐元素写出——**底层是 Tomcat Servlet，不是 Netty**。
- 同一段 `return flux.map(...)` 代码在 MVC 和 WebFlux 都能跑，区别在运行时（Servlet async vs Netty event loop）和背压（MVC 无原生背压 vs WebFlux 有）。

```java
// MVC 控制器（Tomcat）也能这样写——Spring MVC 自动处理 Flux
@GetMapping(value="/chat", produces=MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<ServerSentEvent<String>> chat(@RequestParam String p) {
    return chatClient.prompt().user(p).stream().content()
        .map(t -> ServerSentEvent.builder(t).event("delta").build())
        .concatWith(Flux.just(ServerSentEvent.builder("[DONE]").event("done").build()));
}
```

**SpringMVC 与 SpringWebFlux 的关系**：不是"冲突"——是平行两栈，Spring Boot 选一个作主栈：
- `spring-boot-starter-web` → MVC + Servlet 容器（Tomcat）。
- `spring-boot-starter-webflux` → WebFlux + Netty。
- **两个都引** → Spring Boot **默认 MVC（Servlet）作主栈**，WebFlux 不激活，但 `WebClient` / 响应式返回类型仍可用。

**结论**：已有 MVC 项目用 Spring AI 直接返回 `Flux<ServerSentEvent>` 即可，别为 Spring AI 换 WebFlux。只有当服务本质是高并发 LLM 网关、或已全栈 WebFlux 时才考虑 WebFlux。

**决策树**
```
用 Spring AI / LangChain4j reactive？ → WebFlux Flux<ServerSentEvent>
高并发 LLM 网关（10k+）？          → WebFlux + WebClient SSE 透传
已全栈 WebFlux？                    → WebFlux Flux<ServerSentEvent>
否则                                 → Spring MVC + SseEmitter + VT（默认）
```

### 1. 网关/代理缓冲
- Nginx 默认 `proxy_buffering on` → 流被缓存到完整再发，前端看不到打字效果。
- 解法：`proxy_buffering off;` 或 `X-Accel-Buffering: no`。

### 2. 终止信号混用
- OpenAI 检测 `data: [DONE]`；Anthropic 检测 `event: message_stop`。SDK 各自处理，自己写解析器别混。

### 3. 解析跨 chunk 截断
- SSE 事件可能被 TCP chunk 切到一半（`data: {"text":"Hel` + `lo"}`）→ 解析器要按 `

` 缓冲到完整事件再解析 JSON。

### 4. 鉴权 + EventSource
- 只能 cookie / query token；带 JWT header 要改 `fetch` 自解析。

### 5. 重连后重复输出
- AI 推理有状态难续，前端一般重发完整请求而非续传——别盲目依赖 `Last-Event-ID`。

### 6. 浏览器关页面服务端不知
- 客户端 `close()` 后服务端 write 会异常 → 后端要 try-catch + 清理资源。
- **关键：浏览器断开必须 abort 上游 LLM 调用**——`SseEmitter` 用 `onCompletion`/`onTimeout`/`onError` 回调调 `streamingClient.abort()`；`Flux` 客户端断会自动 `cancel` 传到上游 WebClient。不 abort → 用户关页面后服务还在向 LLM API 付费推 token。

### 7. 前端别用 `EventSource` 调 LLM
- `EventSource` 只支持 GET、不能带 POST body 和 JWT header——聊天接口要 POST + 鉴权 header，必须用 `fetch` + `ReadableStream` 自解析 SSE：
```javascript
const resp = await fetch('/chat', { method:'POST',
  headers:{'Authorization':jwt,'Content-Type':'application/json'},
  body: JSON.stringify({prompt}) });
const reader = resp.body.getReader();
const decoder = new TextDecoder();
let buf = '';
while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  buf += decoder.decode(value, { stream:true });
  const events = buf.split('\n\n'); buf = events.pop();  // 留半截
  for (const e of events) parseAndRender(e);
}
```

### 8. 格式建议跟随 OpenAI 风格
- `data: {json}\n\n` + 终止 `data: [DONE]` —— 第三方 SDK / 工具链兼容性最好。
- token usage 放最后一条 `data:` 再 `[DONE]`。

### 9. 心跳防代理超时
- 长输出时定期发 `: ping\n\n`（注释行，客户端忽略，保活防 Nginx/防火墙超时断连）。

### 10. 透传别解码再重编码
- 高并发网关场景，WebClient `bodyToFlux(ServerSentEvent.class)` 直接 emit，不要解码成对象再序列化回去——浪费 CPU。

### 7. HTTP/1.1 6 连接限制
- 多标签页 + 多 SSE → 撞墙。升 HTTP/2 或合并事件流。

## 易错点
- 把 SSE 当双向 → 是单向，client→server 要另发请求。
- 以为 SSE 是独立协议 → 是 HTTP 之上的事件格式 + EventSource API。
- 以为 WebSocket 替代 SSE → 双向才该用 WS，单向推送 SSE 更简单。
- `EventSource` 带 header → 不支持，要 fetch 自解析。
- Nginx 不关 buffering → 前端收不到流。
- HTTP/1.1 多 SSE → 6 连接限制。
- AI 终止信号当统一 → OpenAI `[DONE]` vs Anthropic `message_stop`。
- 跨 chunk 当完整事件 → 必须按 `

` 缓冲。

## 延伸

## 延伸

- 关联题：[[networks/okhttpclient-design.md]]
- 关联题：[[backend/microservices/spring-webflux.md]]
- 关联题：[[ml-ai/agent/agent-memory-management.md]]
- 关联题：[[ml-ai/mcp/mcp-protocol-understanding.md]]
