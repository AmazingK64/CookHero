# app/rag/config.py
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict

# --- Nested Configuration Models ---

class PathsConfig(BaseModel):
    data_path: str

class VectorStoreConfig(BaseModel):
    type: str
    host: str
    port: int
    collection_name: str

class EmbeddingConfig(BaseModel):
    mode: Literal['local', 'remote']
    local_model: str
    remote_model: str
    api_url: str
    batch_size: int
    api_key: Optional[str] = None  # Sensitive, will be loaded from .env

class LLMConfig(BaseModel):
    model_name: str
    base_url: Optional[str] = None
    temperature: float
    max_tokens: int
    api_key: Optional[str] = None  # Sensitive, will be loaded from .env

class RetrievalConfig(BaseModel):
    top_k: int
    rrf_k: int

class HowToCookConfig(BaseModel):
    headers_to_split_on: List[List[str]]

class DataSourceConfig(BaseModel):
    howtocook: HowToCookConfig

# --- Main Configuration Model ---

class RAGConfig(BaseModel):
    """
    The main configuration model, composed of nested sub-models.
    This structure mirrors the `config.yml` file.
    """
    paths: PathsConfig
    vector_store: VectorStoreConfig
    embedding: EmbeddingConfig
    llm: LLMConfig
    retrieval: RetrievalConfig
    data_source: DataSourceConfig


