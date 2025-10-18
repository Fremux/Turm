"""API endpoints for task management."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Depends, Query
from sqlmodel import Session, select, func

from app.core.config import settings
from app.core.limiter import limiter
from app.core.logging import logger
from app.services.database import get_db_session
from app.models.task import Task, TaskStatus
from app.models.category import Category
from app.core.langgraph.task_extractor import task_extractor
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskResponse, TasksListResponse,
    TaskExtractionRequest, TaskExtractionResponse
)

router = APIRouter()


# Task Management Endpoints

@router.post("/tasks", response_model=TaskResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def create_task(
    request: Request,
    task: TaskCreate,
    db: Session = Depends(get_db_session)
):
    """Create a new task.
    
    Args:
        request: FastAPI request
        task: Task data
        db: Database session
        
    Returns:
        TaskResponse: Created task
    """
    try:
        # Verify category exists if provided
        category_name = None
        if task.category_id:
            category = db.get(Category, task.category_id)
            if not category:
                raise HTTPException(status_code=404, detail="Category not found")
            category_name = category.name
        
        # Create task
        new_task = Task(
            summary=task.summary,
            description=task.description,
            assignee=task.assignee,
            category_id=task.category_id,
            priority=task.priority,
            original_message=task.original_message,
            created_by=task.created_by,
            status=TaskStatus.PENDING
        )
        
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        
        logger.info(
            "task_created",
            task_id=new_task.id,
            summary=new_task.summary,
            category=category_name
        )
        
        return TaskResponse(
            id=new_task.id,
            summary=new_task.summary,
            description=new_task.description,
            assignee=new_task.assignee,
            status=new_task.status,
            priority=new_task.priority,
            category_id=new_task.category_id,
            category_name=category_name,
            created_by=new_task.created_by,
            original_message=new_task.original_message,
            completed_at=new_task.completed_at,
            completed_by=new_task.completed_by,
            notes=new_task.notes,
            created_at=new_task.created_at,
            updated_at=new_task.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("task_creation_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create task")


@router.get("/tasks", response_model=TasksListResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def list_tasks(
    request: Request,
    status: Optional[str] = Query(default=None),
    category_id: Optional[int] = Query(default=None),
    priority: Optional[str] = Query(default=None),
    created_by: Optional[int] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session)
):
    """List all tasks with optional filtering.
    
    Args:
        request: FastAPI request
        status: Filter by status
        category_id: Filter by category
        priority: Filter by priority
        created_by: Filter by creator
        limit: Maximum number of results
        offset: Offset for pagination
        db: Database session
        
    Returns:
        TasksListResponse: List of tasks
    """
    try:
        # Build query
        query = select(Task)
        
        if status:
            query = query.where(Task.status == status)
        if category_id:
            query = query.where(Task.category_id == category_id)
        if priority:
            query = query.where(Task.priority == priority)
        if created_by:
            query = query.where(Task.created_by == created_by)
        
        # Order by created_at descending
        query = query.order_by(Task.created_at.desc())
        
        # Get total count
        count_query = select(func.count()).select_from(Task)
        if status:
            count_query = count_query.where(Task.status == status)
        if category_id:
            count_query = count_query.where(Task.category_id == category_id)
        if priority:
            count_query = count_query.where(Task.priority == priority)
        if created_by:
            count_query = count_query.where(Task.created_by == created_by)
        
        total = db.exec(count_query).first() or 0
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        tasks = db.exec(query).all()
        
        # Build responses with category names
        responses = []
        for task in tasks:
            category_name = None
            if task.category_id:
                category = db.get(Category, task.category_id)
                if category:
                    category_name = category.name
            
            responses.append(TaskResponse(
                id=task.id,
                summary=task.summary,
                description=task.description,
                assignee=task.assignee,
                status=task.status,
                priority=task.priority,
                category_id=task.category_id,
                category_name=category_name,
                created_by=task.created_by,
                original_message=task.original_message,
                completed_at=task.completed_at,
                completed_by=task.completed_by,
                notes=task.notes,
                created_at=task.created_at,
                updated_at=task.updated_at
            ))
        
        return TasksListResponse(tasks=responses, total=total)
        
    except Exception as e:
        logger.error("list_tasks_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list tasks")


@router.get("/tasks/{task_id}", response_model=TaskResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def get_task(
    request: Request,
    task_id: int,
    db: Session = Depends(get_db_session)
):
    """Get a specific task.
    
    Args:
        request: FastAPI request
        task_id: Task ID
        db: Database session
        
    Returns:
        TaskResponse: Task details
    """
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get category name
    category_name = None
    if task.category_id:
        category = db.get(Category, task.category_id)
        if category:
            category_name = category.name
    
    return TaskResponse(
        id=task.id,
        summary=task.summary,
        description=task.description,
        assignee=task.assignee,
        status=task.status,
        priority=task.priority,
        category_id=task.category_id,
        category_name=category_name,
        created_by=task.created_by,
        original_message=task.original_message,
        completed_at=task.completed_at,
        completed_by=task.completed_by,
        notes=task.notes,
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def update_task(
    request: Request,
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db_session)
):
    """Update a task.
    
    Args:
        request: FastAPI request
        task_id: Task ID
        task_update: Updated task data
        db: Database session
        
    Returns:
        TaskResponse: Updated task
    """
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update fields
    if task_update.summary is not None:
        task.summary = task_update.summary
    if task_update.description is not None:
        task.description = task_update.description
    if task_update.assignee is not None:
        task.assignee = task_update.assignee
    if task_update.status is not None:
        task.status = task_update.status
    if task_update.priority is not None:
        task.priority = task_update.priority
    if task_update.notes is not None:
        task.notes = task_update.notes
    if task_update.completed_at is not None:
        task.completed_at = task_update.completed_at
    if task_update.completed_by is not None:
        task.completed_by = task_update.completed_by
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # Get category name
    category_name = None
    if task.category_id:
        category = db.get(Category, task.category_id)
        if category:
            category_name = category.name
    
    logger.info("task_updated", task_id=task_id, status=task.status)
    
    return TaskResponse(
        id=task.id,
        summary=task.summary,
        description=task.description,
        assignee=task.assignee,
        status=task.status,
        priority=task.priority,
        category_id=task.category_id,
        category_name=category_name,
        created_by=task.created_by,
        original_message=task.original_message,
        completed_at=task.completed_at,
        completed_by=task.completed_by,
        notes=task.notes,
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@router.delete("/tasks/{task_id}")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def delete_task(
    request: Request,
    task_id: int,
    db: Session = Depends(get_db_session)
):
    """Delete a task.
    
    Args:
        request: FastAPI request
        task_id: Task ID
        db: Database session
        
    Returns:
        Dict with success message
    """
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(task)
    db.commit()
    
    logger.info("task_deleted", task_id=task_id)
    return {"message": "Task deleted successfully", "task_id": task_id}


# Task Extraction Endpoint

@router.post("/tasks/extract", response_model=TaskExtractionResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def extract_task_info(
    request: Request,
    extraction_request: TaskExtractionRequest
):
    """Extract task information from user message using LLM.
    
    Args:
        request: FastAPI request
        extraction_request: Message to extract task from
        
    Returns:
        TaskExtractionResponse: Extracted task information
    """
    try:
        extraction = await task_extractor.extract_task_info(
            message=extraction_request.message,
            category=extraction_request.category
        )
        
        if not extraction:
            raise HTTPException(
                status_code=400,
                detail="Failed to extract task information from message"
            )
        
        return extraction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("task_extraction_api_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to extract task information")

