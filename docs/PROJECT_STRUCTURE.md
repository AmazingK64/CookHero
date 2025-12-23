# CookHero 项目结构详解

本文档详细说明 CookHero 项目的目录结构和各模块职责。

---

## 一、项目根目录

```
CookHero/
├── app/                    # 后端应用主目录
├── frontend/               # 前端应用
├── scripts/                # 工具脚本
├── tests/                  # 测试文件
├── data/                   # 数据目录
├── deployments/            # 部署配置
├── docs/                   # 项目文档
├── config.yml              # 主配置文件
├── .env.example            # 环境变量模板
├── requirements.txt        # Python 依赖
├── README_ZH.md           # 中文说明文档
└── .gitignore             # Git 忽略规则
```

---

## 二、后端应用 (`app/`)

### 2.1 API 层 (`app/api/`)

```
api/
└── v1/
    └── endpoints/
        ├── auth.py           # 用户认证接口（注册、登录、令牌刷新）
        ├── conversation.py   # 对话接口（创建、查询、流式响应）
        ├── personal_docs.py  # 个人文档接口（上传、删除、列表）
        └── user.py          # 用户信息接口（获取、更新）
```

**职责**：
- 定义 RESTful API 端点
- 请求验证（Pydantic 模型）
- 调用服务层处理业务逻辑
- 返回标准化响应

---

### 2.2 配置模块 (`app/config/`)

```
config/
├── config_loader.py      # 配置加载器（从 config.yml 和 .env 加载）
├── config.py             # 全局配置类
├── database_config.py    # 数据库配置（PostgreSQL, Redis, Milvus）
├── llm_config.py         # LLM 提供商配置（fast/normal 两层）
├── rag_config.py         # RAG 管道配置（检索参数、重排序）
└── web_search_config.py  # Web 搜索配置（Tavily）
```

**职责**：
- 统一管理项目配置
- 环境变量注入
- 配置验证和默认值处理

---

### 2.3 对话管理 (`app/conversation/`)

```
conversation/
├── intent.py             # 意图识别（查询、推荐、闲聊等）
├── query_rewriter.py     # 查询改写（优化用户输入）
├── llm_orchestrator.py   # LLM 编排（多模型选择、调用）
└── repository.py         # 对话数据访问（数据库 CRUD）
```

**职责**：
- 理解用户意图
- 优化查询语句
- 管理对话历史
- 持久化会话数据

---

### 2.4 上下文管理 (`app/context/`)

```
context/
├── manager.py            # 上下文管理器（构建检索上下文）
└── compress.py           # 上下文压缩（提取关键片段）
```

**职责**：
- 管理对话上下文窗口
- 压缩长文本以节省 token
- 提取最相关的检索结果

---

### 2.5 数据库层 (`app/database/`)

```
database/
├── models.py             # ORM 模型（User, Conversation, Message 等）
├── session.py            # 数据库会话管理（连接池、事务）
└── document_repository.py # 文档仓库（元数据缓存、CRUD）
```

**职责**：
- 定义数据表结构
- 管理数据库连接
- 提供数据访问接口

---

### 2.6 LLM 提供商 (`app/llm/`)

```
llm/
└── provider.py           # 多 LLM 提供商适配器
```

**职责**：
- 统一 LLM 调用接口
- 支持多模型切换（OpenAI, Anthropic, 自定义 API）
- 错误处理和重试机制

---

### 2.7 RAG 核心模块 (`app/rag/`)

#### 2.7.1 缓存系统 (`app/rag/cache/`)

```
cache/
├── base.py               # 缓存基类
├── backends.py           # Redis 和 Milvus 缓存后端实现
└── cache_manager.py      # 缓存管理器（L1+L2 双层缓存）
```

**职责**：
- L1 缓存（Redis）：精确匹配查询
- L2 缓存（Milvus）：语义相似查询
- 缓存失效和更新策略

#### 2.7.2 嵌入模型 (`app/rag/embeddings/`)

```
embeddings/
└── embedding_factory.py  # 嵌入模型工厂（HuggingFace, OpenAI）
```

**职责**：
- 加载和管理嵌入模型
- 文本向量化

#### 2.7.3 检索管道 (`app/rag/pipeline/`)

```
pipeline/
├── retrieval.py          # 检索模块（向量检索、BM25、混合检索）
├── generation.py         # 生成模块（LLM 答案生成）
├── metadata_filter.py    # 元数据过滤（烹饪时间、难度等）
└── document_processor.py # 文档处理（分块、解析、索引）
```

**职责**：
- 实现 RAG 全流程
- 多种检索策略融合
- 生成最终答案

#### 2.7.4 重排序器 (`app/rag/rerankers/`)

```
rerankers/
├── base.py               # 重排序器基类
└── siliconflow_reranker.py # SiliconFlow Reranker 实现
```

**职责**：
- 对初步检索结果进行精排
- 提高结果相关性

#### 2.7.5 向量存储 (`app/rag/vector_stores/`)

```
vector_stores/
└── vector_store_factory.py # 向量存储工厂（Milvus 集合管理）
```

**职责**：
- 初始化向量数据库
- 管理多个集合（全局食谱、个人食谱）
- 向量 CRUD 操作

---

### 2.8 业务服务层 (`app/services/`)

```
services/
├── auth_service.py           # 认证服务（注册、登录、JWT）
├── conversation_service.py   # 对话服务（会话管理、消息处理）
├── rag_service.py            # RAG 服务（检索、生成）
├── personal_document_service.py # 个人文档服务（上传、索引）
└── user_service.py           # 用户服务（用户信息管理）
```

**职责**：
- 实现核心业务逻辑
- 协调多个模块协同工作
- 事务管理和错误处理

---

### 2.9 工具集 (`app/tools/`)

```
tools/
└── web_search.py         # Web 搜索工具（Tavily 集成）
```

**职责**：
- 提供外部工具调用接口
- 扩展 RAG 系统能力

---

### 2.10 工具函数 (`app/utils/`)

```
utils/
└── structured_json.py    # JSON 解析和验证工具
```

**职责**：
- 通用工具函数
- 数据格式化和验证

---

### 2.11 应用入口 (`app/main.py`)

**职责**：
- FastAPI 应用初始化
- 中间件配置（CORS、异常处理）
- 路由注册
- 生命周期管理（数据库初始化、缓存清理）

---

## 三、前端应用 (`frontend/`)

```
frontend/
├── src/
│   ├── components/       # React 组件
│   │   ├── ChatMessage.tsx       # 聊天消息组件
│   │   ├── ChatInput.tsx         # 输入框组件
│   │   ├── ConversationList.tsx  # 会话列表
│   │   ├── Header.tsx            # 页面头部
│   │   └── ...
│   ├── pages/            # 页面组件
│   │   ├── Chat.tsx              # 聊天页面
│   │   ├── Login.tsx             # 登录页面
│   │   ├── Register.tsx          # 注册页面
│   │   └── Profile.tsx           # 个人中心
│   ├── services/         # API 服务
│   │   ├── api.ts                # Axios 实例配置
│   │   ├── authService.ts        # 认证 API
│   │   └── conversationService.ts# 对话 API
│   ├── contexts/         # React Context
│   │   └── AuthContext.tsx       # 认证状态管理
│   ├── hooks/            # 自定义 Hooks
│   │   └── useAuth.tsx           # 认证 Hook
│   ├── types/            # TypeScript 类型定义
│   │   └── index.ts
│   ├── utils/            # 工具函数
│   ├── App.tsx           # 应用根组件
│   ├── main.tsx          # 应用入口
│   └── index.css         # 全局样式
├── public/               # 静态资源
│   ├── favicon.ico       # 网站图标
│   └── logo.svg          # Logo 文件
├── package.json          # 依赖配置
├── tsconfig.json         # TypeScript 配置
├── vite.config.ts        # Vite 配置
└── tailwind.config.ts    # TailwindCSS 配置
```

**技术栈**：
- React 19 + TypeScript
- Vite（构建工具）
- TailwindCSS（样式）
- React Router（路由）
- Axios（HTTP 客户端）

---

## 四、工具脚本 (`scripts/`)

```
scripts/
├── howtocook_loader.py   # HowToCook 数据加载器
├── run_ingestion.py      # 数据摄取主脚本
├── sync_data.py          # 数据同步工具
└── list_categories.py    # 列出菜谱分类
```

**职责**：
- 数据预处理
- 向量化和索引
- 数据库初始化

---

## 五、测试 (`tests/`)

```
tests/
├── test_rag.py           # RAG 系统测试
├── test_llm_api.py       # LLM API 调用测试
├── test_deep_agent.py    # Agent 功能测试
└── test_user_personalization.py # 用户个性化测试
```

**职责**：
- 单元测试
- 集成测试
- 端到端测试

---

## 六、数据目录 (`data/`)

```
data/
├── HowToCook/            # HowToCook 食谱库（Git Submodule）
│   ├── dishes/           # 菜谱 Markdown 文件
│   ├── tips/             # 烹饪技巧
│   └── README.md
└── debug/                # 调试数据（可选）
    ├── child_chunks.jsonl
    └── parent_documents.jsonl
```

---

## 七、部署配置 (`deployments/`)

```
deployments/
├── docker-compose.yml    # Docker Compose 编排文件
├── init-scripts/         # 数据库初始化脚本
│   └── init.sql
└── volumes/              # 持久化数据卷
    ├── postgres/
    ├── redis/
    ├── milvus/
    ├── minio/
    └── etcd/
```

**职责**：
- 一键启动基础设施
- 数据持久化
- 服务编排

---

## 八、文档目录 (`docs/`)

```
docs/
├── LOGO_DESIGN.md        # Logo 设计方案
├── ARCHITECTURE.md       # 架构设计文档（待添加）
└── API.md                # API 文档（待添加）
```

---

## 九、配置文件

### 9.1 `config.yml`
主配置文件，包含：
- LLM 提供商配置
- 数据库连接信息
- RAG 管道参数
- 缓存策略

### 9.2 `.env`
环境变量文件（不提交到 Git），包含：
- API Keys
- 数据库密码
- JWT 密钥

### 9.3 `requirements.txt`
Python 依赖列表，包含所有后端依赖的精确版本号。

---

## 十、数据流示例

### 用户查询流程

1. **用户输入**：前端发送查询请求到 `/api/v1/conversation/query`
2. **API 层**：`conversation.py` 接收请求，验证身份
3. **服务层**：`conversation_service.py` 处理业务逻辑
4. **意图识别**：`intent.py` 判断查询类型
5. **查询改写**：`query_rewriter.py` 优化查询
6. **缓存查询**：`cache_manager.py` 检查 Redis/Milvus 缓存
7. **检索**：`retrieval.py` 执行混合检索
8. **重排序**：`siliconflow_reranker.py` 精排结果
9. **生成答案**：`generation.py` 调用 LLM 生成回复
10. **返回结果**：流式或完整返回给前端

---

## 十一、扩展指南

### 添加新数据源
1. 在 `scripts/` 下创建新的数据加载器
2. 实现数据解析和向量化逻辑
3. 在 `config.yml` 中添加数据源配置

### 添加新检索策略
1. 在 `app/rag/pipeline/retrieval.py` 中实现新策略
2. 在 `config.yml` 中配置策略参数
3. 在 `rag_service.py` 中集成新策略

### 添加新 Reranker
1. 在 `app/rag/rerankers/` 下创建新文件
2. 继承 `BaseReranker` 基类
3. 在 `rag_service.py` 中注册新 Reranker

---

**此文档将随项目发展持续更新。**
