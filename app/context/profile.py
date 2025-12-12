# app/context/profile.py
"""
用户画像模块 - UserProfile Pydantic 模型

存储用户的静态信息：
- 基础身体数据（身高、体重、年龄、性别）
- 饮食限制（过敏、忌口、宗教限制）
- 生活方式（运动频率、作息时间）
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class ActivityLevel(str, Enum):
    """活动水平"""
    SEDENTARY = "sedentary"           # 久坐不动
    LIGHTLY_ACTIVE = "lightly_active"  # 轻度活动
    MODERATELY_ACTIVE = "moderately_active"  # 中度活动
    VERY_ACTIVE = "very_active"        # 高度活动
    EXTRA_ACTIVE = "extra_active"      # 专业运动员


class DietaryRestrictions(BaseModel):
    """饮食限制"""
    allergies: List[str] = Field(default_factory=list, description="过敏食材，如：花生、海鲜、牛奶")
    intolerances: List[str] = Field(default_factory=list, description="不耐受，如：乳糖不耐受")
    dislikes: List[str] = Field(default_factory=list, description="不喜欢的食材，如：香菜、内脏")
    religious_restrictions: List[str] = Field(default_factory=list, description="宗教限制，如：清真、素食")
    
    def has_restriction(self, ingredient: str) -> bool:
        """检查某食材是否在限制列表中"""
        ingredient_lower = ingredient.lower()
        all_restrictions = self.allergies + self.intolerances + self.dislikes + self.religious_restrictions
        return any(r.lower() in ingredient_lower or ingredient_lower in r.lower() for r in all_restrictions)


class PhysicalStats(BaseModel):
    """身体数据"""
    height_cm: Optional[float] = Field(None, ge=50, le=250, description="身高(cm)")
    weight_kg: Optional[float] = Field(None, ge=20, le=300, description="体重(kg)")
    age: Optional[int] = Field(None, ge=1, le=120, description="年龄")
    gender: Optional[Gender] = None
    body_fat_percentage: Optional[float] = Field(None, ge=1, le=60, description="体脂率(%)")
    
    @property
    def bmi(self) -> Optional[float]:
        """计算BMI"""
        if self.height_cm and self.weight_kg:
            height_m = self.height_cm / 100
            return round(self.weight_kg / (height_m ** 2), 1)
        return None
    
    def calculate_bmr(self) -> Optional[float]:
        """
        计算基础代谢率 (BMR) - Mifflin-St Jeor 公式
        男性: BMR = 10 × 体重(kg) + 6.25 × 身高(cm) - 5 × 年龄 + 5
        女性: BMR = 10 × 体重(kg) + 6.25 × 身高(cm) - 5 × 年龄 - 161
        """
        if not all([self.height_cm, self.weight_kg, self.age, self.gender]):
            return None
        
        bmr = 10 * self.weight_kg + 6.25 * self.height_cm - 5 * self.age
        if self.gender == Gender.MALE:
            bmr += 5
        else:
            bmr -= 161
        return round(bmr, 0)


class NutritionTargets(BaseModel):
    """营养目标"""
    daily_calories: Optional[int] = Field(None, ge=500, le=10000, description="每日目标热量(kcal)")
    protein_g: Optional[float] = Field(None, ge=0, description="蛋白质目标(g)")
    carbs_g: Optional[float] = Field(None, ge=0, description="碳水化合物目标(g)")
    fat_g: Optional[float] = Field(None, ge=0, description="脂肪目标(g)")
    fiber_g: Optional[float] = Field(None, ge=0, description="膳食纤维目标(g)")
    sodium_mg: Optional[float] = Field(None, ge=0, description="钠目标(mg)")


class LifestylePreferences(BaseModel):
    """生活方式偏好"""
    activity_level: ActivityLevel = ActivityLevel.MODERATELY_ACTIVE
    wake_up_time: Optional[str] = Field(None, description="起床时间，如 '07:00'")
    sleep_time: Optional[str] = Field(None, description="睡觉时间，如 '23:00'")
    preferred_meal_times: List[str] = Field(
        default_factory=lambda: ["08:00", "12:00", "18:00"],
        description="偏好的用餐时间"
    )
    cooking_skill_level: int = Field(default=3, ge=1, le=5, description="烹饪技能等级 1-5")
    max_cooking_time_minutes: int = Field(default=60, ge=5, le=240, description="单餐最长烹饪时间")


class UserProfile(BaseModel):
    """
    用户完整画像 - 核心数据模型
    
    这是用户上下文湖的核心，存储所有静态用户信息。
    动态信息（历史行为、偏好变化）存储在 PreferenceLedger 中。
    """
    user_id: str = Field(..., description="用户唯一标识")
    nickname: Optional[str] = None
    
    # 身体数据
    physical_stats: PhysicalStats = Field(default_factory=PhysicalStats)
    
    # 饮食限制
    dietary_restrictions: DietaryRestrictions = Field(default_factory=DietaryRestrictions)
    
    # 营养目标
    nutrition_targets: NutritionTargets = Field(default_factory=NutritionTargets)
    
    # 生活方式
    lifestyle: LifestylePreferences = Field(default_factory=LifestylePreferences)
    
    # 元信息
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def calculate_tdee(self) -> Optional[float]:
        """
        计算每日总消耗热量 (TDEE)
        TDEE = BMR × 活动系数
        """
        bmr = self.physical_stats.calculate_bmr()
        if bmr is None:
            return None
        
        activity_multipliers = {
            ActivityLevel.SEDENTARY: 1.2,
            ActivityLevel.LIGHTLY_ACTIVE: 1.375,
            ActivityLevel.MODERATELY_ACTIVE: 1.55,
            ActivityLevel.VERY_ACTIVE: 1.725,
            ActivityLevel.EXTRA_ACTIVE: 1.9,
        }
        multiplier = activity_multipliers.get(self.lifestyle.activity_level, 1.55)
        return round(bmr * multiplier, 0)
    
    def to_context_dict(self) -> dict:
        """
        转换为可注入 Agent 的上下文字典
        只包含关键信息，避免 prompt 过长
        """
        context = {
            "user_id": self.user_id,
        }
        
        # 身体数据
        if self.physical_stats.height_cm:
            context["height_cm"] = self.physical_stats.height_cm
        if self.physical_stats.weight_kg:
            context["weight_kg"] = self.physical_stats.weight_kg
        if self.physical_stats.bmi:
            context["bmi"] = self.physical_stats.bmi
        
        # 饮食限制 - 合并为一个列表
        restrictions = []
        if self.dietary_restrictions.allergies:
            restrictions.extend([f"过敏:{a}" for a in self.dietary_restrictions.allergies])
        if self.dietary_restrictions.intolerances:
            restrictions.extend([f"不耐受:{i}" for i in self.dietary_restrictions.intolerances])
        if self.dietary_restrictions.dislikes:
            restrictions.extend([f"不吃:{d}" for d in self.dietary_restrictions.dislikes])
        if restrictions:
            context["dietary_restrictions"] = restrictions
        
        # 营养目标
        if self.nutrition_targets.daily_calories:
            context["target_calories"] = self.nutrition_targets.daily_calories
        if self.nutrition_targets.protein_g:
            context["target_protein_g"] = self.nutrition_targets.protein_g
        
        # 生活方式
        context["cooking_skill"] = self.lifestyle.cooking_skill_level
        context["max_cooking_time"] = self.lifestyle.max_cooking_time_minutes
        
        return context

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_001",
                "nickname": "小明",
                "physical_stats": {
                    "height_cm": 178,
                    "weight_kg": 75,
                    "age": 28,
                    "gender": "male"
                },
                "dietary_restrictions": {
                    "intolerances": ["乳糖"],
                    "dislikes": ["香菜", "内脏"]
                },
                "nutrition_targets": {
                    "daily_calories": 2800,
                    "protein_g": 180
                }
            }
        }
