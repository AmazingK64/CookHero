# app/core/config.py
import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """
    System-wide settings.
    """
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "CookHero"

settings = Settings()
