---
type: question
id: networks/tcp-handshake-teardown
title: TCP 三次握手 / 四次挥手 / TIME_WAIT
category: networks
subcategory: networks
difficulty: medium
tags: [tcp, handshake, teardown, time-wait, congestion-control]
languages: []
role: [ai-app, sde, backend]
companies: [OPPO]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# TCP 三次握手 / 四次挥手 / TIME_WAIT / 拥塞控制

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
