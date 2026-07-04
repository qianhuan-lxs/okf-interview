---
type: question
id: frontend/js-create-object
title: JS 创建对象的方式
category: frontend
subcategory: frontend
difficulty: easy
tags: [javascript, object, prototype, frontend]
languages: []
role: [ai-app, sde, backend]
companies: [中泓一线]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# JS 创建对象的方式

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

## 延伸

- 关联题：[[frontend/vue-interceptors]]
