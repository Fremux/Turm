"""Chatbot API endpoints for handling chat interactions.

This module provides endpoints for chat interactions, including regular chat,
streaming chat, message history management, and chat history clearing.
"""

import json
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)
from fastapi.responses import StreamingResponse
from app.core.metrics import llm_stream_duration_seconds
from app.core.config import settings
from app.core.langgraph.graph import LangGraphAgent
from app.core.langgraph.entity_extractor import EntityExtractor
from app.core.langgraph.classifier import classification_agent
from app.core.langgraph.react_agent import get_react_agent
from app.core.langgraph.task_extractor import task_extractor
from app.core.limiter import limiter
from app.core.logging import logger
from app.models.entity import UserEntity
from app.models.agent_analysis import AgentAnalysis
from app.models.task import Task
from app.models.category import Category
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    Message,
    StreamResponse,
)
from app.schemas.classification import TicketCategory
from app.services.database import get_session as get_db_session
from sqlmodel import Session

router = APIRouter()
agent = LangGraphAgent()
entity_extractor = EntityExtractor()


async def _extract_and_store_entities(messages: List[Message], session_id: str, user_id: int, db):
    """Extract entities from user messages and store them in the database.
    
    Args:
        messages: List of messages to extract entities from
        session_id: The session ID
        user_id: The user ID
        db: Database session (sync SQLModel session)
    """
    try:
        # Only extract from the latest user message
        user_messages = [msg for msg in messages if msg.role == "user"]
        if not user_messages:
            return
        
        last_message = user_messages[-1]
        entities = await entity_extractor.extract_entities(last_message.content)
        
        if entities:
            # Store entities in database (sync operations)
            for entity_data in entities:
                entity = UserEntity(
                    user_id=user_id,
                    session_id=session_id,
                    entity_type=entity_data["entity_type"],
                    entity_value=entity_data["entity_value"],
                    context=entity_data.get("context"),
                    confidence=1.0
                )
                db.add(entity)
            
            db.commit()  # Sync commit, not await
            logger.info("entities_stored", count=len(entities), session_id=session_id)
    except Exception as e:
        # Don't fail the chat request if entity extraction fails
        logger.error("entity_extraction_failed", error=str(e), session_id=session_id, exc_info=True)


async def _create_task_if_needed(user_message: str, classification, user_id: int, db):
    """Check if intent is task_creation and create a task if confidence is high enough.
    
    Args:
        user_message: User message text
        classification: Classification result with intent
        user_id: User ID
        db: Database session (sync SQLModel session)
    
    Returns:
        Task object if created, None otherwise
    """
    try:
        # Check if intent is task_creation
        if not classification:
            return None
        
        # Get intent name (handle None case)
        intent_name = None
        if hasattr(classification, 'intent') and classification.intent:
            intent_name = classification.intent if isinstance(classification.intent, str) else getattr(classification.intent, 'name', None)
        
        if intent_name != "task_creation":
            logger.debug("intent_not_task_creation", intent=intent_name)
            return None
        
        logger.info("task_creation_intent_detected", user_message=user_message)
        
        # Extract task information
        category_name = classification.category if hasattr(classification, 'category') else None
        extraction = await task_extractor.extract_task_info(user_message, category=category_name)
        
        if not extraction:
            logger.warning("task_extraction_failed", user_message=user_message)
            return None
        
        # Check confidence threshold
        if extraction.confidence < 0.7:
            logger.info("task_confidence_too_low", confidence=extraction.confidence)
            return None
        
        # Get category_id if category exists
        category_id = None
        if category_name:
            from sqlmodel import select
            category = db.exec(select(Category).where(Category.name == category_name)).first()
            if category:
                category_id = category.id
        
        # Try to assign to a role based on task content
        assigned_role = None
        try:
            from app.services.role_assignment_service import role_assignment_service
            assigned_role = role_assignment_service.find_best_role(
                task_summary=extraction.summary,
                task_description=extraction.description,
                category=category_name,
                session=db
            )
        except Exception as role_error:
            logger.warning(f"Could not assign role: {role_error}")
        
        # Create task
        task = Task(
            summary=extraction.summary,
            description=extraction.description,
            assignee=extraction.assignee,
            category_id=category_id,
            assigned_role_id=assigned_role.id if assigned_role else None,
            priority=extraction.priority,
            original_message=user_message,
            created_by=user_id,
            status="pending"
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        logger.info(
            "task_created_successfully",
            task_id=task.id,
            summary=task.summary,
            priority=task.priority,
            confidence=extraction.confidence
        )
        
        # Try to create task in YouTrack (non-blocking, optional)
        try:
            from app.services.youtrack_service import youtrack_service
            
            if youtrack_service.is_enabled():
                # Create task in YouTrack with only summary and description
                yt_task = youtrack_service.create_task(
                    summary=task.summary,
                    description=task.description
                )
                
                if yt_task:
                    # Update task notes with YouTrack ID
                    yt_id = yt_task.get('idReadable', 'Unknown')
                    task.notes = f"YouTrack: {yt_id}"
                    db.commit()
                    logger.info("task_synced_to_youtrack", task_id=task.id, youtrack_id=yt_id)
                else:
                    logger.warning("task_youtrack_sync_failed", task_id=task.id, reason="Creation failed")
            else:
                logger.debug("youtrack_sync_skipped", task_id=task.id, reason="Integration disabled")
                
        except Exception as yt_error:
            # Don't fail the whole operation if YouTrack sync fails
            logger.error(
                "youtrack_sync_error",
                task_id=task.id,
                error=str(yt_error),
                message="Задача создана в системе, но не удалось добавить в YouTrack"
            )
        
        return task
        
    except Exception as e:
        logger.error("task_creation_failed", error=str(e), exc_info=True)
        return None



@router.post("/chat", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["chat"][0])
async def chat(
    request: Request,
    chat_request: ChatRequest,
    session_id: str,
    user_id: int,
    db = Depends(get_db_session),
    use_react_agent: bool = False,
):
    """Process a chat request using LangGraph.

    Args:
        request: The FastAPI request object for rate limiting.
        chat_request: The chat request containing messages.
        session_id: The session ID for this chat.
        user_id: The user ID.
        db: Database session for storing entities.
        use_react_agent: If True, classifies message and uses ReAct agent if category is not "other"

    Returns:
        ChatResponse: The processed chat response.

    Raises:
        HTTPException: If there's an error processing the request.
    """
    try:
        logger.info(
            "chat_request_received",
            session_id=session_id,
            user_id=user_id,
            message_count=len(chat_request.messages),
            use_react_agent=use_react_agent,
        )

        # Extract entities from user messages (run in background)
        await _extract_and_store_entities(chat_request.messages, session_id, user_id, db)

        # Get the last user message for classification
        user_messages = [msg for msg in chat_request.messages if msg.role == "user"]
        last_user_message = user_messages[-1].content if user_messages else ""

        # Always classify user messages for task detection
        classification = None
        created_task = None
        if last_user_message:
            classification = await classification_agent.classify(last_user_message)
            
            # Try to create task if intent is task_creation
            created_task = await _create_task_if_needed(last_user_message, classification, user_id, db)
        
        # If use_react_agent is enabled, use ReAct agent for non-"other" categories
        # BUT skip ReAct agent if task was created (task_creation intent)
        if use_react_agent and classification and last_user_message and not created_task:
            # Check if category is not "other" (both enum and string comparison for safety)
            is_not_other = (
                classification and 
                classification.category != TicketCategory.OTHER and
                str(classification.category).lower() != "other"
            )
            
            logger.info(
                "react_agent_decision_non_stream",
                session_id=session_id,
                category=str(classification.category) if classification else None,
                will_trigger=is_not_other,
                task_created=False
            )
            
            if is_not_other:
                logger.info(
                    "triggering_react_agent",
                    session_id=session_id,
                    category=classification.category,
                    priority=classification.priority
                )
                
                try:
                    # Use ReAct agent for analysis
                    react_agent_instance = get_react_agent()
                    analysis_result = await react_agent_instance.analyze_problem(
                        user_message=last_user_message,
                        classification=classification,
                        session_id=session_id
                    )
                    
                    # Save analysis to database ONLY if there's a concrete solution
                    # (not just questions for clarification)
                    has_solution = analysis_result.get('has_solution', True)
                    
                    if has_solution:
                        try:
                            from app.services.database import database_service
                            
                            agent_analysis = AgentAnalysis(
                                user_id=user_id,
                                session_id=session_id,
                                problem=analysis_result['problem'],
                                category=analysis_result['classification']['category'],
                                priority=analysis_result['classification']['priority'],
                                confidence=analysis_result['classification']['confidence'],
                                reasoning=analysis_result['classification']['reasoning'],
                                solution=analysis_result['solution'],
                                summary=analysis_result['summary']
                            )
                            
                            # Use sync session from database service
                            with Session(database_service.engine) as sync_db:
                                sync_db.add(agent_analysis)
                                sync_db.commit()
                                sync_db.refresh(agent_analysis)
                            
                            logger.info(
                                "agent_analysis_saved",
                                analysis_id=agent_analysis.id,
                                session_id=session_id,
                                user_id=user_id
                            )
                        except Exception as db_error:
                            logger.error(
                                "agent_analysis_save_failed",
                                error=str(db_error),
                                session_id=session_id,
                                exc_info=True
                            )
                            # Don't fail the request if DB save fails
                    else:
                        logger.info(
                            "agent_analysis_not_saved",
                            reason="insufficient_data",
                            session_id=session_id,
                            message="Agent asked clarifying questions instead of providing solution"
                        )
                    
                    # Format the response as a chat message
                    response_content = f"""**Анализ проблемы завершен**

**Классификация:**
- Категория: {analysis_result['classification']['category'].upper()}
- Приоритет: {analysis_result['classification']['priority'].upper()}

**Решение:**
{analysis_result['solution']}
"""
                    
                    result = [Message(role="assistant", content=response_content)]
                    
                    logger.info("react_agent_response_sent", session_id=session_id)
                    return ChatResponse(messages=result)
                    
                except Exception as react_error:
                    logger.error(
                        "react_agent_failed_fallback_to_regular",
                        error=str(react_error),
                        session_id=session_id,
                        exc_info=True
                    )
                    # Fall through to regular agent

        # If task was created, just return the task notification
        if created_task:
            task_notification = f"""✅ **Задача создана!**

**Задача #{created_task.id}:** {created_task.summary}
**Описание:** {created_task.description}
**Исполнитель:** {created_task.assignee}
**Приоритет:** {created_task.priority.upper()}
**Статус:** Ожидает выполнения

Вы можете отслеживать статус задачи в админ-панели."""
            
            result = [Message(role="assistant", content=task_notification)]
            logger.info("chat_request_processed_task_created", session_id=session_id, task_id=created_task.id)
            return ChatResponse(messages=result)
        
        # Use regular agent (only if no task was created)
        result = await agent.get_response(
            chat_request.messages, session_id, user_id=user_id
        )

        logger.info("chat_request_processed", session_id=session_id, task_created=False)

        return ChatResponse(messages=result)
    except Exception as e:
        logger.error("chat_request_failed", session_id=session_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["chat_stream"][0])
async def chat_stream(
    request: Request,
    chat_request: ChatRequest,
    session_id: str,
    user_id: int,
    db = Depends(get_db_session),
    use_react_agent: bool = False,
):
    """Process a chat request using LangGraph with streaming response.

    Args:
        request: The FastAPI request object for rate limiting.
        chat_request: The chat request containing messages.
        session_id: The session ID for this chat.
        user_id: The user ID.
        db: Database session for storing entities.
        use_react_agent: If True, classifies message and uses ReAct agent if category is not "other"

    Returns:
        StreamingResponse: A streaming response of the chat completion.

    Raises:
        HTTPException: If there's an error processing the request.
    """
    try:
        logger.info(
            "stream_chat_request_received",
            session_id=session_id,
            user_id=user_id,
            message_count=len(chat_request.messages),
            use_react_agent=use_react_agent,
        )
        
        # Extract entities from user messages (run in background)
        await _extract_and_store_entities(chat_request.messages, session_id, user_id, db)

        # Get the last user message for classification
        user_messages = [msg for msg in chat_request.messages if msg.role == "user"]
        last_user_message = user_messages[-1].content if user_messages else ""
        
        # Always classify and try to create task
        classification = None
        created_task = None
        if last_user_message:
            classification = await classification_agent.classify(last_user_message)
            created_task = await _create_task_if_needed(last_user_message, classification, user_id, db)

        async def event_generator():
            """Generate streaming events.

            Yields:
                str: Server-sent events in JSON format.

            Raises:
                Exception: If there's an error during streaming.
            """
            try:
                # Send task notification first if task was created
                if created_task:
                    task_notification = f"""✅ **Задача создана!**

**Задача #{created_task.id}:** {created_task.summary}
**Описание:** {created_task.description}
**Исполнитель:** {created_task.assignee}
**Приоритет:** {created_task.priority.upper()}
**Статус:** Ожидает выполнения

Вы можете отслеживать статус задачи в админ-панели.

---

"""
                    # Stream task notification
                    chunk_size = 50
                    for i in range(0, len(task_notification), chunk_size):
                        chunk = task_notification[i:i + chunk_size]
                        response = StreamResponse(content=chunk, done=False)
                        yield f"data: {json.dumps(response.model_dump())}\n\n"
                    
                    # Send final message and return (don't call regular agent)
                    final_response = StreamResponse(content="", done=True)
                    yield f"data: {json.dumps(final_response.model_dump())}\n\n"
                    logger.info("stream_task_created_completed", session_id=session_id, task_id=created_task.id)
                    return
                
                # Check if we should use ReAct agent (classification already done above)
                # Note: This won't be reached if task was created (we return above)
                should_use_react = use_react_agent and classification and last_user_message
                
                if should_use_react:
                    # Check if category is not "other" (both enum and string comparison for safety)
                    is_not_other = (
                        classification and 
                        classification.category != TicketCategory.OTHER and
                        str(classification.category).lower() != "other"
                    )
                    
                    logger.info(
                        "react_agent_decision",
                        session_id=session_id,
                        category=str(classification.category) if classification else None,
                        will_trigger=is_not_other
                    )
                    
                    if is_not_other:
                        logger.info(
                            "triggering_react_agent_stream",
                            session_id=session_id,
                            category=classification.category,
                            priority=classification.priority
                        )
                        
                        try:
                            # Use ReAct agent for analysis
                            react_agent_instance = get_react_agent()
                            analysis_result = await react_agent_instance.analyze_problem(
                                user_message=last_user_message,
                                classification=classification,
                                session_id=session_id
                            )
                            
                            # Save analysis to database ONLY if there's a concrete solution
                            # (not just questions for clarification)
                            has_solution = analysis_result.get('has_solution', True)
                            
                            if has_solution:
                                try:
                                    from app.services.database import database_service
                                    
                                    agent_analysis = AgentAnalysis(
                                        user_id=user_id,
                                        session_id=session_id,
                                        problem=analysis_result['problem'],
                                        category=analysis_result['classification']['category'],
                                        priority=analysis_result['classification']['priority'],
                                        confidence=analysis_result['classification']['confidence'],
                                        reasoning=analysis_result['classification']['reasoning'],
                                        solution=analysis_result['solution'],
                                        summary=analysis_result['summary']
                                    )
                                    
                                    # Use sync session from database service
                                    with Session(database_service.engine) as sync_db:
                                        sync_db.add(agent_analysis)
                                        sync_db.commit()
                                        sync_db.refresh(agent_analysis)
                                    
                                    logger.info(
                                        "agent_analysis_saved",
                                        analysis_id=agent_analysis.id,
                                        session_id=session_id,
                                        user_id=user_id
                                    )
                                except Exception as db_error:
                                    logger.error(
                                        "agent_analysis_save_failed",
                                        error=str(db_error),
                                        session_id=session_id,
                                        exc_info=True
                                    )
                                    # Don't fail the request if DB save fails
                            else:
                                logger.info(
                                    "agent_analysis_not_saved_stream",
                                    reason="insufficient_data",
                                    session_id=session_id,
                                    message="Agent asked clarifying questions instead of providing solution"
                                )
                            
                            # Format the response
                            response_content = f"""**🤖 Анализ проблемы завершен**

**📋 Классификация:**
- **Категория**: {analysis_result['classification']['category'].upper()}
- **Приоритет**: {analysis_result['classification']['priority'].upper()}
- **Уверенность**: {analysis_result['classification']['confidence']:.0%}

**💡 Решение:**

{analysis_result['solution']}
"""
                            
                            # Stream the response in chunks for better UX
                            chunk_size = 50
                            for i in range(0, len(response_content), chunk_size):
                                chunk = response_content[i:i + chunk_size]
                                response = StreamResponse(content=chunk, done=False)
                                yield f"data: {json.dumps(response.model_dump())}\n\n"
                            
                            # Send final message
                            final_response = StreamResponse(content="", done=True)
                            yield f"data: {json.dumps(final_response.model_dump())}\n\n"
                            
                            logger.info("react_agent_stream_completed", session_id=session_id)
                            return
                            
                        except Exception as react_error:
                            logger.error(
                                "react_agent_stream_failed_fallback",
                                error=str(react_error),
                                session_id=session_id,
                                exc_info=True
                            )
                            # Fall through to regular streaming
                    else:
                        logger.info(
                            "skipping_react_agent_stream",
                            session_id=session_id,
                            category=str(classification.category) if classification else None,
                            reason="Category is 'other' or classification failed"
                        )
                        # Fall through to regular streaming
                
                # Regular streaming response
                full_response = ""
                with llm_stream_duration_seconds.labels(model=agent.llm.model_name).time():
                    async for chunk in agent.get_stream_response(
                        chat_request.messages, session_id, user_id=user_id
                     ):
                        full_response += chunk
                        response = StreamResponse(content=chunk, done=False)
                        yield f"data: {json.dumps(response.model_dump())}\n\n"

                # Send final message indicating completion
                final_response = StreamResponse(content="", done=True)
                yield f"data: {json.dumps(final_response.model_dump())}\n\n"

            except Exception as e:
                logger.error(
                    "stream_chat_request_failed",
                    session_id=session_id,
                    error=str(e),
                    exc_info=True,
                )
                error_response = StreamResponse(content=str(e), done=True)
                yield f"data: {json.dumps(error_response.model_dump())}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        logger.error(
            "stream_chat_request_failed",
            session_id=session_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def get_session_messages(
    request: Request,
    session_id: str,
):
    """Get all messages for a session.

    Args:
        request: The FastAPI request object for rate limiting.
        session_id: The session ID to retrieve messages for.

    Returns:
        ChatResponse: All messages in the session.

    Raises:
        HTTPException: If there's an error retrieving the messages.
    """
    try:
        messages = await agent.get_chat_history(session_id)
        return ChatResponse(messages=messages)
    except Exception as e:
        logger.error("get_messages_failed", session_id=session_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/messages")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def clear_chat_history(
    request: Request,
    session_id: str,
):
    """Clear all messages for a session.

    Args:
        request: The FastAPI request object for rate limiting.
        session_id: The session ID to clear messages for.

    Returns:
        dict: A message indicating the chat history was cleared.
    """
    try:
        await agent.clear_chat_history(session_id)
        return {"message": "Chat history cleared successfully"}
    except Exception as e:
        logger.error("clear_chat_history_failed", session_id=session_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
