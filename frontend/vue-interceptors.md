---
type: question
id: frontend/vue-interceptors
title: Vue 拦截器 (响应式原理)
category: frontend
subcategory: frontend
difficulty: medium
tags: [vue, reactivity, proxy, defineproperty, frontend]
languages: []
role: [ai-app, sde, backend]
companies: [中泓一线]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# Vue 拦截器 (响应式原理)

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

## 延伸

- 关联题：[[frontend/js-create-object]]
- 关联题：[[frontend/css-position-layout]]
