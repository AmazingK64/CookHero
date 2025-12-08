# CookHero 开发任务清单

本文档列出了 CookHero 项目接下来可以进行的开发任务，按照优先级和可行性进行分类。

---

## 🚀 高优先级任务（技术债务与基础优化）

### 任务 1: 实现查询结果缓存 ⚡
**优先级**: 🔴 高  
**难度**: ⭐⭐ 中等  
**预计时间**: 2-3 天  
**收益**: 显著提升响应速度，减少 API 调用成本

**任务描述**:
- 集成 Redis 作为缓存层
- 实现查询结果缓存（基于查询文本的 hash）
- 实现检索结果缓存（基于查询 + 数据源）
- 支持缓存过期和失效策略

**技术要点**:
- 使用 `redis-py` 或 `aioredis` 连接 Redis
- 缓存 key 设计：`rag:query:{hash}` 和 `rag:retrieval:{source}:{hash}`
- TTL 设置：查询结果 1 小时，检索结果 30 分钟
- 缓存预热：常见查询预加载

**相关文件**:
- `app/rag/rag_service.py` - 添加缓存层
- `app/core/config.py` - 添加 Redis 配置
- `config.yml` - 添加缓存配置项
- `deployments/docker-compose.yml` - 添加 Redis 服务

---

### 任务 2: 完善错误处理与降级机制 🛡️
**优先级**: 🔴 高  
**难度**: ⭐⭐ 中等  
**预计时间**: 2 天  
**收益**: 提升系统稳定性和用户体验

**任务描述**:
- 实现分层错误处理（API层、RAG层、检索层）
- 添加降级策略（rerank失败→跳过rerank，LLM失败→返回检索结果）
- 实现重试机制（带指数退避）
- 添加错误类型分类和友好错误消息

**技术要点**:
- 自定义异常类：`RAGError`, `RetrievalError`, `GenerationError`
- 降级策略：rerank失败时返回原始排序结果
- 重试机制：使用 `tenacity` 库实现重试
- 错误监控：记录错误统计和告警

**相关文件**:
- `app/rag/exceptions.py` - 新建异常类
- `app/rag/rag_service.py` - 添加错误处理和降级
- `app/api/v1/endpoints/chat.py` - 改进错误响应

---

### 任务 3: 增加单元测试覆盖 ✅
**优先级**: 🟡 中高  
**难度**: ⭐⭐ 中等  
**预计时间**: 3-4 天  
**收益**: 提升代码质量和可维护性

**任务描述**:
- 为核心模块添加单元测试
- 使用 pytest 和 mock 进行测试
- 目标覆盖率：核心模块 > 80%

**测试范围**:
- `RAGService` - 测试查询流程、并行检索、后处理
- `RetrievalOptimizationModule` - 测试混合搜索、智能排序器
- `GenerationIntegrationModule` - 测试查询重写、响应生成
- `HowToCookDataSource` - 测试数据加载、索引文档创建
- `SiliconFlowReranker` - 测试重排序逻辑

**相关文件**:
- `tests/test_rag_service.py` - 新建
- `tests/test_retrieval.py` - 新建
- `tests/test_generation.py` - 新建
- `tests/test_data_sources.py` - 新建
- `pytest.ini` - 配置文件

---

### 任务 4: 添加健康检查和监控端点 📊
**优先级**: 🟡 中高  
**难度**: ⭐ 简单  
**预计时间**: 1 天  
**收益**: 便于运维和问题诊断

**任务描述**:
- 添加 `/health` 端点检查服务状态
- 添加 `/metrics` 端点（Prometheus 格式）
- 添加 `/status` 端点显示系统信息
- 记录关键指标（查询数、响应时间、错误率）

**技术要点**:
- 使用 `prometheus-client` 记录指标
- 健康检查：Milvus 连接、LLM API 可用性
- 指标：请求数、延迟、错误率、缓存命中率

**相关文件**:
- `app/api/v1/endpoints/health.py` - 新建
- `app/core/metrics.py` - 新建
- `app/main.py` - 注册新路由

---

## 🎯 中优先级任务（功能增强）

### 任务 5: 实现智能代理（Agent）系统 🤖
**优先级**: 🟡 中  
**难度**: ⭐⭐⭐ 较难  
**预计时间**: 5-7 天  
**收益**: 支持复杂多步骤任务

**任务描述**:
- 基于 LangChain Agents 构建智能代理
- 实现任务分解和工具调用
- 支持多步骤任务（如"制定一周饮食计划并生成购物清单"）

**核心功能**:
- 任务解析：识别复杂任务并分解为子任务
- 工具调用：RAG查询、推荐生成、数据计算
- 结果整合：合并多个工具的输出
- 自我纠错：任务失败时重试或调整策略

**技术要点**:
- 使用 `langchain.agents` 构建 Agent
- 定义工具：`rag_query_tool`, `recommendation_tool`, `plan_generator_tool`
- Agent 类型：ReAct Agent 或 Plan-and-Execute Agent

**相关文件**:
- `app/rag/agents/` - 新建目录
- `app/rag/agents/base_agent.py` - Agent 基类
- `app/rag/agents/cookhero_agent.py` - 主 Agent 实现
- `app/rag/agents/tools.py` - 工具定义
- `app/api/v1/endpoints/agent.py` - Agent API 端点

---

### 任务 6: 实现基础推荐系统 📋
**优先级**: 🟡 中  
**难度**: ⭐⭐⭐ 较难  
**预计时间**: 4-6 天  
**收益**: 提供个性化推荐能力

**任务描述**:
- 实现基于规则的推荐（营养目标、忌口过滤）
- 实现基于相似度的推荐（菜品 embedding 相似度）
- 实现简单的饮食计划生成

**核心功能**:
- 用户偏好管理（显式设置 + 隐式学习）
- 菜品过滤（过敏、忌口、营养目标）
- 相似度计算（基于菜品 embedding）
- 计划生成（每日/每周饮食计划）

**技术要点**:
- 使用菜品 embedding 计算相似度
- 规则引擎：Pydantic 模型定义规则
- 计划生成：基于营养目标和用户偏好

**相关文件**:
- `app/services/recommendation/` - 新建目录
- `app/services/recommendation/recommender.py` - 推荐器
- `app/services/recommendation/planner.py` - 计划生成器
- `app/api/v1/endpoints/recommendation.py` - 推荐 API

---

### 任务 7: 实现多模态 RAG（图像输入）🖼️
**优先级**: 🟢 中低  
**难度**: ⭐⭐⭐⭐ 困难  
**预计时间**: 7-10 天  
**收益**: 支持"以图搜菜"功能

**任务描述**:
- 集成多模态 embedding 模型（如 CLIP）
- 支持图像上传和向量化
- 实现图像-文本跨模态检索
- 支持"这是什么食材"、"能做什么菜"等查询

**技术要点**:
- 使用 `transformers` 加载多模态模型
- 图像预处理和向量化
- Milvus 支持多模态向量存储
- API 支持 multipart/form-data 上传

**相关文件**:
- `app/rag/embeddings/multimodal_embedding.py` - 新建
- `app/rag/data_sources/image_data_source.py` - 新建
- `app/api/v1/endpoints/image.py` - 新建

---

## 🔮 低优先级任务（长期规划）

### 任务 8: 实现 Correction RAG 🔍
**优先级**: 🟢 低  
**难度**: ⭐⭐⭐⭐ 困难  
**预计时间**: 10-14 天  
**收益**: 提升系统鲁棒性，处理知识不足的情况

**任务描述**:
- 实现检索评估器（判断检索结果相关性）
- 实现知识搜索模块（Web Search）
- 实现查询重写和外部知识补全

**核心功能**:
- 检索评估：LLM 判断文档相关性（Correct/Incorrect/Ambiguous）
- 知识搜索：当检索不足时触发 Web 搜索
- 知识精炼：结合多个相关文档生成答案

---

### 任务 9: 实现用户画像系统 👤
**优先级**: 🟢 低  
**难度**: ⭐⭐⭐ 较难  
**预计时间**: 5-7 天  
**收益**: 支持深度个性化推荐

**任务描述**:
- 设计用户画像数据模型
- 实现用户偏好学习（显式 + 隐式）
- 实现画像持久化存储
- 集成到推荐系统

**技术要点**:
- 使用 SQLite 或 PostgreSQL 存储用户数据
- 特征向量：口味偏好、营养目标、历史行为
- 增量学习：基于用户交互更新画像

---

### 任务 10: 开发前端界面 🎨
**优先级**: 🟢 低  
**难度**: ⭐⭐⭐⭐ 困难  
**预计时间**: 14-21 天  
**收益**: 提供用户友好的交互界面

**任务描述**:
- 使用 React + TypeScript 开发前端
- 实现对话界面、菜谱浏览、推荐界面
- 实现用户管理功能

---

## 📋 推荐开发顺序

### 第一阶段（1-2周）：技术债务清理
1. ✅ 任务 4: 健康检查和监控端点（1天）
2. ✅ 任务 2: 错误处理与降级机制（2天）
3. ✅ 任务 3: 单元测试（3-4天）
4. ✅ 任务 1: 查询结果缓存（2-3天）

### 第二阶段（2-3周）：核心功能增强
5. ✅ 任务 5: 智能代理系统（5-7天）
6. ✅ 任务 6: 基础推荐系统（4-6天）

### 第三阶段（长期）：高级功能
7. ✅ 任务 7: 多模态 RAG
8. ✅ 任务 8: Correction RAG
9. ✅ 任务 9: 用户画像系统
10. ✅ 任务 10: 前端界面

---

## 💡 快速开始建议

**如果你想快速看到效果**，建议从以下任务开始：

1. **任务 4（健康检查）** - 1天即可完成，立即提升可运维性
2. **任务 2（错误处理）** - 2天完成，显著提升稳定性
3. **任务 1（缓存）** - 2-3天完成，立即提升性能

**如果你想实现新功能**，建议：

1. **任务 5（智能代理）** - 最有价值的新功能，支持复杂任务
2. **任务 6（推荐系统）** - 核心业务功能，提升用户体验

---

## 📝 注意事项

- 每个任务都应该有清晰的验收标准
- 建议使用 feature branch 进行开发
- 完成每个任务后更新文档和测试
- 保持代码质量和测试覆盖率

