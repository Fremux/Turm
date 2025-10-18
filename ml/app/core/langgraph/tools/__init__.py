"""LangGraph tools for enhanced language model capabilities.

This package contains custom tools that can be used with LangGraph to extend
the capabilities of language models.

Currently, the ReAct agent operates in autonomous mode without external tools.
"""

from langchain_core.tools.base import BaseTool

# No tools currently - agent uses pure reasoning
tools: list[BaseTool] = []
