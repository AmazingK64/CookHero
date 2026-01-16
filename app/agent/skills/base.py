"""
Skill 基类和辅助类

Skill 是可注入到 Agent 系统提示词的专业知识模块。
采用渐进式披露：元数据始终可用，完整 prompt 按需加载。
"""

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from app.agent.types import SkillMeta

logger = logging.getLogger(__name__)


class BaseSkill(ABC):
    """
    Skill 基类。

    Skill 分两阶段加载：
    1. 元数据（始终加载）：name, description, keywords
    2. 完整 prompt（按需加载）：用于注入系统提示词
    """

    # 轻量元数据（始终加载）
    meta: SkillMeta

    # 完整 prompt（按需加载）
    _full_prompt: Optional[str] = None
    _loaded: bool = False

    def __init__(self, meta: SkillMeta):
        """
        初始化 Skill。

        Args:
            meta: Skill 元数据
        """
        self.meta = meta
        self._full_prompt = None
        self._loaded = False

    @property
    def name(self) -> str:
        """Skill 名称。"""
        return self.meta.name

    @property
    def description(self) -> str:
        """Skill 描述。"""
        return self.meta.description

    @abstractmethod
    def load_full(self) -> None:
        """
        加载完整 prompt。

        子类必须实现此方法来加载 Skill 的完整内容。
        """
        pass

    def get_prompt(self) -> str:
        """
        获取完整 prompt，自动触发加载。

        Returns:
            Skill 的完整 prompt
        """
        if not self._loaded:
            self.load_full()
            self._loaded = True
        return self._full_prompt or ""

    def to_dict(self) -> dict:
        """转换为字典（仅元数据）。"""
        return self.meta.model_dump()

    def __repr__(self) -> str:
        return f"<Skill: {self.name}>"


class FileSkill(BaseSkill):
    """
    基于文件的 Skill。

    从 markdown 文件加载 Skill 内容。
    文件格式：
    ```
    ---
    name: skill_name
    description: Skill description
    keywords: [keyword1, keyword2]
    ---

    # Skill Content
    ...
    ```
    """

    def __init__(self, meta: SkillMeta, file_path: str):
        """
        初始化文件 Skill。

        Args:
            meta: Skill 元数据
            file_path: Skill 文件路径
        """
        super().__init__(meta)
        self.file_path = file_path

    def load_full(self) -> None:
        """从文件加载完整 prompt。"""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 跳过 frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    self._full_prompt = parts[2].strip()
                else:
                    self._full_prompt = content
            else:
                self._full_prompt = content

            logger.debug(f"Loaded skill {self.name} from {self.file_path}")
        except Exception as e:
            logger.error(f"Failed to load skill {self.name}: {e}")
            self._full_prompt = ""

    @classmethod
    def from_file(cls, file_path: str) -> Optional["FileSkill"]:
        """
        从文件创建 Skill。

        Args:
            file_path: Skill 文件路径

        Returns:
            FileSkill 实例，如果解析失败返回 None
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 解析 frontmatter
            if not content.startswith("---"):
                logger.warning(f"Skill file {file_path} missing frontmatter")
                return None

            parts = content.split("---", 2)
            if len(parts) < 3:
                logger.warning(f"Invalid skill file format: {file_path}")
                return None

            frontmatter = parts[1].strip()
            meta_dict = {}

            for line in frontmatter.split("\n"):
                line = line.strip()
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()

                    # 解析列表
                    if value.startswith("[") and value.endswith("]"):
                        value = [
                            v.strip().strip('"').strip("'")
                            for v in value[1:-1].split(",")
                            if v.strip()
                        ]

                    meta_dict[key] = value

            if "name" not in meta_dict or "description" not in meta_dict:
                logger.warning(f"Skill file {file_path} missing required fields")
                return None

            meta = SkillMeta(
                name=meta_dict["name"],
                description=meta_dict["description"],
                keywords=meta_dict.get("keywords", []),
            )

            return cls(meta, file_path)

        except Exception as e:
            logger.error(f"Failed to parse skill file {file_path}: {e}")
            return None


class InlineSkill(BaseSkill):
    """
    内联 Skill。

    直接在代码中定义的 Skill。
    """

    def __init__(
        self,
        name: str,
        description: str,
        prompt: str,
        keywords: Optional[list[str]] = None,
    ):
        """
        初始化内联 Skill。

        Args:
            name: Skill 名称
            description: Skill 描述
            prompt: Skill 完整 prompt
            keywords: 关键词列表
        """
        meta = SkillMeta(
            name=name,
            description=description,
            keywords=keywords or [],
        )
        super().__init__(meta)
        self._full_prompt = prompt
        self._loaded = True  # 内联 Skill 已经加载

    def load_full(self) -> None:
        """内联 Skill 无需加载。"""
        pass


class SkillLoader:
    """
    Skill 加载器。

    负责从目录加载所有 Skill。
    """

    def __init__(self, skills_dir: Optional[str] = None):
        """
        初始化加载器。

        Args:
            skills_dir: Skill 文件目录
        """
        self.skills_dir = skills_dir

    def load_all(self) -> dict[str, BaseSkill]:
        """
        加载目录中的所有 Skill。

        Returns:
            Skill 名称到实例的映射
        """
        skills = {}

        if not self.skills_dir or not os.path.exists(self.skills_dir):
            return skills

        for file_name in os.listdir(self.skills_dir):
            if file_name.endswith(".md"):
                file_path = os.path.join(self.skills_dir, file_name)
                skill = FileSkill.from_file(file_path)
                if skill:
                    skills[skill.name] = skill
                    logger.info(f"Loaded skill: {skill.name}")

        return skills

    def get_metas(self, skills: dict[str, BaseSkill]) -> list[dict]:
        """
        获取所有 Skill 的元数据。

        Args:
            skills: Skill 字典

        Returns:
            元数据列表
        """
        return [skill.to_dict() for skill in skills.values()]
