# app/rag/data_sources/generic_text_data_source.py
import logging
import uuid
from pathlib import Path
from typing import List

from langchain_core.documents import Document

# Note: This implementation requires the 'llama-index' package.
# Please install it using: pip install llama-index
try:
    from llama_index.core.node_parser import SentenceWindowNodeParser
    from llama_index.core import Document as LlamaDocument
except ImportError:
    raise ImportError(
        "LlamaIndex is not installed. Please install it with 'pip install llama-index' to use the GenericTextDataSource."
    )

from app.rag.data_sources.base import BaseDataSource

logger = logging.getLogger(__name__)

DOC_NAMESPACE = uuid.UUID('7a7de5f8-7435-4354-9b1b-d50a09848520')


class GenericTextDataSource(BaseDataSource):
    """
    Data source for handling arbitrary text files using a Sentence Window Indexing strategy.
    """

    def __init__(self, data_path: str, window_size: int, **kwargs):
        super().__init__(data_source_label="generic_text")
        self.data_path = Path(data_path)
        self.window_size = window_size

    def get_chunks(self) -> List[Document]:
        logger.info(f"Loading and processing data from Generic Text source: {self.data_path}")
        chunks = super().get_chunks()
        logger.info(
            "Processing complete. Found %d text documents and created %d chunks.",
            len(self.parent_documents),
            len(chunks),
        )
        return chunks

    def post_process_retrieval(self, retrieved_chunks: List[Document]) -> List[Document]:
        """
        For sentence window indexing, the retrieved chunks (sentences) are what we need.
        The actual context assembly happens in the RAGService using the 'window' metadata.
        This method can simply return the chunks as is.
        """
        return retrieved_chunks

    def _load_parent_documents(self) -> List[Document]:
        documents: List[Document] = []
        base_path = Path(self.data_path)

        if not base_path.exists():
            logger.warning(
                "Data path for generic_text does not exist: %s. No documents will be loaded.",
                base_path,
            )
            base_path.mkdir(parents=True, exist_ok=True)
            return documents

        for file_path in base_path.glob("**/*.txt"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                doc_id = str(uuid.uuid5(DOC_NAMESPACE, str(file_path)))
                metadata = self._build_metadata(
                    source=str(file_path),
                    parent_id=None,
                    dish_name=file_path.stem,
                    category="Text",
                    difficulty="未知",
                    is_dish_index=False,
                )
                documents.append(
                    self._create_document(doc_id=doc_id, page_content=text, metadata=metadata)
                )
            except Exception as e:
                logger.error(f"Error loading file {file_path}: {e}")
        logger.info(f"Loaded {len(documents)} text documents from {self.data_path}")
        return documents

    def _create_child_chunks(self, parent_documents: List[Document]) -> List[Document]:
        if not parent_documents:
            return []

        logger.info(
            "Splitting documents using Sentence Window strategy with window size: %d",
            self.window_size,
        )
        parser = SentenceWindowNodeParser.from_defaults(
            window_size=self.window_size,
            window_metadata_key="window",
            original_text_metadata_key="original_text",
        )

        all_chunks: List[Document] = []
        for doc in parent_documents:
            llama_doc = LlamaDocument(text=doc.page_content, metadata={})
            nodes = parser.get_nodes_from_documents([llama_doc])

            for node in nodes:
                window_text = node.metadata.get("window") or node.get_content()
                chunk_metadata = self._clone_metadata(doc.metadata, parent_id=doc.id)
                chunk = self._create_document(
                    doc_id=str(uuid.uuid4()),
                    page_content=window_text,
                    metadata=chunk_metadata,
                )
                all_chunks.append(chunk)

        logger.info(
            "Split %d documents into %d sentence chunks.",
            len(parent_documents),
            len(all_chunks),
        )
        return all_chunks
