---
type: question
id: languages/java/jvm-class-loading
title: JVM 类加载 (5 阶段 / 双亲委派 / 破坏双亲委派)
category: languages
subcategory: java
difficulty: medium
tags: [jvm, class-loading, classloader, parent-delegation, java]
languages: [java]
role: [sde, backend]
companies: []
source: ""
status: reviewed
timestamp: 2026-07-05
---

# JVM 类加载 (5 阶段 / 双亲委派 / 破坏双亲委派)

## 问题描述

JVM 类加载过程？双亲委派是什么？为什么有破坏双亲委派？哪些场景破坏？

## 解答

## 一、类加载 5 阶段（加载→验证→准备→解析→初始化）

### 1. 加载
- 通过类的全限定名获取定义此类的二进制字节流（从 jar/class/网络/动态生成）。
- 转为方法区的运行时数据结构；在堆生成 `java.lang.Class` 对象作为方法区数据访问入口。

### 2. 验证
- 文件格式、元数据、字节码、符号引用验证——确保 class 文件安全合规。

### 3. 准备
- **为类静态变量分配内存并设零值**（`static int v = 123` 此刻 v=0，赋值在初始化阶段；`static final` 常量在此阶段就赋值）。

### 4. 解析
- 常量池内的符号引用替换为直接引用（指针/偏移量）。可发生在初始化前（解析）或延迟到首次使用（懒解析）。

### 5. 初始化
- 执行 `<clinit>` 类构造器：按源码顺序执行 `static` 变量赋值 + `static` 块。**线程安全**（JVM 加锁保证一个类只初始化一次）。
- 触发时机：new 实例 / 调静态方法 / 访问静态字段（非 final 常量）/ 反射 / 子类初始化触发父类 / main 类。

## 二、类加载器与双亲委派

### 三层类加载器（JDK 9 前）
| 加载器 | 加载范围 | 实现 |
| --- | --- | --- |
| **Bootstrap ClassLoader**（启动） | `rt.jar`/核心库 | C++ 实现，JVM 一部分，无 Java 对象 |
| **Extension ClassLoader**（扩展） | `ext` 目录 | Java，`ExtClassLoader` |
| **Application ClassLoader**（应用） | classpath | Java，`AppClassLoader` |
- JDK 9 模块化后改为 Bootstrap → Platform ClassLoader → Application。

### 双亲委派模型
- 加载类时**先委托父加载器**加载，父加载不了才自己加载。
- 流程：`AppClassLoader` → 委托 `ExtClassLoader` → 委托 `Bootstrap`；Bootstrap 找不到 → ExtClassLoader 找 → AppClassLoader 找。
- **目的**：
  1. **安全**：防止用户伪造核心类（如自己写 `java.lang.String`，会被 Bootstrap 加载的官方 String 覆盖）。
  2. **唯一性**：同一个类只会被同一个加载器加载一次，保证类型一致（不同加载器加载的同名类是不同 Class）。

## 三、破坏双亲委派（重点面试题）

### 为什么需要破坏
- 双亲委派是"父优先"，但有些场景需要"子优先"或自定义加载顺序。

### 经典破坏场景

#### 1. JDBC（SPI 机制）
- `DriverManager` 在 Bootstrap 加载的核心类里，要用 `Class.forName("com.mysql.cj.jdbc.Driver")` 加载第三方驱动，但第三方驱动在 classpath，Bootstrap 加载不到。
- 解法：**Thread Context ClassLoader**（线程上下文加载器，默认 AppClassLoader）——父加载器反向用子加载器加载 SPI 实现。`ServiceLoader.load(Driver.class)` 用 TCCL。
- 这是"父加载器请求子加载器加载"——经典破坏。

#### 2. Tomcat（Web 应用隔离）
- 一个 Tomcat 跑多个 webapp，它们各自有 `lib`，类要互相隔离（webapp A 的 Spring 4 不影响 webapp B 的 Spring 5）。
- Tomcat 自定义 `WebappClassLoader`，**每个 webapp 一个**，**先自己加载（webapp WEB-INF/classes 和 lib）再委托父**——破坏双亲委派。
- 但核心类（`java.lang.*`）仍走双亲委派，避免被覆盖。

#### 3. OSGi（模块化）
- OSGi 用网状类加载器，每个 bundle 一个，可指定导入导出——彻底打破双亲委派的树状结构。

#### 4. 热部署 / 热加载
- 修改 class 后新建 ClassLoader 重新加载类——旧 ClassLoader 不可复用（已加载类不可卸载，除非加载器卸载）。
- JRebel / arthas redefine / Spring DevTools 用此机制。

## 四、类初始化顺序（高频）
1. 父类静态变量 + 静态块（按源码顺序）。
2. 子类静态变量 + 静态块。
3. 父类实例变量 + 实例块。
4. 父类构造函数。
5. 子类实例变量 + 实例块。
6. 子类构造函数。

## 易错点
- 以为 `static int v = 123` 在准备阶段赋值 → 准备阶段设零值，赋值在初始化。
- 以为双亲委派绝对安全 → SPI/Tomcat/OSGi 都要破坏。
- 不同加载器加载同名类当同一个 → 是不同 Class，`instanceof` 不通过。
- 以为类能卸载 → 只有加载该类的 ClassLoader 卸载时类才卸载（连同其 Class 对象）。

## 延伸

## 延伸

- 关联题：[[languages/java/jvm-memory-structure]]
- 关联题：[[languages/java/jvm-object-layout-jit]]
- 关联题：[[languages/java/jvm-garbage-collection]]
