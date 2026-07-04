#!/usr/bin/env python3
"""Seeder: devops + networks + security + frontend + system-design + algorithms + behavioral."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from seed_louis_ai import q

# --- devops/ --------------------------------------------------------------- #

q("devops/cicd-pipeline-jenkins.md",
  "CI/CD 流水线 (Jenkins → 构建 → 镜像 → 部署)",
  "devops", "devops", "medium",
  ["ci-cd", "jenkins", "docker", "pipeline", "devops"],
  ["OPPO"],
  '''# CI/CD 流水线 (Jenkins → 构建 → 镜像 → 部署)

## 问题描述
容器化部署负责的两个功能点？具体流水线打包流程？用过 Jenkins 吗？

## 解答

### 典型流水线
```
1. Code Commit  → Git push 触发 webhook
2. CI 阶段
   - Checkout / 拉代码
   - 静态检查（lint、SonarQube）
   - 单元测试 + 覆盖率
   - 构建（Maven/Gradle/Go build）
   - 构建 Docker 镜像 → 推 Harbor
   - 镜像扫描（Trivy/Clair）
3. CD 阶段
   - 改 K8s 部署镜像 tag
   - kubectl apply / Helm upgrade
   - 滚动更新
   - 健康检查 / 灰度
4. 验证：smoke test、监控告警
```

### Jenkinsfile（声明式）
```groovy
pipeline {
  agent any
  stages {
    stage("Build")   { steps { sh "mvn -B clean package" } }
    stage("Image")   { steps { sh "docker build -t reg/app:${env.BUILD_NUMBER} ." } }
    stage("Push")    { steps { sh "docker push reg/app:${env.BUILD_NUMBER}" } }
    stage("Deploy")  { steps { sh "kubectl set image deploy/app app=reg/app:${env.BUILD_NUMBER}" } }
  }
}
```

### 工具栈
- 流水线：Jenkins / GitLab CI / GitHub Actions / ArgoCD（GitOps）。
- 镜像仓库：Harbor。
- 部署：Helm / Kustomize / ArgoCD。

### OPPO 场景追问：状态机 & 资源泄露
- **状态机**：流水线任务有 pending/running/success/failed/canceled，状态机驱动 UI 与重试。
- **资源泄露**：构建 pod 没清理、Docker layer 堆积、临时 volume 没回收 → 定期 GC + 配额。

## 延伸
''',
  links=["devops/k8s-rolling-update-health-probe",
         "devops/offline-deployment"])

q("devops/k8s-rolling-update-health-probe.md",
  "K8S 滚动更新 / 健康检查探针",
  "devops", "devops", "medium",
  ["kubernetes", "rolling-update", "liveness", "readiness", "probe", "devops"],
  ["OPPO"],
  '''# K8S 滚动更新 / 健康检查探针

## 问题描述
K8S 滚动更新 / 健康检查探针（OPPO 主管面预测题）。

## 解答

### 三种探针
| 探针 | 作用 | 失败后果 |
| --- | --- | --- |
| **livenessProbe** | 容器是否"活着" | 重启容器 |
| **readinessProbe** | 容器是否"就绪接流量" | 从 Service Endpoints 摘除，不重启 |
| **startupProbe**（1.16+） | 启动是否完成 | 启动前禁用 liveness/readiness，避免慢启动被杀 |

探针机制：HTTP GET / TCP socket / exec command。

### 滚动更新（RollingUpdate）
- `strategy.type=RollingUpdate`，`maxSurge`（最多多出多少副本）、`maxUnavailable`（最多不可用多少）。
- 流程：新 pod 起 → readiness 通过 → 旧 pod 摘流量并终止。
- 始终保持 `replicas - maxUnavailable` 个可用，零停机。

### 配合探针
- 启动慢的应用配 startupProbe + 较大 failureThreshold。
- readiness 探针保证新 pod 健康才接流量。
- liveness 探针检测死锁等假死，重启恢复。

### 常见坑
- liveness 探针过严 → 临时抖动导致雪崩重启。
- readiness 与 liveness 用同一接口 → 就绪失败也重启。
- 滚动更新时 maxUnavailable=0 但 readiness 没配 → 旧 pod 等不到新 pod ready，超时卡死。

## 延伸
''',
  links=["devops/cicd-pipeline-jenkins",
         "devops/k8s-environment-labels-resource-management"])

q("devops/k8s-environment-labels-resource-management.md",
  "K8S 环境标签 / 资源管理",
  "devops", "devops", "medium",
  ["kubernetes", "labels", "resource-quota", "devops"],
  ["有赞", "探迹"],
  '''# K8S 环境标签 / 资源管理

## 问题描述
K8S 资源为什么要统一打环境标签？环境标签打好之后的作用？资源不足时清理的优先级？

## 解答

### 统一打环境标签
- 给所有资源打 `env=dev/test/prod`、`team=xxx`、`tier=frontend/backend`。
- 作用：
  1. **Selector 路由**：Service 用 `selector` 选同标签 Pod。
  2. **NetworkPolicy**：按标签限定网络可达。
  3. **ResourceQuota / LimitRange**：按 namespace/标签分资源配额。
  4. **监控/告警/成本分摊**：按标签聚合 Prometheus 指标、计算团队成本。
  5. **清理策略**：dev 资源夜间回收，prod 长驻。

### 资源管理
- **requests**（调度依据，保证量）/ **limits**（上限，超则 throttle/kill）。
- CPU limit 超则 throttle（cgroup）；memory limit 超则 OOMKilled。
- **ResourceQuota** 限 namespace 总量；**LimitRange** 限单个 pod 默认/范围。

### 资源不足清理优先级
- **PriorityClass**：低优先级 pod（如批处理）先被驱逐。
- **QoS 等级**：Guaranteed（req=limit）> Burstable（req<limit）> BestEffort（无 req/limit）。节点压力时 BestEffort 先杀。
- **节点压力驱逐**：kubelet 在内存/磁盘压力时按 QoS + Priority 驱逐。
- **dev 环境定时清理**：CronJob 夜间 scale 0 或删非关键 deployment。

## 易错点
- 不设 requests → 调度器不知道需求，节点超卖。
- memory limit 设小于 JVM 堆 + 元空间 + 堆外 → OOMKilled（Java 应用 Xmx 应 < limit - headroom）。

## 延伸
''',
  links=["devops/k8s-rolling-update-health-probe",
         "ml-ai/mcp/sandbox-vs-normal-container"])

q("devops/offline-deployment.md",
  "离线部署经验",
  "devops", "devops", "medium",
  ["offline-deployment", "air-gapped", "kubernetes", "devops"],
  ["OPPO"],
  '''# 离线部署经验

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
''',
  links=["devops/cicd-pipeline-jenkins"])

q("devops/devops-direction-understanding.md",
  "对 DevOps 方向的了解",
  "devops", "devops", "easy",
  ["devops", "concept", "culture"],
  ["OPPO"],
  '''# 对 DevOps 方向的了解

## 问题描述
你对 DevOps 这个方向了解吗？

## 解答

### DevOps = Development + Operations
不是某个工具，而是**文化 + 实践 + 工具**，目标：缩短从代码到生产的周期、提升交付质量与频率。

### 核心实践
1. **CI/CD**：自动化构建、测试、部署。
2. **IaC（基础设施即代码）**：Terraform / Pulumi / Ansible，环境可版本化可复现。
3. **容器化 + 编排**：Docker / Kubernetes。
4. **可观测性**：Metrics（Prometheus）+ Logs（Loki/ELK）+ Traces（OpenTelemetry/SkyWalking）。
5. **GitOps**：ArgoCD/Flux，Git 作为唯一真相源。
6. **SRE 实践**：SLI/SLO/Error Budget、错误预算驱动发布节奏。
7. **安全左移（DevSecOps）**：镜像扫描、依赖扫描、密钥扫描进流水线。

### 岗位技能栈
- Linux/网络基础。
- 至少一门脚本语言（Python/Go/Shell）。
- Docker/K8s 实操。
- CI/CD 工具（Jenkins/GitLab CI/Argo）。
- 监控告警体系。
- IaC。

### 与"开发"的关系
DevOps 不只是运维的事，是让开发能自助发布、自助运维，强调**共同责任**。

## 延伸
''',
  links=["devops/cicd-pipeline-jenkins",
         "devops/k8s-environment-labels-resource-management"])

# --- networks/ + backend/security/ ---------------------------------------- #

q("networks/tcp-handshake-teardown.md",
  "TCP 三次握手 / 四次挥手 / TIME_WAIT",
  "networks", "networks", "medium",
  ["tcp", "handshake", "teardown", "time-wait", "congestion-control"],
  ["OPPO"],
  '''# TCP 三次握手 / 四次挥手 / TIME_WAIT / 拥塞控制

## 问题描述
TCP 三次握手 / 四次挥手 / TIME_WAIT / 拥塞控制（OPPO 主管面预测题）。

## 解答

### 三次握手（建立）
1. C → S：SYN, seq=x
2. S → C：SYN+ACK, seq=y, ack=x+1
3. C → S：ACK, ack=y+1
- **为什么 3 次**：双向确认双方收发能力；2 次无法防历史连接请求（旧 SYN 导致 S 误开连接）。

### 四次挥手（关闭）
1. A → B：FIN
2. B → A：ACK（B 还可能有数据要发）
3. B → A：FIN
4. A → B：ACK
- 全双工关闭需各方向独立 FIN。

### TIME_WAIT（主动关闭方进入）
- 持续 2MSL。
- **作用**：1) 确保最后 ACK 到达 B，B 没收到则 B 重发 FIN，A 还能再发 ACK；2) 让旧连接的延迟报文消亡，避免新连接复用同四元组时受旧报文污染。
- **问题**：高并发短连接服务器 TIME_WAIT 堆积耗尽端口。
- **优化**：用 `SO_REUSEADDR` / 缩短 `tcp_fin_timeout` / 改长连接。

### 拥塞控制
- **慢启动**：cwnd 从 1 指数增长到 ssthresh。
- **拥塞避免**：到 ssthresh 后线性增长。
- **快重传**：连续 3 个重复 ACK 立即重传不等超时。
- **快恢复**：cwnd 减半而非回到 1。
- 算法演进：Reno → Cubic（Linux 默认）→ BBR（Google，基于带宽/延迟而非丢包）。

## 延伸
''',
  links=[])

q("backend/security/xss-attack.md",
  "XSS 攻击与防御",
  "backend", "security", "medium",
  ["xss", "security", "web", "csrf", "csp"],
  ["北京用友"],
  '''# XSS 攻击与防御

## 问题描述
你知道 XSS 攻击吗？跨站脚本攻击。

## 解答

**XSS (Cross-Site Scripting)**：攻击者把恶意脚本注入到网页，在其他用户浏览器执行。

### 三类
| 类型 | 注入点 | 特征 |
| --- | --- | --- |
| **存储型** | 持久化到 DB（评论/个人资料） | 危害最大，访问者都中招 |
| **反射型** | URL 参数即时回显 | 需诱导点击特制链接 |
| **DOM 型** | 前端 JS 操作 DOM 注入 | 不经过服务端 |

### 危害
盗 cookie/session、键盘记录、钓鱼、蠕虫传播、CSRF 配合。

### 防御
1. **输出转义**：往 HTML/JS/URL/属性里输出时按上下文 escape（`<` → `&lt;` 等）。OWASP Java Encoder / `HtmlUtils.htmlEscape`。
2. **CSP（Content Security Policy）**：`Content-Security-Policy: default-src 'self'`，禁内联脚本、限制资源来源。
3. **HttpOnly Cookie**：JS 读不到 cookie，降低盗用。
4. **富文本用白名单过滤**（如 OWASP Java HTML Sanitizer / jsoup），不要 regex 黑名单。
5. **框架自动转义**：Vue/React 默认转义，避免 `v-html` / `dangerouslySetInnerHTML`。

### 与 CSRF 区别
- XSS 是**偷**用户身份（执行脚本）；CSRF 是**借**用户身份（诱导已登录用户访问恶意站点发请求）。
- CSRF 防御：SameSite Cookie / CSRF Token / Referer 校验 / 关键操作二次确认。

## 延伸
''',
  links=["backend/security/two-factor-authentication",
         "backend/security/login-authentication"])

q("backend/security/two-factor-authentication.md",
  "双因素认证 (2FA)",
  "backend", "security", "medium",
  ["2fa", "mfa", "totp", "otp", "security", "authentication"],
  ["北京用友"],
  '''# 双因素认证 (2FA)

## 问题描述
知道什么叫双因素认证吗？

## 解答

**2FA (Two-Factor Authentication)**：登录时除密码（你知道的）外，再加一个第二种因素（你有的 / 你是谁），双因素通过才放行。

### 三类认证因素
- **知识因素**（你知道）：密码、PIN。
- **拥有因素**（你有）：手机（短信/TOTP 验证码）、硬件 key、邮箱。
- **生物因素**（你是）：指纹、FaceID。

2FA = 密码 + 上述任一第二因素。

### 实现方式
| 方式 | 实现 | 安全性 |
| --- | --- | --- |
| **短信验证码** | 短信网关 | 中（SIM 劫持、嗅探风险） |
| **TOTP**（Google Authenticator） | 共享密钥 + 时间窗口 HMAC，6 位码 30s | 高（离线生成，需密钥安全存储） |
| **推送通知** | App 收到推送点确认 | 高（需装 App） |
| **硬件 Key**（U2F/FIDO2） | 公私钥挑战响应 | 极高（防钓鱼） |

### TOTP 原理
- 服务端给用户生成随机 secret，存双方。
- 客户端按 `HMAC-SHA1(secret, current_time / 30)` 取后 6 位。
- 服务端同样算法校验，允许 ±1 时间窗口容错。
- 标准：RFC 6238（TOTP）/ RFC 4226（HOTP，计数器版）。

### 工程要点
- secret 加密存 DB，不能明文。
- 备份恢复码（recovery codes）防丢手机。
- 时间同步（NTP）。
- 登录后发审计通知。

## 延伸
''',
  links=["backend/security/login-authentication",
         "backend/security/xss-attack"])

q("backend/security/login-authentication.md",
  "登录鉴权方案 (Session / JWT / OAuth)",
  "backend", "security", "medium",
  ["authentication", "session", "jwt", "oauth", "security", "login"],
  ["北京用友", "探迹"],
  '''# 登录鉴权方案 (Session / JWT / OAuth)

## 问题描述
你做过登录鉴权吗？API 需要认证怎么做？

## 解答

### 认证（Authentication，你是谁）vs 授权（Authorization，你能干啥）
- 登录 = 认证；权限校验 = 授权。常被混说。

### 主流方案

#### 1. Session + Cookie（有状态）
- 登录成功服务端建 Session，返 `Set-Cookie: JSESSIONID=...`。
- 后续请求带 Cookie，服务端按 sessionId 查 session。
- 优点：服务端可随时吊销。缺点：多实例需 session 共享（Redis）；跨域麻烦；移动端不友好。

#### 2. JWT (JSON Web Token，无状态)
- 登录返 `header.payload.signature`，客户端存（localStorage/cookie），请求放 `Authorization: Bearer <jwt>`。
- 服务端验签（HMAC/RSA），不存状态。
- 优点：无状态、易扩展、跨域。缺点：签发后到过期前**无法吊销**（需黑名单/短 TTL + refresh token）。
- 注意：payload 是 base64 不是加密，别放敏感数据；用 `HS256` 时密钥要保密，多用 `RS256`。

#### 3. OAuth 2.0 / OIDC（第三方登录）
- 授权码模式（最常用）：客户端 → 授权服务器 → 资源服务器。
- SSO（单点登录）：CAS / Keycloak / Auth0 / 自建 OIDC。

#### 4. API 鉴权
- API Key / Secret + 签名（HMAC 请求体 + 时间戳防重放）。
- mTLS（服务间强认证）。
- 网关统一鉴权，业务服务信任网关透传的 `X-User-Id`（见 [[backend/microservices/microservice-user-context-propagation]]）。

### 工程要点
- 密码用 BCrypt/Argon2 加盐慢哈希，不要 MD5/SHA256。
- 登录限速防爆破、验证码、异地登录告警。
- HTTPS 强制，防中间人。
- refresh token 轮换、滑动过期。

## 延伸
''',
  links=["backend/microservices/microservice-user-context-propagation",
         "backend/security/two-factor-authentication"])

# --- frontend/ ------------------------------------------------------------ #

q("frontend/js-create-object.md",
  "JS 创建对象的方式",
  "frontend", "frontend", "easy",
  ["javascript", "object", "prototype", "frontend"],
  ["中泓一线"],
  '''# JS 创建对象的方式

## 问题描述
JS 怎么创建一个对象？

## 解答

```javascript
// 1. 字面量
const o1 = { a: 1 };

// 2. new Object
const o2 = new Object(); o2.a = 1;

// 3. 构造函数
function Foo(x) { this.x = x; }
const o3 = new Foo(1);

// 4. Object.create（指定原型）
const o4 = Object.create({ proto: 1 });

// 5. ES6 class
class Bar { constructor(x) { this.x = x; } }
const o5 = new Bar(1);
```

### new 的过程
1. 创建空对象 {}，`__proto__` 指向构造函数的 `prototype`。
2. 构造函数的 this 指向新对象，执行构造函数。
3. 若构造函数返回对象则用之，否则返回新对象。

### 原型链
- 每个对象有 `__proto__`（即 `[[Prototype]]`）指向其构造函数的 `prototype`。
- 访问属性沿原型链查找，到 `Object.prototype` 终止。

## 延伸
''',
  links=["frontend/vue-interceptors"])

q("frontend/vue-interceptors.md",
  "Vue 拦截器 (响应式原理)",
  "frontend", "frontend", "medium",
  ["vue", "reactivity", "proxy", "defineproperty", "frontend"],
  ["中泓一线"],
  '''# Vue 拦截器 (响应式原理)

## 问题描述
Vue 的拦截器有哪些种？

## 解答

题目"拦截器"在 Vue 语境指**响应式系统的属性拦截机制**，以及**HTTP 拦截器**。

### 响应式拦截

#### Vue 2：`Object.defineProperty`
- 对 data 对象每个属性定义 getter/setter，setter 时通知依赖（Dep → Watcher）。
- 缺点：
  - 无法检测新增/删除属性（需 `Vue.set` / `Vue.delete`）。
  - 无法监听数组索引和 length 变化（需重写 7 个数组方法）。
  - 深度监听需递归遍历，初始化开销大。

#### Vue 3：`Proxy`
- 整对象代理，拦截 13 种操作（get/set/has/deleteProperty/ownKeys 等）。
- 优点：
  - 能检测新增/删除属性。
  - 能监听数组变化。
  - 惰性响应式（访问到才递归代理）。
  - 性能更好。

### HTTP 拦截器（axios）
- `axios.interceptors.request.use(config => { 加 token; return config })`。
- `axios.interceptors.response.use(res => ..., err => { 401 跳登录; return Promise.reject(err) })`。
- 用于统一加 token、错误处理、loading、重试。

### 路由拦截器（vue-router）
- `router.beforeEach((to, from, next) => { 鉴权; next() })`。
- 用于登录态校验、权限路由。

## 延伸
''',
  links=["frontend/js-create-object", "frontend/css-position-layout"])

q("frontend/css-position-layout.md",
  "CSS 定位布局",
  "frontend", "frontend", "easy",
  ["css", "position", "layout", "flexbox", "frontend"],
  ["中泓一线"],
  '''# CSS 定位布局

## 问题描述
CSS 前端的定位布局有哪些种？

## 解答

### position 定位
| 值 | 脱离文档流 | 参照 |
| --- | --- | --- |
| `static`（默认） | 否 | 正常流 |
| `relative` | 否 | 自身原位置 |
| `absolute` | 是 | 最近非 static 祖先 |
| `fixed` | 是 | 视口（或 transform 祖先） |
| `sticky` | 否 | 滚动到阈值前 relative，越界后 fixed |

### 布局方案
- **正常流**：block / inline / inline-block。
- **Float**：老布局，已少用。
- **Flexbox**（一维）：`display:flex; justify-content; align-items`。
- **Grid**（二维）：`display:grid; grid-template-columns`。
- **定位**：上述 position 组合。
- **多列**：column-count。

### 居中速查
- Flex：`display:flex; justify-content:center; align-items:center;`（最通用）
- Grid：`place-items:center`
- 绝对定位：`position:absolute; top:50%; left:50%; transform:translate(-50%,-50%)`
- 行内：父 `text-align:center`；行高 = 高度则垂直居中

### BFC（块级格式化上下文）
- 触发：overflow 非 visible / float / position:absolute,fixed / display:flex,inline-block 等。
- 作用：清浮动、避免 margin 重叠、隔离布局。

## 延伸
''',
  links=["frontend/vue-interceptors"])

# --- system-design/ ------------------------------------------------------- #

q("system-design/short-url-system.md",
  "短链接系统设计",
  "system-design", "system-design", "hard",
  ["system-design", "short-url", "hash", "base62", "cache"],
  ["拼多多"],
  '''# 短链接系统设计

## 问题描述
设计一个短链接系统。长链接映射到短链接，访问短链接时跳转回原始长链接。访问短链接怎么跳回？需要考虑哪些点？怎么生成短链接？数据结构具体什么样？

## 思路

核心三问：**短码怎么生成？长短怎么存？跳转怎么实现？**

## 解答

### 1. 短码生成
- **方案 A：发号器 + Base62**
  - 分布式发号器（Snowflake / Redis INCR / 数据库号段）产 `long id`。
  - `id` 转 Base62（0-9a-zA-Z，62 进制），6 位可表 568 亿，够用。
  - 优点：短、定长、不重复、不依赖 hash。
- **方案 B：MD5/MurmurHash 取前 6~7 位**
  - 优点：无需中心发号。缺点：冲突需处理（加盐或重试）。
- **方案 C：预生成短码池**：离线生成一批入库，用即取。

推荐 **A**：可控、可预测、无冲突。

### 2. 存储数据结构
```
short_url | long_url | create_time | expire_time | owner | click_count
```
- 主键 `short_url`，索引 `long_url`（防止重复生成、查重）。
- 量级估算：千亿级 → 分库分表，按 short_url hash 分片。
- 冷热分离：近期热点放 Redis，历史归档。

### 3. 跳转流程
```
1. 用户访问 s.xx/abc123
2. 网关/服务：先查 Redis（命中 99%+）→ 未命中查 DB 回填
3. 302 重定向到 long_url（302 不缓存，便于统计/过期控制；301 缓存则丢统计）
4. 异步记点击日志（UA/IP/referer/时间）→ Kafka → 分析
```

### 4. 关键考虑点
- **缓存**：短→长 高频读，Redis 缓存 + 本地 Caffeine 二级，命中率 >99%。
- **防滥用**：长链接白名单、限频、敏感域名拦截。
- **过期与失效**：expire_time + 失效返回 404 或兜底页。
- **自定义短码**：用户指定 slug，需查重。
- **HTTPS + 短域名**：越短越好。
- **防碰撞/防猜测**：发号器递增易被遍历，可加随机位或加密 id（如 Feistel 网络混淆）。
- **高可用**：服务多副本、缓存集群、DB 主从；跳转是核心链路不能挂。

### 5. 容量估算
- 100亿 短链 × 0.5KB/条 ≈ 5TB → 分 64 库 × 64 表。
- QPS：读 10w/s（302 跳转），写 1k/s。读多写少，缓存主导。

## 易错点
- 用 301 永久重定向 → 浏览器缓存导致后续跳转不经过服务，统计丢失。
- 用 hash 不处理冲突 → 同长链可能同短码。

## 延伸
''',
  links=["system-design/bi-data-analysis-agent",
         "system-design/vertical-observation-pipeline"])

q("system-design/bi-data-analysis-agent.md",
  "BI 数据分析智能体设计",
  "system-design", "system-design", "hard",
  ["system-design", "bi", "ai-agent", "rag", "nl2sql"],
  ["广州大娱"],
  '''# BI 数据分析智能体设计

## 问题描述
让你做一个 AI 智能体对 BI 系统里的报表做数据分析，怎么实现？后台 BI 系统，通过微信/钉钉对话来分析数据，智能体应该怎么做？

## 思路

关键：**对话入口 → 意图识别 → NL2SQL/取数 → 分析 → 图文回填**。不是简单套 LLM，要拆清楚每一步对应什么方案。

## 解答

### 系统分层

```
[微信/钉钉] → [接入网关(钉钉/企微回调)] 
            → [对话编排 Agent]
                ├─ 意图识别：闲聊 / 取数分析 / 报表订阅 / 异常追问
                ├─ 上下文记忆：多轮指代"上个月的销售额"→ 解析时间
                ├─ NL2SQL：把自然语言 → SQL（限定库表 schema 注入）
                ├─ 取数执行：调 BI 数据源（MySQL/ClickHouse/Doris）
                ├─ 分析洞察：LLM 基于结果生成解读 + 异常归因
                └─ 回填渲染：图表（折线/柱/饼）+ 文字 → 卡片消息
```

### 各环节方案
1. **入口**：钉钉/企微机器人 webhook；OAuth 绑定企业账号 → 拿到数据权限。
2. **意图识别**：轻量分类器或 LLM router，区分"取数分析 / 闲聊 / 配置订阅"。
3. **NL2SQL**：
   - 把库 schema、维度指标字典、示例 QA 作为 few-shot 注入 prompt。
   - 用 SQL 语法校验 + 沙箱执行（只读账号 + 行数限制 + 超时）。
   - 加 RAG：把历史成功 SQL 当召回库，提精度。
   - 复杂指标预定义成"指标 API"，LLM 选指标而非裸写 SQL，降错率。
4. **取数**：调 BI 后端既有数据接口（不要让 agent 直连生产 DB），保留 BI 的权限/缓存。
5. **分析**：LLM 拿到表格数据 → 生成"环比/同比/异常点/归因"文字。
6. **可视化**：服务端用 ECharts 服务端渲染图，转图片或卡片消息发回。
7. **多轮记忆**：保留最近 N 轮 + 指代消解（"上个月"= 哪月）。

### 工程难点
- **NL2SQL 准确率**：宽表多指标时易错。策略：限定 schema + 指标白名单 + 校验 + 失败重写。
- **权限**：按企业账号 + 角色 + 行级权限控制可查数据范围。
- **性能**：慢查询保护（超时即返回"查询中，结果稍后推送"）。
- **可观测**：每次 NL2SQL 记录 query/SQL/结果/是否人工修正，回流评测改进。

### 反例（面试官追问"没有系统性思路"）
不能只说"用 LLM 调一调"，要分阶段给方案：意图、NL2SQL、取数、分析、渲染、回填，每段都有选型。

## 延伸
''',
  links=["ml-ai/agent/multi-agent-orchestration-architecture",
         "ml-ai/rag/rag-full-pipeline",
         "system-design/short-url-system"])

q("system-design/vertical-observation-pipeline.md",
  "垂直观测链路系统设计",
  "system-design", "system-design", "hard",
  ["system-design", "observability", "tracing", "evaluation", "ai-agent"],
  ["探迹"],
  '''# 垂直观测链路系统设计

## 问题描述
知道我们公司做什么？如果参与进来做垂直观测链路系统，你怎么设计？从买家消息到 AI 答案整个数据流转应该怎样？

## 思路

"垂直观测链路"= 把一条 AI 业务（买家消息→AI 答案）的**全链路数据流和评测**串起来，做问题定位、质量度量、回流改进。本质是 AI 版的 APM + 数据飞轮。

## 解答

### 全链路数据流
```
1. 买家消息 (IM/客服) 
   → 2. 接入网关 (脱敏、限流、traceId 注入)
   → 3. 编排 Agent (意图分类 → RAG/Tool/Memory)
       ├─ 3.1 RAG 检索 (query 改写 / 向量召回 / rerank)
       ├─ 3.2 Tool 调用 (CRM 查订单 / 知识库)
       └─ 3.3 LLM 生成 (prompt / model / params)
   → 4. 后处理 (审核 / 引用标注 / 安全过滤)
   → 5. 答案回传买家
   → 6. 用户反馈 (点赞/点踩/转人工)
   → 7. 评测回流 (自动指标 + 人工标注)
```

### 观测维度（每段都打点）
| 维度 | 指标 |
| --- | --- |
| 链路 | traceId 串联，每 step input/output/latency/token/cost |
| 业务 | 解决率、转人工率、满意度、首次响应时长 |
| RAG | 召回 recall@k、引用准确率、片段命中 |
| 安全 | 敏感词命中、PII 泄漏、幻觉率 |
| 成本 | token / 调用次数 / 单会话成本 |

### 系统架构
- **采集**：SDK / OpenTelemetry instrumentation 在各环节打 span + 事件。
- **传输**：Kafka 解耦，避免业务阻塞。
- **存储**：
  - trace：ClickHouse / Tempo / Jaeger（高写入、查链路）。
  - 事件明细：ES（全文搜"哪条会话出错"）。
  - 指标：Prometheus + VictoriaMetrics。
  - 原始会话：对象存储 + Hive/Iceberg 离线分析。
- **查询/展示**：Grafana 面板 + 自研会话回放页（按 traceId 还原全流程，含每步 prompt/response）。
- **评测回流**：
  - 在线：自动指标（回答长度、引用是否在召回集、用户点踩率）。
  - 离线：人工标注 + LLM-as-Judge 打分，导 bad case 给 prompt/skill 迭代。
  - 形成"线上观测→bad case→离线评测→prompt/RAG 改进→上线"闭环。

### 测试链路（追问）
- 录制线上流量做离线回放（影子库），新 prompt/模型灰度对比指标。
- 黄金集回归：固定一批 QA，每次模型/prompt 变更跑一遍，监控指标漂移。
- A/B：流量分桶对比新旧版本。

### 体量
- 假设 100w 会话/天，每会话 5 step → 500w span/天，单 span ~1KB → 5GB/天，ClickHouse 轻松。
- 保留热数据 7 天 + 冷归档。

## 延伸
''',
  links=["ml-ai/agent/multi-agent-orchestration-architecture",
         "ml-ai/rag/rag-recall-algorithms",
         "devops/devops-direction-understanding"])

# --- algorithms/arrays-strings/ ------------------------------------------- #

q("algorithms/arrays-strings/string-to-integer.md",
  "String to Integer (atoi) 编码题",
  "algorithms", "arrays-strings", "medium",
  ["string", "atoi", "edge-case", "leetcode", "coding"],
  ["拼多多"],
  '''# String to Integer (atoi) 编码题

## 问题描述
写一个方法把字符串解析为整数。输入 "1234" 返回整数 1234。然后让你测试，把测试用例范围都写一下（5 轮边界追问）。

> LeetCode 8. String to Integer (atoi)

## 输入输出 / 约束
- 去前导空格
- 可选正负号
- 跳过非数字字符后停止
- 越界返回 INT_MAX (2147483647) / INT_MIN (-2147483648)

## 解答

```python
def myAtoi(s: str) -> int:
    INT_MAX, INT_MIN = 2**31 - 1, -2**31
    i, n = 0, len(s)
    # 1. 去前导空格
    while i < n and s[i] == " ":
        i += 1
    if i == n:
        return 0
    # 2. 符号
    sign = 1
    if s[i] in "+-":
        if s[i] == "-":
            sign = -1
        i += 1
    # 3. 数字（边累加边判越界）
    num = 0
    while i < n and s[i].isdigit():
        d = ord(s[i]) - ord("0")
        # 越界预判：避免累加后再判溢出
        if num > (INT_MAX - d) // 10:
            return INT_MAX if sign == 1 else INT_MIN
        num = num * 10 + d
        i += 1
    return sign * num
```

### 测试用例（5 轮追问要点）
1. **正常**："1234" → 1234；"0" → 0；"-5" → -5
2. **空格**："   123" → 123；"   " → 0
3. **符号**："+1" → 1；"-1" → -1；"+-1" → 0；"--1" → 0
4. **非数字**："123abc" → 123；"abc123" → 0；"  12.3" → 12
5. **越界**："2147483647" → 2147483647；"2147483648" → 2147483647；"-2147483648" → -2147483648；"-2147483649" → -2147483648
6. **边界**："" → 0；"+" → 0；"  +  1" → 0（符号后有空格）

## 易错点
- 累加后再判溢出 → 已溢出，应在累加前用 `(INT_MAX - d) // 10` 预判。
- 多个符号 "+-1" 应返回 0 而非 -1。
- 前导空格但符号后又有空格不算数字。

## 延伸
''',
  links=["algorithms/dynamic-programming/longest-increasing-subsequence"])

# --- behavioral/ ---------------------------------------------------------- #

q("behavioral/resignation-reason-and-relocation.md",
  "离职原因 / Relocation / 通勤 (软性)",
  "behavioral", "behavioral", "easy",
  ["behavioral", "resignation", "relocation", "soft"],
  ["华大制造", "中泓一线", "安克创新", "OPPO", "北京用友", "探迹"],
  '''# 离职原因 / Relocation / 通勤 (软性)

## 问题描述
离职原因？几月份走的？现在在哪个城市？能接受 relocation / 出差吗？

## 应对要点（脱敏通用模板）

### 离职原因（避免抱怨前公司）
- 业务方向调整 / 个人成长瓶颈 / 想深耕 AI 方向（与目标岗位对齐）。
- 不要说"和领导冲突""加班太狠"等负面理由。

### 在职状态/到岗时间
- 离职 / 在职可月底到岗 / 1 个月内。

### Relocation / 通勤
- 提前想好可接受城市、是否带家属、通勤上限。
- 出差：明确频次可接受范围（如月 1-2 次可，长期驻外不行）。

### 反问机会
- 团队规模、业务方向、晋升路径、技术栈。

## 延伸
''',
  links=["behavioral/career-planning-engineering-vs-pm"])

q("behavioral/career-planning-engineering-vs-pm.md",
  "职业规划 (工程 vs 项目推进者)",
  "behavioral", "behavioral", "easy",
  ["behavioral", "career-planning", "soft"],
  ["安克创新", "华大制造"],
  '''# 职业规划 (工程 vs 项目推进者)

## 问题描述
未来两三年职业规划？想做偏工程还是项目推进者？

## 应对要点

### 短期（1 年）
- 把当前 AI 工程方向吃透：Multi-Agent 编排、RAG、MCP 生态。
- 主导 1-2 个高价值项目落地。

### 中期（2-3 年）
- 成为 AI 应用方向技术骨干，能独立 owner 复杂系统。
- 在团队内沉淀方法论、带 1-2 个新人。

### 工程路线（建议主线）
- 偏技术深度：架构设计、性能、可靠性、AI 工程化。
- 给出具体方向（如"AI Agent 工程化"），避免空泛。

### 项目推进路线
- 如果对方是创业公司 / 小团队，可表达"工程为主 + 兼顾推进"的复合能力，但主线仍以技术立足。

### 避雷
- 不要说"想转管理"（技术岗面试官忌讳）。
- 不要空喊"成为专家"不给路径。

## 延伸
''',
  links=["behavioral/resignation-reason-and-relocation",
         "behavioral/technical-learning-sources"])

q("behavioral/language-preference.md",
  "语言偏好 (Java vs Python vs Go)",
  "behavioral", "behavioral", "easy",
  ["behavioral", "language", "java", "python", "go", "soft"],
  ["OPPO", "安克创新"],
  '''# 语言偏好 (Java vs Python vs Go)

## 问题描述
以后还是希望在 Java 上深耕吗？编程语言熟哪些？几个语言之间的区别？日常后端更喜欢哪个？

## 应对要点

### 各语言定位
- **Java**：企业后端、生态成熟、强类型、JVM 跨平台、适合大型系统。啰嗦但稳。
- **Python**：AI/数据/脚本之王，生态丰富，动态类型开发快，性能弱、部署生产需小心。
- **Go**：云原生（K8s/Docker 都 Go）、并发原语（goroutine）优秀、二进制部署简单、性能好。生态新。
- **C++**：性能极致、底层；心智负担重。

### 回应建议
- 表达"主语言 + 第二语言"组合，例如"Java 为主、Python 做 AI、Go 做基础设施"，体现适应力。
- 不要执着"我只用 Java"——AI 时代岗位常需 Python；云原生常需 Go。
- "更喜欢的"选与目标岗位匹配的，并给理由（生态 / 团队 / 工程性）。

### 反问
- 团队主语言、新项目技术栈（OPPO 答"Python 应用层 / Go 网络层"）。

## 延伸
''',
  links=["behavioral/career-planning-engineering-vs-pm"])

q("behavioral/overtime-and-travel.md",
  "加班 / 出差态度",
  "behavioral", "behavioral", "easy",
  ["behavioral", "overtime", "travel", "soft"],
  ["华大制造", "海颐"],
  '''# 加班 / 出差态度

## 问题描述
你对加班的看法？能接受出差吗？

## 应对要点

### 加班
- 不抗拒合理加班（项目攻坚、线上故障），不鼓励无效加班。
- 表达高效工作的态度：把事做完比把时间填满重要。
- 避免两个极端：①"绝对不加" ②"996 没问题"。

### 出差
- 明确频次/时长上限：短期（1-2 周）OK，长期驻外视家庭情况。
- 反问：出差场景是什么？驻场实施还是客户对接？

### 反问技巧
- 团队工作节奏、是否大小周、加班强度真实情况。

## 延伸
''',
  links=["behavioral/resignation-reason-and-relocation"])

q("behavioral/achievement-source.md",
  "成就感来源",
  "behavioral", "behavioral", "easy",
  ["behavioral", "achievement", "soft"],
  ["华大制造"],
  '''# 成就感来源

## 问题描述
一年多工作哪项让你最有成就感？

## 应对要点（STAR 结构）

挑选一个**可量化、与你简历核心项目一致**的故事：
- **S** 场景：某个项目/线上问题。
- **T** 任务：你负责什么。
- **A** 行动：你具体做了什么（技术决策 + 落地）。
- **R** 结果：量化收益（性能提升 X%、故障下降 Y%、节省 token 成本 Z 元/月、推动 N 个团队接入）。

### 示例方向
- 自研 MCP 网关把 N 个工具统一收口，下游接入工作量降 X 倍。
- 优化 RAG 召回，回答准确率从 X 提升到 Y。
- K8s 资源治理让集群成本降 X%。

### 避雷
- 不要说"学会了 XX"——成就感是产出，不是学习。
- 不要把团队功劳全揽自己。

## 延伸
''',
  links=["behavioral/career-planning-engineering-vs-pm"])

q("behavioral/technical-learning-sources.md",
  "技术学习途径",
  "behavioral", "behavioral", "easy",
  ["behavioral", "learning", "soft"],
  ["中泓一线", "安克创新"],
  '''# 技术学习途径

## 问题描述
平时获取最新技术信息的途径有哪些？你自己平常学习 AI 领域新东西的途径和方法？

## 应对要点（给具体清单 + 方法论）

### 信息源
- 一手：官方文档 / GitHub Releases / arXiv / 模型 release notes / RFC。
- 公司工程博客：Anthropic / OpenAI / Google Research / Meta / Netflix / ByteDance。
- 社区：Hacker News、Reddit r/MachineLearning、Twitter/X 上研究者、知乎、微信公众号（机器之心等）。
- 视频/会议：NeurIPS/ICML/ACL keynote、GTC、QCon、ArchSummit。

### 方法论（这是面试官真正想听的）
- **跟主线不跟热点**：盯 3-5 个核心方向（Agent / RAG / 推理），新概念按"是否影响主线"判断深读与否。
- **手搓验证**：新框架/新模型必本地跑一遍 demo，不止看博客。
- **输出倒逼输入**：写笔记 / 内部分享 / GitHub 项目，能讲清楚才算懂。
- **建知识库**：把读过的整理成可检索的笔记（呼应本仓库的 OKF 思想）。

## 延伸
''',
  links=["behavioral/ai-coding-tools-usage"])

q("behavioral/ai-coding-tools-usage.md",
  "AI Coding 工具使用 (Claude Code / Codex / 千问)",
  "behavioral", "behavioral", "easy",
  ["behavioral", "ai-coding", "claude-code", "codex", "soft"],
  ["探迹", "北京用友", "安克创新"],
  '''# AI Coding 工具使用 (Claude Code / Codex / 千问)

## 问题描述
平常 AI coding 怎么用？用 CC 吗？CC+DeepSeek？code 自己付费还是公司提供？千问 code 用过吗？

## 应对要点

### 用什么
- **Claude Code** / Cursor / Copilot / Cline / Aider / Codex。
- 国产：DeepSeek、通义千问 code、CodeGeeX。

### 怎么用（区分场景）
- **样板/CRUD**：让 AI 直接生成，人工 review。
- **复杂逻辑**：AI 出草稿，自己改；或让 AI 解释/重构既有代码。
- **调试**：贴报错 + 上下文让 AI 给假设，自己验证。
- **学习**：让 AI 解释源码、给对比例子。

### 注意（体现工程素养）
- 不盲信：AI 会幻觉 API、混淆版本，必须读官方文档验证。
- 安全：别贴密钥/敏感代码到公网模型；公司敏感代码用私有部署 / 不传。
- 评测：关键代码自己跑测试，不靠 AI"看起来对"。

### 付费 vs 公司
- 表达愿意自己投资学习（订阅 Claude/Cursor），也接受公司提供。

## 延伸
''',
  links=["behavioral/technical-learning-sources",
         "behavioral/china-us-ai-gap"])

q("behavioral/china-us-ai-gap.md",
  "中美 AI 差距看法",
  "behavioral", "behavioral", "medium",
  ["behavioral", "ai-industry", "opinion", "soft"],
  ["安克创新"],
  '''# 中美 AI 差距看法

## 问题描述
你觉得中美之间的 AI 差距是在变大还是变小？为什么所有创新都是美国的？

## 应对要点（理性、有数据、不情绪化）

### 现状
- **基座模型**：美国（OpenAI/Anthropic/Google/Meta）仍领先，前沿能力（推理、长上下文、多模态）1-2 年差距。
- **应用层**：中国追赶快，开源生态（Qwen/DeepSeek/GLM）已接近 GPT-4 级，部分中文场景反超。
- **算力**：美国出口管制限制高端 GPU（H100/H200），中国靠国产卡（昇腾）+ 算法优化对冲。
- **数据**：中文高质量数据相对少，但合成数据、RL 范式降低对绝对数据量依赖。

### 差距变大还是变小
- **前沿基座**：短期内仍可能拉大（美国资本 + 人才 + 芯片 + 生态聚集）。
- **应用与开源**：差距在缩小，DeepSeek-V3/R1、Qwen3 等开源模型证明工程能力追上来了。
- **范式红利窗口**：每次新范式（RLHF→MoE→推理时计算）出现时差距会短暂拉大，开源追赶后又缩小。

### 为什么创新多在美国
- 资本密度、产学研一体、人才全球化流动、芯片生态、对失败容忍度。
- 但中国擅长工程化 + 大规模落地 + 成本压缩（DeepSeek 训练成本即例）。

### 个人态度
- 不妄自菲薄也不盲目乐观；抓住应用层与工程化机会，同时关注基座前沿。

## 延伸
''',
  links=["behavioral/ai-coding-tools-usage"])

q("behavioral/github-tech-blog.md",
  "GitHub / 技术博客",
  "behavioral", "behavioral", "easy",
  ["behavioral", "github", "blog", "soft"],
  ["安克创新"],
  '''# GitHub / 技术博客

## 问题描述
GitHub 用了多久？首页写这么多技术栈干什么？你的文章从 24 年就停了？

## 应对要点

### GitHub
- 用途：个人项目、面经沉淀、开源贡献、技能展示。
- "首页写多技术栈"：应解释是"接触过"还是"精通"，避免被打"广而不精"。建议改 README 突出 1-2 个核心项目。

### 技术博客停更
- 诚实给原因（工作忙 / 优先级调整），并表达仍以其他形式输出（GitHub README / 内部分享）。
- 建议恢复轻量输出：哪怕月 1 篇，保持可见的"在持续学习"信号。
- 把面经/项目复盘整理成仓库（本面试题库就是一例）。

## 延伸
''',
  links=["behavioral/technical-learning-sources"])

q("behavioral/八股-attitude-and-disliked-java.md",
  "八股态度 / Java 最讨厌的地方 / 设计模式偏好",
  "behavioral", "behavioral", "easy",
  ["behavioral", "java", "design-pattern", "opinion", "soft"],
  ["安克创新"],
  '''# 八股态度 / Java 最讨厌的地方 / 设计模式偏好

## 问题描述
八股重要吗？高中生背得应该比你快吧？Java 最讨厌的地方？最常用/最优雅的设计模式？

## 应对要点

### 八股重要吗
- 重要但不该是全部：八股是**地基**（并发/JVM/网络/数据库），决定能不能答上来；项目深挖和系统设计决定上限。
- "高中生背得比你快"——反驳点：八股不是纯背诵，要能解释原理 + 联系项目取舍，这是经验优势。

### Java 最讨厌的地方
给**真实但有建设性**的回答，避免纯吐槽：
- **啰嗦**：getter/setter/equals/hashCode/toString 样板（Lombok / Records 缓解）。
- **类型系统偏弱**：擦除泛型、数组协变坑。
- **JVM 启动慢、内存大**：云原生时代对微服务不友好（GraalVM Native Image 缓解）。
- **历史包袱**：Date/Calendar 设计糟糕（java.time 才修复）。

### 最常用 / 最优雅的设计模式
- 常用：模板方法（Spring XxxTemplate）、策略（消除 if-else）、建造者（链式构造）、责任链（Filter/Interceptor）。
- 最优雅示例：**策略 + 工厂** 消除长 if-else；或 **观察者 / 事件总线** 解耦。

## 延伸
''',
  links=["languages/java/template-method-pattern",
         "behavioral/career-planning-engineering-vs-pm"])

q("behavioral/major-biology-relation.md",
  "专业与生命科学/生物的关联",
  "behavioral", "behavioral", "easy",
  ["behavioral", "major", "soft"],
  ["华大制造"],
  '''# 专业与生命科学/生物的关联

## 问题描述
你专业跟生命科学/生物的关联？（华大制造背景）

## 应对要点

华大基因是基因组学公司，问此题是看你是否理解业务背景。

### 回应思路
- 若专业相关：直接讲交叉点（如生物信息学需要大数据/AI 分析基因数据）。
- 若不相关：承认专业不直接相关，但强调**计算机/AI 与生物的交叉价值**——
  - 基因数据需要大规模存储与计算（HPC/分布式）。
  - AI for Science：蛋白质结构预测（AlphaFold）、序列分析、药物发现。
  - 华里的 AI 应用方向可能是把 LLM/RAG 用于科研文献、实验记录、基因报告解读。
- 表达对业务方向的好奇与学习意愿。

## 延伸
''',
  links=["behavioral/resignation-reason-and-relocation"])

print("\nDone: devops + networks + security + frontend + system-design + algorithms + behavioral")
