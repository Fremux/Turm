"""Qdrant service for vector storage and retrieval using Chonkie."""

import hashlib
import csv
import io
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal

from chonkie import TokenChunker, SentenceChunker, RecursiveChunker, SemanticChunker, SlumberChunker
from chonkie.genie import OpenAIGenie
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from app.core.config import settings
from app.core.logging import logger
from app.services.deepinfra_embeddings import deepinfra_embeddings

# Type for chunker selection
ChunkerType = Literal["token", "sentence", "recursive", "semantic", "slumber"]

# Qdrant has a 1024 character limit per payload field value (gRPC Value constraint)
# Embedding APIs also have input length limits (typically ~512-8192 chars)
# We use a conservative limit to satisfy both constraints
MAX_QDRANT_FIELD_LENGTH = 512  # Safe for both Qdrant (1024 limit) and most embedding APIs


class QdrantService:
    """Service for managing document storage and retrieval in Qdrant using Chonkie.
    
    Note: Multiple constraints apply:
    - Qdrant enforces a 1024 character limit per payload field value
    - Embedding APIs have input length limits (varies by model, typically 512-8192 chars)
    - Long chunk texts are automatically truncated to MAX_QDRANT_FIELD_LENGTH (512 chars)
    - Original length is preserved in metadata
    """
    
    def __init__(self):
        """Initialize Qdrant client."""
        # Initialize Qdrant client
        self.client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
        )
        
        # Default collection name (can be overridden)
        self.default_collection_name = settings.QDRANT_COLLECTION
        self.default_embedding_model = settings.EMBEDDING_MODEL
        self.default_embedding_dimension = settings.EMBEDDING_DIMENSION
        
        # Use DeepInfra embeddings
        self.embeddings = deepinfra_embeddings
        
        logger.info(
            "qdrant_service_initialized",
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            default_collection=self.default_collection_name,
            embedding_model=self.default_embedding_model,
            embedding_dimension=self.default_embedding_dimension
        )
    
    def list_collections(self) -> List[Dict[str, Any]]:
        """List all collections with their details.
        
        Returns:
            List of collections with metadata
        """
        try:
            collections = self.client.get_collections().collections
            
            result = []
            for col in collections:
                # Get collection info
                col_info = self.client.get_collection(col.name)
                
                result.append({
                    "name": col.name,
                    "vectors_count": col_info.points_count,
                    "vector_size": col_info.config.params.vectors.size if hasattr(col_info.config.params, 'vectors') else 0,
                })
            
            return result
        except Exception as e:
            logger.error("list_collections_error", error=str(e), exc_info=True)
            raise
    
    def create_collection(
        self,
        collection_name: str,
        embedding_size: int,
        distance: str = "Cosine"
    ) -> Dict[str, Any]:
        """Create a new collection.
        
        Args:
            collection_name: Name of the collection
            embedding_size: Dimension of embeddings
            distance: Distance metric (Cosine, Euclid, Dot)
            
        Returns:
            Dict with creation result
        """
        try:
            # Map distance string to Distance enum
            distance_map = {
                "Cosine": Distance.COSINE,
                "Euclid": Distance.EUCLID,
                "Dot": Distance.DOT,
            }
            
            distance_metric = distance_map.get(distance, Distance.COSINE)
            
            # Check if collection already exists
            collections = self.client.get_collections().collections
            if collection_name in [col.name for col in collections]:
                raise ValueError(f"Collection '{collection_name}' already exists")
            
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=embedding_size,
                    distance=distance_metric
                )
            )
            
            logger.info("collection_created", collection=collection_name, size=embedding_size)
            
            return {
                "collection_name": collection_name,
                "embedding_size": embedding_size,
                "distance": distance,
                "status": "created"
            }
        except Exception as e:
            logger.error("create_collection_error", error=str(e), collection=collection_name, exc_info=True)
            raise
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection.
        
        Args:
            collection_name: Name of the collection to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            self.client.delete_collection(collection_name=collection_name)
            logger.info("collection_deleted", collection=collection_name)
            return True
        except Exception as e:
            logger.error("delete_collection_error", error=str(e), collection=collection_name, exc_info=True)
            raise
    
    def clear_collection(self, collection_name: str) -> bool:
        """Clear all points from a collection.
        
        Args:
            collection_name: Name of the collection to clear
            
        Returns:
            True if cleared successfully
        """
        try:
            # Delete and recreate collection to clear it
            col_info = self.client.get_collection(collection_name)
            vector_size = col_info.config.params.vectors.size if hasattr(col_info.config.params, 'vectors') else self.default_embedding_dimension
            distance = col_info.config.params.vectors.distance if hasattr(col_info.config.params, 'vectors') else Distance.COSINE
            
            self.client.delete_collection(collection_name=collection_name)
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance
                )
            )
            
            logger.info("collection_cleared", collection=collection_name)
            return True
        except Exception as e:
            logger.error("clear_collection_error", error=str(e), collection=collection_name, exc_info=True)
            raise
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get detailed information about a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection information
        """
        try:
            col_info = self.client.get_collection(collection_name)
            
            return {
                "name": collection_name,
                "points_count": col_info.points_count,
                "vector_size": col_info.config.params.vectors.size if hasattr(col_info.config.params, 'vectors') else 0,
                "distance": str(col_info.config.params.vectors.distance) if hasattr(col_info.config.params, 'vectors') else "Unknown",
            }
        except Exception as e:
            logger.error("get_collection_info_error", error=str(e), collection=collection_name, exc_info=True)
            raise
    
    def _get_genie(self):
        """Get OpenAI Genie instance for SlumberChunker.
        
        Returns:
            OpenAIGenie instance configured with user's LLM settings
        """
        try:
            genie = OpenAIGenie(
                model=settings.LLM_MODEL,
                base_url=settings.LLM_BASE_URL,
                api_key=settings.LLM_API_KEY
            )
            logger.info(
                "genie_initialized",
                model=settings.LLM_MODEL,
                base_url=settings.LLM_BASE_URL
            )
            return genie
        except Exception as e:
            logger.error("genie_initialization_error", error=str(e), exc_info=True)
            raise
    
    def _get_chunker(
        self,
        chunker_type: ChunkerType = "token",
        chunk_size: int = 512,
        chunk_overlap: int = 128
    ):
        """Get appropriate chunker based on type.
        
        Args:
            chunker_type: Type of chunker to use
            chunk_size: Size of chunks
            chunk_overlap: Overlap between chunks
            
        Returns:
            Initialized chunker instance
        """
        if chunker_type == "token":
            return TokenChunker(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        elif chunker_type == "sentence":
            return SentenceChunker(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                min_sentences_per_chunk=1,
            )
        elif chunker_type == "recursive":
            return RecursiveChunker(
                chunk_size=chunk_size,
            )
        elif chunker_type == "semantic":
            # Use DeepInfra embeddings for semantic chunking
            # This ensures consistent embeddings throughout the pipeline
            # Warning: Large chunk_size may produce chunks > 512 chars
            if chunk_size > 300:
                logger.warning(
                    "large_chunk_size_for_semantic",
                    chunk_size=chunk_size,
                    recommended_max=300,
                    message=f"SemanticChunker with chunk_size={chunk_size} may produce chunks > {MAX_QDRANT_FIELD_LENGTH} chars, causing truncation"
                )
            return SemanticChunker(
                embedding_model=self.embeddings,  # DeepInfra embeddings
                chunk_size=chunk_size,
                threshold=0.7,  # Similarity threshold
            )
        elif chunker_type == "slumber":
            # Use LLM-powered agentic chunking (SlumberChunker)
            # This uses the user's configured LLM to intelligently determine chunk boundaries
            # Warning: Large chunk_size may produce chunks > 512 chars
            if chunk_size > 300:
                logger.warning(
                    "large_chunk_size_for_slumber",
                    chunk_size=chunk_size,
                    recommended_max=300,
                    message=f"SlumberChunker with chunk_size={chunk_size} may produce chunks > {MAX_QDRANT_FIELD_LENGTH} chars, causing truncation"
                )
            genie = self._get_genie()
            return SlumberChunker(
                genie=genie,
                chunk_size=chunk_size,
                candidate_size=min(128, chunk_size // 4),  # Window for LLM to examine
                min_characters_per_chunk=24,
                verbose=False  # Set to True for debugging
            )
        else:
            logger.warning(f"Unknown chunker type: {chunker_type}, using token chunker")
            return TokenChunker(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
    
    async def upload_document(
        self,
        file_path: str,
        content: str,
        user_id: int,
        metadata: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None,
        chunk_size: int = 512,
        chunk_overlap: int = 128,
        chunker_type: ChunkerType = "token"
    ) -> Dict[str, Any]:
        """Upload a document to Qdrant using Chonkie.
        
        Args:
            file_path: Path to the file
            content: Document content
            user_id: User ID who uploaded the document
            metadata: Additional metadata
            collection_name: Target collection (default: default collection)
            chunk_size: Size of chunks in tokens
            chunk_overlap: Overlap between chunks
            
        Returns:
            Dict with upload statistics
        """
        try:
            collection = collection_name or self.default_collection_name
            
            # Ensure collection exists
            collections = self.client.get_collections().collections
            if collection not in [col.name for col in collections]:
                # Create with default settings
                self.create_collection(
                    collection_name=collection,
                    embedding_size=self.default_embedding_dimension
                )
            
            # Get collection info
            col_info = self.client.get_collection(collection)
            embedding_size = col_info.config.params.vectors.size if hasattr(col_info.config.params, 'vectors') else self.default_embedding_dimension
            
            # Validate embedding size matches
            if embedding_size != self.default_embedding_dimension:
                logger.warning(
                    "embedding_size_mismatch",
                    collection_size=embedding_size,
                    expected_size=self.default_embedding_dimension,
                    collection=collection
                )
            
            # Initialize Chonkie chunker based on type
            chunker = self._get_chunker(
                chunker_type=chunker_type,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            logger.info(
                "chunker_initialized",
                chunker_type=chunker_type,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            doc_id = hashlib.md5(f"{user_id}:{file_path}".encode()).hexdigest()
            
            chunks = chunker.chunk(content)
            
            logger.info(
                "document_chunked",
                doc_id=doc_id,
                file_path=file_path,
                chunks_count=len(chunks)
            )
            
            # Process chunks and prepare for Qdrant upload
            # Extract only text from chunks to avoid any hidden fields
            points = []
            truncated_count = 0
            
            for idx, chunk in enumerate(chunks):
                # Extract text from chunk
                # CRITICAL: chunk.text can be a LIST (from SemanticChunker storing sentences)
                # We must join list items into a single string BEFORE converting
                if hasattr(chunk, 'text'):
                    chunk_text_value = chunk.text
                    
                    # Check if it's a list/tuple of sentences
                    if isinstance(chunk_text_value, (list, tuple)):
                        # Join list into single string
                        chunk_text_raw = " ".join(str(item) for item in chunk_text_value)
                        logger.debug(
                            "chunk_text_was_list",
                            chunk_index=idx,
                            list_length=len(chunk_text_value),
                            joined_length=len(chunk_text_raw)
                        )
                    else:
                        chunk_text_raw = str(chunk_text_value)
                else:
                    chunk_text_raw = str(chunk)
                
                original_length = len(chunk_text_raw)
                
                # Truncate if needed
                if original_length > MAX_QDRANT_FIELD_LENGTH:
                    chunk_text = chunk_text_raw[:MAX_QDRANT_FIELD_LENGTH]
                    truncated_count += 1
                    truncated = True
                else:
                    chunk_text = chunk_text_raw
                    truncated = False
                
                # Generate embedding for this chunk
                # Important: Embedding API also has input length limits (typically ~8000 chars or ~2000 tokens)
                # Use truncated text (already limited to MAX_QDRANT_FIELD_LENGTH = 900 chars)
                try:
                    # Ensure text is not too long for embedding API
                    # Most embedding models have ~512-8192 token limits
                    # We're already at 900 chars max, which is safe for most models
                    embedding = self.embeddings.embed(chunk_text)
                    embedding_list = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
                except Exception as e:
                    logger.error(
                        "embedding_generation_failed",
                        chunk_index=idx,
                        chunk_text_length=len(chunk_text),
                        error=str(e),
                        error_message=str(e),
                        exc_info=True
                    )
                    # Skip this chunk instead of failing entire upload
                    logger.warning(
                        "skipping_chunk_due_to_embedding_error",
                        chunk_index=idx,
                        chunk_preview=chunk_text[:100]
                    )
                    continue  # Skip this chunk and continue with others
                
                # Create MINIMAL safe payload - only essential fields
                # Ensure ALL values are safe types and strings are truncated
                safe_file_path = str(file_path)[:MAX_QDRANT_FIELD_LENGTH] if len(str(file_path)) > MAX_QDRANT_FIELD_LENGTH else str(file_path)
                
                payload = {
                    "document_id": str(doc_id),
                    "user_id": int(user_id),
                    "file_path": safe_file_path,
                    "chunk_index": int(idx),
                    "chunk_text": str(chunk_text),  # Already truncated
                    "original_length": int(original_length),
                    "truncated": bool(truncated),
                }
                
                # Add metadata fields ONLY if they're safe
                if metadata:
                    for key, value in metadata.items():
                        # Only add simple types
                        if isinstance(value, (str, int, float, bool)):
                            if isinstance(value, str):
                                # Truncate strings
                                if len(value) > MAX_QDRANT_FIELD_LENGTH:
                                    payload[f"meta_{key}"] = value[:MAX_QDRANT_FIELD_LENGTH]
                                else:
                                    payload[f"meta_{key}"] = value
                            else:
                                payload[f"meta_{key}"] = value
                        # Skip lists, dicts, and complex objects
                
                # Create point with UUID
                point_id = str(uuid.uuid4())
                point = PointStruct(
                    id=point_id,
                    vector=embedding_list,
                    payload=payload
                )
                points.append(point)
            
            if truncated_count > 0:
                logger.warning(
                    "chunks_truncated_for_qdrant",
                    doc_id=doc_id,
                    truncated_count=truncated_count,
                    total_chunks=len(chunks),
                    max_length=MAX_QDRANT_FIELD_LENGTH,
                    message=f"{truncated_count}/{len(chunks)} chunks exceeded {MAX_QDRANT_FIELD_LENGTH} chars and were truncated due to Qdrant field limit"
                )
            
            # Debug: Log payload sizes before upload
            if points:
                logger.info(
                    "preparing_qdrant_upload",
                    points_count=len(points),
                    sample_payload_keys=list(points[0].payload.keys()) if points else [],
                    sample_text_length=len(points[0].payload.get("chunk_text", "")) if points else 0
                )
                
                # Check for any fields exceeding limit
                for idx, point in enumerate(points[:5]):  # Check first 5
                    for key, value in point.payload.items():
                        if isinstance(value, str) and len(value) > MAX_QDRANT_FIELD_LENGTH:
                            logger.error(
                                "field_exceeds_limit",
                                point_index=idx,
                                field_name=key,
                                field_length=len(value),
                                max_length=MAX_QDRANT_FIELD_LENGTH,
                                field_preview=value[:100]
                            )
            
            # Upload points to Qdrant in batches to avoid issues
            BATCH_SIZE = 100
            total_uploaded = 0
            
            try:
                for i in range(0, len(points), BATCH_SIZE):
                    batch = points[i:i + BATCH_SIZE]
                    self.client.upsert(
                        collection_name=collection,
                        points=batch
                    )
                    total_uploaded += len(batch)
                    
                    logger.debug(
                        "batch_uploaded",
                        batch_num=i // BATCH_SIZE + 1,
                        batch_size=len(batch),
                        total_uploaded=total_uploaded,
                        total_points=len(points)
                    )
                    
            except Exception as e:
                logger.error(
                    "qdrant_upsert_failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    total_points=len(points),
                    uploaded_so_far=total_uploaded,
                    exc_info=True
                )
                raise
            
            logger.info(
                "document_uploaded",
                doc_id=doc_id,
                chunks_uploaded=len(chunks),
                user_id=user_id,
                collection=collection
            )
            
            return {
                "document_id": doc_id,
                "file_path": file_path,
                "chunks_count": len(chunks),
                "total_chars": len(content),
                "collection": collection,
                "chunker_type": chunker_type
            }
            
        except Exception as e:
            logger.error(
                "document_upload_error",
                error=str(e),
                file_path=file_path,
                exc_info=True
            )
            raise
    
    async def upload_csv_document(
        self,
        file_path: str,
        content: str,
        user_id: int,
        metadata: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None,
        chunk_size: int = 512,
        chunk_overlap: int = 128,
        chunker_type: ChunkerType = "token"
    ) -> Dict[str, Any]:
        """Upload a CSV document to Qdrant.
        
        Args:
            file_path: Path to the file
            content: CSV content
            user_id: User ID who uploaded the document
            metadata: Additional metadata
            collection_name: Target collection
            chunk_size: Size of chunks
            chunk_overlap: Overlap between chunks
            
        Returns:
            Dict with upload statistics
        """
        try:
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(content))
            rows = list(csv_reader)
            
            # Convert CSV to text format
            text_parts = []
            for idx, row in enumerate(rows):
                row_text = f"Row {idx + 1}:\n"
                for key, value in row.items():
                    row_text += f"  {key}: {value}\n"
                text_parts.append(row_text)
            
            text_content = "\n".join(text_parts)
            
            # Upload as regular document
            return await self.upload_document(
                file_path=file_path,
                content=text_content,
                user_id=user_id,
                metadata={
                    **(metadata or {}),
                    "file_type": "csv",
                    "rows_count": len(rows)
                },
                collection_name=collection_name,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                chunker_type=chunker_type
            )
            
        except Exception as e:
            logger.error(
                "csv_upload_error",
                error=str(e),
                file_path=file_path,
                exc_info=True
            )
            raise
    
    async def search_documents(
        self,
        query: str,
        user_id: Optional[int] = None,
        limit: int = 5,
        collection_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant chunks (alias for search).
        
        Args:
            query: Search query
            user_id: Optional user ID to filter results
            limit: Maximum number of results
            collection_name: Collection to search in
            
        Returns:
            List of relevant chunks with scores
        """
        return await self.search(query, user_id, limit, collection_name)
    
    async def search(
        self,
        query: str,
        user_id: Optional[int] = None,
        limit: int = 5,
        collection_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant chunks using embeddings.
        
        Args:
            query: Search query
            user_id: Optional user ID to filter results
            limit: Maximum number of results
            collection_name: Collection to search in
            
        Returns:
            List of relevant chunks with scores
        """
        try:
            collection = collection_name or self.default_collection_name
            
            # Generate embedding for query
            query_embedding = self.embeddings.embed(query)
            query_vector = query_embedding.tolist() if hasattr(query_embedding, 'tolist') else list(query_embedding)
            
            # Build filter for user_id if provided
            query_filter = None
            if user_id is not None:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=user_id)
                        )
                    ]
                )
            
            # Search in Qdrant
            search_results = self.client.search(
                collection_name=collection,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit,
                with_payload=True
            )
            
            # Format results
            formatted_results = []
            for result in search_results:
                payload = result.payload
                formatted_results.append({
                    "text": payload.get("chunk_text", ""),
                    "chunk_text": payload.get("chunk_text", ""),
                    "file_path": payload.get("file_path", ""),
                    "score": result.score,
                    "document_id": payload.get("document_id", ""),
                    "chunk_index": payload.get("chunk_index", 0),
                    "metadata": {
                        "file_path": payload.get("file_path", ""),
                        "chunk_index": payload.get("chunk_index", 0),
                        "original_length": payload.get("original_length", 0),
                        "truncated": payload.get("truncated", False)
                    }
                })
            
            logger.info(
                "search_completed",
                query_length=len(query),
                results_count=len(formatted_results),
                user_id=user_id,
                collection=collection
            )
            
            return formatted_results
            
        except Exception as e:
            logger.error("search_error", error=str(e), collection=collection_name, exc_info=True)
            raise
    
    def get_user_documents(
        self,
        user_id: int,
        collection_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all documents for a user.
        
        Args:
            user_id: User ID
            collection_name: Collection to search in
            
        Returns:
            List of documents
        """
        try:
            collection = collection_name or self.default_collection_name
            
            # Scroll through all points for the user
            results, _ = self.client.scroll(
                collection_name=collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=user_id)
                        )
                    ]
                ),
                limit=1000,
                with_payload=True,
                with_vectors=False
            )
            
            # Group by document_id
            documents = {}
            for point in results:
                doc_id = point.payload.get("document_id", "unknown")
                if doc_id not in documents:
                    documents[doc_id] = {
                        "document_id": doc_id,
                        "file_path": point.payload.get("file_path", ""),
                        "chunks_count": 0,
                        "collection": collection
                    }
                documents[doc_id]["chunks_count"] += 1
            
            return list(documents.values())
            
        except Exception as e:
            logger.error("get_documents_error", error=str(e), user_id=user_id, exc_info=True)
            raise
    
    def delete_document(
        self,
        document_id: str,
        user_id: int,
        collection_name: Optional[str] = None
    ) -> bool:
        """Delete a document and all its chunks.
        
        Args:
            document_id: Document ID
            user_id: User ID (for security check)
            collection_name: Collection containing the document
            
        Returns:
            True if deleted successfully
        """
        try:
            collection = collection_name or self.default_collection_name
            
            # Delete all points with this document_id and user_id
            self.client.delete(
                collection_name=collection,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        ),
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=user_id)
                        )
                    ]
                )
            )
            
            logger.info("document_deleted", document_id=document_id, user_id=user_id, collection=collection)
            return True
            
        except Exception as e:
            logger.error(
                "document_delete_error",
                error=str(e),
                document_id=document_id,
                exc_info=True
            )
            raise


# Global instance
qdrant_service = QdrantService()
