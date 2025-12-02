# CookHero 构建与开发指南

本文档为开发者提供清晰的指南，说明如何配置开发环境、构建和运行 CookHero 项目。

---

## 1. 环境与配置

### 1.1. 环境准备 (Prerequisites)

在开始之前，请确保您的开发环境中已安装以下工具：

- **Python**: 版本 `3.9` 或更高。请通过 `python --version` 或 `python3 --version` 命令确认。
- **Docker** 与 **Docker Compose**: 用于快速启动 Milvus 向量数据库等依赖服务。
- **Git**: 用于版本控制和克隆项目知识库数据。

### 1.2. 配置文件说明

CookHero 采用 **`config.yml`** 作为唯一的中心配置文件，并结合 **`.env`** 文件来管理敏感凭证。

- **`config.yml`**: 包含了所有应用程序的配置项，如模型名称、检索参数、数据源路径等。你可以直接修改此文件来调整系统行为。

- **`.env` 文件**: 用于存储敏感数据，主要是第三方服务的 API 密钥。在项目根目录下创建一个 `.env` 文件，并至少填入以下内容：
    ```dotenv
    LLM_API_KEY="your-llm-api-key"
    # 如果 Embedding 模型或 Reranker 模型使用独立的 key，也在此处添加
    # EMBEDDING_API_KEY="your-embedding-api-key"
    # RERANKER_API_KEY="your-reranker-api-key"
    ```
    `config_loader.py` 会在程序启动时自动加载此文件，并将密钥安全地注入到配置中。

**重要提示**: `.env` 文件已被添加到 `.gitignore` 中，请勿将其提交到版本控制系统。

---

## 2. 快速开始 (本地开发)

### 2.1. 启动依赖服务

项目依赖 Milvus 向量数据库。我们提供了一个 `docker-compose.yml` 文件用于快速启动所有必要的后端服务。

在 `deployments/` 目录下，运行：
```sh
docker-compose up -d
```
此命令会以后台模式启动 Milvus 数据库及其所有依赖项。

### 2.2. 同步知识库数据

项目所需的菜谱和技巧知识库存储在一个独立的 Git 仓库中。首次运行时，你需要同步该数据。

在项目根目录下，执行以下脚本：
```sh
python ./scripts/sync_data.py
```
此脚本会将 `data/HowToCook` 仓库克隆到本地，为后续的数据入库做准备。

### 2.3. 安装 Python 依赖

1. **创建并激活虚拟环境** (推荐):
   ```sh
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
   ```

2. **安装依赖包**:
   ```sh
   pip install -r requirements.txt
   ```
   *如果 `requirements.txt` 不存在或不完整, 你可能需要手动安装核心依赖:*
   ```sh
   pip install fastapi "uvicorn[standard]" pydantic PyYAML python-dotenv langchain langchain-openai langchain-milvus sentence-transformers httpx scikit-learn
   ```

### 2.4. 数据入库 (Ingestion)

在首次运行或知识库更新后，你需要运行数据入库脚本，将菜谱和技巧文档处理并存入 Milvus 数据库。

**重要**: 确保你的 Python 虚拟环境已激活，并且 `PYTHONPATH` 设置正确。
```sh
PYTHONPATH=. ./.venv/bin/python scripts/run_ingestion.py
```
此脚本会连接到 Docker 中运行的 Milvus 服务，清空并重建 `cook_hero_recipes` 和 `cook_hero_tips` 两个集合，然后将所有文档的向量化表示存入其中。

### 2.5. 运行应用

完成数据入库后，启动 FastAPI 后端服务：
```sh
PYTHONPATH=. ./.venv/bin/uvicorn app.main:app --reload
```
服务启动后，你可以通过 `http://localhost:8000/docs` 访问自动生成的 Swagger UI 接口文档，并进行在线调试。

---

## 3. 核心功能测试

项目在 `tests/` 目录下提供了一个测试脚本，用于快速验证 RAG 管道的核心功能是否正常工作。

**运行测试**:
```sh
PYTHONPATH=. ./.venv/bin/python tests/test_rag.py
```
此脚本会模拟用户提问，并打印出 RAG 服务从路由、检索、重排到最终生成答案的全过程日志，是调试和验证系统行为的重要工具。