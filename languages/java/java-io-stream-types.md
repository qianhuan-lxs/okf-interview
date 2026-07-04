---
type: question
id: languages/java/java-io-stream-types
title: Java IO 流的种类
category: languages
subcategory: java
difficulty: easy
tags: [io, stream, nio, java, basics]
languages: []
role: [ai-app, sde, backend]
companies: [海颐]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# Java IO 流的种类

## 解答

按**流向**：输入流 / 输出流（相对程序而言）。
按**数据单位**：字节流（InputStream/OutputStream，1 byte）/ 字符流（Reader/Writer，1 char，需 charset 解码）。
按**功能**：节点流（直接连数据源） / 处理流（包装别的流加缓冲/转换/对象序列化）。

### 字节流
- `FileInputStream / FileOutputStream`
- `BufferedInputStream / BufferedOutputStream`（处理流，缓冲）
- `DataInputStream / DataInputStream`（读基本类型）

### 字符流
- `FileReader / FileWriter`
- `BufferedReader / BufferedReader`（行读 `readLine`）
- `InputStreamReader / OutputStreamWriter`（字节↔字符桥接，指定 charset）

### NIO（JDK 1.4+）
- **Channel + Buffer + Selector**，面向缓冲、可非阻塞、多路复用。
- `ByteBuffer / FileChannel / SocketChannel / Selector`。
- 适合高并发 IO（Netty 基于 NIO）。

### 选型
- 文本 → 字符流或 InputStreamReader 指定 UTF-8。
- 二进制 → 字节流。
- 高并发网络 → NIO / Netty / AIO。

## 延伸
