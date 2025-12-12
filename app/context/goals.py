# app/context/goals.py
"""
目标卡系统 - Goal Cards

用户可以设定多个目标（减脂、增肌、马拉松PB等），
每个目标是一个独立的卡片，包含：
- 目标类型和描述
- 时间范围
- 进度追踪
- 相关约束条件

目标卡会影响 Agent 的规划策略。
"""

from datetime import datetime, date
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GoalType(str, Enum):
    """目标类型"""
    # 体重管理
    WEIGHT_LOSS = "weight_loss"        # 减脂
    WEIGHT_GAIN = "weight_gain"        # 增重
    MAINTAIN_WEIGHT = "maintain_weight"  # 保持体重
    
    # 运动目标
    MARATHON = "marathon"              # 马拉松
    HALF_MARATHON = "half_marathon"    # 半马
    MUSCLE_GAIN = "muscle_gain"        # 增肌
    ENDURANCE = "endurance"            # 耐力提升
    
    # 健康目标
    LOWER_BLOOD_SUGAR = "lower_blood_sugar"  # 控制血糖
    LOWER_CHOLESTEROL = "lower_cholesterol"  # 降低胆固醇
    IMPROVE_SLEEP = "improve_sleep"    # 改善睡眠
    
    # 饮食目标
    EAT_MORE_VEGETABLES = "eat_more_vegetables"  # 多吃蔬菜
    REDUCE_SODIUM = "reduce_sodium"    # 减少钠摄入
    INCREASE_PROTEIN = "increase_protein"  # 增加蛋白质
    
    # 学习目标
    LEARN_COOKING = "learn_cooking"    # 学习烹饪
    
    # 通用
    CUSTOM = "custom"                  # 自定义目标


class GoalStatus(str, Enum):
    """目标状态"""
    ACTIVE = "active"          # 进行中
    COMPLETED = "completed"    # 已完成
    PAUSED = "paused"          # 已暂停
    ABANDONED = "abandoned"    # 已放弃


class GoalCard(BaseModel):
    """
    目标卡 - 单个目标的完整信息
    """
    goal_id: str = Field(..., description="目标唯一ID")
    user_id: str = Field(..., description="用户ID")
    
    # 基本信息
    goal_type: GoalType
    title: str = Field(..., description="目标标题，如'4月底跑完半马'")
    description: Optional[str] = Field(None, description="详细描述")
    
    # 时间范围
    start_date: date = Field(default_factory=date.today)
    target_date: Optional[date] = Field(None, description="目标完成日期")
    
    # 量化指标
    target_value: Optional[float] = Field(None, description="目标值，如目标体重65kg")
    current_value: Optional[float] = Field(None, description="当前值")
    unit: Optional[str] = Field(None, description="单位，如 kg, km, 分钟")
    
    # 约束条件
    constraints: Dict[str, Any] = Field(
        default_factory=dict,
        description="相关约束，如 {'max_daily_calories': 2000, 'min_protein_g': 150}"
    )
    
    # 状态
    status: GoalStatus = GoalStatus.ACTIVE
    priority: int = Field(default=5, ge=1, le=10, description="优先级 1-10，10最高")
    
    # 元信息
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @property
    def progress_percentage(self) -> Optional[float]:
        """计算完成进度百分比"""
        if self.target_value is None or self.current_value is None:
            return None
        
        # 对于减重目标，需要反向计算
        if self.goal_type == GoalType.WEIGHT_LOSS:
            # 假设初始值存在 constraints 中
            initial = self.constraints.get("initial_value")
            if initial and initial != self.target_value:
                progress = (initial - self.current_value) / (initial - self.target_value) * 100
                return min(max(progress, 0), 100)
        
        # 一般目标：当前值/目标值
        if self.target_value != 0:
            return min((self.current_value / self.target_value) * 100, 100)
        return None
    
    @property
    def days_remaining(self) -> Optional[int]:
        """距离目标日期的剩余天数"""
        if self.target_date:
            delta = self.target_date - date.today()
            return max(delta.days, 0)
        return None
    
    def to_context_dict(self) -> Dict[str, Any]:
        """转换为可注入 Agent 的上下文"""
        context = {
            "goal_id": self.goal_id,
            "goal_type": self.goal_type.value,
            "title": self.title,
            "priority": self.priority,
        }
        
        if self.target_value:
            context["target_value"] = f"{self.target_value} {self.unit or ''}"
        if self.current_value:
            context["current_value"] = f"{self.current_value} {self.unit or ''}"
        if self.progress_percentage:
            context["progress"] = f"{self.progress_percentage:.1f}%"
        if self.days_remaining is not None:
            context["days_remaining"] = self.days_remaining
        if self.constraints:
            context["constraints"] = self.constraints
        
        return context

    class Config:
        json_schema_extra = {
            "example": {
                "goal_id": "goal_001",
                "user_id": "user_001",
                "goal_type": "half_marathon",
                "title": "4月底完成半马",
                "target_date": "2024-04-30",
                "target_value": 21.1,
                "unit": "km",
                "constraints": {
                    "min_daily_calories": 2500,
                    "min_protein_g": 150,
                    "weekly_long_run_km": 15
                },
                "priority": 8
            }
        }


class GoalManager:
    """
    目标管理器
    
    管理用户的所有目标卡，支持：
    - 增删改查
    - 冲突检测（两个目标的约束是否矛盾）
    - 优先级排序
    - 上下文提取（给 Agent 用）
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self._goals: Dict[str, GoalCard] = {}
        self._goal_counter = 0
    
    def add_goal(self, goal: GoalCard) -> GoalCard:
        """添加目标"""
        if goal.goal_id in self._goals:
            raise ValueError(f"Goal {goal.goal_id} already exists")
        self._goals[goal.goal_id] = goal
        return goal
    
    def create_goal(
        self,
        goal_type: GoalType,
        title: str,
        description: Optional[str] = None,
        target_date: Optional[date] = None,
        target_value: Optional[float] = None,
        unit: Optional[str] = None,
        constraints: Optional[Dict[str, Any]] = None,
        priority: int = 5,
    ) -> GoalCard:
        """创建并添加新目标"""
        self._goal_counter += 1
        goal = GoalCard(
            goal_id=f"goal_{self.user_id}_{self._goal_counter}",
            user_id=self.user_id,
            goal_type=goal_type,
            title=title,
            description=description,
            target_date=target_date,
            target_value=target_value,
            unit=unit,
            constraints=constraints or {},
            priority=priority,
        )
        return self.add_goal(goal)
    
    def get_goal(self, goal_id: str) -> Optional[GoalCard]:
        """获取单个目标"""
        return self._goals.get(goal_id)
    
    def get_active_goals(self) -> List[GoalCard]:
        """获取所有进行中的目标，按优先级排序"""
        active = [g for g in self._goals.values() if g.status == GoalStatus.ACTIVE]
        return sorted(active, key=lambda g: g.priority, reverse=True)
    
    def update_goal(self, goal_id: str, **updates) -> Optional[GoalCard]:
        """更新目标"""
        goal = self._goals.get(goal_id)
        if goal:
            for key, value in updates.items():
                if hasattr(goal, key):
                    setattr(goal, key, value)
            goal.updated_at = datetime.now()
        return goal
    
    def complete_goal(self, goal_id: str) -> Optional[GoalCard]:
        """标记目标完成"""
        return self.update_goal(goal_id, status=GoalStatus.COMPLETED)
    
    def pause_goal(self, goal_id: str) -> Optional[GoalCard]:
        """暂停目标"""
        return self.update_goal(goal_id, status=GoalStatus.PAUSED)
    
    def detect_conflicts(self) -> List[Dict[str, Any]]:
        """
        检测目标间的冲突
        
        例如：
        - 减脂目标要求热量缺口，增肌目标要求热量盈余
        - 两个目标的时间重叠但约束矛盾
        """
        conflicts = []
        active_goals = self.get_active_goals()
        
        for i, goal1 in enumerate(active_goals):
            for goal2 in active_goals[i+1:]:
                conflict = self._check_pair_conflict(goal1, goal2)
                if conflict:
                    conflicts.append(conflict)
        
        return conflicts
    
    def _check_pair_conflict(self, goal1: GoalCard, goal2: GoalCard) -> Optional[Dict[str, Any]]:
        """检查两个目标是否冲突"""
        # 减脂 vs 增肌 冲突
        conflicting_pairs = [
            (GoalType.WEIGHT_LOSS, GoalType.MUSCLE_GAIN),
            (GoalType.WEIGHT_LOSS, GoalType.WEIGHT_GAIN),
        ]
        
        for pair in conflicting_pairs:
            if (goal1.goal_type, goal2.goal_type) in [pair, pair[::-1]]:
                return {
                    "goal1_id": goal1.goal_id,
                    "goal2_id": goal2.goal_id,
                    "conflict_type": "goal_type_conflict",
                    "description": f"目标'{goal1.title}'和'{goal2.title}'可能存在冲突",
                    "suggestion": "建议优先完成其中一个目标，或调整目标优先级"
                }
        
        # 约束冲突检测
        c1 = goal1.constraints
        c2 = goal2.constraints
        
        # 热量约束冲突
        if c1.get("max_daily_calories") and c2.get("min_daily_calories"):
            if c1["max_daily_calories"] < c2["min_daily_calories"]:
                return {
                    "goal1_id": goal1.goal_id,
                    "goal2_id": goal2.goal_id,
                    "conflict_type": "calorie_conflict",
                    "description": f"热量约束冲突：{goal1.title}要求最多{c1['max_daily_calories']}kcal，{goal2.title}要求至少{c2['min_daily_calories']}kcal",
                    "suggestion": "需要调整其中一个目标的热量约束"
                }
        
        return None
    
    def get_merged_constraints(self) -> Dict[str, Any]:
        """
        合并所有活跃目标的约束条件
        用于传递给 Agent 作为硬约束
        """
        merged = {}
        
        for goal in self.get_active_goals():
            for key, value in goal.constraints.items():
                if key not in merged:
                    merged[key] = value
                else:
                    # 对于 min 类型约束，取最大值
                    if key.startswith("min_"):
                        merged[key] = max(merged[key], value)
                    # 对于 max 类型约束，取最小值
                    elif key.startswith("max_"):
                        merged[key] = min(merged[key], value)
        
        return merged
    
    def get_context_for_agent(self) -> Dict[str, Any]:
        """
        生成可注入 Agent 的目标上下文
        """
        active_goals = self.get_active_goals()
        
        return {
            "active_goals": [g.to_context_dict() for g in active_goals[:5]],  # 最多5个
            "merged_constraints": self.get_merged_constraints(),
            "conflicts": self.detect_conflicts(),
        }
    
    def to_list(self) -> List[Dict]:
        """导出所有目标（用于持久化）"""
        return [g.model_dump() for g in self._goals.values()]
    
    def load_from_list(self, goals: List[Dict]):
        """从列表加载目标（从持久化恢复）"""
        for g in goals:
            goal = GoalCard(**g)
            self._goals[goal.goal_id] = goal
        self._goal_counter = len(self._goals)
