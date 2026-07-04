---
type: question
id: databases/mysql/oracle-gaussdb
title: Oracle / 高斯数据库了解
category: databases
subcategory: mysql
difficulty: easy
tags: [oracle, gaussdb, database, domestic-db]
languages: []
role: [ai-app, sde, backend]
companies: [海颐]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# Oracle / 高斯数据库了解

## 问题描述
Oracle 或者说华为的高斯数据库有没有了解过？

## 解答

### Oracle
- 商业闭源关系数据库龙头。
- 特性：RAC（集群）、Data Guard（主备）、表空间、PL/SQL、物化视图、分区表、强大优化器。
- 企业级 OLTP/OLAP 常见，金融/电信/制造业深使用。

### GaussDB（华为高斯）
- 华为自研分布式数据库，主打国产化/信创。
- 系列：
  - **GaussDB(for MySQL)** —— MySQL 兼容，云原生存算分离。
  - **GaussDB(for PostgreSQL)** / **GaussDB 200**（数仓）—— PG 兼容。
  - **openGauss** —— 2020 开源版本（基于 PG），国产化常用。
- 架构：分布式共享存储、一写多读、HTAP。

### 信创背景
国产化替代推进，金融/政企从 Oracle/MySQL 迁移到达梦/人大金仓/GaussDB/OceanBase/TiDB。

### 与 MySQL 差异点（迁移注意）
- SQL 方言、函数、自增主键写法、字符集、连接池驱动不同。
- 部分语法/索引行为差异（PG 系）。

## 延伸

## 延伸

- 关联题：[[databases/mysql/mysql-btree-index]]
