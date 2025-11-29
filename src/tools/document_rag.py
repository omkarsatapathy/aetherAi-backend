"""Document RAG tool using LlamaIndex with Gemini 2.5 Flash and Context Caching."""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Settings,
    Document
)
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.llms.google_genai import GoogleGenAI as Gemini
from strands import tool
from ..config import Config
from ..logging_config import get_logger
import google.generativeai as genai
from google.generativeai import caching

logger = get_logger("chatbot.tools.document_rag")

# Global storage for RAG managers per session
_rag_managers: Dict[str, 'DocumentRAGManager'] = {}


class DocumentRAGManager:
    """Manages document indexing and querying for a specific session with Gemini context caching."""

    def __init__(self, session_id: str):
        """Initialize RAG manager for a session."""
        self.session_id = session_id
        self.vector_db_path = Path("vector_db") / session_id
        self.upload_dir = Path("uploads") / session_id
        self.index: Optional[VectorStoreIndex] = None
        self.cache: Optional[caching.CachedContent] = None
        self.cached_documents: list[Document] = []

        # Ensure directories exist
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # Get Gemini credentials and configuration
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        # Configure Gemini
        genai.configure(api_key=gemini_api_key)

        # Get configuration
        self.embedding_model = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")
        self.llm_model = os.getenv("GEMINI_MODEL_ID", "gemini-2.5-flash")
        self.cache_ttl = int(os.getenv("GEMINI_CACHE_TTL", "600"))  # 10 minutes default
        self.min_cache_tokens = int(os.getenv("GEMINI_MIN_CACHE_TOKENS", "1024"))

        # Configure LlamaIndex settings with Gemini
        Settings.embed_model = GeminiEmbedding(
            model_name=f"models/{self.embedding_model}",
            api_key=gemini_api_key
        )
        Settings.llm = Gemini(
            model=self.llm_model,
            api_key=gemini_api_key,
            temperature=0.1
        )

        logger.info(
            f"Initialized DocumentRAGManager with Gemini",
            extra={"extra_data": {
                "session_id": session_id,
                "vector_db_path": str(self.vector_db_path),
                "upload_dir": str(self.upload_dir),
                "embedding_model": self.embedding_model,
                "llm_model": self.llm_model,
                "cache_ttl": self.cache_ttl
            }}
        )

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using Gemini's tokenizer."""
        try:
            model = genai.GenerativeModel(self.llm_model)
            return model.count_tokens(text).total_tokens
        except Exception as e:
            logger.warning(
                f"Error counting tokens, estimating",
                extra={"extra_data": {"error": str(e)}}
            )
            # Rough estimation: 1 token ≈ 4 characters
            return len(text) // 4

    def _create_or_refresh_cache(self, documents: list[Document]) -> None:
        """Create or refresh Gemini context cache with document content."""
        try:
            # Combine all document text
            combined_text = "\n\n---\n\n".join([doc.text for doc in documents])
            token_count = self._count_tokens(combined_text)

            logger.info(
                f"Document token count",
                extra={"extra_data": {
                    "session_id": self.session_id,
                    "token_count": token_count,
                    "min_required": self.min_cache_tokens
                }}
            )

            # Only cache if above minimum token threshold
            if token_count < self.min_cache_tokens:
                logger.info(
                    f"Documents below minimum token threshold, skipping cache",
                    extra={"extra_data": {
                        "session_id": self.session_id,
                        "token_count": token_count
                    }}
                )
                self.cache = None
                return

            # Delete existing cache if present
            if self.cache:
                try:
                    self.cache.delete()
                    logger.info(
                        f"Deleted existing cache",
                        extra={"extra_data": {"session_id": self.session_id}}
                    )
                except Exception as e:
                    logger.warning(
                        f"Error deleting cache",
                        extra={"extra_data": {"error": str(e)}}
                    )

            # Create new cache
            self.cache = caching.CachedContent.create(
                model=self.llm_model,
                display_name=f"rag_cache_{self.session_id}",
                system_instruction=(
                    "You are a helpful AI assistant that answers questions based on the provided document context. "
                    "Always provide accurate answers from the documents. If the answer is not in the documents, "
                    "clearly state that you cannot find the information in the provided context."
                ),
                contents=[combined_text],
                ttl=timedelta(seconds=self.cache_ttl)
            )

            self.cached_documents = documents

            logger.info(
                f"Created context cache",
                extra={"extra_data": {
                    "session_id": self.session_id,
                    "cache_name": self.cache.name,
                    "token_count": token_count,
                    "ttl_seconds": self.cache_ttl,
                    "expire_time": self.cache.expire_time
                }}
            )

        except Exception as e:
            logger.error(
                f"Error creating context cache",
                extra={"extra_data": {
                    "session_id": self.session_id,
                    "error": str(e)
                }},
                exc_info=True
            )
            self.cache = None

    def load_existing_index(self) -> bool:
        """Load existing vector index if available."""
        try:
            if (self.vector_db_path / "docstore.json").exists():
                logger.info(
                    f"Loading existing vector index",
                    extra={"extra_data": {"session_id": self.session_id}}
                )
                storage_context = StorageContext.from_defaults(
                    persist_dir=str(self.vector_db_path)
                )
                self.index = load_index_from_storage(storage_context)

                # Reconstruct documents from index for caching
                documents = []
                for doc_id in self.index.docstore.docs:
                    doc = self.index.docstore.get_document(doc_id)
                    documents.append(doc)

                # Create cache with loaded documents
                if documents:
                    self._create_or_refresh_cache(documents)

                logger.info(
                    f"Successfully loaded existing index",
                    extra={"extra_data": {
                        "session_id": self.session_id,
                        "num_documents": len(documents)
                    }}
                )
                return True
            return False
        except Exception as e:
            logger.error(
                f"Error loading existing index",
                extra={"extra_data": {"session_id": self.session_id, "error": str(e)}},
                exc_info=True
            )
            return False

    def add_documents(self, file_paths: list[str]) -> Dict[str, Any]:
        """
        Add new documents to the index.

        Args:
            file_paths: List of file paths to add

        Returns:
            Status dictionary with success/error info
        """
        try:
            logger.info(
                f"Adding documents to index",
                extra={"extra_data": {
                    "session_id": self.session_id,
                    "num_files": len(file_paths)
                }}
            )

            # Load documents
            documents = []
            for file_path in file_paths:
                if not os.path.exists(file_path):
                    logger.warning(
                        f"File not found",
                        extra={"extra_data": {"file_path": file_path}}
                    )
                    continue

                # Use SimpleDirectoryReader for single file
                file_dir = os.path.dirname(file_path)
                filename = os.path.basename(file_path)

                reader = SimpleDirectoryReader(
                    input_dir=file_dir,
                    required_exts=[os.path.splitext(filename)[1]],
                    filename_as_id=True
                )
                docs = reader.load_data()
                documents.extend(docs)

                logger.debug(
                    f"Loaded document",
                    extra={"extra_data": {
                        "filename": filename,
                        "num_chunks": len(docs)
                    }}
                )

            if not documents:
                return {
                    "success": False,
                    "error": "No valid documents found to index"
                }

            # Create or update index
            if self.index is None:
                # Try to load existing index first
                if not self.load_existing_index():
                    # Create new index
                    logger.info(
                        f"Creating new vector index",
                        extra={"extra_data": {
                            "session_id": self.session_id,
                            "num_documents": len(documents)
                        }}
                    )
                    self.index = VectorStoreIndex.from_documents(documents)
                    # Create cache for new documents
                    self._create_or_refresh_cache(documents)
                else:
                    # Add to existing index
                    logger.info(
                        f"Adding to existing index",
                        extra={"extra_data": {
                            "session_id": self.session_id,
                            "num_new_documents": len(documents)
                        }}
                    )
                    for doc in documents:
                        self.index.insert(doc)
                    # Refresh cache with all documents
                    all_docs = self.cached_documents + documents
                    self._create_or_refresh_cache(all_docs)
            else:
                # Index already loaded, just insert new documents
                logger.info(
                    f"Inserting documents into loaded index",
                    extra={"extra_data": {
                        "session_id": self.session_id,
                        "num_new_documents": len(documents)
                    }}
                )
                for doc in documents:
                    self.index.insert(doc)
                # Refresh cache with all documents
                all_docs = self.cached_documents + documents
                self._create_or_refresh_cache(all_docs)

            # Persist index
            self.index.storage_context.persist(persist_dir=str(self.vector_db_path))

            logger.info(
                f"Successfully indexed documents",
                extra={"extra_data": {
                    "session_id": self.session_id,
                    "num_documents": len(documents),
                    "vector_db_path": str(self.vector_db_path),
                    "cache_active": self.cache is not None
                }}
            )

            # Delete the uploads directory after successful indexing
            try:
                if self.upload_dir.exists():
                    import shutil
                    shutil.rmtree(self.upload_dir)
                    logger.info(
                        f"Deleted upload directory after indexing",
                        extra={"extra_data": {
                            "session_id": self.session_id,
                            "upload_dir": str(self.upload_dir)
                        }}
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to delete upload directory",
                    extra={"extra_data": {
                        "session_id": self.session_id,
                        "upload_dir": str(self.upload_dir),
                        "error": str(e)
                    }}
                )

            return {
                "success": True,
                "num_documents": len(documents),
                "vector_db_path": str(self.vector_db_path),
                "cache_active": self.cache is not None
            }

        except Exception as e:
            logger.error(
                f"Error adding documents to index",
                extra={"extra_data": {
                    "session_id": self.session_id,
                    "error": str(e)
                }},
                exc_info=True
            )
            return {
                "success": False,
                "error": f"Failed to index documents: {str(e)}"
            }

    def _query_with_simple_prompt(self, query_text: str, document_text: str) -> str:
        """
        Query using simple prompt concatenation for small documents below cache threshold.

        Args:
            query_text: User's question
            document_text: Combined document text

        Returns:
            Answer string
        """
        try:
            model = genai.GenerativeModel(self.llm_model)

            prompt = f"""Based on the following document context, please answer the question.

Document Context:
{document_text}

Question: {query_text}

Answer the question using only the information provided in the document context. If the answer is not in the context, clearly state that you cannot find the information."""

            response = model.generate_content(prompt)
            return response.text

        except Exception as e:
            logger.error(
                f"Error in simple prompt query",
                extra={"extra_data": {
                    "session_id": self.session_id,
                    "error": str(e)
                }},
                exc_info=True
            )
            raise

    def query(self, query_text: str) -> Dict[str, Any]:
        """
        Query the document index using context caching or simple prompting.

        Args:
            query_text: The query string

        Returns:
            Query result dictionary
        """
        try:
            # Load index if not already loaded
            if self.index is None:
                if not self.load_existing_index():
                    return {
                        "success": False,
                        "error": "No documents have been indexed yet. Please upload a document first."
                    }

            logger.info(
                f"Querying document index",
                extra={"extra_data": {
                    "session_id": self.session_id,
                    "query": query_text,
                    "using_cache": self.cache is not None
                }}
            )

            # Check if we should use cached query or simple prompting
            if self.cache is not None:
                # Use cached content for query
                logger.info(
                    f"Using cached content for query",
                    extra={"extra_data": {"session_id": self.session_id}}
                )

                # Refresh cache TTL on each query
                try:
                    self.cache.update(ttl=timedelta(seconds=self.cache_ttl))
                    logger.debug(
                        f"Refreshed cache TTL",
                        extra={"extra_data": {"session_id": self.session_id}}
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to refresh cache TTL",
                        extra={"extra_data": {"error": str(e)}}
                    )

                # Query using cache
                model = genai.GenerativeModel.from_cached_content(cached_content=self.cache)
                response = model.generate_content(query_text)
                answer = response.text

                logger.info(
                    f"Cached query completed successfully",
                    extra={"extra_data": {
                        "session_id": self.session_id,
                        "response_length": len(answer)
                    }}
                )

                return {
                    "success": True,
                    "answer": answer,
                    "method": "cached",
                    "cache_name": self.cache.name
                }

            else:
                # Documents below cache threshold, use simple prompt
                logger.info(
                    f"Using simple prompt method (below cache threshold)",
                    extra={"extra_data": {"session_id": self.session_id}}
                )

                # Get all document text
                combined_text = "\n\n---\n\n".join([doc.text for doc in self.cached_documents])

                answer = self._query_with_simple_prompt(query_text, combined_text)

                logger.info(
                    f"Simple prompt query completed successfully",
                    extra={"extra_data": {
                        "session_id": self.session_id,
                        "response_length": len(answer)
                    }}
                )

                return {
                    "success": True,
                    "answer": answer,
                    "method": "simple_prompt"
                }

        except Exception as e:
            logger.error(
                f"Error querying document index",
                extra={"extra_data": {
                    "session_id": self.session_id,
                    "query": query_text,
                    "error": str(e)
                }},
                exc_info=True
            )
            return {
                "success": False,
                "error": f"Failed to query documents: {str(e)}"
            }


def get_rag_manager(session_id: str) -> DocumentRAGManager:
    """Get or create RAG manager for a session."""
    if session_id not in _rag_managers:
        _rag_managers[session_id] = DocumentRAGManager(session_id)
    return _rag_managers[session_id]


@tool
def query_documents(query: str, session_id: str) -> str:
    """
    Strands tool: Query uploaded documents for information using RAG with Gemini 2.5 Flash.

    This tool allows you to search through uploaded PDF and document files
    to find relevant information and answer questions based on the document content.
    Uses context caching for faster responses and cost savings.

    Use this tool when the user asks questions about their uploaded documents or
    wants to extract information from PDFs they've shared.

    Args:
        query: The question or search query about the documents
        session_id: The current chat session ID

    Returns:
        JSON string with the answer from the documents or error message
    """
    import json
    logger.info(
        f"query_documents tool called",
        extra={"extra_data": {
            "query": query,
            "session_id": session_id
        }}
    )

    try:
        rag_manager = get_rag_manager(session_id)
        result = rag_manager.query(query)

        if result["success"]:
            logger.info(
                f"Document query successful",
                extra={"extra_data": {
                    "session_id": session_id,
                    "query": query,
                    "method": result.get("method", "unknown")
                }}
            )
            return json.dumps({
                "answer": result["answer"],
                "method": result.get("method"),
                "cache_name": result.get("cache_name")
            })
        else:
            logger.warning(
                f"Document query failed",
                extra={"extra_data": {
                    "session_id": session_id,
                    "error": result.get("error")
                }}
            )
            return json.dumps({
                "error": result.get("error", "Unknown error occurred")
            })

    except Exception as e:
        logger.error(
            f"Unexpected error in query_documents tool",
            extra={"extra_data": {
                "session_id": session_id,
                "query": query,
                "error": str(e)
            }},
            exc_info=True
        )
        return json.dumps({
            "error": f"Failed to query documents: {str(e)}"
        })
