# 项目上下文

## 项目背景

这是一个聚合多 OJ 提交信息，支持从多个 OJ 平台获取题目与提交信息。

## 实体

- **sources**: 第三方 OJ 平台，比如 VJ、SDUTACM、POJ 等
- **user**: 用户在本平台的账号，可以绑定多个 OJ 账号
- **source_user**: 用户本平台账号与第三方 OJ 账号的绑定关系
- **problem**: 第三方 OJ 平台的题目
- **solution**: 第三方 OJ 平台的提交记录
- **step**: 由多个平台的题目聚合而成的训练计划
- **group**: 本平台的组织，一个组织可以包含多个训练计划

## 技术栈

### 前端

- **框架**: Vue3
- **语言**: TypeScript
- **样式**: ElementPlus
- **状态管理**: Pinia

### 后端

- **框架**: FastAPI
- **语言**: Python
- **数据库**: SQLAlchemy
- **Schemas**: Pydantic

## 核心规则

- 禁止使用 `any` 类型

## 目录约定

- `apps/api` - FastAPI 后端项目
- `apps/web` - Vue 前端项目
