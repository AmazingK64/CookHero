import logging
from typing import List
from pymilvus import utility, connections
from langchain_milvus import Milvus
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.rag.config import RAGConfig

logger = logging.getLogger(__name__)

class IndexConstructionModule:
    """
    Handles the creation and connection to the Milvus vector store using LangChain's abstractions.
    """
    def __init__(self, config: RAGConfig):
        """
        Initializes the index construction module.
        Args:
            config: The RAG configuration object.
        """
        self.config = config
        self.embeddings: Embeddings = self._init_embeddings()
        self.vectorstore: Milvus | None = None

    def _init_embeddings(self) -> Embeddings:
        """Initializes the embedding model based on the configuration."""
        if self.config.EMBEDDING_MODE == 'local':
            from langchain_huggingface import HuggingFaceEmbeddings
            logger.info(f"Initializing local embedding model: {self.config.LOCAL_EMBEDDING_MODEL}")
            return HuggingFaceEmbeddings(
                model_name=self.config.LOCAL_EMBEDDING_MODEL,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
        elif self.config.EMBEDDING_MODE == 'remote':
            from langchain_openai import OpenAIEmbeddings
            logger.info(f"Initializing remote embedding model: {self.config.REMOTE_EMBEDDING_MODEL}")
            if not self.config.EMBEDDING_API_KEY or self.config.EMBEDDING_API_KEY == "None":
                raise ValueError("EMBEDDING_API_KEY must be set in config for remote embedding mode.")
            
            return OpenAIEmbeddings(
                model=self.config.REMOTE_EMBEDDING_MODEL,
                api_key=self.config.EMBEDDING_API_KEY, # type: ignore
                base_url=self.config.EMBEDDING_API_URL,
                chunk_size=self.config.EMBEDDING_BATCH_SIZE,
            )
        else:
            raise ValueError(f"Invalid EMBEDDING_MODE: {self.config.EMBEDDING_MODE}")

    def build_or_connect_index(self, chunks: List[Document], force_rebuild: bool = False):
        """
        Connects to the Milvus collection, creating it if it doesn't exist.
        Relies on LangChain's Milvus class to handle schema creation.
        """
        collection_name = self.config.MILVUS_COLLECTION_NAME
        connection_args = {"host": self.config.MILVUS_HOST, "port": self.config.MILVUS_PORT}
        alias = "default"

        logger.info(f"Managing Milvus connection at {connection_args['host']}:{connection_args['port']}")
        
        try:
            connections.connect(alias=alias, **connection_args)
            if force_rebuild and utility.has_collection(collection_name, using=alias):
                logger.warning(f"Dropping existing Milvus collection: {collection_name}")
                _=utility.drop_collection(collection_name, using=alias)
            
            collection_exists = utility.has_collection(collection_name, using=alias)
        finally:
            if connections.has_connection(alias):
                connections.disconnect(alias)
                logger.info(f"Disconnected from Milvus alias '{alias}' used for pre-flight checks.")

        if not collection_exists:
            logger.info(f"Milvus collection '{collection_name}' not found. Creating via LangChain...")
            if not chunks:
                raise ValueError("Cannot build a new collection from an empty list of chunks.")

            self.vectorstore = Milvus.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                collection_name=collection_name,
                connection_args=connection_args,
                # Explicitly define field names for LangChain to use
                text_field="text",
                vector_field="embedding",
            )
            logger.info(f"Successfully created and populated Milvus collection: {collection_name}")
        else:
            logger.info(f"Connecting to existing Milvus collection: {collection_name}")
            self.vectorstore = Milvus(
                embedding_function=self.embeddings,
                collection_name=collection_name,
                connection_args=connection_args,
                text_field="text",
                vector_field="embedding",
            )
            logger.info(f"Successfully connected to Milvus collection: {collection_name}")

    def get_vectorstore(self) -> Milvus:
        if not self.vectorstore:
            raise ValueError("Vectorstore has not been built or connected.")
        return self.vectorstore
