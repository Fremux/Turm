"""Classification agent for support ticket classification."""

import json
from typing import Optional
from functools import lru_cache

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from sqlmodel import Session, select

from app.core.config import settings
from app.core.logging import logger
from app.schemas.classification import TicketClassification
from app.models.category import Category
from app.services.database import database_service


class ClassificationAgent:
    """Agent for classifying support tickets using LLM."""

    def __init__(self):
        """Initialize the classification agent."""
        # Use the same model as main LLM for consistency, but with lower max_tokens
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0.1,  # Low temperature for consistent classification
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL if settings.LLM_BASE_URL else None,
            streaming=False,  # Disable streaming for faster response
        )
        
        # Simple cache for recent classifications
        self._cache = {}
        
        # Load categories from database and generate prompt
        self._load_categories()
    
    def _load_categories(self):
        """Load categories from database and generate system prompt."""
        try:
            with Session(database_service.engine) as session:
                # Get all active categories
                categories = session.exec(
                    select(Category).where(Category.is_active == True)
                ).all()
                
                if not categories:
                    logger.warning("no_active_categories_found_using_fallback")
                    self._use_fallback_prompt()
                    return
                
                # Generate dynamic system prompt
                self.system_prompt = self._generate_system_prompt(categories)
                logger.info(
                    "categories_loaded_for_classification",
                    categories_count=len(categories),
                    category_names=[cat.name for cat in categories]
                )
        except Exception as e:
            logger.error("failed_to_load_categories_for_classification", error=str(e), exc_info=True)
            self._use_fallback_prompt()
    
    def _generate_system_prompt(self, categories: list[Category]) -> str:
        """Generate system prompt dynamically from categories.
        
        Args:
            categories: List of Category objects from database
            
        Returns:
            Generated system prompt string
        """
        # Build categories section
        categories_text = ""
        category_names = []
        border_cases_list = []
        
        for cat in categories:
            category_names.append(cat.name)
            categories_text += f"\n### **{cat.name}** — {cat.display_name}\n"
            
            # Add description (basic info)
            if cat.description:
                categories_text += f"Описание: {cat.description}\n\n"
            
            # Add detailed "О чём" section if available
            if cat.about_text:
                categories_text += f"О чём: {cat.about_text}\n\n"
            
            # Add "Частые интенты" section if available
            if cat.common_intents:
                categories_text += f"Частые интенты: {cat.common_intents}\n\n"
            
            # Add "Ключевые маркеры" section if available
            if cat.key_markers:
                categories_text += f"Ключевые маркеры: {cat.key_markers}\n\n"
            
            # Add "Примеры" section if available
            if cat.example_queries:
                categories_text += f"Примеры: {cat.example_queries}\n\n"
            
            # Collect border cases for later
            if cat.border_cases:
                border_cases_list.append(cat.border_cases)
        
        # Add 'other' as fallback
        category_names.append("other")
        categories_text += "\n### **other** — Другое (все остальное)\n"
        categories_text += "О чём: любые запросы, которые не относятся к указанным выше категориям. Это могут быть общие вопросы, личные обращения, нерабочие темы, неясные или нерелевантные сообщения.\n\n"
        categories_text += "Примеры: вопросы о погоде, личные беседы, поздравления, запросы не связанные с работой компании, неясные или бессвязные сообщения, тестовые сообщения.\n"
        
        # Build border cases section
        border_cases_text = ""
        if border_cases_list:
            border_cases_text = "\n## Пограничные случаи:\n"
            for bc in border_cases_list:
                border_cases_text += f"- {bc}\n"
        
        # Build valid categories string
        valid_categories = "|".join(category_names)
        
        prompt = f"""Ты эксперт по классификации заявок службы поддержки по отделам.

ВАЖНО: Отвечай ТОЛЬКО на русском языке. Не используй символы или слова из других языков кроме английского и русского. 

Анализируй сообщения и классифицируй их по категориям (отделам) и приоритетам.

## Категории (отделы):
{categories_text}
{border_cases_text}

## Приоритеты:
- **urgent**: Критично, система не работает, блокирует работу многих людей
- **high**: Важная функция сломана, срочная задача
- **medium**: Стандартная заявка, не критично
- **low**: Общие вопросы, консультация

## Намерения (intents) - ОБЯЗАТЕЛЬНОЕ ПОЛЕ:
- **task_creation**: Пользователь просит ВЫПОЛНИТЬ действие (починить, создать, оформить, заменить, установить, сделать, настроить)
- **ask_question**: Пользователь задает вопрос или просит информацию (как, где, когда, что, почему)
- **report_issue**: Пользователь сообщает о проблеме без явного запроса на действие
- **request_document**: Пользователь просит предоставить документ/справку

**ВАЖНО**: Если видишь слова ПОЧИНИТЬ, СДЕЛАТЬ, СОЗДАТЬ, ОФОРМИТЬ, ЗАМЕНИТЬ, УСТАНОВИТЬ - это ВСЕГДА intent="task_creation"!

Верни ТОЛЬКО JSON в формате:
{{"category": "{valid_categories}", "priority": "urgent|high|medium|low", "intent": "task_creation|ask_question|report_issue|request_document", "reasoning": "краткое объяснение", "confidence": 0.85}}

ОБЯЗАТЕЛЬНО включи поле "intent" в ответ!"""

        return prompt
    
    def _use_fallback_prompt(self):
        """Use fallback minimal prompt if database load fails.
        
        This is only used as emergency fallback when database is unavailable.
        Normal operation loads categories from database dynamically.
        """
        logger.warning("using_fallback_prompt_database_unavailable")
        
        self.system_prompt = """Ты эксперт по классификации заявок службы поддержки по отделам.

ВАЖНО: Отвечай ТОЛЬКО на русском языке.

Анализируй сообщения и классифицируй их по категориям и приоритетам.

## Категории:
- **hr**: HR, кадры, отпуска, зарплата, справки для сотрудников
- **it**: IT, доступы, ПО, сеть, почта, оборудование
- **finance**: Финансы, бухгалтерия, налоги, платежи
- **office**: Офис, пропуска, парковка, переговорные, рабочие места
- **other**: Все остальное

## Приоритеты:
- **urgent**: Критично, блокирует работу
- **high**: Важная срочная задача
- **medium**: Стандартная заявка
- **low**: Общие вопросы

## Намерения (intents):
- **task_creation**: Пользователь просит ВЫПОЛНИТЬ действие (починить, создать, оформить, заменить, установить, сделать)
- **ask_question**: Пользователь задает вопрос или просит информацию (как, где, когда, что)
- **report_issue**: Пользователь сообщает о проблеме без явного запроса на действие
- **request_document**: Пользователь просит предоставить документ/справку

Верни ТОЛЬКО JSON в формате:
{"category": "hr|it|finance|office|other", "priority": "urgent|high|medium|low", "intent": "task_creation|ask_question|report_issue|request_document", "reasoning": "краткое объяснение", "confidence": 0.85}

**ВАЖНО**: Если пользователь просит что-то СДЕЛАТЬ/ПОЧИНИТЬ/СОЗДАТЬ/ОФОРМИТЬ - это ОБЯЗАТЕЛЬНО intent="task_creation"!"""

    async def classify(self, message: str) -> Optional[TicketClassification]:
        """Classify a support ticket message.
        
        Args:
            message: The user message to classify
            
        Returns:
            TicketClassification object or None if classification fails
        """
        try:
            # Trim message if too long for faster classification
            message_trimmed = message[:500] if len(message) > 500 else message
            
            # Check cache first
            cache_key = message_trimmed.lower().strip()
            if cache_key in self._cache:
                logger.info("classification_cache_hit")
                return self._cache[cache_key]
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=message_trimmed)
            ]
            
            # Increased max_tokens to allow full JSON response with reasoning
            response = await self.llm.ainvoke(messages, max_tokens=500)
            
            # Parse JSON response
            content = response.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            # Parse JSON
            data = json.loads(content)
            
            # Create TicketClassification object
            classification = TicketClassification(
                category=data["category"],
                priority=data["priority"],
                intent=data.get("intent"),  # Optional field
                reasoning=data.get("reasoning", ""),
                confidence=data.get("confidence", 0.8)
            )
            
            # Cache the result (limit cache size to 100 entries)
            if len(self._cache) > 100:
                # Remove oldest entry
                self._cache.pop(next(iter(self._cache)))
            self._cache[cache_key] = classification
            
            logger.info(
                "message_classified",
                category=classification.category,
                priority=classification.priority,
                intent=classification.intent,
                confidence=classification.confidence
            )
            
            return classification
            
        except json.JSONDecodeError as e:
            logger.error("classification_json_parse_error", error=str(e), response=content)
            
            # Try to extract category from incomplete JSON
            try:
                import re
                category_match = re.search(r'"category":\s*"([^"]+)"', content)
                priority_match = re.search(r'"priority":\s*"([^"]+)"', content)
                
                if category_match:
                    category = category_match.group(1)
                    priority = priority_match.group(1) if priority_match else "medium"
                    
                    logger.warning(
                        "classification_partial_recovery",
                        category=category,
                        priority=priority,
                        message="Recovered category/priority from incomplete JSON"
                    )
                    
                    return Classification(
                        category=category,
                        priority=priority,
                        reasoning="Partial extraction from incomplete response",
                        confidence=0.5
                    )
            except Exception as recovery_error:
                logger.error("classification_recovery_failed", error=str(recovery_error))
            
            return None
        except Exception as e:
            logger.error("classification_error", error=str(e), exc_info=True)
            return None
    
    def refresh_categories(self):
        """Refresh categories from database and regenerate system prompt.
        
        This should be called when categories are added/updated/deleted.
        """
        logger.info("refreshing_categories_for_classification")
        self._cache.clear()  # Clear cache when categories change
        self._load_categories()


# Global instance
classification_agent = ClassificationAgent()

