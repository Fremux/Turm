"""LangGraph tools for enhanced language model capabilities.

This package contains custom tools that can be used with LangGraph to extend
the capabilities of language models.
"""

from langchain_core.tools.base import BaseTool
from app.core.langgraph.tools.knowledge_search import KnowledgeSearchTool

# Available tools for the agent
knowledge_search_tool = KnowledgeSearchTool()

tools: list[BaseTool] = [
    knowledge_search_tool
]
