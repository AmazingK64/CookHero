# app/rag/data_sources/generic_text_data_source.py
import logging
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


class GenericTextDataSource(BaseDataSource):
    """
    Data source for handling arbitrary text files using a Sentence Window Indexing strategy.
    """

    def __init__(self, data_path: str, window_size: int, **kwargs):
        self.data_path = Path(data_path)
        self.window_size = window_size

    def get_chunks(self) -> List[Document]:
        """
        Loads, processes, and chunks documents from the data source.
        """
        documents = self._load_data()
        return self._split_chunks(documents)

    def post_process_retrieval(self, retrieved_chunks: List[Document]) -> List[Document]:
        """
        For sentence window indexing, the retrieved chunks (sentences) are what we need.
        The actual context assembly happens in the RAGService using the 'window' metadata.
        This method can simply return the chunks as is.
        """
        return retrieved_chunks

    def _load_data(self) -> List[Document]:
        """
        Loads all .txt files from the specified data path, including subdirectories.
        """
        documents = []
        base_path = Path(self.data_path)
        
        if not base_path.exists():
            logger.warning(f"Data path for generic_text does not exist: {base_path}. No documents will be loaded.")
            base_path.mkdir(parents=True, exist_ok=True)
            return documents

        for file_path in base_path.glob("**/*.txt"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                documents.append(
                    Document(
                        page_content=text,
                        metadata={"source": str(file_path)},
                    )
                )
            except Exception as e:
                logger.error(f"Error loading file {file_path}: {e}")
        logger.info(f"Loaded {len(documents)} text documents from {self.data_path}")
        return documents

    def _split_chunks(self, documents: List[Document]) -> List[Document]:
        """
        Splits documents into sentence chunks using the SentenceWindowNodeParser.
        The context window is stored in the metadata of each chunk.
        """
        if not documents:
            return []
            
        logger.info(f"Splitting documents using Sentence Window strategy with window size: {self.window_size}")

        parser = SentenceWindowNodeParser.from_defaults(
            window_size=self.window_size,
            window_metadata_key="window",
            original_text_metadata_key="original_text",
        )

        all_chunks = []
        for doc in documents:
            llama_doc = LlamaDocument(text=doc.page_content, metadata=doc.metadata)
            nodes = parser.get_nodes_from_documents([llama_doc])

            for node in nodes:
                chunk = Document(page_content=node.get_content(), metadata=node.metadata)
                all_chunks.append(chunk)

        logger.info(f"Split {len(documents)} documents into {len(all_chunks)} sentence chunks.")
        return all_chunks
