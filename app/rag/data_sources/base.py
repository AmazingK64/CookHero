# app/rag/data_sources/base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any, ClassVar, Dict, List, Optional

from langchain_core.documents import Document


@dataclass(frozen=True, slots=True)
class StructuredMetadata:
    source: str
    parent_id: Optional[str]
    dish_name: str
    category: str
    difficulty: str
    is_dish_index: bool
    data_source: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BaseDataSource(ABC):
    REQUIRED_KEYS: ClassVar[tuple[str, ...]] = (
        "source",
        "parent_id",
        "dish_name",
        "category",
        "difficulty",
        "is_dish_index",
        "data_source",
    )
    RUNTIME_ONLY_KEYS: ClassVar[set[str]] = {"retrieval_score"}

    def __init__(self, data_source_label: str):
        self.data_source_label = data_source_label
        self.parent_documents: List[Document] = []
        self.child_chunks: List[Document] = []
        self.parent_doc_map: Dict[str, Document] = {}

    def get_chunks(self) -> List[Document]:
        if self.child_chunks:
            return self.child_chunks
        self.parent_documents = self._load_parent_documents()
        self.parent_doc_map = {doc.id: doc for doc in self.parent_documents if doc.id is not None}
        self.child_chunks = self._create_child_chunks(self.parent_documents)
        return self.child_chunks

    @abstractmethod
    def _load_parent_documents(self) -> List[Document]:
        """Load top-level documents for this data source."""

    @abstractmethod
    def _create_child_chunks(self, parent_documents: List[Document]) -> List[Document]:
        """Split parents into chunk documents."""

    @abstractmethod
    def post_process_retrieval(self, retrieved_chunks: List[Document]) -> List[Document]:
        """Convert retrieved chunks back into final documents."""

    def _build_metadata(
        self,
        *,
        source: str,
        parent_id: Optional[str],
        dish_name: str,
        category: str,
        difficulty: str,
        is_dish_index: bool,
    ) -> Dict[str, Any]:
        metadata = StructuredMetadata(
            source=source,
            parent_id=parent_id,
            dish_name=dish_name,
            category=category,
            difficulty=difficulty,
            is_dish_index=is_dish_index,
            data_source=self.data_source_label,
        ).to_dict()
        return metadata

    def _clone_metadata(
        self,
        metadata: Dict[str, Any],
        *,
        parent_id: Optional[str] = None,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        cloned = {key: metadata[key] for key in self.REQUIRED_KEYS if key in metadata}
        if parent_id is not None:
            cloned["parent_id"] = parent_id
        if overrides:
            cloned.update(overrides)
        self._validate_metadata(cloned)
        return cloned

    def _create_document(self, *, doc_id: str, page_content: str, metadata: Dict[str, Any]) -> Document:
        self._validate_metadata(metadata)
        return Document(id=doc_id, page_content=page_content, metadata=metadata)

    @classmethod
    def _validate_metadata(cls, metadata: Dict[str, Any]) -> None:
        missing = [key for key in cls.REQUIRED_KEYS if key not in metadata]
        extra = [key for key in metadata.keys() if key not in cls.REQUIRED_KEYS]
        if missing or extra:
            raise ValueError(
                "Invalid metadata schema. Missing keys: "
                f"{missing}. Extra keys: {extra}."
            )
