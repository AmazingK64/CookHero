# 构建指南

## 前置要求

### 系统要求
- **操作系统**: macOS, Linux, Windows (推荐使用 WSL2)
- **Python**: 3.8 或更高版本
- **Docker**: 20.10 或更高版本 (用于部署)
- **内存**: 至少 8GB RAM
- **磁盘空间**: 至少 10GB 可用空间

### 依赖版本
- **Milvus**: v2.5.14
- **Redis**: Alpine 最新版
- **MinIO**: RELEASE.2023-03-20T20-16-18Z
- **etcd**: v3.5.16

## 安装步骤

### 1. 克隆仓库
```bash
git clone https://github.com/Decade-qiu/CookHero.git
cd CookHero
```

### 2. 安装 Python 依赖
```bash
# 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量
创建 `.env` 文件并配置必要的 API 密钥:
```bash
# .env 文件内容示例
SILICONFLOW_API_KEY=your_api_key_here
REDIS_PASSWORD=your_redis_password  # 如果需要
```

### 4. 启动基础设施服务
使用 Docker Compose 启动 Milvus, Redis, MinIO, etcd:
```bash
cd deployments
docker-compose up -d
```

等待所有服务启动完成 (大约 2-3 分钟):
```bash
# 检查服务状态
docker-compose ps
```

### 5. 数据摄取
运行数据摄取脚本来构建向量索引:
```bash
cd scripts
python run_ingestion.py
```

此过程可能需要几分钟到几十分钟，取决于数据量。

## 构建与运行

### 开发环境

#### 启动后端服务
```bash
cd app
python main.py
```

服务将在 `http://localhost:8000` 启动。

#### API 文档
访问 `http://localhost:8000/docs` 查看交互式 API 文档。

#### 测试服务
```bash
cd tests
python test_rag.py
```

### 生产环境

#### 使用 Docker Compose 部署
```bash
cd deployments
docker-compose -f docker-compose.prod.yml up -d  # 如果有生产配置文件
```

#### 直接运行
```bash
# 设置生产环境变量
export ENVIRONMENT=production

# 启动服务
python app/main.py
```

### 测试

#### 单元测试
```bash
pytest tests/
```

#### 集成测试
```bash
# 确保所有服务运行
python tests/test_rag.py
```

#### 性能测试
```bash
# 使用工具如 locust 或 artillery 进行负载测试
# 示例: 测试并发查询
ab -n 100 -c 10 http://localhost:8000/api/v1/chat
```

## 故障排除

### 常见问题

#### 1. Milvus 连接失败
**错误**: `Connection to Milvus failed`
**解决方案**:
- 检查 Docker 服务是否运行: `docker-compose ps`
- 确认端口映射: `netstat -tlnp | grep 19530`
- 重启 Milvus 服务: `docker-compose restart milvus`

#### 2. Redis 缓存问题
**错误**: `Redis connection error`
**解决方案**:
- 检查 Redis 服务: `docker-compose logs redis`
- 验证密码配置是否正确
- 确认端口 6379 未被占用

#### 3. 数据摄取失败
**错误**: `Ingestion failed for source X`
**解决方案**:
- 检查数据文件是否存在: `ls -la data/HowToCook/`
- 验证配置文件: `cat config.yml`
- 查看详细日志: `python scripts/run_ingestion.py 2>&1 | tee ingestion.log`

#### 4. API 密钥问题
**错误**: `Authentication failed`
**解决方案**:
- 检查 `.env` 文件中的 API 密钥
- 确认 SiliconFlow API 额度充足
- 验证网络连接到 `api.siliconflow.cn`

#### 5. 内存不足
**错误**: `Out of memory` 或服务崩溃
**解决方案**:
- 增加 Docker 内存限制
- 减少 `config.yml` 中的 `top_k` 值
- 使用更小的 embedding 模型

#### 6. 向量搜索无结果
**问题**: 查询返回空结果
**解决方案**:
- 检查向量索引是否正确构建
- 降低 `score_threshold` 配置
- 验证查询文本质量

### 调试技巧

#### 查看服务日志
```bash
# 基础设施服务日志
docker-compose logs -f

# 应用日志
tail -f app.log
```

#### 检查系统资源
```bash
# CPU 和内存使用
top

# 磁盘空间
df -h

# Docker 资源使用
docker stats
```

#### 重置系统
```bash
# 停止所有服务
docker-compose down

# 清理数据卷 (警告: 会删除所有数据)
docker-compose down -v

# 重新启动
docker-compose up -d
python scripts/run_ingestion.py
```

### 性能优化

- **缓存调优**: 调整 `config.yml` 中的 TTL 值
- **检索参数**: 优化 `top_k` 和 `score_threshold`
- **模型选择**: 使用更快的 embedding 模型
- **并发配置**: 调整 FastAPI worker 数量

### 获取帮助

如果问题持续存在:
1. 查看 GitHub Issues: https://github.com/Decade-qiu/CookHero/issues
2. 检查 README.md 中的详细文档
3. 提供完整的错误日志和系统信息

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
