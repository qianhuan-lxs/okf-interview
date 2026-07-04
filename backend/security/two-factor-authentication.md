---
type: question
id: backend/security/two-factor-authentication
title: 双因素认证 (2FA)
category: backend
subcategory: security
difficulty: medium
tags: [2fa, mfa, totp, otp, security, authentication]
languages: []
role: [ai-app, sde, backend]
companies: [北京用友]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 双因素认证 (2FA)

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

## 延伸

- 关联题：[[backend/security/login-authentication]]
- 关联题：[[backend/security/xss-attack]]
