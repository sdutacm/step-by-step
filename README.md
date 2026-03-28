# Step By Step

## 项目结构

```plain
step-by-step/
├── apps/
│   ├── web/                    # Vue 3 前端
│   │   ├── src/
│   │   ├── public/
│   │   ├── package.json        # 仅前端依赖
│   │   ├── vite.config.ts
│   │   └── tsconfig.json
│   │
│   └── api/                    # FastAPI 后端
│       ├── app/
│       │   ├── main.py
│       │   ├── dependencies/   # 依赖注入（DB 会话等）
│       │   ├── routers/        # API 路由
│       │   ├── services/       # 业务逻辑层
│       │   └── core/           # 配置、安全等
│       │
│       ├── db/                 # 数据库层（独立）
│       │   ├── models/         # SQLAlchemy ORM 模型
│       │   │   ├── user.py
│       │   │   └── __init__.py
│       │   ├── session.py      # 数据库会话管理
│       │   └── base.py         # ORM 基类
│       │
│       └── schemas/            # Pydantic 模型（API 层）
│           ├── user.py
│           └── __init__.py
│
├── requirements.txt
└── README.md
```
