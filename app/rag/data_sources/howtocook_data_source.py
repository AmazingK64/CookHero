# app/rag/data_sources/howtocook_data_source.py
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document

from app.rag.data_sources.base import BaseDataSource

logger = logging.getLogger(__name__)

# A specific namespace for generating document IDs
DOC_NAMESPACE = uuid.UUID('7a7de5f8-7435-4354-9b1b-d50a09848520')

class HowToCookDataSource(BaseDataSource):
    """
    Data source for loading and processing recipes from the HowToCook repository.
    """
    CATEGORY_MAPPING = {
        'meat_dish': '荤菜',
        'vegetable_dish': '素菜',
        'soup': '汤品',
        'dessert': '甜品',
        'breakfast': '早餐',
        'staple': '主食',
        'aquatic': '水产',
        'condiment': '调料',
        'drink': '饮品',
        'semi-finished': '半成品',
    }

    def __init__(self, data_path: str, headers_to_split_on: list):
        super().__init__(data_source_label="recipes")
        self.data_path = Path(data_path)
        self.headers_to_split_on = headers_to_split_on

    def get_chunks(self) -> List[Document]:
        """
        Loads documents, processes them, and returns the final chunks for indexing.
        """
        logger.info(f"Loading and processing data from HowToCook source: {self.data_path}")
        chunks = super().get_chunks()
        self._save_debug_files(self.parent_documents, chunks)
        logger.info(
            "Processing complete. Found %d documents and created %d chunks.",
            len(self.parent_documents),
            len(chunks),
        )
        return chunks

    def post_process_retrieval(self, retrieved_chunks: List[Document]) -> List[Document]:
        """
        Converts retrieved child chunks back to their full parent documents.
        This implements the "small to large" retrieval pattern.
        Preserves the highest retrieval score from child chunks to parent documents.
        Special handling for dish index chunks: returns the index document as-is.
        """
        if not self.parent_doc_map:
            logger.warning("Parent document map not loaded for recipes. Loading now.")
            self.parent_documents = self._load_parent_documents()
            self.parent_doc_map = {doc.id: doc for doc in self.parent_documents if doc.id is not None}

        # Check if any retrieved chunks are from the dish index
        index_chunks = [chunk for chunk in retrieved_chunks if chunk.metadata.get("is_dish_index")]
        regular_chunks = [chunk for chunk in retrieved_chunks if not chunk.metadata.get("is_dish_index")]
        
        final_docs = []
        
        # Handle dish index chunks separately - return the index document as-is
        if index_chunks:
            # Get the highest score from index chunks
            max_index_score = max(
                (chunk.metadata.get("retrieval_score", 0.0) for chunk in index_chunks),
                default=0.0
            )
            # Find the index document
            index_doc_id = index_chunks[0].metadata.get("parent_id")
            if index_doc_id and index_doc_id in self.parent_doc_map:
                index_doc = self.parent_doc_map[index_doc_id]
                # Create a copy with the score
                index_doc_copy = Document(
                    id=index_doc.id,
                    page_content=index_doc.page_content,
                    metadata=index_doc.metadata.copy()
                )
                index_doc_copy.metadata['retrieval_score'] = max_index_score
                final_docs.append(index_doc_copy)
                logger.info(f"Retrieved dish index document with score {max_index_score:.4f}")

        # Handle regular chunks: group by parent_id and find the highest score for each parent
        parent_scores = {}
        for chunk in regular_chunks:
            parent_id = chunk.metadata.get("parent_id")
            if parent_id:
                score = chunk.metadata.get("retrieval_score", 0.0)
                if parent_id not in parent_scores or score > parent_scores[parent_id]:
                    parent_scores[parent_id] = score

        # Get parent documents and set their retrieval scores
        for parent_id, max_score in parent_scores.items():
            if parent_id in self.parent_doc_map:
                parent_doc = self.parent_doc_map[parent_id]
                if parent_doc.metadata.get("is_dish_index"):
                    continue
                # Create a copy to avoid modifying the original
                parent_doc = Document(
                    id=parent_doc.id,
                    page_content=parent_doc.page_content,
                    metadata=parent_doc.metadata.copy()
                )
                parent_doc.metadata['retrieval_score'] = max_score
                final_docs.append(parent_doc)
        
        logger.info(f"Retrieved {len(retrieved_chunks)} chunks ({len(index_chunks)} index, {len(regular_chunks)} regular), "
                    f"corresponding to {len(final_docs)} unique parent documents.")
        return final_docs

    def _load_parent_documents(self) -> List[Document]:
        """Loads all markdown files as 'parent' documents."""
        documents: List[Document] = []
        dishes_by_category: Dict[str, List[str]] = {}
        dishes_by_difficulty: Dict[str, List[str]] = {}
        dishes_by_mixed: Dict[Tuple[str, str], List[str]] = {}

        for md_file in self.data_path.rglob("*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                doc_id = str(uuid.uuid5(DOC_NAMESPACE, str(md_file)))
                dish_name, category, difficulty = self._extract_recipe_metadata(md_file, content)
                metadata = self._build_metadata(
                    source=str(md_file),
                    parent_id=None,
                    dish_name=dish_name,
                    category=category,
                    difficulty=difficulty,
                    is_dish_index=False,
                )
                doc = self._create_document(doc_id=doc_id, page_content=content, metadata=metadata)
                documents.append(doc)

                dishes_by_category.setdefault(category, []).append(dish_name)
                dishes_by_difficulty.setdefault(difficulty, []).append(dish_name)
                dishes_by_mixed.setdefault((category, difficulty), []).append(dish_name)
            except Exception as e:
                logger.warning(f"Failed to read file {md_file}: {e}")
        
        # Create multiple dish index documents:
        #  - one overall index
        #  - one index per category
        #  - one index per difficulty
        #  - one index per (category, difficulty) combination
        index_docs = []
        overall_index = self._create_dish_index_document(
            dishes_by_category=dishes_by_category,
            dishes_by_difficulty=dishes_by_difficulty,
        )
        if overall_index:
            index_docs.append(overall_index)

        for category, names in dishes_by_category.items():
            doc = self._create_single_index_doc(
                key_type="category",
                key_value=category,
                dish_list=sorted(set(names)),
            )
            if doc:
                index_docs.append(doc)

        for difficulty, names in dishes_by_difficulty.items():
            doc = self._create_single_index_doc(
                key_type="difficulty",
                key_value=difficulty,
                dish_list=sorted(set(names)),
            )
            if doc:
                index_docs.append(doc)

        # for (category, difficulty), names in dishes_by_mixed.items():
        #     doc = self._create_single_index_doc(
        #         key_type="category_difficulty",
        #         key_value=f"{category}::{difficulty}",
        #         dish_list=sorted(set(names)),
        #     )
        #     if doc:
        #         index_docs.append(doc)

        for idx in index_docs:
            documents.append(idx)
        logger.info(f"Created {len(index_docs)} dish index documents (overall + per-metadata indices)")
        
        return documents
    
    def _create_dish_index_document(
        self,
        dishes_by_category: Dict[str, List[str]],
        dishes_by_difficulty: Dict[str, List[str]],
    ) -> Document | None:
        if not dishes_by_category and not dishes_by_difficulty:
            return None
        """
        Creates a special index document containing all dish names organized by
        multiple metadata axes: category, dish_name and difficulty. This document
        will be used for recommendation queries and will also carry metadata keys
        that _create_index_chunk_content expects (e.g. 'categories', 'total_dishes').
        """

        # Build the index content with multiple sections
        content_parts = ["# 菜谱索引\n\n"]
        content_parts.append("本索引包含所有可用的菜谱名称，按多种元数据组织（类别、菜名、难度）。\n\n")

        # Add dishes by category
        content_parts.append("## 按类别分类\n\n")
        for category in sorted(dishes_by_category.keys()):
            dishes = sorted(set(dishes_by_category[category]))
            content_parts.append(f"### {category}\n\n")
            content_parts.append("菜谱列表：")
            content_parts.append("、".join(dishes))
            content_parts.append("\n\n")

        # Add dishes by difficulty
        content_parts.append("## 按难度分类\n\n")
        for diff in sorted(dishes_by_difficulty.keys()):
            dishes = sorted(set(dishes_by_difficulty[diff]))
            content_parts.append(f"### {diff}\n\n")
            content_parts.append("菜谱列表：")
            content_parts.append("、".join(dishes))
            content_parts.append("\n\n")

        # Add a global summary section
        content_parts.append("## 所有菜谱\n\n")

        all_dishes = []
        for dishes in dishes_by_category.values():
            all_dishes.extend(dishes)
        unique_all = sorted(set(all_dishes))
        content_parts.append("推荐菜，菜谱列表，所有菜谱：")
        content_parts.append("、".join(unique_all))
        content_parts.append("\n")

        index_content = "".join(content_parts)

        # Generate a special ID for the index document
        index_id = str(uuid.uuid5(DOC_NAMESPACE, "dish_index"))
        metadata = self._build_metadata(
            source="dish_index::all",
            parent_id=None,
            dish_name="菜谱索引",
            category="索引",
            difficulty="未知",
            is_dish_index=True,
        )

        return self._create_document(
            doc_id=index_id,
            page_content=index_content,
            metadata=metadata,
        )

    def _create_single_index_doc(self, key_type: str, key_value: str, dish_list: List[str]) -> Document | None:
        """
        Create a single index document for a specific metadata value.
        key_type: one of 'category', 'difficulty', 'dish_name'
        key_value: the value for that key (e.g. '甜品')
        dish_list: list of dish names belonging to this key
        """

        title = f"菜谱索引 - {key_value}"
        content = "、".join(dish_list)

        if not dish_list:
            return None

        category_value = "索引"
        difficulty_value = "未知"
        if key_type == "category":
            category_value = key_value
        elif key_type == "difficulty":
            difficulty_value = key_value
        elif key_type == "category_difficulty":
            category_value, difficulty_value = key_value.split("::")

        index_content = f"{title}\n\n" + content
        index_id = str(uuid.uuid5(DOC_NAMESPACE, f"dish_index::{key_type}::{key_value}"))
        metadata = self._build_metadata(
            source=f"dish_index::{key_type}",
            parent_id=None,
            dish_name="菜谱索引",
            category=category_value,
            difficulty=difficulty_value,
            is_dish_index=True,
        )
        return self._create_document(doc_id=index_id, page_content=index_content, metadata=metadata)

    def _extract_recipe_metadata(self, file_path: Path, content: str) -> Tuple[str, str, str]:
        category = '其他'
        for key, value in self.CATEGORY_MAPPING.items():
            if key in file_path.parts:
                category = value
                break

        dish_name = file_path.stem

        if '★★★★★' in content:
            difficulty = '非常困难'
        elif '★★★★' in content:
            difficulty = '困难'
        elif '★★★' in content:
            difficulty = '中等'
        elif '★★' in content:
            difficulty = '简单'
        elif '★' in content:
            difficulty = '非常简单'
        else:
            difficulty = '未知'

        return dish_name, category, difficulty

    def _create_child_chunks(self, parent_documents: List[Document]) -> List[Document]:
        """Splits documents into smaller chunks."""
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            strip_headers=False,
        )
        all_chunks: List[Document] = []

        for doc in parent_documents:
            if doc.metadata.get("is_dish_index"):
                chunk_content = self._create_index_chunk_content(doc.metadata)
                chunk_metadata = self._clone_metadata(doc.metadata, parent_id=doc.id)
                chunk = self._create_document(
                    doc_id=str(uuid.uuid4()),
                    page_content=chunk_content,
                    metadata=chunk_metadata,
                )
                all_chunks.append(chunk)
                continue

            md_chunks = markdown_splitter.split_text(doc.page_content)
            for chunk_doc in md_chunks:
                chunk_metadata = self._clone_metadata(doc.metadata, parent_id=doc.id)
                chunk = self._create_document(
                    doc_id=str(uuid.uuid4()),
                    page_content=chunk_doc.page_content,
                    metadata=chunk_metadata,
                )
                all_chunks.append(chunk)
        return all_chunks
    
    def _create_index_chunk_content(self, index_metadata: Dict[str, Any]) -> str:
        """
        Creates chunk content for the dish index that focuses on recommendation keywords
        without including actual dish names. This improves semantic matching for 
        recommendation queries.
        """

        content_parts = ["推荐菜,菜谱列表,菜品,食谱,有哪些菜品推荐"]
        source = index_metadata.get("source", "")
        category = index_metadata.get("category", "")
        difficulty = index_metadata.get("difficulty", "")

        if source.startswith("dish_index::category") and category:
            content_parts.append(f"{category}推荐，")
        elif source.startswith("dish_index::difficulty") and difficulty:
            content_parts.append(f"{difficulty}难度推荐，")
        elif source.startswith("dish_index::category_difficulty"):
            if category:
                content_parts.append(f"{category}类别，")
            if difficulty:
                content_parts.append(f"{difficulty}难度推荐，")

        content_parts.append("欢迎根据口味挑选合适的菜谱")
        return "".join(content_parts)

    def _save_debug_files(self, parent_docs: List[Document], child_chunks: List[Document]):
        """Saves documents to jsonl files for debugging."""
        debug_path = Path("data/debug")
        debug_path.mkdir(exist_ok=True)
        
        logger.info(f"Saving debug files to {debug_path}...")
        with open(debug_path / "parent_documents.jsonl", "w", encoding="utf-8") as f:
            for doc in parent_docs:
                f.write(doc.model_dump_json(exclude_unset=True) + "\n")
        with open(debug_path / "child_chunks.jsonl", "w", encoding="utf-8") as f:
            for chunk in child_chunks:
                f.write(chunk.model_dump_json(exclude_unset=True) + "\n")
