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

```markdown
# CookHero 构建与开发指南

本文档为开发者提供清晰的指南，说明如何配置开发环境、构建和运行 CookHero 项目。

---

## 1. 环境与配置

### 1.1. 环境准备 (Prerequisites)

在本项目中建议使用以下环境：

- **Python**: 3.9 或更高（推荐 3.11+）。通过 `python --version` 确认。
- **Docker** 与 **Docker Compose**: 用于本地启动 Milvus、Redis、MinIO 等依赖。
- **Git**: 管理仓库和同步知识库数据。

可选但推荐：`poetry` 或 `pip-tools` 用于依赖管理与可重复构建。

### 1.2. 配置文件说明

主要配置集中在 `config.yml`，敏感凭证放在 `.env`：

- `config.yml`: 控制模型、向量存储、检索参数、缓存等关键配置。
- `.env`: 存放 LLM/API keys、Redis 密码等敏感信息。

示例 `.env`：
```dotenv
LLM_API_KEY="your-llm-api-key"
REDIS_PASSWORD="your-redis-password"
```

`app/core/config_loader.py` 会读取 `config.yml` 并注入 `.env` 中的密钥。

---

## 2. 快速开始（本地开发）

下面给出一组可复制的步骤，帮助你在本地构建并验证系统。

### 2.1. 启动依赖服务（Docker Compose）

项目在 `deployments/docker-compose.yml` 提供一键启动依赖服务：

```bash
cd deployments
docker-compose up -d
```

将启动（视 compose 文件而定）：
- Milvus（向量服务，默认 19530）
- Redis（缓存，默认 6379）
- etcd / MinIO（Milvus 依赖）

检查服务：
```bash
docker ps | grep milvus
curl http://localhost:9091/healthz
redis-cli -h localhost -p 6379 ping
# 返回 PONG
```

### 2.2. 同步知识库数据（仅首次或更新时）

项目的数据仓库位于 `data/HowToCook`（作为子模块或同步脚本管理）。执行：

```bash
python ./scripts/sync_data.py
```

这会把外部知识库克隆/同步到 `data/HowToCook` 下。

### 2.3. 安装依赖

推荐使用虚拟环境（venv / conda / poetry）：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

若遇到 GPU/本地模型需求，请参考 `requirements.txt` 中的注释或 README 指示安装相应依赖。

### 2.4. 数据入库（Ingestion）

构建并重建 Milvus 集合的脚本位于 `scripts/run_ingestion.py`。首次入库或需要重建索引时运行：

```bash
PYTHONPATH=. python scripts/run_ingestion.py --rebuild
```

脚本将：
- 读取 `data/HowToCook`、`data/tips`、`data/generic_text` 等目录
- 生成 parent documents 与 child chunks（支持 markdown header 拆分、句子窗口）
- 创建/重建 Milvus collections：
  - `cook_hero_recipes`
  - `cook_hero_tips`
  - `cook_hero_generic_text`
- 为 recipes 创建菜谱索引文档（overall + per-metadata），并为其生成推荐关键词 chunk

入库完成后，可在 `data/debug/{parent_documents.jsonl,child_chunks.jsonl}` 查看生成的文档样式用于调试。

### 2.5. 启动应用

启动 FastAPI 服务：

```bash
PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问：
- Swagger UI: `http://localhost:8000/docs`
- Chat API: `POST /api/v1/chat`

---

## 3. 测试

项目提供基础的集成式测试脚本以快速验证 RAG 流水线：

```bash
PYTHONPATH=. python tests/test_rag.py
```

该脚本会跑通查询重写、并行检索、后处理、重排序和生成等环节并打印日志，便于调试。

如需用 `pytest` 运行全部测试（当更多单测加入时）：

```bash
pytest -q
```

---

## 4. 关键配置说明（摘要）

- `retrieval.top_k`: 每个数据源检索文档数量（默认 5）。推荐类查询会扩大检索规模以增加多样性。
- `retrieval.ranker_weights`: 混合搜索权重 `[dense, bm25]`（示例: `[0.4,0.6]`）
- `reranker.enabled`: 是否启用 reranker（推荐用于生产环境以保证上下文质量）
- `cache.enabled`: 是否启用缓存（Redis）。当启用时会显著加速响应。

建议在本地先把 `top_k` 设置为较小值（例如 3-5），在 Milvus 索引稳定后再调高以评估召回效果。

---

## 5. 常见故障及排查要点

- Milvus 连接失败：检查 `docker ps`、端口占用、容器日志；如有需要，重建集合并观察 ingestion 日志。
- 数据入库异常：确认 `data/HowToCook` 结构与脚本期望一致，并检查 `parent_documents.jsonl` 的内容。
- 检索召回太少：检查 `retrieval.ranker_weights` 与 `top_k`，并确认 embeddings 是否正确生成。

---

## 6. 生产注意事项（简要）

- 使用 Gunicorn + Uvicorn workers 提升并发；使用 Nginx 做反向代理与 TLS 终端。
- 在生产环境中建议开启 `cache.enabled` 并配置专用 Redis 实例与定期备份策略。
- 定期重建 Milvus 索引或做增量更新策略以保证检索质量。

---

## 7. 下一步建议

- 运行 `python scripts/run_ingestion.py --rebuild` 完整构建索引并验证推荐类查询（示例查询："推荐一些甜品"）。
- 若需要我执行自动化测试或生成示例请求结果，请回复我运行 `tests/test_rag.py`。

```
```dotenv
