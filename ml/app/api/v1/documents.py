"""Documents endpoints for RAG document management."""

from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Request, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.limiter import limiter
from app.core.logging import logger
from app.services.qdrant_service import qdrant_service

router = APIRouter()


# Collection Models
class CollectionCreate(BaseModel):
    """Request to create a new collection."""
    
    name: str = Field(..., description="Collection name", min_length=1, max_length=100)
    embedding_size: int = Field(..., description="Embedding vector size", ge=1, le=4096)
    distance: str = Field(default="Cosine", description="Distance metric (Cosine, Euclid, Dot)")


class CollectionInfo(BaseModel):
    """Collection information."""
    
    name: str = Field(..., description="Collection name")
    vectors_count: int = Field(..., description="Number of vectors in collection")
    vector_size: int = Field(..., description="Size of vectors")


class CollectionDetail(BaseModel):
    """Detailed collection information."""
    
    name: str = Field(..., description="Collection name")
    points_count: int = Field(..., description="Number of points")
    vector_size: int = Field(..., description="Vector size")
    distance: str = Field(..., description="Distance metric")


# Document Models
class DocumentUploadResponse(BaseModel):
    """Response for document upload."""
    
    document_id: str = Field(..., description="Unique document ID")
    file_path: str = Field(..., description="File path")
    chunks_count: int = Field(..., description="Number of chunks")
    total_chars: int = Field(..., description="Total characters")
    collection: str = Field(..., description="Collection name")
    chunker_type: str = Field(..., description="Type of chunker used")


class DocumentInfo(BaseModel):
    """Document information."""
    
    document_id: str = Field(..., description="Document ID")
    file_path: str = Field(..., description="File path")
    chunks_count: int = Field(..., description="Number of chunks")
    collection: str = Field(..., description="Collection name")


class SearchRequest(BaseModel):
    """Search request."""
    
    query: str = Field(..., description="Search query", min_length=1, max_length=500)
    limit: int = Field(default=5, description="Number of results", ge=1, le=20)
    collection_name: Optional[str] = Field(None, description="Collection to search in")


class SearchResult(BaseModel):
    """Search result."""
    
    chunk_text: str = Field(..., description="Chunk text")
    file_path: str = Field(..., description="Source file")
    score: float = Field(..., description="Relevance score")
    document_id: str = Field(..., description="Document ID")
    chunk_index: int = Field(..., description="Chunk index in document")


class SearchResponse(BaseModel):
    """Search response."""
    
    results: List[SearchResult] = Field(..., description="Search results")
    query: str = Field(..., description="Original query")


# Collection Management Endpoints

@router.post("/collections", response_model=CollectionCreate)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def create_collection(
    request: Request,
    collection: CollectionCreate
):
    """Create a new collection.
    
    Args:
        request: FastAPI request
        collection: Collection parameters
        
    Returns:
        CollectionCreate: Created collection info
    """
    try:
        result = qdrant_service.create_collection(
            collection_name=collection.name,
            embedding_size=collection.embedding_size,
            distance=collection.distance
        )
        
        logger.info("collection_created_via_api", collection=collection.name)
        
        # Map collection_name to name for Pydantic model
        return CollectionCreate(
            name=result['collection_name'],
            embedding_size=result['embedding_size'],
            distance=result['distance']
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("create_collection_api_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create collection")


@router.get("/collections", response_model=List[CollectionInfo])
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def list_collections(request: Request):
    """List all collections.
    
    Args:
        request: FastAPI request
        
    Returns:
        List[CollectionInfo]: List of collections
    """
    try:
        collections = qdrant_service.list_collections()
        return [CollectionInfo(**col) for col in collections]
    except Exception as e:
        logger.error("list_collections_api_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list collections")


@router.get("/collections/{collection_name}", response_model=CollectionDetail)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def get_collection(
    request: Request,
    collection_name: str
):
    """Get detailed information about a collection.
    
    Args:
        request: FastAPI request
        collection_name: Name of the collection
        
    Returns:
        CollectionDetail: Collection details
    """
    try:
        info = qdrant_service.get_collection_info(collection_name)
        return CollectionDetail(**info)
    except Exception as e:
        logger.error("get_collection_api_error", error=str(e), collection=collection_name, exc_info=True)
        raise HTTPException(status_code=404, detail="Collection not found")


@router.delete("/collections/{collection_name}")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def delete_collection(
    request: Request,
    collection_name: str
):
    """Delete a collection.
    
    Args:
        request: FastAPI request
        collection_name: Name of the collection to delete
        
    Returns:
        Dict with success message
    """
    try:
        qdrant_service.delete_collection(collection_name)
        return {"message": "Collection deleted successfully", "collection_name": collection_name}
    except Exception as e:
        logger.error("delete_collection_api_error", error=str(e), collection=collection_name, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete collection")


@router.post("/collections/{collection_name}/clear")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def clear_collection(
    request: Request,
    collection_name: str
):
    """Clear all documents from a collection.
    
    Args:
        request: FastAPI request
        collection_name: Name of the collection to clear
        
    Returns:
        Dict with success message
    """
    try:
        qdrant_service.clear_collection(collection_name)
        return {"message": "Collection cleared successfully", "collection_name": collection_name}
    except Exception as e:
        logger.error("clear_collection_api_error", error=str(e), collection=collection_name, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to clear collection")


# Document Management Endpoints

@router.post("/upload", response_model=DocumentUploadResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    user_id: int = Query(default=1),
    collection_name: Optional[str] = Query(default=None),
    chunk_size: int = Query(default=512, ge=100, le=2048),
    chunk_overlap: int = Query(default=128, ge=0, le=512),
    chunker_type: str = Query(default="token", regex="^(token|sentence|recursive|semantic|slumber)$")
):
    """Upload a document (MD or CSV).
    
    Args:
        request: FastAPI request
        file: Uploaded file
        user_id: User ID
        collection_name: Target collection (default: default collection)
        chunk_size: Size of chunks in tokens
        chunk_overlap: Overlap between chunks
        chunker_type: Type of chunker (token, sentence, recursive, semantic)
        
    Returns:
        DocumentUploadResponse: Upload result
    """
    try:
        # Check file extension
        file_ext = file.filename.lower().split('.')[-1]
        if file_ext not in ['md', 'csv']:
            raise HTTPException(
                status_code=400,
                detail="Only .md and .csv files are supported"
            )
        
        # Read file content
        content = await file.read()
        text_content = content.decode('utf-8')
        
        logger.info(
            "document_upload_received",
            filename=file.filename,
            user_id=user_id,
            size=len(text_content),
            file_type=file_ext,
            collection=collection_name
        )
        
        # Upload based on file type
        if file_ext == 'csv':
            result = await qdrant_service.upload_csv_document(
                file_path=file.filename,
                content=text_content,
                user_id=user_id,
                metadata={"filename": file.filename},
                collection_name=collection_name,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                chunker_type=chunker_type
            )
        else:  # md
            result = await qdrant_service.upload_document(
                file_path=file.filename,
                content=text_content,
                user_id=user_id,
                metadata={"filename": file.filename},
                collection_name=collection_name,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                chunker_type=chunker_type
            )
        
        return DocumentUploadResponse(**result)
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be valid UTF-8 encoded text"
        )
    except Exception as e:
        logger.error(
            "document_upload_error",
            error=str(e),
            user_id=user_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.get("/list", response_model=List[DocumentInfo])
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def list_documents(
    request: Request,
    user_id: int = Query(default=1),
    collection_name: Optional[str] = Query(default=None)
):
    """List all user documents.
    
    Args:
        request: FastAPI request
        user_id: User ID
        collection_name: Collection to list from
        
    Returns:
        List[DocumentInfo]: List of documents
    """
    try:
        documents = qdrant_service.get_user_documents(user_id, collection_name)
        return [DocumentInfo(**doc) for doc in documents]
    except Exception as e:
        logger.error(
            "list_documents_error",
            error=str(e),
            user_id=user_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to list documents"
        )


@router.post("/search", response_model=SearchResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def search_documents(
    request: Request,
    search_request: SearchRequest,
    user_id: Optional[int] = Query(default=None)
):
    """Search in documents.
    
    Args:
        request: FastAPI request
        search_request: Search parameters
        user_id: Optional user ID to filter results
        
    Returns:
        SearchResponse: Search results
    """
    try:
        results = await qdrant_service.search(
            query=search_request.query,
            user_id=user_id,
            limit=search_request.limit,
            collection_name=search_request.collection_name
        )
        
        return SearchResponse(
            results=[SearchResult(**r) for r in results],
            query=search_request.query
        )
    except Exception as e:
        logger.error(
            "search_documents_error",
            error=str(e),
            user_id=user_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search documents: {str(e)}"
        )


@router.delete("/delete/{document_id}")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def delete_document(
    request: Request,
    document_id: str,
    user_id: int = Query(default=1),
    collection_name: Optional[str] = Query(default=None)
):
    """Delete a document.
    
    Args:
        request: FastAPI request
        document_id: Document ID to delete
        user_id: User ID
        collection_name: Collection containing the document
        
    Returns:
        Dict with success message
    """
    try:
        success = qdrant_service.delete_document(document_id, user_id, collection_name)
        
        if success:
            return {"message": "Document deleted successfully", "document_id": document_id}
        else:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "delete_document_error",
            error=str(e),
            user_id=user_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to delete document"
        )
