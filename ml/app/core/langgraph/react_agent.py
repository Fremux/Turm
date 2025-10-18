"""ReAct Agent for problem analysis and resolution.

This module implements a ReAct (Reasoning + Acting) agent that analyzes user problems,
uses tools to gather information, and provides comprehensive solutions.
"""

import json
from typing import Annotated, Sequence, TypedDict, Optional, List, Dict, Any
from functools import lru_cache

from langchain_core.messages import (
    BaseMessage, 
    SystemMessage, 
    HumanMessage,
    AIMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.core.config import settings
from app.core.logging import logger
from app.schemas.classification import TicketClassification


class AgentState(TypedDict):
    """The state of the ReAct agent.
    
    Attributes:
        messages: The conversation history with the agent
        session_id: The session ID for tracking
        classification: The initial classification of the problem
        problem_summary: A summary of the analyzed problem
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    session_id: str
    classification: Optional[Dict[str, Any]]
    problem_summary: Optional[str]


class ReActAgent:
    """ReAct Agent for analyzing and solving user problems.
    
    This agent uses autonomous reasoning to:
    1. Analyze if there's enough information about the problem
    2. Ask clarifying questions if needed (2-3 specific questions)
    3. Provide comprehensive solutions with step-by-step instructions
    4. Return a structured result with classification and summary
    
    The agent operates in autonomous mode without external tools,
    relying on its own knowledge and reasoning capabilities.
    """
    
    def __init__(self, tools: List[BaseTool] = None):
        """Initialize the ReAct agent.
        
        Args:
            tools: List of tools available to the agent (not used currently)
        """
        # No tools for now - model works autonomously
        self.tools = []
        self.tools_by_name = {}
        
        # Initialize LLM for the agent
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0.4,  # Slightly higher for more creative problem-solving
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL if settings.LLM_BASE_URL else None,
            streaming=False,
        )
        
        # No tools binding - pure reasoning agent
        self.llm_with_tools = self.llm
        
        # System prompt for the agent
        self.system_prompt = """Ты эксперт-помощник IT службы поддержки. Ты анализируешь технические проблемы и помогаешь их решать.

ВАЖНО: Отвечай ТОЛЬКО на русском языке. Никогда не используй символы из других языков (кроме английских технических терминов).

Твоя задача - АВТОНОМНЫЙ АНАЛИЗ проблемы:

1. **Оценка информации**: Проанализируй, достаточно ли данных для решения
   
2. **Если информации НЕДОСТАТОЧНО** (проблема описана слишком общо, например "не работает X"):
   Начни ответ с: **Оценка информации**: Информации недостаточно
   Затем раздел: **Вопросы для уточнения**:
   - Какая точная ошибка? (текст ошибки, код)
   - Какие команды/действия уже пробовали?
   - Что изменилось перед появлением проблемы?
   НЕ давай решение, если данных недостаточно - только вопросы!
   
3. **Если информации ДОСТАТОЧНО** (есть конкретные симптомы, ошибки, контекст):
   Начни ответ с: **Оценка информации**: Данных достаточно для начала анализа
   Обязательно включи разделы:
   - **Анализ**: опиши что происходит и почему
   - **Вероятная причина**: определи корень проблемы
   - **Решение**: дай пошаговую инструкцию с конкретными командами
   - **Проверка**: как убедиться, что проблема решена

Стиль работы:
- Анализируй системно: от симптомов к причине
- Думай как опытный системный администратор
- Предлагай реальные, проверенные решения
- Структурируй ответ четко: проблема → причина → решение → проверка

КРИТИЧЕСКИ ВАЖНО:
- Если проблема слишком общая ("не работает докер", "ошибка") - ОБЯЗАТЕЛЬНО задай вопросы
- НЕ придумывай детали, если их нет в описании проблемы
- ЛИБО вопросы, ЛИБО решение - не смешивай их в одном ответе
- НЕ используй несуществующие инструменты или базы знаний
- Основывайся на своих знаниях IT систем (Linux, Docker, сети и т.д.)

САМ РЕШАЙ когда достаточно информации для решения - не спрашивай разрешения."""
        
        # Create the graph
        self.graph = None
        
    def _create_graph(self):
        """Create the ReAct agent graph."""
        if self.graph is not None:
            return self.graph
            
        # Create the state graph (simplified - no tools)
        workflow = StateGraph(AgentState)
        
        # Add only agent node (no tools)
        workflow.add_node("agent", self._call_agent)
        
        # Set entry point and finish point
        workflow.set_entry_point("agent")
        workflow.set_finish_point("agent")
        
        # Compile the graph
        self.graph = workflow.compile()
        
        logger.info("react_agent_graph_created", mode="autonomous_reasoning")
        return self.graph
    
    async def _call_agent(self, state: AgentState) -> Dict[str, Any]:
        """Call the agent with the current state.
        
        Args:
            state: The current agent state
            
        Returns:
            Updated state with new messages
        """
        messages = state["messages"]
        
        # Add system prompt if this is the first call
        if len(messages) == 1:
            messages = [SystemMessage(content=self.system_prompt)] + list(messages)
        
        try:
            response = await self.llm_with_tools.ainvoke(messages)
            logger.info(
                "react_agent_response_generated",
                session_id=state.get("session_id"),
                has_tool_calls=bool(response.tool_calls)
            )
            return {"messages": [response]}
        except Exception as e:
            logger.error("react_agent_call_failed", error=str(e), exc_info=True)
            # Return an error message
            error_msg = AIMessage(content=f"Извините, произошла ошибка при анализе проблемы: {str(e)}")
            return {"messages": [error_msg]}
    
    
    async def analyze_problem(
        self,
        user_message: str,
        classification: TicketClassification,
        session_id: str,
    ) -> Dict[str, Any]:
        """Analyze a user's problem and provide a solution.
        
        Args:
            user_message: The user's message describing the problem
            classification: The classification of the problem
            session_id: The session ID for tracking
            
        Returns:
            A dictionary containing:
                - classification: The problem classification
                - session_id: The session ID
                - summary: A summary of the problem and solution
                - messages: The full conversation history
        """
        try:
            logger.info(
                "react_agent_analysis_started",
                session_id=session_id,
                category=classification.category,
                priority=classification.priority
            )
            
            # Create the graph if not exists
            if self.graph is None:
                self._create_graph()
            
            # Prepare the initial message with context
            context_message = f"""Пользователь обратился с проблемой:

**Проблема**: {user_message}

**Классификация**:
- Категория: {classification.category.upper()}
- Приоритет: {classification.priority.upper()}
- Обоснование: {classification.reasoning}
- Уверенность: {classification.confidence:.0%}

Проанализируй проблему. Если информации достаточно - сразу предложи решение. Если нет - задай 2-3 конкретных вопроса."""
            
            # Initial state
            initial_state = {
                "messages": [HumanMessage(content=context_message)],
                "session_id": session_id,
                "classification": {
                    "category": classification.category,
                    "priority": classification.priority,
                    "reasoning": classification.reasoning,
                    "confidence": classification.confidence,
                },
                "problem_summary": None,
            }
            
            # Run the agent
            final_state = await self.graph.ainvoke(initial_state)
            
            # Extract the final response
            messages = final_state["messages"]
            
            # Get the last AI message as the solution
            ai_messages = [msg for msg in messages if isinstance(msg, AIMessage)]
            final_response = ai_messages[-1].content if ai_messages else "Не удалось сгенерировать решение."
            
            # Check if the agent is asking questions (insufficient data) or providing a solution
            has_solution = self._check_has_solution(final_response)
            
            # Create summary
            summary = self._create_summary(user_message, classification, final_response)
            
            logger.info(
                "react_agent_analysis_completed",
                session_id=session_id,
                message_count=len(messages),
                has_solution=has_solution
            )
            
            return {
                "classification": {
                    "category": classification.category,
                    "priority": classification.priority,
                    "reasoning": classification.reasoning,
                    "confidence": classification.confidence,
                },
                "session_id": session_id,
                "summary": summary,
                "solution": final_response,
                "problem": user_message,
                "has_solution": has_solution,  # Flag indicating if concrete solution was provided
            }
            
        except Exception as e:
            logger.error(
                "react_agent_analysis_failed",
                error=str(e),
                session_id=session_id,
                exc_info=True
            )
            raise
    
    def _check_has_solution(self, response: str) -> bool:
        """Check if the response contains a concrete solution or just questions.
        
        Args:
            response: The agent's response
            
        Returns:
            bool: True if response has a concrete solution, False if asking questions
        """
        # Keywords that indicate insufficient data / asking questions
        question_indicators = [
            "Информации недостаточно",
            "Вопросы для уточнения",
            "недостаточно данных",
            "Оценка информации**: Информации недостаточно",
            "задай 2-3 конкретных вопроса",
            "После получения дополнительной информации",
        ]
        
        response_lower = response.lower()
        
        # If any question indicator is found, it means no concrete solution
        for indicator in question_indicators:
            if indicator.lower() in response_lower:
                return False
        
        # If response contains solution indicators, it has a solution
        solution_indicators = [
            "**Решение:**",
            "**Решение**:",
            "Решение:",
            "**Вероятная причина**:",
            "**Диагностика**:",
            "Выполните следующие шаги",
            "Используйте команду",
        ]
        
        for indicator in solution_indicators:
            if indicator.lower() in response_lower:
                return True
        
        # Default: if no clear indicators, assume it has a solution
        # (to avoid breaking existing functionality)
        return True
    
    def _create_summary(
        self,
        problem: str,
        classification: TicketClassification,
        solution: str
    ) -> str:
        """Create a summary of the problem and solution.
        
        Args:
            problem: The original problem description
            classification: The classification of the problem
            solution: The proposed solution
            
        Returns:
            A formatted summary string
        """
        summary = f"""
=== АНАЛИЗ ПРОБЛЕМЫ ===

Проблема пользователя:
{problem}

Классификация:
- Отдел: {classification.category.upper()}
- Приоритет: {classification.priority.upper()}
- Обоснование: {classification.reasoning}

Решение:
{solution}

=== КОНЕЦ АНАЛИЗА ===
"""
        return summary.strip()


# Global instance factory
_react_agent_instance: Optional[ReActAgent] = None


def get_react_agent() -> ReActAgent:
    """Get or create the global ReAct agent instance.
    
    Returns:
        The ReAct agent instance
    """
    global _react_agent_instance
    
    if _react_agent_instance is None:
        # Create agent without tools (autonomous reasoning mode)
        _react_agent_instance = ReActAgent()
        logger.info("react_agent_instance_created", mode="autonomous")
    
    return _react_agent_instance

