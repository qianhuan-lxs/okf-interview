---
type: question
id: backend/security/login-authentication
title: 登录鉴权方案 (Session / JWT / OAuth)
category: backend
subcategory: security
difficulty: medium
tags: [authentication, session, jwt, oauth, security, login]
languages: []
role: [ai-app, sde, backend]
companies: [北京用友, 探迹]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 登录鉴权方案 (Session / JWT / OAuth)

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

## 延伸

- 关联题：[[backend/microservices/microservice-user-context-propagation]]
- 关联题：[[backend/security/two-factor-authentication]]
