"""Dynamic agent loader for loading and managing agents from database."""

import time
from typing import Optional, Dict, Any
from datetime import datetime

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from sqlmodel import Session, select

from app.core.config import settings
from app.core.logging import logger
from app.models.agent_config import AgentConfiguration, AgentInvocationLog
from app.services.database import database_service


class DynamicAgentLoader:
    """Loads and manages agents from database configurations.
    
    This allows creating and configuring agents through UI without code changes.
    Agents are loaded from database and can be triggered based on various conditions.
    """
    
    def __init__(self):
        """Initialize the agent loader."""
        self._agents: Dict[str, Dict[str, Any]] = {}
        self._llm_instances: Dict[str, ChatOpenAI] = {}
        
        try:
            self.load_agents()
            logger.info(
                "dynamic_agent_loader_initialized",
                agents_count=len(self._agents)
            )
        except Exception as e:
            logger.error("agent_loader_initialization_error", error=str(e), exc_info=True)
            # Don't fail initialization - allow app to start
    
    def load_agents(self):
        """Load all active agents from database."""
        try:
            with Session(database_service.engine) as session:
                # Get all active agents ordered by priority
                configs = session.exec(
                    select(AgentConfiguration)
                    .where(AgentConfiguration.is_active == True)
                    .order_by(AgentConfiguration.priority.desc())
                ).all()
                
                for config in configs:
                    try:
                        self._agents[config.name] = self._create_agent_config(config)
                        logger.debug(
                            "agent_loaded",
                            agent_name=config.name,
                            agent_type=config.agent_type,
                            trigger_type=config.trigger_type
                        )
                    except Exception as e:
                        logger.error(
                            "agent_load_failed",
                            agent_name=config.name,
                            error=str(e)
                        )
                
                logger.info(
                    "agents_loaded_from_database",
                    total_configs=len(configs),
                    loaded_successfully=len(self._agents)
                )
                
        except Exception as e:
            logger.error("load_agents_error", error=str(e), exc_info=True)
    
    def _create_agent_config(self, config: AgentConfiguration) -> Dict[str, Any]:
        """Create agent configuration dictionary from database model.
        
        Args:
            config: AgentConfiguration from database
            
        Returns:
            Dictionary with agent configuration and LLM instance
        """
        # Create or reuse LLM instance for this model configuration
        llm_key = f"{config.model}:{config.temperature}:{config.max_tokens}"
        
        if llm_key not in self._llm_instances:
            self._llm_instances[llm_key] = ChatOpenAI(
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_BASE_URL if settings.LLM_BASE_URL else None,
                streaming=False
            )
        
        return {
            'id': config.id,
            'agent_type': config.agent_type,
            'name': config.name,
            'display_name': config.display_name,
            'llm': self._llm_instances[llm_key],
            'system_prompt': config.system_prompt,
            'trigger_type': config.trigger_type,
            'trigger_value': config.trigger_value,
            'priority': config.priority,
            'additional_config': config.additional_config
        }
    
    def should_trigger_agent(self, agent_name: str, context: Dict[str, Any]) -> bool:
        """Check if agent should be triggered based on context.
        
        Args:
            agent_name: Name of the agent
            context: Context dictionary with 'message', 'category', 'intent', 'priority'
            
        Returns:
            True if agent should be triggered, False otherwise
        """
        agent = self._agents.get(agent_name)
        if not agent:
            logger.warning("agent_not_found_for_trigger_check", agent_name=agent_name)
            return False
        
        trigger_type = agent['trigger_type']
        trigger_value = agent['trigger_value']
        
        # Always trigger
        if trigger_type == 'always':
            return True
        
        # Trigger by category
        elif trigger_type == 'category':
            categories = trigger_value.get('categories', [])
            return context.get('category') in categories
        
        # Trigger by intent
        elif trigger_type == 'intent':
            intents = trigger_value.get('intents', [])
            return context.get('intent') in intents
        
        # Trigger by keyword
        elif trigger_type == 'keyword':
            message = context.get('message', '').lower()
            keywords = trigger_value.get('keywords', [])
            mode = trigger_value.get('mode', 'any')  # 'any' or 'all'
            
            if mode == 'all':
                return all(kw.lower() in message for kw in keywords)
            else:
                return any(kw.lower() in message for kw in keywords)
        
        # Trigger by priority
        elif trigger_type == 'priority':
            priorities = trigger_value.get('priorities', [])
            return context.get('priority') in priorities
        
        # Custom trigger logic (can be extended)
        elif trigger_type == 'custom':
            # Implement custom trigger logic here
            return False
        
        logger.warning(
            "unknown_trigger_type",
            agent_name=agent_name,
            trigger_type=trigger_type
        )
        return False
    
    def get_triggered_agents(self, context: Dict[str, Any]) -> list[Dict[str, Any]]:
        """Get all agents that should be triggered for given context.
        
        Args:
            context: Context dictionary
            
        Returns:
            List of agent configurations sorted by priority
        """
        triggered = []
        
        for agent_name, agent_config in self._agents.items():
            if self.should_trigger_agent(agent_name, context):
                triggered.append(agent_config)
        
        # Sort by priority (higher first)
        triggered.sort(key=lambda x: x['priority'], reverse=True)
        
        return triggered
    
    async def execute_agent(
        self,
        agent_name: str,
        message: str,
        context: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute an agent with given message and context.
        
        Args:
            agent_name: Name of the agent to execute
            message: User message
            context: Context dictionary
            session_id: Optional session ID for logging
            
        Returns:
            Dictionary with 'response', 'confidence', and other agent-specific data
        """
        agent = self._agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found")
        
        start_time = time.time()
        agent_id = agent['id']
        
        try:
            # Prepare messages
            messages = []
            
            if agent['system_prompt']:
                messages.append(SystemMessage(content=agent['system_prompt']))
            
            # Add context to user message if needed
            user_prompt = message
            if context:
                context_str = f"\nКонтекст: Категория={context.get('category')}, Намерение={context.get('intent')}, Приоритет={context.get('priority')}"
                user_prompt = message + context_str
            
            messages.append(HumanMessage(content=user_prompt))
            
            # Invoke LLM
            response = await agent['llm'].ainvoke(messages)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Parse response
            result = {
                'response': response.content,
                'confidence': 0.8,  # Default, can be extracted from response
                'agent_name': agent_name,
                'execution_time_ms': execution_time
            }
            
            # Log invocation
            if session_id:
                self._log_invocation(
                    agent_id=agent_id,
                    session_id=session_id,
                    message=message,
                    context=context,
                    response=response.content,
                    execution_time_ms=execution_time,
                    status="success"
                )
            
            # Update agent stats
            self._update_agent_stats(agent_id, 0.8, execution_time)
            
            logger.info(
                "agent_executed",
                agent_name=agent_name,
                execution_time_ms=execution_time,
                response_length=len(response.content)
            )
            
            return result
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            
            logger.error(
                "agent_execution_error",
                agent_name=agent_name,
                error=str(e),
                exc_info=True
            )
            
            # Log failed invocation
            if session_id:
                self._log_invocation(
                    agent_id=agent_id,
                    session_id=session_id,
                    message=message,
                    context=context,
                    response=None,
                    execution_time_ms=execution_time,
                    status="error",
                    error_message=str(e)
                )
            
            raise
    
    def _log_invocation(
        self,
        agent_id: int,
        session_id: str,
        message: str,
        context: Dict[str, Any],
        response: Optional[str],
        execution_time_ms: int,
        status: str,
        error_message: Optional[str] = None
    ):
        """Log agent invocation to database."""
        try:
            with Session(database_service.engine) as session:
                log = AgentInvocationLog(
                    agent_config_id=agent_id,
                    session_id=session_id,
                    user_message=message[:1000],  # Truncate if too long
                    category=context.get('category'),
                    intent=context.get('intent'),
                    priority=context.get('priority'),
                    agent_response=response[:2000] if response else None,
                    execution_time_ms=execution_time_ms,
                    status=status,
                    error_message=error_message[:500] if error_message else None
                )
                session.add(log)
                session.commit()
        except Exception as e:
            logger.error("log_invocation_error", error=str(e))
    
    def _update_agent_stats(self, agent_id: int, confidence: float, execution_time_ms: int):
        """Update agent statistics."""
        try:
            with Session(database_service.engine) as session:
                agent = session.get(AgentConfiguration, agent_id)
                if agent:
                    # Update counters
                    agent.total_invocations += 1
                    
                    # Update average confidence
                    if agent.avg_confidence is None:
                        agent.avg_confidence = confidence
                    else:
                        # Running average
                        agent.avg_confidence = (
                            agent.avg_confidence * (agent.total_invocations - 1) + confidence
                        ) / agent.total_invocations
                    
                    agent.last_invoked_at = datetime.utcnow()
                    
                    session.add(agent)
                    session.commit()
        except Exception as e:
            logger.error("update_agent_stats_error", agent_id=agent_id, error=str(e))
    
    def get_agent(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get agent configuration by name.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent configuration dictionary or None
        """
        return self._agents.get(agent_name)
    
    def refresh(self):
        """Reload agents from database.
        
        This should be called when agent configurations are added/updated/deleted.
        """
        logger.info("refreshing_agents_from_database")
        self._agents.clear()
        # Don't clear LLM instances - they can be reused
        self.load_agents()
    
    def get_agents_by_type(self, agent_type: str) -> list[Dict[str, Any]]:
        """Get all agents of a specific type.
        
        Args:
            agent_type: Type of agents to get
            
        Returns:
            List of agent configurations
        """
        return [
            agent for agent in self._agents.values()
            if agent['agent_type'] == agent_type
        ]


# Global instance - initialized when imported
agent_loader = DynamicAgentLoader()

