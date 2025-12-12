# app/context/__init__.py
"""
用户上下文湖（User Context Lake）

取代长 prompt 的核心模块，管理用户的所有状态信息：
- Profile Card: 静态画像（身高、体重、忌口等）
- Preference Ledger: 偏好事件账本
- Goal Cards: 目标卡系统
- Long-term Memory: 长期记忆管理
"""

from app.context.profile import UserProfile, DietaryRestrictions, PhysicalStats
from app.context.ledger import PreferenceLedger, PreferenceEvent
from app.context.goals import GoalCard, GoalType, GoalManager
from app.context.memory import LongTermMemory

__all__ = [
    # Profile
    "UserProfile",
    "DietaryRestrictions", 
    "PhysicalStats",
    # Ledger
    "PreferenceLedger",
    "PreferenceEvent",
    # Goals
    "GoalCard",
    "GoalType",
    "GoalManager",
    # Memory
    "LongTermMemory",
]
