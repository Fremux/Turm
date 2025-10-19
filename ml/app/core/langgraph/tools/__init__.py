"""LangGraph tools for enhanced language model capabilities.

This package contains custom tools that can be used with LangGraph to extend
the capabilities of language models.

Tool Registry System:
- All available tools are registered here with metadata
- Agents can select which tools they need
- Tools are categorized for easy discovery
"""

from typing import Dict, List, Any
from langchain_core.tools.base import BaseTool

from app.core.langgraph.tools.knowledge_search import KnowledgeSearchTool
from app.core.langgraph.tools.web_search import WebSearchTool
from app.core.langgraph.tools.calculator import CalculatorTool
from app.core.langgraph.tools.datetime_tool import DateTimeTool
from app.core.langgraph.tools.email_tool import EmailTool


class ToolMetadata:
    """Metadata for a tool."""
    
    def __init__(
        self,
        tool_id: str,
        tool_class: type,
        display_name: str,
        category: str,
        description: str,
        requires_config: bool = False,
        config_fields: List[str] = None
    ):
        self.tool_id = tool_id
        self.tool_class = tool_class
        self.display_name = display_name
        self.category = category
        self.description = description
        self.requires_config = requires_config
        self.config_fields = config_fields or []
        self._instance = None
    
    def get_instance(self) -> BaseTool:
        """Get or create tool instance."""
        if self._instance is None:
            self._instance = self.tool_class()
        return self._instance
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "tool_id": self.tool_id,
            "display_name": self.display_name,
            "category": self.category,
            "description": self.description,
            "requires_config": self.requires_config,
            "config_fields": self.config_fields
        }


class ToolRegistry:
    """Central registry for all available tools."""
    
    def __init__(self):
        self._tools: Dict[str, ToolMetadata] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register all default tools."""
        # Knowledge Base Search
        self.register(
            tool_id="knowledge_search",
            tool_class=KnowledgeSearchTool,
            display_name="🔍 Поиск в базе знаний",
            category="knowledge",
            description="Ищет информацию во внутренней базе знаний компании по категориям (IT, HR, Finance, Office)"
        )
        
        # Web Search
        self.register(
            tool_id="web_search",
            tool_class=WebSearchTool,
            display_name="🌐 Поиск в интернете",
            category="external",
            description="Ищет актуальную информацию в интернете (требует настройки API)",
            requires_config=True,
            config_fields=["search_api_key", "search_engine"]
        )
        
        # Calculator
        self.register(
            tool_id="calculator",
            tool_class=CalculatorTool,
            display_name="🔢 Калькулятор",
            category="utility",
            description="Выполняет математические вычисления (+, -, *, /, **)"
        )
        
        # DateTime Helper
        self.register(
            tool_id="datetime",
            tool_class=DateTimeTool,
            display_name="📅 Работа с датами",
            category="utility",
            description="Помогает с датами: текущее время, добавление дней, разница между датами, форматирование"
        )
        
        # Email Sender
        self.register(
            tool_id="send_email",
            tool_class=EmailTool,
            display_name="📧 Отправка email",
            category="communication",
            description="Отправляет email уведомления через SMTP. Убедитесь, что SMTP настроен в разделе Настройки.",
            requires_config=False  # Проверка настроек SMTP происходит внутри инструмента
        )
    
    def register(
        self,
        tool_id: str,
        tool_class: type,
        display_name: str,
        category: str,
        description: str,
        requires_config: bool = False,
        config_fields: List[str] = None
    ):
        """Register a new tool.
        
        Args:
            tool_id: Unique identifier for the tool
            tool_class: Class of the tool (subclass of BaseTool)
            display_name: User-friendly name
            category: Category (knowledge/external/utility/communication/etc)
            description: Brief description
            requires_config: Whether tool needs configuration
            config_fields: List of required config field names
        """
        metadata = ToolMetadata(
            tool_id=tool_id,
            tool_class=tool_class,
            display_name=display_name,
            category=category,
            description=description,
            requires_config=requires_config,
            config_fields=config_fields
        )
        self._tools[tool_id] = metadata
    
    def get_tool(self, tool_id: str) -> BaseTool:
        """Get tool instance by ID.
        
        Args:
            tool_id: Tool identifier
            
        Returns:
            Tool instance
            
        Raises:
            KeyError: If tool not found
        """
        if tool_id not in self._tools:
            raise KeyError(f"Tool '{tool_id}' not found in registry")
        return self._tools[tool_id].get_instance()
    
    def get_tools(self, tool_ids: List[str]) -> List[BaseTool]:
        """Get multiple tool instances by IDs.
        
        Args:
            tool_ids: List of tool identifiers
            
        Returns:
            List of tool instances
        """
        tools = []
        for tool_id in tool_ids:
            try:
                tools.append(self.get_tool(tool_id))
            except KeyError:
                # Log warning but don't fail - skip unknown tools
                from app.core.logging import logger
                logger.warning("unknown_tool_requested", tool_id=tool_id)
        return tools
    
    def list_all(self) -> List[Dict[str, Any]]:
        """List all available tools with metadata.
        
        Returns:
            List of tool metadata dictionaries
        """
        return [meta.to_dict() for meta in self._tools.values()]
    
    def list_by_category(self, category: str) -> List[Dict[str, Any]]:
        """List tools by category.
        
        Args:
            category: Category name
            
        Returns:
            List of tool metadata dictionaries
        """
        return [
            meta.to_dict()
            for meta in self._tools.values()
            if meta.category == category
        ]
    
    def get_metadata(self, tool_id: str) -> ToolMetadata:
        """Get tool metadata.
        
        Args:
            tool_id: Tool identifier
            
        Returns:
            Tool metadata
        """
        return self._tools.get(tool_id)


# Global tool registry instance
tool_registry = ToolRegistry()


# Legacy exports for backward compatibility
knowledge_search_tool = tool_registry.get_tool("knowledge_search")
tools: list[BaseTool] = [knowledge_search_tool]  # Default tools for existing code
