"""This file contains the graph utilities for the application."""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage

from app.core.config import settings
from app.schemas import Message


def dump_messages(messages: list[Message | BaseMessage]) -> list[dict]:
    """Dump the messages to a list of dictionaries.

    Args:
        messages (list[Message | BaseMessage]): The messages to dump.

    Returns:
        list[dict]: The dumped messages.
    """
    # Mapping from LangChain message types to API role names
    type_to_role = {
        "human": "user",
        "ai": "assistant",
        "system": "system",
        "tool": "tool",
    }
    
    result = []
    for message in messages:
        if isinstance(message, BaseMessage):
            role = type_to_role.get(message.type, message.type)
            result.append({"role": role, "content": message.content})
        else:
            result.append(message.model_dump())
    return result


def prepare_messages(messages: list[BaseMessage], llm: BaseChatModel, system_prompt: str) -> list[BaseMessage]:
    """Prepare the messages for the LLM.

    Args:
        messages (list[BaseMessage]): The messages to prepare (LangChain BaseMessage objects).
        llm (BaseChatModel): The LLM to use.
        system_prompt (str): The system prompt to use.

    Returns:
        list[BaseMessage]: The prepared messages.
    """
    # Use character-based trimming instead of token-based to avoid model compatibility issues
    max_chars = settings.MAX_TOKENS * 4  # Approximate: 1 token ≈ 4 characters
    
    # Calculate system prompt length
    current_length = len(system_prompt)
    
    # Add messages from the end (most recent first) until we reach the limit
    trimmed_messages = []
    for msg in reversed(messages):
        msg_content = msg.content if isinstance(msg.content, str) else str(msg.content)
        msg_length = len(msg_content)
        if current_length + msg_length > max_chars:
            break
        trimmed_messages.insert(0, msg)
        current_length += msg_length
    
    # If we have messages but the first one isn't from human, try to start with human message
    if trimmed_messages and trimmed_messages[0].type != "human":
        # Find the first human message
        for i, msg in enumerate(trimmed_messages):
            if msg.type == "human":
                trimmed_messages = trimmed_messages[i:]
                break
    
    # Always include system prompt at the beginning
    return [SystemMessage(content=system_prompt)] + trimmed_messages
