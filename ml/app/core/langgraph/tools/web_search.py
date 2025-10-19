"""Web search tool for finding information on the internet.

This tool enables the agent to search for information online using web search.
Useful when internal knowledge base doesn't have the answer.
"""

from typing import Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from app.core.logging import logger


class WebSearchInput(BaseModel):
    """Input schema for web search."""
    
    query: str = Field(
        ...,
        description="Поисковый запрос для поиска в интернете. Должен быть конкретным."
    )
    limit: int = Field(
        default=5,
        description="Максимальное количество результатов (по умолчанию 5)"
    )


class WebSearchTool(BaseTool):
    """Tool for searching information on the internet."""
    
    name: str = "search_web"
    description: str = """
    Ищет информацию в интернете когда ответа нет в базе знаний компании.
    
    Используй этот инструмент когда:
    - База знаний не содержит нужной информации
    - Нужна актуальная информация о технологиях, продуктах
    - Требуется информация о публичных событиях или новостях
    
    Входные параметры:
    - query: конкретный поисковый запрос
    - limit: количество результатов (по умолчанию 5)
    
    Возвращает список результатов поиска с кратким описанием.
    """
    args_schema: Type[BaseModel] = WebSearchInput
    
    async def _arun(
        self,
        query: str,
        limit: int = 5
    ) -> str:
        """Search the web asynchronously.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            Formatted search results as string
        """
        try:
            logger.info("web_search_started", query=query, limit=limit)
            
            # TODO: Integrate with actual web search API (DuckDuckGo, Google, etc.)
            # For now, return a placeholder message
            result = f"""Веб-поиск по запросу "{query}" временно недоступен.

Для включения веб-поиска необходимо:
1. Настроить API ключ для поисковой системы (DuckDuckGo, Google Custom Search, Bing)
2. Интегрировать поисковый API в этот инструмент

Пока используйте только базу знаний компании через search_knowledge_base."""
            
            logger.info("web_search_not_configured", query=query)
            return result
            
        except Exception as e:
            error_msg = f"Ошибка при веб-поиске: {str(e)}"
            logger.error("web_search_error", error=str(e), query=query, exc_info=True)
            return error_msg
    
    def _run(
        self,
        query: str,
        limit: int = 5
    ) -> str:
        """Synchronous version (not implemented - use async)."""
        raise NotImplementedError("Use async version (_arun) instead")




