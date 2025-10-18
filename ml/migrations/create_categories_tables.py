#!/usr/bin/env python3
"""Create categories and intents tables."""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings
from app.core.logging import logger
from app.models.category import Category, Intent


def create_tables():
    """Create categories and intents tables."""
    try:
        # Create engine using same method as database.py
        connection_url = (
            f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )
        engine = create_engine(connection_url, echo=True)
        
        logger.info("Creating categories and intents tables...")
        
        # Create tables
        SQLModel.metadata.create_all(engine)
        
        logger.info("✅ Tables created successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}", exc_info=True)
        sys.exit(1)


def init_default_categories():
    """Initialize default categories (HR, IT, Finance, Office)."""
    try:
        connection_url = (
            f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )
        engine = create_engine(connection_url)
        
        with Session(engine) as session:
            # Check if categories already exist
            existing = session.query(Category).first()
            if existing:
                logger.info("Categories already exist, skipping initialization")
                return
            
            logger.info("Initializing default categories...")
            
            # Default categories
            default_categories = [
                {
                    "name": "hr",
                    "display_name": "Human Resources",
                    "description": "Вопросы по кадрам, отпускам, документам, зарплате",
                    "collection_name": "hr",
                    "color": "#3b82f6",
                    "icon": "users"
                },
                {
                    "name": "it",
                    "display_name": "IT Support",
                    "description": "Технические проблемы, доступы, оборудование",
                    "collection_name": "it",
                    "color": "#8b5cf6",
                    "icon": "cpu"
                },
                {
                    "name": "finance",
                    "display_name": "Finance",
                    "description": "Финансовые вопросы, бухгалтерия, компенсации",
                    "collection_name": "finance",
                    "color": "#10b981",
                    "icon": "dollar-sign"
                },
                {
                    "name": "office",
                    "display_name": "Office Management",
                    "description": "Офисные вопросы, помещения, общие услуги",
                    "collection_name": "office",
                    "color": "#f59e0b",
                    "icon": "building"
                }
            ]
            
            for cat_data in default_categories:
                category = Category(**cat_data)
                session.add(category)
            
            session.commit()
            logger.info(f"✅ Created {len(default_categories)} default categories")
            
            # Default intents
            default_intents = [
                {
                    "name": "ask_question",
                    "display_name": "Ask Question",
                    "description": "User wants to ask a general question",
                    "examples": [
                        "Как мне?",
                        "Подскажите пожалуйста",
                        "У меня вопрос",
                        "Можно узнать?"
                    ],
                    "priority": "normal"
                },
                {
                    "name": "report_issue",
                    "display_name": "Report Issue",
                    "description": "User wants to report a problem",
                    "examples": [
                        "У меня проблема",
                        "Не работает",
                        "Ошибка",
                        "Сломалось"
                    ],
                    "priority": "high"
                },
                {
                    "name": "request_document",
                    "display_name": "Request Document",
                    "description": "User needs a document or certificate",
                    "examples": [
                        "Нужна справка",
                        "Выдайте документ",
                        "Оформите пожалуйста",
                        "Мне нужен сертификат"
                    ],
                    "priority": "normal"
                },
                {
                    "name": "urgent_request",
                    "display_name": "Urgent Request",
                    "description": "Urgent matter requiring immediate attention",
                    "examples": [
                        "Срочно!",
                        "Очень нужно",
                        "Горящий вопрос",
                        "Критично"
                    ],
                    "priority": "urgent"
                }
            ]
            
            for intent_data in default_intents:
                intent = Intent(**intent_data)
                session.add(intent)
            
            session.commit()
            logger.info(f"✅ Created {len(default_intents)} default intents")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize categories: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 80)
    print("CATEGORIES & INTENTS MIGRATION")
    print("=" * 80)
    
    create_tables()
    init_default_categories()
    
    print("\n✅ Migration completed successfully!")
    print("\nNext steps:")
    print("1. Start the server: uvicorn app.main:app --reload")
    print("2. Access API docs: http://localhost:8000/docs")
    print("3. Go to 'admin' section to manage categories")

