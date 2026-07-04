---
type: question
id: backend/security/xss-attack
title: XSS 攻击与防御
category: backend
subcategory: security
difficulty: medium
tags: [xss, security, web, csrf, csp]
languages: []
role: [ai-app, sde, backend]
companies: [北京用友]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# XSS 攻击与防御

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

## 延伸

- 关联题：[[backend/security/two-factor-authentication]]
- 关联题：[[backend/security/login-authentication]]
