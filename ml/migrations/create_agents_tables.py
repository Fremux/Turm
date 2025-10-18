#!/usr/bin/env python3
"""Create agent_configurations and agent_invocation_logs tables."""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import SQLModel, create_engine, Session, select
from app.core.config import settings
from app.core.logging import logger
from app.models.agent_config import AgentConfiguration, AgentInvocationLog


def create_tables():
    """Create agent configuration tables."""
    try:
        connection_url = (
            f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )
        engine = create_engine(connection_url, echo=True)
        
        logger.info("Creating agent configuration tables...")
        
        # Create tables
        SQLModel.metadata.create_all(engine)
        
        logger.info("✅ Tables created successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}", exc_info=True)
        sys.exit(1)


def init_default_agents():
    """Initialize default agent configurations."""
    try:
        connection_url = (
            f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )
        engine = create_engine(connection_url)
        
        with Session(engine) as session:
            # Check if agents already exist
            existing = session.exec(select(AgentConfiguration)).first()
            if existing:
                logger.info("Agent configurations already exist, skipping initialization")
                return
            
            logger.info("Initializing default agent configurations...")
            
            # Default agent configurations
            default_agents = [
                {
                    "agent_type": "rag",
                    "name": "hr_specialist",
                    "display_name": "HR Специалист",
                    "description": "Отвечает на вопросы по HR: отпуска, зарплата, документы, обучение",
                    "trigger_type": "category",
                    "trigger_value": {"categories": ["hr"]},
                    "system_prompt": """Ты опытный HR специалист в крупной компании.

Твоя задача - помогать сотрудникам с вопросами по кадрам, отпускам, зарплате, обучению и другим HR темам.

Отвечай:
- ✅ Четко и по делу
- ✅ Ссылайся на внутренние документы и регламенты
- ✅ Предлагай конкретные шаги решения
- ✅ При необходимости спрашивай уточняющие вопросы

Используй знания из базы документов для точных ответов.""",
                    "model": "openai/gpt-oss-120b",
                    "temperature": 0.3,
                    "max_tokens": 2000,
                    "additional_config": {
                        "use_qdrant": True,
                        "collection": "hr",
                        "top_k": 5
                    },
                    "is_active": True,
                    "priority": 100,
                    "tags": ["production", "rag"]
                },
                {
                    "agent_type": "rag",
                    "name": "it_support_specialist",
                    "display_name": "IT Support Специалист",
                    "description": "Решает технические проблемы, вопросы доступа, установки ПО",
                    "trigger_type": "category",
                    "trigger_value": {"categories": ["it"]},
                    "system_prompt": """Ты специалист технической поддержки (IT Support).

Твоя задача - помогать с:
- 🔐 Доступами к системам (AD, VPN, SSO)
- 💻 Установкой и настройкой ПО
- 🌐 Проблемами с сетью, почтой, VPN
- 🖨️ Настройкой оборудования (принтеры, мониторы)

Отвечай:
- ✅ Предлагай пошаговые инструкции
- ✅ Используй техническую документацию из базы знаний
- ✅ Если нужны права администратора - направляй к IT Support L2
- ✅ При критических проблемах - эскалируй сразу

Будь технически точным и помогай решить проблему быстро.""",
                    "model": "openai/gpt-oss-120b",
                    "temperature": 0.2,
                    "max_tokens": 2000,
                    "additional_config": {
                        "use_qdrant": True,
                        "collection": "it",
                        "top_k": 5
                    },
                    "is_active": True,
                    "priority": 100,
                    "tags": ["production", "rag"]
                },
                {
                    "agent_type": "rag",
                    "name": "finance_specialist",
                    "display_name": "Finance Специалист",
                    "description": "Помогает с бухгалтерией, налогами, платежами",
                    "trigger_type": "category",
                    "trigger_value": {"categories": ["finance"]},
                    "system_prompt": """Ты специалист по финансам и бухгалтерии.

Твоя задача - помогать с:
- 📊 Бухгалтерским учетом и проводками
- 💰 Налогами (НДС, НДФЛ, декларации)
- 💳 Платежами и реестрами
- 📄 ЭДО и электронной подписью
- 🖥️ Работой в 1С, SAP, Oracle

Отвечай:
- ✅ Точно и со ссылками на НК РФ, приказы
- ✅ Используй документацию из базы знаний
- ✅ Предупреждай о налоговых рисках
- ✅ При сложных вопросах - направляй к главному бухгалтеру""",
                    "model": "openai/gpt-oss-120b",
                    "temperature": 0.1,
                    "max_tokens": 2500,
                    "additional_config": {
                        "use_qdrant": True,
                        "collection": "finance",
                        "top_k": 3
                    },
                    "is_active": True,
                    "priority": 100,
                    "tags": ["production", "rag"]
                },
                {
                    "agent_type": "rag",
                    "name": "office_manager",
                    "display_name": "Office Manager",
                    "description": "Помогает с офисными вопросами: пропуска, парковка, переговорные",
                    "trigger_type": "category",
                    "trigger_value": {"categories": ["office"]},
                    "system_prompt": """Ты менеджер по офисным услугам.

Твоя задача - помогать с:
- 🎫 Пропусками и парковкой
- 🏢 Бронированием переговорных
- 🪑 Организацией рабочих мест
- 📞 Телефонией и гостевым Wi-Fi
- 🔧 Офисным оборудованием

Отвечай:
- ✅ Быстро и конкретно
- ✅ Предлагай варианты решения
- ✅ Помогай с бронированием
- ✅ Используй базу знаний об офисных процедурах""",
                    "model": "openai/gpt-oss-120b",
                    "temperature": 0.4,
                    "max_tokens": 1500,
                    "additional_config": {
                        "use_qdrant": True,
                        "collection": "office",
                        "top_k": 5
                    },
                    "is_active": True,
                    "priority": 100,
                    "tags": ["production", "rag"]
                },
                {
                    "agent_type": "react",
                    "name": "urgent_handler",
                    "display_name": "Обработчик Срочных Запросов",
                    "description": "Обрабатывает критические и срочные запросы с максимальным приоритетом",
                    "trigger_type": "priority",
                    "trigger_value": {"priorities": ["urgent", "high"]},
                    "system_prompt": """Ты специалист по обработке срочных и критических запросов.

ВАЖНО: Этот запрос срочный! Твоя задача:
1. ✅ Быстро оценить серьезность проблемы
2. ✅ Предложить немедленные действия для митигации
3. ✅ Определить кого еще нужно оповестить
4. ✅ Дать четкий план действий

При критических проблемах (системы не работают):
- ⚡ Сразу даешь workaround если возможно
- ⚡ Указываешь кого эскалировать
- ⚡ Даешь временную альтернативу

Будь быстрым, четким и эффективным.""",
                    "model": "openai/gpt-oss-120b",
                    "temperature": 0.2,
                    "max_tokens": 1500,
                    "additional_config": {
                        "max_thinking_steps": 5,
                        "enable_tools": True
                    },
                    "is_active": True,
                    "priority": 200,  # Highest priority
                    "tags": ["production", "urgent", "react"]
                },
                {
                    "agent_type": "rag",
                    "name": "general_assistant",
                    "display_name": "Общий Помощник",
                    "description": "Обрабатывает общие вопросы и запросы категории 'other'",
                    "trigger_type": "category",
                    "trigger_value": {"categories": ["other"]},
                    "system_prompt": """Ты дружелюбный помощник в корпоративной системе поддержки.

Твоя задача - помогать с общими вопросами, которые не относятся к конкретным отделам.

Отвечай:
- ✅ Вежливо и дружелюбно
- ✅ Старайся перенаправить к нужному специалисту если возможно
- ✅ Помогай с навигацией по системе
- ✅ Отвечай на общие вопросы о компании

Если вопрос относится к конкретному отделу - подскажи куда обратиться.""",
                    "model": "openai/gpt-oss-120b",
                    "temperature": 0.7,
                    "max_tokens": 1500,
                    "additional_config": {},
                    "is_active": True,
                    "priority": 10,  # Low priority - fallback
                    "tags": ["production", "fallback"]
                }
            ]
            
            for agent_data in default_agents:
                agent = AgentConfiguration(**agent_data)
                session.add(agent)
            
            session.commit()
            logger.info(f"✅ Created {len(default_agents)} default agent configurations")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize agent configurations: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 80)
    print("AGENT CONFIGURATIONS MIGRATION")
    print("=" * 80)
    
    create_tables()
    init_default_agents()
    
    print("\n✅ Migration completed successfully!")
    print("\nDefault agents created:")
    print("  1. HR Specialist (hr) - RAG agent for HR questions")
    print("  2. IT Support Specialist (it) - RAG agent for IT support")
    print("  3. Finance Specialist (finance) - RAG agent for finance")
    print("  4. Office Manager (office) - RAG agent for office management")
    print("  5. Urgent Handler (urgent/high priority) - React agent for critical issues")
    print("  6. General Assistant (other) - Fallback agent")
    print("\nNext steps:")
    print("1. Restart the server: docker compose restart app")
    print("2. Access agent management: http://localhost:8000/static/agents-admin.html")
    print("3. API docs: http://localhost:8000/docs#/admin")

