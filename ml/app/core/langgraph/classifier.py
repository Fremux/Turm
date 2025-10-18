"""Classification agent for support ticket classification."""

import json
from typing import Optional
from functools import lru_cache

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.logging import logger
from app.schemas.classification import TicketClassification


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
        
        self.system_prompt = """Ты эксперт по классификации заявок службы поддержки по отделам.

ВАЖНО: Отвечай ТОЛЬКО на русском языке. Не используй символы или слова из других языков кроме английского и русского. 

Анализируй сообщения и классифицируй их по категориям (отделам) и приоритетам.

## Категории (отделы):

### **hr** — HR (кадры, зарплата, льготы, ЛК, обучение)
О чём: трудовые отношения и персонал — оформление/изменение условий, отпуска/командировки, справки для сотрудника, ЛК, обучение/LMS, льготы/ДМС, индексация/оклад.

Частые интенты: согласовать/оформить/изменить; предоставить справку; открыть доступ к ЛК; записать на обучение; исправить начисление.

Ключевые маркеры: «отпуск», «приказ/допсоглашение», «ЛК сотрудника», «ДМС/льготы», «2-НДФЛ/182н», «обучение/LMS», «оклад/индексация», «справка для сотрудника», «командировка», «график работы».

Примеры: оформить отпуск, справка 2-НДФЛ, доступ к ЛК сотрудника, запись на обучение, изменить график работы, льготы/ДМС.

### **it** — IT (доступы, ПО, сеть, почта, DevOps, инфра)
О чём: учётные записи и права (AD/VPN/SSO/MFA), рабочее ПО и установка, сеть/VPN/Wi-Fi/почта, Exchange/M365, Dev/CI/CD/K8s, бэкапы, мониторинг/логи, VDI/RDP, файлы/хранилища.

Частые интенты: создать/восстановить доступ; выдать права/AD; установить ПО; починить сеть/VPN/почту; настроить оборудование (драйвер/принтер); восстановить из бэкапа; устранить инциденты CI/CD/K8s.

Ключевые маркеры: «AD/группа/SSO/VPN/MFA», «Teams/Outlook/SharePoint», «почта не приходит», «GitLab/Jenkins/K8s/Helm», «Prometheus/Grafana/Splunk», «RDP/VDI», «принтер не печатает (драйвер/доступ)», «установить ПО», «настроить», «не работает (про ПО/сеть)».

Примеры: создать учётку AD, установить ПО, проблема с почтой, настроить VPN, восстановить доступ, проблемы с Teams/Outlook, CI/CD pipeline не работает.

### **finance** — Finance (бухгалтерия, налоги, платежи, ЭДО)
О чём: бухучёт/ЗУП (в части бухгалтерии), налоги (НДС, 6-НДФЛ, книга покупок/продаж), отчётность/декларации, платежи/реестры/банки, ЭДО/ЭП, ERP (1С/SAP/Oracle EBS).

Частые интенты: проверить/исправить алгоритм (проводки/начисления); сформировать/выгрузить отчёт/декларацию; настроить налоговые коды/толеранс; оформить платёж/реестр; выдать справки (фин.); настроить ЭП/ЭДО.

Ключевые маркеры: «проводки/сверка/реестр», «НДС/6-НДФЛ/книга покупок», «выгрузка отчёта/декларации», «платёж/банк-клиент», «ЭП/Крипто-провайдер», «Диадок/СБИС/Контур», «1С/SAP/Oracle», «бухгалтерия», «налог».

Примеры: проверить проводки, сформировать декларацию, оформить платёж, настроить ЭДО, выгрузка отчёта, книга покупок/продаж.

### **office** — Office (пропуска, парковка, переговорные, рабочие места)
О чём: физический офис и сервисы — пропуска/парковка/турникеты, переговорные (бронирование/настройка AV), организация/перенос рабочих мест, ремонт/замена офисного оборудования, гостевой Wi-Fi, телефония, ресепшен.

Частые интенты: пропуск оформить/заменить/продлить; парковку добавить/продлить; доступ к турникетам/этажам; переговорные забронировать/настроить; организовать/перенести рабочее место; ремонт/замена офисного оборудования; гостевые сервисы; телефония.

Ключевые маркеры: «пропуск/парковка/турникет», «переговорная/проектор/AV», «перенос рабочего места/монтаж», «ресепшен/очередь», «гостевой Wi-Fi», «внутренняя телефония/ATS», «забронировать», «организовать место».

Примеры: оформить пропуск, продлить парковку, забронировать переговорную, перенести рабочее место, гостевой Wi-Fi, настроить проектор, телефония.

### **other** — Другое (все остальное)
О чём: любые запросы, которые не относятся к HR, IT, Finance или Office. Это могут быть общие вопросы, личные обращения, нерабочие темы, неясные или нерелевантные сообщения.

Примеры: вопросы о погоде, личные беседы, поздравления, запросы не связанные с работой компании, неясные или бессвязные сообщения, тестовые сообщения.

## Пограничные случаи:
- Справка для сотрудника (2-НДФЛ, стаж) → **hr**; финансовые справки по контрагентам → **finance**
- Доступ к системам/установка ПО/почта → **it**; отпуск/ЛК сотрудника → **hr**
- Принтер не печатает (драйвер/права) → **it**; переставить принтер → **office**
- Outlook не синхронизирует календарь → **it**; забронировать переговорную → **office**
- Проблемы входа в банк-клиент (ПО/токен) → **it**; операция платежа → **finance**

## Приоритеты:
- **urgent**: Критично, система не работает, блокирует работу многих людей
- **high**: Важная функция сломана, срочная задача
- **medium**: Стандартная заявка, не критично
- **low**: Общие вопросы, консультация

Верни ТОЛЬКО JSON в формате:
{"category": "hr|it|finance|office|other", "priority": "urgent|high|medium|low", "reasoning": "краткое объяснение", "confidence": 0.85}"""

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


# Global instance
classification_agent = ClassificationAgent()

