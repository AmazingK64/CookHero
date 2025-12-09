# CookHero: 需求规格与项目规划

```markdown
# CookHero: 需求规格与项目规划

---

## 第一部分：需求规格概述

CookHero 是一个以 RAG（检索增强生成）为核心的智能饮食助手，面向个人与家庭用户，提供菜谱检索、烹饪技巧、推荐与个性化建议。

系统结构与关键组件：

- **数据层**: 多源知识库（菜谱、技巧、通用文本），使用 Milvus 存储向量索引。
- **检索层**: 支持混合检索（稠密向量 + BM25），并行检索多源数据。
- **排序层**: 结果预过滤 + 可插拔 Reranker（SiliconFlow）提升上下文质量。
- **生成层**: 使用 LLM（LangChain 封装）进行查询重写与最终回答生成。

---

## 功能性需求（Functional Requirements）

以下按模块列出当前实现状态与重要说明（✅ 已完成，🚧 进行中，📋 计划中）：

### 1) 数据入库与索引 ✅
- FR-1: ✅ 支持多数据源（recipes, tips, generic_text）并为各自创建独立 Milvus collections。
- FR-2: ✅ 文档采用确定性 UUID（基于路径，UUID v5），保证 child→parent 映射稳定。
- FR-3: ✅ 支持混合索引（稠密向量 + BM25），并通过 `vector_store_factory` 支持 scalar metadata 字段（category/dish_name/difficulty）。
- FR-4: ✅ 新增菜谱索引文档：生成 overall index 与 per-metadata index（category / difficulty / dish_name），用于推荐查询以返回完整名称列表。

### 2) 检索与排序 ✅
- FR-5: ✅ 查询重写（deterministic LLM，temperature=0），改写结果在需要时会被附带原始 query 以便审计/展示。
- FR-6: ✅ 并行检索多数据源；预过滤并按 score 排序以截取 Top-K 进入 rerank 阶段。
- FR-7: ✅ 实现智能排序器参数（dynamic ranker weights），在 `retrieval.ranker_weights` 中可配置默认权重，检索时可根据 query 特征调整。

### 3) 重排序与生成 ✅
- FR-8: ✅ 可插拔 `BaseReranker`，已实现 `SiliconFlowReranker`。r​eranker 可根据配置启用/禁用。
- FR-9: ✅ 生成模块封装在 `GenerationIntegrationModule`，提供 `rewrite_query` 与 `generate_response` 两个能力。

### 4) 缓存与性能 ✅
- FR-10: ✅ 混合缓存（L1 Redis + L2 内存向量缓存）已实现，支持检索结果与响应缓存与可配置 TTL。

### 5) API 与用户交互 ✅
- FR-11: ✅ 提供 `/api/v1/chat` 接口，支持流式与非流式返回。

---

## 非功能性需求（NFR）

- **性能**: 并行检索 + 预过滤使平均检索延迟下降显著；Rerank 输入量缩减支持更低延迟响应。
- **可扩展性**: 抽象化的 DataSource / Reranker / VectorStore 工厂便于接入新模型或数据源。
- **可维护性**: 清晰模块划分、日志记录与 debug 输出（`data/debug`），利于问题排查。
- **可测试性**: 提供 `tests/test_rag.py` 做端到端验证；建议逐步补充单元测试覆盖率。

---

## 项目里程碑（当前状态）

- MVP（RAG 基础管道） — ✅ 完成
- 多源并行检索 & Small-to-Large 模式 — ✅ 完成
- 混合缓存系统与 Reranker 集成 — ✅ 完成
- 推荐索引与推荐查询优化 — ✅ 完成（新增 per-metadata index docs）
- 智能代理 / 多模态 / 个性化推荐 — 🚧 规划中

---

## 开发计划（短期）

第一阶段（1-2 周）
- 检查并扩充单元测试，覆盖 `retrieval.py`、`howtocook_data_source.py`、`rag_service.py`。
- 增加 CI 验证（pytest + lint）。

第二阶段（2-6 周）
- 优化 Milvus schema（scalar 字段索引），评估索引参数对召回/延迟的影响。
- 提升 ingestion 并行速度与增量更新能力。

第三阶段（长期）
- 引入 Correction RAG、智能代理与前端界面。

---

## 技术债务与改进建议

1. 错误处理与降级策略：补充更多可观测的指标与异常处理点。
2. 监控与告警：集成 Prometheus/Grafana、日志采集（ELK）以便生产就绪。
3. 单元测试覆盖率：补充对 ranker、retrieval、index 构建的自动化测试。
4. L2 缓存分布式化：当前 L2 为内存实现，未来考虑迁移到 RedisVector/Milvus 分布式缓存。

---

## 附：关键用户故事（示例）

- 作为一名家庭厨师，我想输入“推荐一些甜品”，系统应返回：
  - 若为推荐类查询，优先返回菜谱索引文档（包含甜品列表）；
  - 同时提供若干具体甜品的做法作为示例。

- 作为一名新手用户，我想问“皮蛋瘦肉粥怎么做？”，系统应返回：
  - 重写查询到更具体检索语句 → 检索最相关子块 → 返回完整父文档并生成步骤化回答。

---

```

