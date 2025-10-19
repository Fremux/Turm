"""API endpoints for category and intent management."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Depends, Query
from sqlmodel import Session, select, func

from app.core.config import settings
from app.core.limiter import limiter
from app.core.logging import logger
from app.services.database import get_db_session
from app.services.qdrant_service import qdrant_service
from app.models.category import Category, Intent
from app.core.langgraph.classifier import classification_agent
from app.schemas.category import (
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoriesListResponse,
    IntentCreate, IntentUpdate, IntentResponse, IntentsListResponse
)

router = APIRouter()


# Category Endpoints

@router.post("/categories", response_model=CategoryResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def create_category(
    request: Request,
    category: CategoryCreate,
    db: Session = Depends(get_db_session)
):
    """Create a new category.
    
    Automatically creates a vector collection in Qdrant if requested.
    """
    try:
        # Check if category with this name already exists
        existing = db.exec(select(Category).where(Category.name == category.name)).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Category '{category.name}' already exists")
        
        # Generate collection name
        collection_name = category.name.lower().replace(" ", "_")
        
        # Check if collection name is taken
        existing_collection = db.exec(
            select(Category).where(Category.collection_name == collection_name)
        ).first()
        if existing_collection:
            raise HTTPException(
                status_code=400,
                detail=f"Collection name '{collection_name}' already in use"
            )
        
        # Create category
        new_category = Category(
            name=category.name,
            display_name=category.display_name,
            description=category.description,
            about_text=category.about_text,
            common_intents=category.common_intents,
            key_markers=category.key_markers,
            example_queries=category.example_queries,
            border_cases=category.border_cases,
            collection_name=collection_name,
            embedding_model=category.embedding_model,
            embedding_dimension=category.embedding_dimension,
            color=category.color,
            icon=category.icon,
            collection_created=False
        )
        
        db.add(new_category)
        db.commit()
        db.refresh(new_category)
        
        # Create Qdrant collection if requested
        if category.create_collection:
            try:
                # Use category-specific embedding dimension or fall back to settings default
                embedding_size = category.embedding_dimension or settings.EMBEDDING_DIMENSION
                qdrant_service.create_collection(
                    collection_name=collection_name,
                    embedding_size=embedding_size
                )
                new_category.collection_created = True
                db.add(new_category)
                db.commit()
                db.refresh(new_category)
                
                logger.info(
                    "category_collection_created",
                    category=category.name,
                    collection=collection_name
                )
            except Exception as e:
                logger.error(
                    "category_collection_creation_failed",
                    category=category.name,
                    error=str(e),
                    exc_info=True
                )
                # Don't fail the category creation if collection fails
        
        # Build response
        response = CategoryResponse(
            id=new_category.id,
            name=new_category.name,
            display_name=new_category.display_name,
            description=new_category.description,
            about_text=new_category.about_text,
            common_intents=new_category.common_intents,
            key_markers=new_category.key_markers,
            example_queries=new_category.example_queries,
            border_cases=new_category.border_cases,
            collection_name=new_category.collection_name,
            collection_created=new_category.collection_created,
            embedding_model=new_category.embedding_model,
            embedding_dimension=new_category.embedding_dimension,
            is_active=new_category.is_active,
            color=new_category.color,
            icon=new_category.icon,
            created_at=new_category.created_at,
            intents_count=0,
            documents_count=0
        )
        
        logger.info("category_created", category=category.name, id=new_category.id)
        
        # Refresh classifier with new categories
        try:
            classification_agent.refresh_categories()
        except Exception as e:
            logger.warning("failed_to_refresh_classifier", error=str(e))
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("category_creation_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create category")


@router.get("/categories", response_model=CategoriesListResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def list_categories(
    request: Request,
    active_only: bool = Query(default=True),
    db: Session = Depends(get_db_session)
):
    """List all categories."""
    try:
        # Build query
        query = select(Category)
        if active_only:
            query = query.where(Category.is_active == True)
        
        query = query.order_by(Category.created_at.desc())
        
        categories = db.exec(query).all()
        
        # Build responses with stats
        responses = []
        for cat in categories:
            # Count intents
            intents_count = db.exec(
                select(func.count(Intent.id)).where(Intent.category_id == cat.id)
            ).first() or 0
            
            # Count documents in collection
            documents_count = 0
            if cat.collection_created:
                try:
                    col_info = qdrant_service.get_collection_info(cat.collection_name)
                    documents_count = col_info.get("points_count", 0)
                except:
                    pass
            
            responses.append(CategoryResponse(
                id=cat.id,
                name=cat.name,
                display_name=cat.display_name,
                description=cat.description,
                about_text=cat.about_text,
                common_intents=cat.common_intents,
                key_markers=cat.key_markers,
                example_queries=cat.example_queries,
                border_cases=cat.border_cases,
                collection_name=cat.collection_name,
                collection_created=cat.collection_created,
                embedding_model=cat.embedding_model,
                embedding_dimension=cat.embedding_dimension,
                is_active=cat.is_active,
                color=cat.color,
                icon=cat.icon,
                created_at=cat.created_at,
                intents_count=intents_count,
                documents_count=documents_count
            ))
        
        return CategoriesListResponse(categories=responses, total=len(responses))
        
    except Exception as e:
        logger.error("list_categories_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list categories")


@router.get("/categories/{category_id}", response_model=CategoryResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def get_category(
    request: Request,
    category_id: int,
    db: Session = Depends(get_db_session)
):
    """Get a specific category."""
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Get stats
    intents_count = db.exec(
        select(func.count(Intent.id)).where(Intent.category_id == category.id)
    ).first() or 0
    
    documents_count = 0
    if category.collection_created:
        try:
            col_info = qdrant_service.get_collection_info(category.collection_name)
            documents_count = col_info.get("points_count", 0)
        except:
            pass
    
    return CategoryResponse(
        id=category.id,
        name=category.name,
        display_name=category.display_name,
        description=category.description,
        about_text=category.about_text,
        common_intents=category.common_intents,
        key_markers=category.key_markers,
        example_queries=category.example_queries,
        border_cases=category.border_cases,
        collection_name=category.collection_name,
        collection_created=category.collection_created,
        embedding_model=category.embedding_model,
        embedding_dimension=category.embedding_dimension,
        is_active=category.is_active,
        color=category.color,
        icon=category.icon,
        created_at=category.created_at,
        intents_count=intents_count,
        documents_count=documents_count
    )


@router.patch("/categories/{category_id}", response_model=CategoryResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def update_category(
    request: Request,
    category_id: int,
    category_update: CategoryUpdate,
    db: Session = Depends(get_db_session)
):
    """Update a category."""
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Update fields
    if category_update.display_name is not None:
        category.display_name = category_update.display_name
    if category_update.description is not None:
        category.description = category_update.description
    if category_update.about_text is not None:
        category.about_text = category_update.about_text
    if category_update.common_intents is not None:
        category.common_intents = category_update.common_intents
    if category_update.key_markers is not None:
        category.key_markers = category_update.key_markers
    if category_update.example_queries is not None:
        category.example_queries = category_update.example_queries
    if category_update.border_cases is not None:
        category.border_cases = category_update.border_cases
    if category_update.embedding_model is not None:
        category.embedding_model = category_update.embedding_model
    if category_update.embedding_dimension is not None:
        category.embedding_dimension = category_update.embedding_dimension
    if category_update.color is not None:
        category.color = category_update.color
    if category_update.icon is not None:
        category.icon = category_update.icon
    if category_update.is_active is not None:
        category.is_active = category_update.is_active
    
    db.add(category)
    db.commit()
    db.refresh(category)
    
    # Get stats
    intents_count = db.exec(
        select(func.count(Intent.id)).where(Intent.category_id == category.id)
    ).first() or 0
    
    documents_count = 0
    if category.collection_created:
        try:
            col_info = qdrant_service.get_collection_info(category.collection_name)
            documents_count = col_info.get("points_count", 0)
        except:
            pass
    
    logger.info("category_updated", category_id=category_id)
    
    # Refresh classifier with updated categories
    try:
        classification_agent.refresh_categories()
    except Exception as e:
        logger.warning("failed_to_refresh_classifier", error=str(e))
    
    return CategoryResponse(
        id=category.id,
        name=category.name,
        display_name=category.display_name,
        description=category.description,
        about_text=category.about_text,
        common_intents=category.common_intents,
        key_markers=category.key_markers,
        example_queries=category.example_queries,
        border_cases=category.border_cases,
        collection_name=category.collection_name,
        collection_created=category.collection_created,
        embedding_model=category.embedding_model,
        embedding_dimension=category.embedding_dimension,
        is_active=category.is_active,
        color=category.color,
        icon=category.icon,
        created_at=category.created_at,
        intents_count=intents_count,
        documents_count=documents_count
    )


@router.delete("/categories/{category_id}")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def delete_category(
    request: Request,
    category_id: int,
    delete_collection: bool = Query(default=False),
    db: Session = Depends(get_db_session)
):
    """Delete a category (soft delete by default)."""
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Soft delete
    category.is_active = False
    db.add(category)
    db.commit()
    
    # Optionally delete Qdrant collection
    if delete_collection and category.collection_created:
        try:
            qdrant_service.delete_collection(category.collection_name)
            logger.info("category_collection_deleted", category=category.name)
        except Exception as e:
            logger.error(
                "category_collection_deletion_failed",
                category=category.name,
                error=str(e)
            )
    
    logger.info("category_deleted", category_id=category_id)
    
    # Refresh classifier with updated categories
    try:
        classification_agent.refresh_categories()
    except Exception as e:
        logger.warning("failed_to_refresh_classifier", error=str(e))
    
    return {"message": "Category deleted successfully", "category_id": category_id}


@router.post("/categories/{category_id}/create-collection")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def create_category_collection(
    request: Request,
    category_id: int,
    force_recreate: bool = Query(default=False, description="Force recreation if collection exists"),
    db: Session = Depends(get_db_session)
):
    """Create a Qdrant collection for a category."""
    try:
        category = db.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        if category.collection_created and not force_recreate:
            raise HTTPException(
                status_code=400,
                detail=f"Collection '{category.collection_name}' already exists. Use force_recreate=true to recreate."
            )
        
        # Use category-specific embedding dimension or fall back to settings default
        embedding_size = category.embedding_dimension or settings.EMBEDDING_DIMENSION
        
        # Delete existing collection if force_recreate
        if force_recreate and category.collection_created:
            try:
                qdrant_service.delete_collection(category.collection_name)
                logger.info(
                    "collection_deleted_for_recreation",
                    collection=category.collection_name
                )
            except Exception as e:
                logger.warning(f"Could not delete existing collection: {e}")
        
        # Create collection in Qdrant
        qdrant_service.create_collection(
            collection_name=category.collection_name,
            embedding_size=embedding_size
        )
        
        # Update category
        category.collection_created = True
        db.add(category)
        db.commit()
        db.refresh(category)
        
        logger.info(
            "category_collection_created_manually",
            category=category.name,
            collection=category.collection_name,
            embedding_size=embedding_size
        )
        
        return {
            "message": "Collection created successfully",
            "category_id": category_id,
            "collection_name": category.collection_name,
            "embedding_size": embedding_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "category_collection_creation_error",
            category_id=category_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to create collection")


# Intent Endpoints

@router.post("/intents", response_model=IntentResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def create_intent(
    request: Request,
    intent: IntentCreate,
    db: Session = Depends(get_db_session)
):
    """Create a new intent."""
    try:
        # Check if intent exists
        existing = db.exec(select(Intent).where(Intent.name == intent.name)).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Intent '{intent.name}' already exists")
        
        # Verify category exists if provided
        if intent.category_id:
            category = db.get(Category, intent.category_id)
            if not category:
                raise HTTPException(status_code=404, detail="Category not found")
        
        # Create intent
        new_intent = Intent(
            name=intent.name,
            display_name=intent.display_name,
            description=intent.description,
            examples=intent.examples,
            category_id=intent.category_id,
            priority=intent.priority
        )
        
        db.add(new_intent)
        db.commit()
        db.refresh(new_intent)
        
        # Get category name
        category_name = None
        if new_intent.category_id:
            category = db.get(Category, new_intent.category_id)
            if category:
                category_name = category.name
        
        logger.info("intent_created", intent=intent.name, id=new_intent.id)
        
        return IntentResponse(
            id=new_intent.id,
            name=new_intent.name,
            display_name=new_intent.display_name,
            description=new_intent.description,
            examples=new_intent.examples,
            category_id=new_intent.category_id,
            category_name=category_name,
            priority=new_intent.priority,
            is_active=new_intent.is_active,
            created_at=new_intent.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("intent_creation_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create intent")


@router.get("/intents", response_model=IntentsListResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def list_intents(
    request: Request,
    category_id: Optional[int] = Query(default=None),
    active_only: bool = Query(default=True),
    db: Session = Depends(get_db_session)
):
    """List all intents."""
    try:
        query = select(Intent)
        if active_only:
            query = query.where(Intent.is_active == True)
        if category_id:
            query = query.where(Intent.category_id == category_id)
        
        query = query.order_by(Intent.created_at.desc())
        
        intents = db.exec(query).all()
        
        # Build responses
        responses = []
        for intent in intents:
            category_name = None
            if intent.category_id:
                category = db.get(Category, intent.category_id)
                if category:
                    category_name = category.name
            
            responses.append(IntentResponse(
                id=intent.id,
                name=intent.name,
                display_name=intent.display_name,
                description=intent.description,
                examples=intent.examples,
                category_id=intent.category_id,
                category_name=category_name,
                priority=intent.priority,
                is_active=intent.is_active,
                created_at=intent.created_at
            ))
        
        return IntentsListResponse(intents=responses, total=len(responses))
        
    except Exception as e:
        logger.error("list_intents_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list intents")


@router.patch("/intents/{intent_id}", response_model=IntentResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def update_intent(
    request: Request,
    intent_id: int,
    intent_update: IntentUpdate,
    db: Session = Depends(get_db_session)
):
    """Update an intent."""
    intent = db.get(Intent, intent_id)
    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")
    
    # Update fields
    if intent_update.display_name is not None:
        intent.display_name = intent_update.display_name
    if intent_update.description is not None:
        intent.description = intent_update.description
    if intent_update.examples is not None:
        intent.examples = intent_update.examples
    if intent_update.category_id is not None:
        # Verify category exists
        category = db.get(Category, intent_update.category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        intent.category_id = intent_update.category_id
    if intent_update.priority is not None:
        intent.priority = intent_update.priority
    if intent_update.is_active is not None:
        intent.is_active = intent_update.is_active
    
    db.add(intent)
    db.commit()
    db.refresh(intent)
    
    # Get category name
    category_name = None
    if intent.category_id:
        category = db.get(Category, intent.category_id)
        if category:
            category_name = category.name
    
    logger.info("intent_updated", intent_id=intent_id)
    
    return IntentResponse(
        id=intent.id,
        name=intent.name,
        display_name=intent.display_name,
        description=intent.description,
        examples=intent.examples,
        category_id=intent.category_id,
        category_name=category_name,
        priority=intent.priority,
        is_active=intent.is_active,
        created_at=intent.created_at
    )


@router.delete("/intents/{intent_id}")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def delete_intent(
    request: Request,
    intent_id: int,
    db: Session = Depends(get_db_session)
):
    """Delete an intent (soft delete)."""
    intent = db.get(Intent, intent_id)
    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")
    
    # Soft delete
    intent.is_active = False
    db.add(intent)
    db.commit()
    
    logger.info("intent_deleted", intent_id=intent_id)
    return {"message": "Intent deleted successfully", "intent_id": intent_id}


# Feedback / Training Endpoints

@router.post("/categories/{category_id}/add-training-example")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def add_category_training_example(
    request: Request,
    category_id: int,
    example: dict,
    db: Session = Depends(get_db_session)
):
    """Add a training example to category's border cases.
    
    When user corrects misclassification, add the example to help improve future classifications.
    
    Args:
        category_id: Correct category ID
        example: {"text": "user message that was misclassified"}
    """
    try:
        category = db.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        text = example.get("text", "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="Example text is required")
        
        # Add to border_cases (or create if doesn't exist)
        current_border_cases = category.border_cases or ""
        
        # Format: add as a new line with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d")
        new_example = f"- [{timestamp}] {text}"
        
        if current_border_cases:
            category.border_cases = f"{current_border_cases}\n{new_example}"
        else:
            category.border_cases = new_example
        
        db.add(category)
        db.commit()
        db.refresh(category)
        
        # Refresh classifier to use updated examples
        classification_agent.refresh_categories()
        
        logger.info(
            "training_example_added",
            category_id=category_id,
            category_name=category.name,
            example_text=text[:100]
        )
        
        return {
            "success": True,
            "message": f"Пример добавлен в категорию '{category.name}'",
            "category_id": category_id,
            "category_name": category.name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("add_training_example_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/intents/{intent_id}/add-training-example")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def add_intent_training_example(
    request: Request,
    intent_id: int,
    example: dict,
    db: Session = Depends(get_db_session)
):
    """Add a training example to intent's examples.
    
    When user corrects intent misclassification, add the example to help improve future classifications.
    
    Args:
        intent_id: Correct intent ID
        example: {"text": "user message that was misclassified"}
    """
    try:
        intent = db.get(Intent, intent_id)
        if not intent:
            raise HTTPException(status_code=404, detail="Intent not found")
        
        text = example.get("text", "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="Example text is required")
        
        # Add to examples
        current_examples = intent.examples or ""
        
        # Format: add as a new line with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d")
        new_example = f"- [{timestamp}] {text}"
        
        if current_examples:
            intent.examples = f"{current_examples}\n{new_example}"
        else:
            intent.examples = new_example
        
        db.add(intent)
        db.commit()
        db.refresh(intent)
        
        # Refresh classifier to use updated examples
        classification_agent.refresh_categories()
        
        logger.info(
            "intent_training_example_added",
            intent_id=intent_id,
            intent_name=intent.name,
            example_text=text[:100]
        )
        
        return {
            "success": True,
            "message": f"Пример добавлен в намерение '{intent.name}'",
            "intent_id": intent_id,
            "intent_name": intent.name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("add_intent_training_example_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

