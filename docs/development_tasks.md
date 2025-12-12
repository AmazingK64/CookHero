# CookHero 开发任务清单

本文档列出了 CookHero 项目接下来可以进行的开发任务，按照优先级和可行性进行分类。

---

## ✅ 阶段一框架已搭建完成 (2025-12-12)

### 已完成的模块

#### 1. 用户上下文湖 (`app/context/`)
- ✅ `profile.py` - 用户画像（身体数据、饮食限制、营养目标、生活方式）
- ✅ `ledger.py` - 偏好事件账本（显式反馈、隐式行为、计划记录）
- ✅ `goals.py` - 目标卡系统（多目标管理、冲突检测、约束合并）
- ✅ `memory.py` - 长期记忆管理（向量检索、记忆遗忘）

#### 2. Structure Cards (`app/cards/`)
- ✅ `base.py` - 卡片基类（状态管理、版本控制）
- ✅ `meal.py` - 餐食卡片（菜品、营养信息、食材）
- ✅ `diet_plan.py` - 饮食计划卡片（日/周计划）
- ✅ `training_plan.py` - 训练计划卡片（运动、日/周计划）
- ✅ `combined.py` - 综合生活计划卡片（饮食+训练整合、冲突检测）

#### 3. 工具层 (`app/tools/`)
- ✅ `base.py` - 工具基类（Pydantic输入输出、LangChain适配）
- ✅ `rag.py` - RAG检索工具（封装现有RAG模块）
- ✅ `nutrition.py` - 营养计算工具（食物营养查询、TDEE计算）
- ✅ `similarity.py` - 相似度工具（食材替换建议）

#### 4. Agent 层 (`app/agents/`)
- ✅ `base.py` - Agent基类（plan/execute/reflect三阶段）
- ✅ `diet_planner.py` - 饮食规划Agent（周计划生成）
- ✅ `rag_agent.py` - RAG检索Agent（菜谱和知识检索）

#### 5. 调度层
- ✅ `conductor.py` - Conductor调度器（意图路由、多Agent编排、结果合并）
- ✅ `router.py` - 意图路由器（规则+关键词匹配、实体提取）

---

## 当前任务

**单纯把 LangChain Agent 套进去是“2024式伪AI原生”**，  
**2026 级、真正可落地、可扩展、可长期演进** 的 CookHero Agent 架构设计，需要彻底实现“模型-结构-运行时”三层解耦。

### 最终目标（2026 愿景在 CookHero 中的落地形态）
用户说一句话：
> “我下周要备战半马，身高178体重75，乳糖不耐受，不吃香菜和内脏，想周一到周日每天跑步+力量搭配，饮食总热量控制在2800kcal左右，蛋白质至少180g，晚餐尽量早吃。”

理想情况下，系统不需要你写一个超级长的 prompt，而是：
1. 意图路由 → 识别这是一个【训练+饮食联合周计划】
2. 自动拉起多智能体协同（训练计划 Agent + 饮食计划 Agent + 营养计算 Agent + RAG检素 Agent）
3. 每个 Agent 都有自己的长期记忆、用户画像片段、工具集
4. 最终由一个 Conductor（调度器）合并结果、冲突检测、迭代优化
5. 输出一个结构化周计划（Structure Card），可直接渲染、可修改、可存入用户事件账本

### 2026 级 CookHero Agent 架构全景（完全解耦版）

```
+-------------------+       +---------------------+
|   用户意图 (语言)   |       |   Conductor（调度器）   |
+-------------------+       +---------------------+
          |                            |
          v                            v
+-----------------------------------------------+
|               Agent Runtime (运行时)           |
|  ├─ User Context Lake（用户全量上下文湖）        |
|  │    ├─ Profile Card（静态画像：身高、体重、忌口…）|
|  │    ├─ Preference Ledger（偏好事件账本）        |
|  │    ├─ Goal Cards（目标卡：减脂、半马PB…）     |
|  │    └─ LongTerm Memory（向量+图谱混合记忆）     |
|                                               |
|  ├─ Agent Registry（智能体注册中心）             |
|  │    ├─ DietPlannerAgent                      |
|  │    ├─ TrainingPlannerAgent                   |
|  │    ├─ NutritionCalculatorAgent               |
|  │    ├─ RecipeRAGAgent                         |
|  │    └─ WebResearchAgent (SerpAPI/Tavily)       |
|                                               |
|  ├─ Tool Registry（工具注册的所有工具）           |
|  │    ├─ rag_query_tool                         |
|  │    ├─ web_search_tool                        |
|  │    ├─ nutrition_calculator_tool              |
|  │    ├─ recipe_similarity_tool                  |
|  │    └─ calendar_booking_tool (未来可扩展)      |
|                                               |
|  ├─ Structure Card Templates（结构卡模板）        |
|       ├─ WeeklyDietPlanCard                    |
|       ├─ WeeklyTrainingPlanCard                 |
|       └─ CombinedLifestylePlanCard             |
+-----------------------------------------------+
          +-----------------+
          ^                                              |   LLM (仅推理CPU)   |
          |                                              +-----------------+
          +----------------- ReAct / Plan-and-Execute 循环 ------------+
```

### 核心解耦实现方式（直接可落地的代码结构建议）

```bash
app/                     # ← 真正 AI-Native 的核心（与模型无关）
   ├── context/               # 用户上下文湖（取代长 prompt）
   │    ├── profile.py         # UserProfile Pydantic 模型
   │    ├── ledger.py          # 偏好/行为事件账本（可存 DB）
   │    ├── goals.py           # 目标卡系统
   │    └── memory.py          # 长期记忆管理（向量店 + Neo4j 图谱）
   │
   ├── agents/                # 每个 Agent 都是“结构+工具+小模型提示”的组合
   │    ├── base.py            # 所有 Agent 继承，强制实现 .plan() .execute() .reflect()
   │    ├── diet_planner.py
   │    ├── training_planner.py
   │    ├── nutrition_calc.py
   │    └── rag_agent.py
   │
   ├── tools/                 # 工具完全独立，可被多个 Agent 复用
   │    ├── __init__.py
   │    ├── rag.py
   │    ├── web_search.py
   │    ├── nutrition.py
   │    └── similarity.py
   │
   ├── cards/                 # Structure Cards —— 未来前端直接消费的结构化输出
   │    ├── base.py
   │    ├── diet_plan.py       # 包含 daily_meals: List[MealCard]
   │    └── training_plan.py
   │
   ├── conductor.py           # 真正的“大脑”：意图路由 + 多智能体编排 + 冲突解决
   └── router.py              # 意图分类器（轻量 classifier 或小模型）
```

#### 阶段一（1-2周）：先跑通“伪解耦”但结构清晰的 ReAct Agent（过渡期必须）
- 用 `langchain.agents` + `create_openai_tools_agent` 或 `create_react_agent`
- 但强制所有工具返回 Pydantic 结构，而不是纯文本
- 把用户画像、目标等信息通过 `RunnablePassthrough.assign` 注入，而不是塞进 prompt
- Agent 最终输出一个 `CombinedLifestylePlanCard`（Pydantic）

#### 阶段二（3-5周）：完全抛弃 LangChain Agent，改用 Plan-and-Execute + Conductor
- 实现 `Conductor` 类，负责：
  - 意图识别 → 决定拉起哪些子 Agent
  - 给每个子 Agent 分配独立的子上下文（只给它需要的画像片段）
  - 收集所有子计划 → 冲突检测（总热量超、训练后无碳水恢复等）
  - 如有冲突 → 触发反思循环（把冲突发给 llm 重新规划）
- 每个子 Agent 内部使用极简 ReAct，只解决单一领域问题

#### 阶段三（长期）：多智能体 + 事件账本 + 人格卡
- 把每次生成的计划写入用户 Ledger
- 下次同类任务先检索历史最优计划 → 做 Delta 更新，而不是从零开始
- 引入 Agent 人格卡（DietPlanner 更保守、TrainingPlanner 更激进）
- 引入工具路由器（某些营养计算走本地公式，不走 LLM）

### 关键原则总结（贴在工位上的那张纸）

1. **模型只做推理，不存状态**
2. **所有状态（画像、偏好、历史计划）都存在应用层**
3. **所有输出必须是 Structure Card，可被后续 Agent 消费**
4. **任何复杂任务必须拆成多 Agent 协作，禁止单体超级 Agent**
5. **工具返回结构化数据，禁止返回长文本再让下一个 Agent 解析**

只要你按这个方向走，CookHero 会在 2026 年直接碾压市面上 99% 的“Chat+UI”伪 AI 应用，成为真正意义上的 AI-Native 生活方式智能体。


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