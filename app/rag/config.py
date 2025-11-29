# app/rag/config.py
from typing import Dict, Any, Optional, Literal
from pydantic_settings import BaseSettings

class RAGConfig(BaseSettings):
    """
    Configuration for the RAG system, loaded from environment variables and .env file.
    """
    # --- Path Settings ---
    DATA_PATH: str = "data/HowToCook"
    
    # --- Milvus Settings ---
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION_NAME: str = "cook_hero_recipes"

    # --- Embedding Settings ---
    # Mode can be 'local' or 'remote'
    EMBEDDING_MODE: Literal['local', 'remote'] = 'remote'
    # Local model for embedding text.
    LOCAL_EMBEDDING_MODEL: str = "BAAI/bge-small-zh-v1.5"
    # Remote API endpoint for embeddings
    EMBEDDING_API_URL: str = "https://api.siliconflow.cn/v1"
    # API Key for remote embedding service
    EMBEDDING_API_KEY: str = "None"
    # Remote model name for embeddings
    REMOTE_EMBEDDING_MODEL: str = "BAAI/bge-large-zh-v1.5"
    # Batch size for remote embedding requests
    EMBEDDING_BATCH_SIZE: int = 64
    
    # --- LLM Settings ---
    LLM_MODEL: str = "gpt-4o-mini"
    
    # --- API Keys ---
    # Will be automatically loaded from environment variables or .env file
    LLM_API_KEY: str = "None"
    LLM_BASE_URL: Optional[str] = None
    
    # --- Retrieval Settings ---
    TOP_K: int = 3
    RRF_K: int = 60

    # --- Generation Settings ---
    TEMPERATURE: float = 0.1
    MAX_TOKENS: int = 4096

    # --- Chunking Settings ---
    # Using a simple list here as pydantic_settings has issues with dataclasses.field
    HEADERS_TO_SPLIT_ON: list = [
        ("#", "header_1"),
        ("##", "header_2"),
        ("###", "header_3")
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

# Create a default config instance for easy import.
DefaultRAGConfig = RAGConfig()
