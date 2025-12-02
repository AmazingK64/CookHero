# CookHero: 需求规格与项目规划

---

### **第一部分：需求规格说明书 (Requirements Specification Document)**

#### **1. 项目概述**

CookHero 是一个面向大众的智能饮食助手系统，提供从厨房准备、菜品学习、营养规划到个性化推荐的全流程支持。系统以 Python 为主要开发语言，使用 LangChain 构建检索增强生成（RAG）能力，采用 Milvus 作为向量数据库，并通过统一的 REST API 对外提供服务。

**核心价值**:

*   **智能化**: 利用 LLM 理解复杂的自然语言查询，并生成高质量的文本。
*   **知识驱动**: 基于 RAG 架构，确保所有回答都源自于可靠、专业的知识库，而非模型凭空想象。
*   **高相关性**: 通过多阶段的检索、过滤和重排（Reranking）机制，最大化上下文与用户查询的相关性。
*   **可扩展性**: 采用模块化和插件式设计，便于未来集成更多知识源和AI模型。

#### **2. 功能性需求 (Functional Requirements)**

**2.1. 数据处理与入库 (Data Ingestion)**

*   **FR-1**: 支持多种异构数据源，已实现菜谱 (`dishes`) 和烹饪技巧 (`tips`)。
*   **FR-2**: 数据源采用可插拔的 `BaseDataSource` 接口设计。
*   **FR-3**: 支持为每个数据源创建独立的 Milvus 集合（Collection）。
*   **FR-4**: 支持为文档生成唯一的、基于文件路径的确定性 ID。
*   **FR-5**: 支持混合索引，同时创建稠密向量和稀疏向量 (BM25)。

**2.2. RAG 核心服务 (`RAGService`)**

*   **FR-6**: 实现基于 LLM 的查询路由（Query Routing），能自动选择查询菜谱库还是技巧库。
*   **FR-7**: 支持查询重写（Query Rewriting），将模糊查询转化为更精确的搜索指令。
*   **FR-8**: 支持混合搜索（Hybrid Search），结合语义与关键词进行检索，并能根据查询意图动态调整权重。
*   **FR-9**: 支持“Small-to-Large”检索模式，检索小块文本，返回完整文档。
*   **FR-10**: 支持可插拔的 `BaseReranker` 重排序模块。
*   **FR-11**: 已实现基于 `SiliconFlow` 专用 API 的高效重排序器。

**2.3. API 接口 (`chat` endpoint)**

*   **FR-12**: 提供统一的 `/chat` API 端点用于接收自然语言查询。
*   **FR-13**: API 支持流式（Streaming）和非流式响应。

**2.4. 智能代理与高级 RAG (未来规划)**

*   **FR-14**: [规划中] 实现一个智能代理（Agent），用于处理多步骤的复杂任务（如“制定一周健身计划并生成购物清单”）。
*   **FR-15**: [规划中] 引入 Correction RAG 流程，包括：
    *   一个用于判断检索内容相关性的“检索评估器”。
    *   一个在检索内容不佳时，触发查询重写和 Web 搜索的“知识搜索”模块。
*   **FR-16**: [规划中] 支持多模态 RAG，能够处理用户上传的图片查询。
*   **FR-17**: [规划中] 引入结构化数据查询能力，能将自然语言转换为 SQL 等查询语言。

#### **3. 非功能性需求 (Non-Functional Requirements)**

*   **NFR-1 (性能)**: 响应延迟应在可接受范围内，流式请求能快速返回首个 token。
*   **NFR-2 (可扩展性)**: 系统通过 `BaseDataSource` 和 `BaseReranker` 等模块的抽象基类设计，支持未来轻松扩展新的数据源和 AI 模型。
*   **NFR-3 (可维护性)**: 所有关键模块都有清晰的日志记录，并提供容器化部署方案。
*   **NFR-4 (可测试性)**: 提供 `tests/test_rag.py` 脚本，用于验证 RAG 管道核心功能的正确性。

-----

### **第二部分：项目计划 (Development Process & Plan)**

**里程碑 1: 核心 RAG 管道搭建 (MVP) - ✅ 已完成**

*   **目标**: 验证核心 RAG 能力，实现基于单一数据源（菜谱）的问答。
*   **核心交付物**:
    *   **`HowToCookDataSource`**: 实现了菜谱数据的加载和处理。
    *   **Milvus 集成**: 能够将文档向量化并存入 Milvus。
    *   **基础 RAG 服务**: `RAGService` 实现基本的“检索-生成”流程。
    *   **FastAPI 接口**: 提供了支持流式响应的 `/chat` 端点。
    *   **确定性 ID**: 解决了因随机 ID 导致的数据映射失败问题。

**里程碑 2: 多源支持与查询路由 - ✅ 已完成**

*   **目标**: 扩展 RAG 管道，使其能够处理多种类型的知识，并能智能区分用户意图。
*   **核心交付物**:
    *   **`BaseDataSource`**: 抽象出数据源基类，提升了可扩展性。
    *   **`TipsDataSource`**: 新增了烹饪技巧数据源。
    *   **多集合支持**: 数据入库脚本和 RAG 服务被重构，能够为不同数据源使用不同的 Milvus 集合。
    *   **查询路由**: 在 `RAGService` 入口处加入了基于 LLM 的查询路由功能，可智能选择知识库。

**里程碑 3: 上下文质量优化 (Reranker) - ✅ 已完成**

*   **目标**: 通过引入重排序步骤，进一步提升提供给 LLM 的上下文质量，减少无关信息的干扰。
*   **核心交付物**:
    *   **`BaseReranker`**: 抽象出重排序器基类。
    *   **`SiliconFlowReranker`**: 实现了基于专用 rerank API 的高效重排序器。
    *   **可配置化**: 在 `config.yml` 中增加了 `reranker` 配置节，可轻松启用/禁用该功能。
    *   **`RAGService` 集成**: 将 reranker 步骤无缝集成到 `ask` 方法的检索流程中。

**里程碑 4: 高级 RAG 与智能化 (🚧 规划中)**

*   **目标**: 引入更强的鲁棒性和自主性，使系统能处理更复杂的任务并从外部获取知识。
*   **核心规划**:
    *   **Correction RAG**: 实现“检索评估器”和“知识搜索”（Web Search）功能，当内部知识不足时，能主动进行网络搜索以补全信息。
    *   **智能代理 (Agent)**: 基于 `LangChain Agents` 构建一个能够分解任务、调用工具（如 RAG、推荐模块）的智能代理，以完成多步骤的复杂指令。
    *   **用户画像模块**: 构建持久化的用户画像系统，用于实现深度个性化推荐和计划制定。
    *   **多模态能力**: 扩展 RAG 管道以支持图像输入，实现“以图搜菜”等功能。

----

### **第三部分：项目结构 (Project Structure)**

项目结构清晰，职责分离，遵循了现代 Python 应用的常用布局。

```
CookHero/
├── app/                  # 项目核心应用代码
│   ├── api/              # FastAPI 的 API 定义
│   ├── core/             # 核心配置 (Pydantic 模型, 全局配置加载)
│   ├── rag/              # RAG 管道的核心实现
│   │   ├── data_sources/ # 数据源 (菜谱, 技巧)
│   │   ├── embeddings/   # Embedding 模型工厂
│   │   ├── rerankers/    # Reranker 实现
│   │   ├── vector_stores/# 向量存储工厂
│   │   ├── generation_integration.py # LLM 生成模块
│   │   ├── rag_service.py            # RAG 核心服务编排
│   │   └── retrieval_optimization.py # 检索与排序优化
│   └── main.py           # FastAPI 应用启动入口
├── data/                 # 项目数据
│   └── HowToCook/        # Git Submodule, 存放原始知识库
├── deployments/          # 部署相关文件 (docker-compose.yml)
├── docs/                 # 项目文档
│   ├── build.md
│   ├── requirement.md
│   └── technology.md
├── scripts/              # 辅助脚本 (数据同步, 数据入库等)
├── tests/                # 测试代码
│   └── test_rag.py
├── .env                  # (本地) 环境变量文件, 存储密钥
├── config.yml            # 主配置文件
└── requirements.txt      # (建议) Python 依赖
```