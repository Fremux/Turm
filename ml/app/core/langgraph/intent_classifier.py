"""Intent classification agent for categorizing user requests by intent type."""

import json
from typing import Optional

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.logging import logger
from app.schemas.classification import IntentClassification


class IntentClassificationAgent:
    """Agent for classifying user intent using LLM."""

    def __init__(self):
        """Initialize the intent classification agent."""
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0.1,  # Low temperature for consistent classification
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL if settings.LLM_BASE_URL else None,
            streaming=False,  # Disable streaming for faster response
        )
        
        # Simple cache for recent classifications
        self._cache = {}
        
        self.system_prompt = """Ты эксперт по классификации намерений (интентов) пользователей в системе поддержки.

ВАЖНО: Отвечай ТОЛЬКО на русском языке. Не используй символы или слова из других языков кроме английского и русского.

Анализируй сообщения и классифицируй их по типу намерения пользователя.

## Категории намерений:

### **access_request** — Получение доступа
О чём: пользователь хочет получить доступ к системе, приложению, данным, помещению, или любому другому ресурсу.

Ключевые маркеры: «дай доступ», «открой доступ», «нужны права», «добавь меня», «создай учётку», «выдай права», «пропуск», «парковка», «доступ к», «не могу войти», «создать аккаунт», «подключить к», «VPN», «AD группа».

Примеры:
- Дай доступ к базе данных
- Открой мне доступ к VPN
- Нужны права на папку
- Создай учётку в AD
- Выдай пропуск в офис
- Добавь меня в группу разработчиков
- Не могу войти в систему (подразумевается запрос на восстановление/выдачу доступа)

### **information_request** — Получение справки/информации
О чём: пользователь хочет получить информацию, справку, документ, консультацию, узнать как что-то работает.

Ключевые маркеры: «как», «где», «когда», «почему», «что такое», «расскажи», «нужна справка», «предоставь справку», «выгрузи отчёт», «покажи», «объясни», «консультация», «информация о», «узнать», «2-НДФЛ», «справка 182н», «выписка».

Примеры:
- Как оформить отпуск?
- Нужна справка 2-НДФЛ
- Где посмотреть расчётный лист?
- Предоставь справку о стаже
- Как работает система бронирования?
- Что делать при увольнении?
- Выгрузи отчёт по зарплате
- Объясни процедуру командировок

### **problem_solving** — Решение проблемы
О чём: пользователь столкнулся с проблемой, ошибкой, неисправностью и хочет её решить.

Ключевые маркеры: «не работает», «сломалось», «ошибка», «проблема», «не могу», «не получается», «упало», «зависло», «не открывается», «не сохраняется», «не отправляется», «исправь», «починить», «восстанови», «не приходит», «не грузится», «медленно работает».

Примеры:
- Не работает почта
- Принтер не печатает
- Ошибка при входе в систему
- Не могу открыть файл
- Сломался компьютер
- Не приходят письма
- Зависло приложение
- Медленно работает интернет
- Не сохраняются данные в системе
- Не могу отправить документ (техническая проблема)

### **other** — Другое
О чём: любые запросы, которые не относятся к получению доступа, получению справки или решению проблемы. Это могут быть благодарности, общие сообщения, нерабочие темы, бронирования, организационные вопросы без конкретного запроса.

Ключевые маркеры: «спасибо», «привет», «здравствуйте», «забронировать», «перенести встречу», «организовать», «заказать», «согласовать», «одобрить», «подтвердить», «хочу», поздравления, тестовые сообщения.

Примеры:
- Спасибо за помощь!
- Привет, как дела?
- Забронируй переговорную на завтра
- Организуй рабочее место для нового сотрудника
- Согласуй отпуск
- Оформи командировку
- Индексация зарплаты
- Хочу пройти обучение

## Пограничные случаи:

- **"Не могу войти в систему"** → **problem_solving** (если это техническая проблема) или **access_request** (если подразумевается запрос на создание/восстановление доступа). При неопределённости выбирай **problem_solving**.

- **"Дай доступ к X"** → всегда **access_request**, даже если доступ был раньше.

- **"Как получить доступ к X?"** → **information_request** (вопрос о процедуре), а не access_request.

- **"Предоставь справку"** → **information_request** (запрос документа).

- **"Оформи отпуск/командировку"** → **other** (организационное действие, не проблема и не доступ).

- **"Не приходят письма"** → **problem_solving** (техническая проблема).

- **"Забронируй переговорную"** → **other** (организационный запрос).

## Уровни уверенности:
- **0.9-1.0**: Чёткие маркеры категории
- **0.7-0.9**: Контекст достаточен для классификации
- **0.5-0.7**: Неоднозначный запрос
- **0.0-0.5**: Очень неясный запрос

Верни ТОЛЬКО JSON в формате:
{"intent": "access_request|information_request|problem_solving|other", "reasoning": "краткое объяснение", "confidence": 0.85}"""

    async def classify(self, message: str) -> Optional[IntentClassification]:
        """Classify user intent.
        
        Args:
            message: The user message to classify
            
        Returns:
            IntentClassification object or None if classification fails
        """
        try:
            # Trim message if too long for faster classification
            message_trimmed = message[:500] if len(message) > 500 else message
            
            # Check cache first
            cache_key = message_trimmed.lower().strip()
            if cache_key in self._cache:
                logger.info("intent_classification_cache_hit")
                return self._cache[cache_key]
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=message_trimmed)
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
            
            # Create IntentClassification object
            classification = IntentClassification(
                intent=data["intent"],
                reasoning=data.get("reasoning", ""),
                confidence=data.get("confidence", 0.8)
            )
            
            # Cache the result (limit cache size to 100 entries)
            if len(self._cache) > 100:
                # Remove oldest entry
                self._cache.pop(next(iter(self._cache)))
            self._cache[cache_key] = classification
            
            logger.info(
                "intent_classified",
                intent=classification.intent,
                confidence=classification.confidence
            )
            
            return classification
            
        except json.JSONDecodeError as e:
            logger.error("intent_classification_json_parse_error", error=str(e), response=content)
            
            # Try to extract intent from incomplete JSON
            try:
                import re
                intent_match = re.search(r'"intent":\s*"([^"]+)"', content)
                
                if intent_match:
                    intent = intent_match.group(1)
                    
                    logger.warning(
                        "intent_classification_partial_recovery",
                        intent=intent,
                        message="Recovered intent from incomplete JSON"
                    )
                    
                    return IntentClassification(
                        intent=intent,
                        reasoning="Partial extraction from incomplete response",
                        confidence=0.5
                    )
            except Exception as recovery_error:
                logger.error("intent_classification_recovery_failed", error=str(recovery_error))
            
            return None
        except Exception as e:
            logger.error("intent_classification_error", error=str(e), exc_info=True)
            return None


# Global instance
intent_classification_agent = IntentClassificationAgent()

