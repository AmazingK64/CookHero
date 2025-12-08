# app/rag/cache/base.py
"""
Cache backend abstractions.

- KeywordCacheBackend: key/value semantics (for exact match, e.g., Redis L1).
- VectorCacheBackend: vector insert/search semantics (for semantic match, e.g., in-memory or future Milvus).
"""
from typing import Any, List, Optional, Tuple, Protocol


class KeywordCacheBackend(Protocol):
    def get(self, key: str) -> Optional[bytes]:
        ...

    def set(self, key: str, value: bytes, ttl_seconds: int | None = None) -> bool:
        ...

    def delete(self, key: str) -> bool:
        ...

    def clear(self, pattern: str | None = None) -> bool:
        ...


class VectorCacheBackend(Protocol):
    def add(self, key: str, embedding: List[float], payload: Any) -> bool:
        ...

    def search(self, embedding: List[float], threshold: float) -> Optional[Tuple[Any, float]]:
        ...

    def clear(self) -> bool:
        ...

