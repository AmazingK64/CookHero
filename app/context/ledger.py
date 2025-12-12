# app/context/ledger.py
"""
偏好事件账本 - Preference Ledger

记录用户的所有偏好变化和行为事件，支持：
- 显式反馈（点赞、收藏、评分）
- 隐式行为（浏览、搜索、跳过）
- 计划执行记录（完成、修改、放弃）

这是实现"增量学习"和"Delta更新"的基础。
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EventType(str, Enum):
    """事件类型"""
    # 显式反馈
    LIKE = "like"                      # 点赞
    DISLIKE = "dislike"                # 点踩
    FAVORITE = "favorite"              # 收藏
    RATE = "rate"                      # 评分
    
    # 隐式行为
    VIEW = "view"                      # 浏览
    SEARCH = "search"                  # 搜索
    SKIP = "skip"                      # 跳过推荐
    CLICK = "click"                    # 点击
    
    # 计划相关
    PLAN_GENERATED = "plan_generated"  # 计划生成
    PLAN_MODIFIED = "plan_modified"    # 计划修改
    PLAN_COMPLETED = "plan_completed"  # 计划完成
    PLAN_ABANDONED = "plan_abandoned"  # 计划放弃
    
    # 对话相关
    QUERY = "query"                    # 用户查询
    FEEDBACK = "feedback"              # 用户反馈


class EntityType(str, Enum):
    """实体类型"""
    RECIPE = "recipe"          # 菜谱
    INGREDIENT = "ingredient"  # 食材
    CUISINE = "cuisine"        # 菜系
    MEAL_PLAN = "meal_plan"    # 餐饮计划
    TRAINING_PLAN = "training_plan"  # 训练计划
    GOAL = "goal"              # 目标


class PreferenceEvent(BaseModel):
    """
    单个偏好事件
    
    设计原则：事件不可变，只增不改
    """
    event_id: str = Field(..., description="事件唯一ID")
    user_id: str = Field(..., description="用户ID")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    event_type: EventType
    entity_type: EntityType
    entity_id: str = Field(..., description="实体ID，如菜谱ID")
    entity_name: Optional[str] = Field(None, description="实体名称，便于展示")
    
    # 事件详情
    value: Optional[Any] = Field(None, description="事件值，如评分分数")
    context: Dict[str, Any] = Field(default_factory=dict, description="事件上下文")
    
    # 来源追踪
    source: str = Field(default="user", description="事件来源：user/system/agent")
    session_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "evt_001",
                "user_id": "user_001",
                "event_type": "like",
                "entity_type": "recipe",
                "entity_id": "recipe_红烧肉",
                "entity_name": "红烧肉",
                "value": None,
                "context": {"meal_type": "dinner", "cook_time_minutes": 45}
            }
        }


class PreferenceLedger:
    """
    偏好账本管理器
    
    支持：
    - 事件写入（只增不改）
    - 事件查询（按时间、类型、实体）
    - 偏好聚合（统计用户偏好）
    - 持久化（可对接 DB）
    
    TODO: 阶段二实现持久化到 PostgreSQL/Redis
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self._events: List[PreferenceEvent] = []
        self._event_counter = 0
    
    def add_event(
        self,
        event_type: EventType,
        entity_type: EntityType,
        entity_id: str,
        entity_name: Optional[str] = None,
        value: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
        source: str = "user",
        session_id: Optional[str] = None,
    ) -> PreferenceEvent:
        """添加一个新事件"""
        self._event_counter += 1
        event = PreferenceEvent(
            event_id=f"evt_{self.user_id}_{self._event_counter}",
            user_id=self.user_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            value=value,
            context=context or {},
            source=source,
            session_id=session_id,
        )
        self._events.append(event)
        return event
    
    def get_events(
        self,
        event_types: Optional[List[EventType]] = None,
        entity_types: Optional[List[EntityType]] = None,
        entity_id: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[PreferenceEvent]:
        """查询事件"""
        result = self._events
        
        if event_types:
            result = [e for e in result if e.event_type in event_types]
        if entity_types:
            result = [e for e in result if e.entity_type in entity_types]
        if entity_id:
            result = [e for e in result if e.entity_id == entity_id]
        if since:
            result = [e for e in result if e.timestamp >= since]
        
        # 按时间倒序，取最新的
        result = sorted(result, key=lambda e: e.timestamp, reverse=True)
        return result[:limit]
    
    def get_liked_entities(self, entity_type: EntityType) -> List[str]:
        """获取用户喜欢的实体ID列表"""
        liked_events = self.get_events(
            event_types=[EventType.LIKE, EventType.FAVORITE],
            entity_types=[entity_type],
        )
        return list(set(e.entity_id for e in liked_events))
    
    def get_disliked_entities(self, entity_type: EntityType) -> List[str]:
        """获取用户不喜欢的实体ID列表"""
        disliked_events = self.get_events(
            event_types=[EventType.DISLIKE, EventType.SKIP],
            entity_types=[entity_type],
        )
        return list(set(e.entity_id for e in disliked_events))
    
    def get_recent_searches(self, limit: int = 10) -> List[str]:
        """获取最近的搜索关键词"""
        search_events = self.get_events(
            event_types=[EventType.SEARCH, EventType.QUERY],
            limit=limit,
        )
        return [e.context.get("query", "") for e in search_events if e.context.get("query")]
    
    def get_preference_summary(self) -> Dict[str, Any]:
        """
        生成偏好摘要，可注入 Agent 上下文
        """
        return {
            "liked_recipes": self.get_liked_entities(EntityType.RECIPE)[:10],
            "disliked_recipes": self.get_disliked_entities(EntityType.RECIPE)[:10],
            "liked_ingredients": self.get_liked_entities(EntityType.INGREDIENT)[:10],
            "disliked_ingredients": self.get_disliked_entities(EntityType.INGREDIENT)[:10],
            "recent_searches": self.get_recent_searches(5),
            "total_events": len(self._events),
        }
    
    def get_recent_plans(self, limit: int = 5) -> List[PreferenceEvent]:
        """获取最近生成的计划（用于 Delta 更新）"""
        return self.get_events(
            event_types=[EventType.PLAN_GENERATED, EventType.PLAN_COMPLETED],
            limit=limit,
        )
    
    def to_list(self) -> List[Dict]:
        """导出所有事件（用于持久化）"""
        return [e.model_dump() for e in self._events]
    
    def load_from_list(self, events: List[Dict]):
        """从列表加载事件（从持久化恢复）"""
        self._events = [PreferenceEvent(**e) for e in events]
        self._event_counter = len(self._events)
