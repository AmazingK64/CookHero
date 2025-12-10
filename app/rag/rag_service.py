# app/rag/rag_service.py
import logging
from pathlib import Path
from typing import Dict

from app.core.config_loader import DefaultRAGConfig
from app.core.rag_config import RAGConfig
from app.rag.data_sources.base import BaseDataSource
from app.rag.data_sources.howtocook_data_source import HowToCookDataSource
from app.rag.data_sources.tips_data_source import TipsDataSource
from app.rag.data_sources.generic_text_data_source import GenericTextDataSource
from app.rag.embeddings.embedding_factory import get_embedding_model
from app.rag.vector_stores.vector_store_factory import get_vector_store
from app.rag.pipeline.retrieval import RetrievalOptimizationModule
from app.rag.pipeline.generation import GenerationIntegrationModule
from app.rag.pipeline.metadata_filter import MetadataFilterExtractor
from app.rag.pipeline.workflow import (
    ContextBuilder,
    DocumentPostProcessor,
    QueryPlanner,
    RetrievalExecutor,
    ResponseGenerator,
)
from app.rag.rerankers.base import BaseReranker
from app.rag.cache import CacheManager

logger = logging.getLogger(__name__)


class RAGService:
    """
    Orchestrates the entire RAG pipeline, supporting multiple data sources
    and query routing.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RAGService, cls).__new__(cls)
        return cls._instance

    def __init__(self, config: RAGConfig | None = None):
        if hasattr(self, '_initialized') and self._initialized:
            return

        logger.info("Initializing RAGService for the first time...")
        self.config = config or DefaultRAGConfig
        
        self.data_sources: Dict[str, BaseDataSource] = {}
        self.retrieval_modules: Dict[str, RetrievalOptimizationModule] = {}
        self.reranker: BaseReranker | None = None
        self.metadata_catalog: Dict[str, Dict[str, list[str]]] = {}

        self._load_knowledge_bases()

        self.generation_module = GenerationIntegrationModule(
            model_name=self.config.llm.model_name,
            temperature=self.config.llm.temperature,
            max_tokens=self.config.llm.max_tokens,
            api_key=self.config.llm.api_key,  # type: ignore
            base_url=self.config.llm.base_url
        )

        self.metadata_filter_extractor = MetadataFilterExtractor(
            model_name=self.config.llm.model_name,
            max_tokens=self.config.llm.max_tokens,
            api_key=self.config.llm.api_key,  # type: ignore
            base_url=self.config.llm.base_url
        )

        if self.config.reranker.enabled:
            if self.config.reranker.type == "siliconflow":
                from app.rag.rerankers.siliconflow_reranker import SiliconFlowReranker
                self.reranker = SiliconFlowReranker(self.config.reranker)
                logger.info("SiliconFlow Reranker initialized.")
            else:
                logger.warning(f"Reranker type '{self.config.reranker.type}' not recognized. Reranking disabled.")

        # Initialize cache manager if enabled
        self.cache_manager: CacheManager | None = None
        if self.config.cache.enabled:
            embeddings = get_embedding_model(self.config)
            self.cache_manager = CacheManager(
                redis_host=self.config.cache.redis_host,
                redis_port=self.config.cache.redis_port,
                redis_db=self.config.cache.redis_db,
                redis_password=self.config.cache.redis_password,
                retrieval_ttl=self.config.cache.retrieval_ttl,
                response_ttl=self.config.cache.response_ttl,
                similarity_threshold=self.config.cache.similarity_threshold,
                embeddings=embeddings,
                l2_enabled=self.config.cache.l2_enabled
            )
            logger.info("Cache manager initialized.")
        else:
            logger.info("Caching is disabled.")

        self._query_planner = QueryPlanner(
            generation_module=self.generation_module,
            metadata_filter_extractor=self.metadata_filter_extractor,
            cache_manager=self.cache_manager,
        )
        self._retrieval_executor = RetrievalExecutor(
            retrieval_modules=self.retrieval_modules,
            cache_manager=self.cache_manager,
        )
        self._post_processor = DocumentPostProcessor(self.data_sources)
        self._context_builder = ContextBuilder()
        self._response_generator = ResponseGenerator(
            generation_module=self.generation_module,
            cache_manager=self.cache_manager,
        )

        self._initialized = True
        logger.info("RAGService initialized successfully with multiple knowledge bases.")

    def _load_knowledge_bases(self):
        """
        Loads data, creates embeddings, and sets up retrievers for all configured sources.
        """
        logger.info("Loading all knowledge bases...")
        embeddings = get_embedding_model(self.config)

        # Define the mapping from source name to class and config
        source_definitions = {
            "recipes": (HowToCookDataSource, self.config.data_source.howtocook),
            "tips": (TipsDataSource, self.config.data_source.tips),
            "generic_text": (GenericTextDataSource, self.config.data_source.generic_text),
        }

        for name, (source_class, source_config) in source_definitions.items():
            logger.info(f"--- Loading source: {name} ---")
            
            # 1. Instantiate Data Source
            data_path = Path(self.config.paths.base_data_path) / source_config.path_suffix
            
            init_params = {"data_path": str(data_path)}
            if hasattr(source_config, 'window_size'):
                init_params['window_size'] = source_config.window_size
            if hasattr(source_config, 'headers_to_split_on'):
                init_params['headers_to_split_on'] = source_config.headers_to_split_on

            data_source = source_class(**init_params)

            child_chunks = data_source.get_chunks()
            self.data_sources[name] = data_source
            self.metadata_catalog[name] = self._build_metadata_catalog(child_chunks)
            
            # Add a check to skip empty data sources
            if not child_chunks:
                logger.warning(f"Source '{name}' yielded no chunks. Skipping vector store and retrieval module setup.")
                continue

            # 2. Get Collection Name
            collection_name = self.config.vector_store.collection_names.get(name)
            if not collection_name:
                logger.error(f"Collection for source '{name}' not in config. Skipping.")
                continue

            # 3. Get Vector Store instance
            vector_store = get_vector_store(
                vs_config=self.config.vector_store,
                collection_name=collection_name,
                embeddings=embeddings,
                chunks=child_chunks,
                force_rebuild=False
            )
            
            # 4. Create and store Retrieval Module
            retrieval_module = RetrievalOptimizationModule(
                vectorstore=vector_store,
                child_chunks=child_chunks,
                score_threshold=self.config.retrieval.score_threshold,
                default_ranker_type=self.config.retrieval.ranker_type,
                default_ranker_weights=self.config.retrieval.ranker_weights
            )
            self.retrieval_modules[name] = retrieval_module
            logger.info(f"--- Source '{name}' loaded successfully. ---")

    def ask(self, query: str, stream: bool = False, use_intelligent_ranker: bool = True):
        """
        Main method to ask a question. It fetches from all data sources in parallel,
        then reranks the aggregated results to generate a response.
        """
        if not all([self.retrieval_modules, self.generation_module, self.data_sources]):
            raise RuntimeError("RAG Service is not properly initialized.")

        plan = self._query_planner.prepare(query, self.metadata_catalog)
        if plan.cached_response is not None:
            return plan.cached_response

        retrieval_top_k = self.config.retrieval.top_k
        all_retrieved_docs = self._retrieval_executor.retrieve(
            plan.rewritten_query,
            retrieval_top_k,
            use_intelligent_ranker,
            plan.metadata_expression,
        )

        reranked_docs = self._rerank_if_needed(plan.rewritten_query, all_retrieved_docs)
        processed_docs = self._post_processor.process(reranked_docs)
        context_parts = self._context_builder.build(processed_docs)
        return self._response_generator.generate(plan.rewritten_query, context_parts, stream)

    # --- Helper methods ---

    def _rerank_if_needed(self, rewritten_query: str, docs_for_rerank):
        if self.reranker and self.config.reranker.enabled:
            logger.info(f"Reranking {len(docs_for_rerank)} documents...")
            return self.reranker.rerank(rewritten_query, docs_for_rerank)
        return docs_for_rerank

    def _build_metadata_catalog(self, chunks: list) -> Dict[str, list[str]]:
        catalog: Dict[str, set[str]] = {}
        for doc in chunks:
            meta = getattr(doc, "metadata", {}) or {}
            for k, v in meta.items():
                if k not in ["category", "dish_name", "difficulty"]:
                    continue
                if v is None:
                    continue
                if isinstance(v, (str, int, float)):
                    catalog.setdefault(k, set()).add(str(v))
        res =  {k: sorted(list(vals)) for k, vals in catalog.items()}
        return res

# Instantiate the singleton service
rag_service_instance = RAGService()
