"""Task extraction agent for extracting task information from user messages."""

import json
from typing import Optional

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.logging import logger
from app.schemas.task import TaskExtractionResponse


class TaskExtractor:
    """Agent for extracting task information from user messages using LLM."""
    
    def __init__(self):
        """Initialize the task extraction agent."""
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0.1,  # Low temperature for consistent extraction
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL if settings.LLM_BASE_URL else None,
            streaming=False,
        )
        
        self.system_prompt = """Ты эксперт по анализу запросов пользователей и созданию задач.

Твоя задача — извлечь из сообщения пользователя информацию о задаче, которую нужно выполнить.

## Что извлекать:

1. **summary** (краткое описание, 5-7 слов):
   - Краткая суть задачи
   - Должно быть понятно, что нужно сделать
   - Примеры: "Починить лампочку в офисе", "Создать справку о стаже"

2. **description** (полное описание):
   - Максимально подробное описание задачи
   - Все детали из сообщения пользователя
   - Что именно нужно сделать, где, когда
   - Почему это нужно (если указано)

3. **assignee** (исполнитель):
   - Всегда возвращай "сотрудник" (по умолчанию)

4. **priority** (приоритет):
   - "urgent" — срочно, критично
   - "high" — важно, нужно скоро
   - "medium" — обычная задача (по умолчанию)
   - "low" — можно отложить

5. **confidence** (уверенность 0-1):
   - Насколько уверен, что это запрос на создание задачи
   - 0.9-1.0 — точно задача
   - 0.7-0.9 — скорее всего задача
   - 0.5-0.7 — может быть задача
   - <0.5 — вряд ли задача

## Примеры:

### Пример 1:
Сообщение: "Помогите, не работает лампочка в переговорной! Срочно нужно починить!"
Результат:
{
  "summary": "Починить лампочку в переговорной",
  "description": "В переговорной комнате не работает лампочка. Требуется срочный ремонт или замена лампы.",
  "assignee": "сотрудник",
  "priority": "urgent",
  "confidence": 0.95
}

### Пример 2:
Сообщение: "Мне нужна справка 2-НДФЛ для банка"
Результат:
{
  "summary": "Создать справку 2-НДФЛ для банка",
  "description": "Необходимо подготовить и оформить справку 2-НДФЛ для предоставления в банк.",
  "assignee": "сотрудник",
  "priority": "medium",
  "confidence": 0.9
}

### Пример 3:
Сообщение: "Как получить пропуск в офис?"
Результат:
{
  "summary": "Консультация по получению пропуска",
  "description": "Пользователь интересуется процедурой получения пропуска в офис. Это скорее вопрос, чем задача для выполнения.",
  "assignee": "сотрудник",
  "priority": "low",
  "confidence": 0.3
}

ВАЖНО: Отвечай ТОЛЬКО на русском языке. Верни ТОЛЬКО JSON без дополнительного текста."""
    
    async def extract_task_info(self, message: str, category: Optional[str] = None) -> Optional[TaskExtractionResponse]:
        """Extract task information from user message.
        
        Args:
            message: User message text
            category: Optional detected category
            
        Returns:
            TaskExtractionResponse or None if extraction fails
        """
        try:
            context = f"\n\nКатегория запроса: {category}" if category else ""
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=f"Сообщение пользователя: {message}{context}")
            ]
            
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
            
            # Create TaskExtractionResponse object
            extraction = TaskExtractionResponse(
                summary=data["summary"],
                description=data["description"],
                assignee=data.get("assignee", "сотрудник"),
                priority=data.get("priority", "medium"),
                confidence=data.get("confidence", 0.8)
            )
            
            logger.info(
                "task_info_extracted",
                summary=extraction.summary,
                priority=extraction.priority,
                confidence=extraction.confidence
            )
            
            return extraction
            
        except json.JSONDecodeError as e:
            logger.error("task_extraction_json_parse_error", error=str(e), response=content)
            return None
        except Exception as e:
            logger.error("task_extraction_error", error=str(e), exc_info=True)
            return None


# Global instance
task_extractor = TaskExtractor()

