"""API endpoints for agent configuration management."""

import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Depends, Query
from sqlmodel import Session, select, func

from app.core.config import settings
from app.core.limiter import limiter
from app.core.logging import logger
from app.services.database import get_db_session
from app.models.agent_config import AgentConfiguration, AgentInvocationLog
from app.schemas.agent_config import (
    AgentConfigCreate,
    AgentConfigUpdate,
    AgentConfigResponse,
    AgentConfigListResponse,
    AgentTestRequest,
    AgentTestResponse,
    AgentInvocationLogResponse,
    AgentStatsResponse
)

router = APIRouter()


# Agent Configuration Endpoints

@router.post("/agents", response_model=AgentConfigResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def create_agent_config(
    request: Request,
    agent_config: AgentConfigCreate,
    db: Session = Depends(get_db_session)
):
    """Create a new agent configuration.
    
    This allows creating custom agents without code changes.
    """
    try:
        # Check if agent with this name already exists
        existing = db.exec(
            select(AgentConfiguration).where(AgentConfiguration.name == agent_config.name)
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Agent '{agent_config.name}' already exists"
            )
        
        # Create agent configuration
        new_agent = AgentConfiguration(
            agent_type=agent_config.agent_type,
            name=agent_config.name,
            display_name=agent_config.display_name,
            description=agent_config.description,
            trigger_type=agent_config.trigger_type,
            trigger_value=agent_config.trigger_value,
            system_prompt=agent_config.system_prompt,
            model=agent_config.model,
            temperature=agent_config.temperature,
            max_tokens=agent_config.max_tokens,
            enabled_tools=agent_config.enabled_tools,
            additional_config=agent_config.additional_config,
            is_active=agent_config.is_active,
            priority=agent_config.priority,
            tags=agent_config.tags
        )
        
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)
        
        logger.info(
            "agent_config_created",
            agent_name=agent_config.name,
            agent_id=new_agent.id,
            agent_type=agent_config.agent_type
        )
        
        # Refresh agent loader
        try:
            from app.services.agent_loader import agent_loader
            agent_loader.refresh()
        except Exception as e:
            logger.warning("failed_to_refresh_agent_loader", error=str(e))
        
        return AgentConfigResponse.from_orm(new_agent)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("agent_config_creation_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create agent configuration")


@router.get("/agents", response_model=AgentConfigListResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def list_agent_configs(
    request: Request,
    agent_type: Optional[str] = Query(default=None),
    active_only: bool = Query(default=True),
    db: Session = Depends(get_db_session)
):
    """List all agent configurations."""
    try:
        query = select(AgentConfiguration)
        
        if active_only:
            query = query.where(AgentConfiguration.is_active == True)
        if agent_type:
            query = query.where(AgentConfiguration.agent_type == agent_type)
        
        query = query.order_by(AgentConfiguration.priority.desc())
        
        agents = db.exec(query).all()
        
        responses = [AgentConfigResponse.from_orm(agent) for agent in agents]
        
        return AgentConfigListResponse(agents=responses, total=len(responses))
        
    except Exception as e:
        logger.error("list_agent_configs_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list agent configurations")


@router.get("/agents/{agent_id}", response_model=AgentConfigResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def get_agent_config(
    request: Request,
    agent_id: int,
    db: Session = Depends(get_db_session)
):
    """Get a specific agent configuration."""
    agent = db.get(AgentConfiguration, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent configuration not found")
    
    return AgentConfigResponse.from_orm(agent)


@router.patch("/agents/{agent_id}", response_model=AgentConfigResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def update_agent_config(
    request: Request,
    agent_id: int,
    agent_update: AgentConfigUpdate,
    db: Session = Depends(get_db_session)
):
    """Update an agent configuration."""
    agent = db.get(AgentConfiguration, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent configuration not found")
    
    # Update fields
    update_data = agent_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(agent, key, value)
    
    db.add(agent)
    db.commit()
    db.refresh(agent)
    
    logger.info("agent_config_updated", agent_id=agent_id)
    
    # Refresh agent loader
    try:
        from app.services.agent_loader import agent_loader
        agent_loader.refresh()
    except Exception as e:
        logger.warning("failed_to_refresh_agent_loader", error=str(e))
    
    return AgentConfigResponse.from_orm(agent)


@router.delete("/agents/{agent_id}")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def delete_agent_config(
    request: Request,
    agent_id: int,
    permanent: bool = Query(default=False),
    db: Session = Depends(get_db_session)
):
    """Delete an agent configuration (soft delete by default)."""
    agent = db.get(AgentConfiguration, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent configuration not found")
    
    if permanent:
        # Hard delete
        db.delete(agent)
        db.commit()
        logger.info("agent_config_permanently_deleted", agent_id=agent_id)
    else:
        # Soft delete
        agent.is_active = False
        db.add(agent)
        db.commit()
        logger.info("agent_config_soft_deleted", agent_id=agent_id)
    
    # Refresh agent loader
    try:
        from app.services.agent_loader import agent_loader
        agent_loader.refresh()
    except Exception as e:
        logger.warning("failed_to_refresh_agent_loader", error=str(e))
    
    return {"message": "Agent configuration deleted", "agent_id": agent_id}


@router.post("/agents/{agent_id}/test", response_model=AgentTestResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def test_agent_config(
    request: Request,
    agent_id: int,
    test_request: AgentTestRequest,
    db: Session = Depends(get_db_session)
):
    """Test an agent configuration with a sample message."""
    agent = db.get(AgentConfiguration, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent configuration not found")
    
    try:
        # Import agent loader
        from app.services.agent_loader import agent_loader
        
        # Build context
        context = {
            'message': test_request.message,
            'category': test_request.category,
            'intent': test_request.intent,
            'priority': test_request.priority
        }
        
        # For testing, we FORCE execution regardless of triggers
        # This allows users to test agent functionality directly
        logger.info("agent_test_forced_execution", agent_id=agent_id, agent_name=agent.name)
        
        # Execute agent (forced)
        start_time = time.time()
        
        try:
            result = await agent_loader.execute_agent(
                agent.name,
                test_request.message,
                context
            )
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return AgentTestResponse(
                agent_id=agent_id,
                agent_name=agent.name,
                triggered=True,
                response=result.get('response'),
                confidence=result.get('confidence'),
                execution_time_ms=execution_time,
                error=None
            )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            logger.error("agent_test_execution_error", agent_id=agent_id, error=str(e))
            
            return AgentTestResponse(
                agent_id=agent_id,
                agent_name=agent.name,
                triggered=True,
                response=None,
                confidence=None,
                execution_time_ms=execution_time,
                error=str(e)
            )
        
    except Exception as e:
        logger.error("agent_test_error", agent_id=agent_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


@router.get("/agents/{agent_id}/stats", response_model=AgentStatsResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def get_agent_stats(
    request: Request,
    agent_id: int,
    db: Session = Depends(get_db_session)
):
    """Get statistics for an agent."""
    agent = db.get(AgentConfiguration, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent configuration not found")
    
    try:
        # Calculate stats from logs
        success_count = db.exec(
            select(func.count(AgentInvocationLog.id))
            .where(AgentInvocationLog.agent_config_id == agent_id)
            .where(AgentInvocationLog.status == "success")
        ).first() or 0
        
        error_count = db.exec(
            select(func.count(AgentInvocationLog.id))
            .where(AgentInvocationLog.agent_config_id == agent_id)
            .where(AgentInvocationLog.status == "error")
        ).first() or 0
        
        avg_execution = db.exec(
            select(func.avg(AgentInvocationLog.execution_time_ms))
            .where(AgentInvocationLog.agent_config_id == agent_id)
            .where(AgentInvocationLog.status == "success")
        ).first()
        
        return AgentStatsResponse(
            agent_id=agent.id,
            agent_name=agent.name,
            total_invocations=agent.total_invocations,
            success_count=success_count,
            error_count=error_count,
            avg_confidence=agent.avg_confidence,
            avg_execution_time_ms=float(avg_execution) if avg_execution else None,
            last_invoked_at=agent.last_invoked_at
        )
        
    except Exception as e:
        logger.error("get_agent_stats_error", agent_id=agent_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get agent statistics")


@router.get("/agents/{agent_id}/logs", response_model=list[AgentInvocationLogResponse])
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def get_agent_logs(
    request: Request,
    agent_id: int,
    limit: int = Query(default=50, ge=1, le=1000),
    db: Session = Depends(get_db_session)
):
    """Get recent invocation logs for an agent."""
    agent = db.get(AgentConfiguration, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent configuration not found")
    
    try:
        logs = db.exec(
            select(AgentInvocationLog)
            .where(AgentInvocationLog.agent_config_id == agent_id)
            .order_by(AgentInvocationLog.created_at.desc())
            .limit(limit)
        ).all()
        
        return [AgentInvocationLogResponse.from_orm(log) for log in logs]
        
    except Exception as e:
        logger.error("get_agent_logs_error", agent_id=agent_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get agent logs")


@router.get("/tools")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def list_available_tools(request: Request):
    """List all available tools from the tool registry.
    
    Returns:
        List of tool metadata (id, name, category, description, etc.)
    """
    try:
        from app.core.langgraph.tools import tool_registry
        
        tools = tool_registry.list_all()
        
        logger.info("tools_listed", count=len(tools))
        return {"tools": tools, "total": len(tools)}
        
    except Exception as e:
        logger.error("list_tools_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list tools")


@router.get("/tools/categories")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def list_tool_categories(request: Request):
    """List all tool categories.
    
    Returns:
        List of unique tool categories
    """
    try:
        from app.core.langgraph.tools import tool_registry
        
        tools = tool_registry.list_all()
        categories = list(set(tool["category"] for tool in tools))
        
        logger.info("tool_categories_listed", count=len(categories))
        return {"categories": categories, "total": len(categories)}
        
    except Exception as e:
        logger.error("list_tool_categories_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list tool categories")

