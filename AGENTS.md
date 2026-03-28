# 项目上下文

## 项目背景

这是一个聚合多 OJ 提交信息，支持从多个 OJ 平台获取题目与提交信息的平台。用户可以注册账号，绑定多个 OJ 平台（VJ、SDUT等），查看题目和提交记录。

## 实体

- **sources**: 第三方 OJ 平台，如 VJ、SDUTACM、POJ 等
- **user**: 用户在本平台的账号，可以绑定多个 OJ 账号
  - 普通用户: 可以绑定账号、查看已参与的计划等
  - 组织管理员: 可以管理计划、为计划导入用户等
  - 超级管理员: 可以管理组织、为其他用户设置权限等
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
- **数据库**: SQLAlchemy (SQLite)
- **认证**: JWT (python-jose + bcrypt)
- **HTTP客户端**: httpx

## 目录约定

```plain
apps/
├── api/           # FastAPI 后端项目
│   ├── app/
│   │   ├── core/          # 核心配置 (config, security)
│   │   ├── routers/       # API 路由 (auth, source)
│   │   └── main.py        # 应用入口
│   ├── db/
│   │   ├── models/        # SQLAlchemy 模型
│   │   ├── base.py        # 声明基类
│   │   └── session.py     # 数据库会话
│   ├── schemas/           # Pydantic schemas
│   └── sources/           # OJ 平台适配器 (vj, sdut)
└── web/           # Vue 前端项目 (待开发)
```

## 数据库模型

| 模型 | 表名 | 说明 |
| ------ | ------ | ------ |
| User | users | 用户账号 |
| SourceUser | source_users | 用户与平台的绑定关系 |
| Problem | problems | OJ 题目 |
| Solution | solutions | 提交记录 |

## API 路由

| 前缀 | 路由 | 说明 |
| ------ | ------ | ------ |
| /api/auth | POST /register | 用户注册 |
| /api/auth | POST /login | 用户登录 |
| /api/auth | GET /me | 获取当前用户信息 |
| /api/auth | PATCH /me | 更新当前用户信息 |
| /api/sources | GET / | 列出所有支持的平台 |
| /api/sources | POST /bind | 绑定平台账号 |
| /api/sources | DELETE /unbind/{source} | 解绑平台账号 |
| /api/sources | GET /bindings | 获取已绑定的平台列表 |

## 已实现的 OJ 平台

### VJ (Virtual Judge)

- **source**: `vj`
- **登录**: POST <https://vjudge.net/user/login>
- **题目URL**: <https://vjudge.net/problem/{pid}>
- **用户URL**: <https://vjudge.net/user/{username}>

### SDUT (SDUT Online Judge)

- **source**: `sdut`
- **登录**: POST <https://oj.sdutacm.cn/onlinejudge3/api/login>
- **题目URL**: <https://oj.sdutacm.cn/onlinejudde3/problems/{pid}>
- **用户URL**: <https://oj.sdutacm.cn/onlinejudge3/users/{username}>

## 枚举值

### ResultEnum (评测结果)

- Accepted = 1
- WrongAnswer = 2
- TimeLimitExceeded = 3
- MemoryLimitExceeded = 4
- RuntimeError = 5
- OutputLimitExceeded = 6
- CompileError = 7
- PresentationError = 8
- SystemError = 9
- Unknown = 999

### LanguageEnum (编程语言)

- C = 1
- Cpp = 2
- Python = 3
- Java = 4
- Go = 5
- Rust = 6
- JavaScript = 7
- TypeScript = 8
- CSharp = 9
- Pascal = 10
- Fortran = 11
- Unknown = 999

## 环境变量

配置项位于 `apps/api/.env`：

| 变量 | 默认值 | 说明 |
| ------ | -------- | ------ |
| SECRET_KEY | your-secret-key-change-in-production | JWT 密钥 |
| ALGORITHM | HS256 | JWT 算法 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 525600 (1年) | Token 过期时间 |
| DATABASE_URL | sqlite:///./step_by_step.db | 数据库连接 |

## 核心规则

- 禁止使用 `any` 类型
- 密码使用 bcrypt 哈希存储
- 平台适配器位于 `sources/` 目录，需实现 `login`、`problems`、`solutions` 静态方法
- 代码修改后使用工具进行规范格式化 `cd apps/api && uv run ruff check --select I --fix && uv run ruff format`

## 开发命令

```bash
# 安装依赖
uv sync

# 运行后端
uv run uvicorn apps.api.app.main:app --reload --dir apps/api

# 或直接运行
cd apps/api && uvicorn app.main:app --reload
```
