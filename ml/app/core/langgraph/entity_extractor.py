"""Entity extraction agent for extracting user information from messages."""

import json
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings
from app.core.logging import logger


ENTITY_EXTRACTION_PROMPT = """Извлекай информацию о пользователе из сообщений.

Типы сущностей:
1. **name** - Имя, фамилия
2. **personal_info** - Возраст, местоположение, профессия, образование
3. **preferences** - Интересы, хобби, предпочтения
4. **usage** - Технологии, инструменты, языки программирования
5. **goals** - Цели, чему хочет научиться
6. **experience** - Уровень опыта
7. **contact** - Телефон, соцсети (НЕ email)
8. **other** - Другая информация

Верни JSON массив:
[{"entity_type": "тип", "entity_value": "значение", "context": "контекст"}]

Если сущностей нет, верни []"""


class EntityExtractor:
    """Extract entities from user messages."""
    
    def __init__(self, use_custom_llm: bool = True):
        """Initialize the entity extractor.
        
        Args:
            use_custom_llm: If True, uses your configured LLM from settings.
                           If False, uses gpt-4o-mini for cost savings.
        """
        # Use configured LLM or fallback to gpt-4o-mini for cost savings
        if use_custom_llm and hasattr(settings, 'LLM_MODEL') and settings.LLM_MODEL:
            model_name = settings.LLM_MODEL
            logger.info("entity_extractor_using_custom_llm", model=model_name)
        else:
            model_name = "gpt-4o-mini"
            logger.info("entity_extractor_using_default_model", model=model_name, reason="cost_savings")
        
        # Check if custom base URL is configured
        model_kwargs = {}
        if hasattr(settings, 'LLM_BASE_URL') and settings.LLM_BASE_URL:
            model_kwargs['base_url'] = settings.LLM_BASE_URL
            
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.1,  # Low temperature for consistent extraction
            api_key=settings.LLM_API_KEY,
            streaming=False,  # Disable streaming for faster response
            **model_kwargs
        )
        logger.info("entity_extractor_initialized", model=model_name)
    
    async def extract_entities(self, message: str) -> List[Dict[str, Any]]:
        """Extract entities from a message.
        
        Args:
            message: The user message to extract entities from
            
        Returns:
            List of extracted entities with type, value, and context
        """
        if not message or len(message.strip()) < 3:
            return []
        
        try:
            # Trim very long messages for faster extraction
            message_trimmed = message[:1000] if len(message) > 1000 else message
            
            messages = [
                SystemMessage(content=ENTITY_EXTRACTION_PROMPT),
                HumanMessage(content=message_trimmed)
            ]
            
            response = await self.llm.ainvoke(messages, max_tokens=300)
            content = response.content.strip()
            
            # Try to extract JSON from the response
            # Sometimes the model might wrap it in markdown code blocks
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            content = content.strip()
            
            # Parse JSON
            entities = json.loads(content)
            
            if not isinstance(entities, list):
                logger.warning("entity_extraction_invalid_format", content=content)
                return []
            
            # Validate and clean entities
            valid_types = {"name", "personal_info", "preferences", "usage", "goals", "experience", "contact", "other"}
            cleaned_entities = []
            
            for entity in entities:
                if not isinstance(entity, dict):
                    continue
                    
                entity_type = entity.get("entity_type", "").lower()
                entity_value = entity.get("entity_value", "").strip()
                
                if entity_type in valid_types and entity_value:
                    cleaned_entities.append({
                        "entity_type": entity_type,
                        "entity_value": entity_value,
                        "context": entity.get("context", "").strip() or None
                    })
            
            logger.info("entities_extracted", count=len(cleaned_entities), message_length=len(message))
            return cleaned_entities
            
        except json.JSONDecodeError as e:
            logger.error("entity_extraction_json_error", error=str(e), content=content)
            return []
        except Exception as e:
            logger.error("entity_extraction_failed", error=str(e), exc_info=True)
            return []

