"""Initialize default data (categories) on application startup."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlmodel import Session, select
from app.services.database import database_service
from app.models.category import Category, Intent
from app.core.logging import logger


DEFAULT_CATEGORIES = {
    "hr": {
        "display_name": "Human Resources",
        "description": "Вопросы по кадрам, отпускам, документам, зарплате",
        "about_text": "Категория HR охватывает все вопросы, связанные с кадровым делопроизводством, трудовыми отношениями, управлением персоналом. Сюда относятся вопросы об оформлении документов, отпусках, больничных, зарплате, льготах и компенсациях.",
        "common_intents": "отпуск (запрос, согласование, перенос), справки (2-НДФЛ, с места работы, для визы), больничный лист, зарплата и премии, трудовой договор, увольнение, адаптация новых сотрудников, ДМС и льготы",
        "key_markers": "отпуск, справка, зарплата, больничный, увольнение, трудовой договор, кадры, отдел кадров, HR, премия, компенсация, ДМС, страховка",
        "example_queries": "- Как оформить отпуск?\n- Нужна справка 2-НДФЛ\n- Когда будет зарплата?\n- Как продлить больничный?\n- Где взять справку с места работы?",
        "border_cases": "Вопросы о корпоративных мероприятиях → hr (если связаны с льготами) или office (если организационные)"
    },
    "it": {
        "display_name": "IT Support",
        "description": "Технические проблемы, доступы, оборудование",
        "about_text": "Категория IT Support включает все технические вопросы: проблемы с компьютером, программным обеспечением, сетью, почтой, доступами к системам, заказ и настройка оборудования.",
        "common_intents": "проблемы с ПК (не включается, тормозит, зависает), доступы (к системам, папкам, почте), почта (не работает, не приходят письма), интернет и сеть, принтер и оргтехника, заказ оборудования (ноутбук, монитор, мышь), установка ПО, VPN",
        "key_markers": "компьютер, ноутбук, почта, email, интернет, wi-fi, доступ, пароль, программа, принтер, сеть, VPN, 1С, CRM, система",
        "example_queries": "- Не работает компьютер\n- Нужен доступ к общей папке\n- Не приходят письма на почту\n- Принтер не печатает\n- Нужен новый ноутбук",
        "border_cases": "Вопросы о доступе в офис (пропуск) → office, не IT"
    },
    "finance": {
        "display_name": "Finance",
        "description": "Финансовые вопросы, бухгалтерия, компенсации",
        "about_text": "Категория Finance охватывает бухгалтерские и финансовые вопросы: документы для оплаты, счета, акты, компенсации расходов, закрывающие документы, налоги.",
        "common_intents": "компенсация расходов (такси, обеды, командировки), выставление счета, получение акта/УПД, оплата поставщикам, закрывающие документы, налоги и отчетность, реквизиты компании",
        "key_markers": "счет, оплата, акт, УПД, компенсация, расходы, бухгалтерия, финансы, налог, реквизиты, закрывающие документы",
        "example_queries": "- Как получить компенсацию за такси?\n- Нужен счет на оплату\n- Где взять акт выполненных работ?\n- Когда придет оплата от клиента?",
        "border_cases": "Зарплата и премии → hr, не finance"
    },
    "office": {
        "display_name": "Office Management",
        "description": "Офисные вопросы, помещения, общие услуги",
        "about_text": "Категория Office Management включает все вопросы, связанные с офисным пространством: пропуска, парковка, переговорные комнаты, кухня, рабочие места, офисные принадлежности, курьерская служба.",
        "common_intents": "пропуск (оформление, продление, замена), парковка (место, пропуск), переговорная комната (бронирование, оборудование), рабочее место (переезд, мебель), офисные принадлежности (канцелярия), курьер и почта, уборка офиса, кухня и кофе",
        "key_markers": "пропуск, парковка, переговорка, офис, рабочее место, канцелярия, курьер, почта, уборка, кухня, кофе",
        "example_queries": "- Нужен пропуск в офис\n- Как забронировать переговорную?\n- Где взять канцелярию?\n- Нужно место на парковке",
        "border_cases": "Корпоративные мероприятия могут быть как office (организация), так и hr (если связаны с льготами)"
    }
}


async def init_default_categories():
    """Initialize default categories if they don't exist."""
    try:
        logger.info("checking_for_default_categories")
        
        with Session(database_service.engine) as session:
            for category_name, data in DEFAULT_CATEGORIES.items():
                # Check if category exists
                existing = session.exec(
                    select(Category).where(Category.name == category_name)
                ).first()
                
                if existing:
                    # Update existing category with full data
                    logger.info(f"updating_existing_category", category=category_name)
                    existing.display_name = data["display_name"]
                    existing.description = data["description"]
                    existing.about_text = data["about_text"]
                    existing.common_intents = data["common_intents"]
                    existing.key_markers = data["key_markers"]
                    existing.example_queries = data["example_queries"]
                    existing.border_cases = data.get("border_cases", "")
                    existing.is_active = True
                    session.add(existing)
                else:
                    # Create new category
                    logger.info(f"creating_new_category", category=category_name)
                    category = Category(
                        name=category_name,
                        display_name=data["display_name"],
                        description=data["description"],
                        about_text=data["about_text"],
                        common_intents=data["common_intents"],
                        key_markers=data["key_markers"],
                        example_queries=data["example_queries"],
                        border_cases=data.get("border_cases", ""),
                        is_active=True
                    )
                    session.add(category)
            
            session.commit()
            logger.info("default_categories_initialized_successfully")
            
    except Exception as e:
        logger.error("failed_to_initialize_default_categories", error=str(e), exc_info=True)
        raise


async def init_task_creation_intent():
    """Initialize task_creation intent if it doesn't exist."""
    try:
        logger.info("checking_for_task_creation_intent")
        
        with Session(database_service.engine) as session:
            # Check if task_creation intent exists
            existing = session.exec(
                select(Intent).where(Intent.name == "task_creation")
            ).first()
            
            if existing:
                # Update existing intent
                logger.info("updating_task_creation_intent")
                existing.display_name = "Создание задачи"
                existing.description = "Пользователь просит выполнить какое-то действие (починить, создать, оформить, сделать что-то)"
                existing.examples = [
                    "Помогите, не работает лампочка",
                    "Нужно починить принтер",
                    "Создайте справку для банка",
                    "Мне нужна справка 2-НДФЛ",
                    "Оформите пропуск в офис",
                    "Замените картридж в принтере",
                    "Нужно заказать канцелярию",
                    "Срочно нужен доступ к системе"
                ]
                existing.priority = "high"
                existing.is_active = True
                session.add(existing)
            else:
                # Create new intent
                logger.info("creating_task_creation_intent")
                intent = Intent(
                    name="task_creation",
                    display_name="Создание задачи",
                    description="Пользователь просит выполнить какое-то действие (починить, создать, оформить, сделать что-то)",
                    examples=[
                        "Помогите, не работает лампочка",
                        "Нужно починить принтер",
                        "Создайте справку для банка",
                        "Мне нужна справка 2-НДФЛ",
                        "Оформите пропуск в офис",
                        "Замените картридж в принтере",
                        "Нужно заказать канцелярию",
                        "Срочно нужен доступ к системе"
                    ],
                    priority="high",
                    is_active=True
                )
                session.add(intent)
            
            session.commit()
            logger.info("task_creation_intent_initialized_successfully")
            
    except Exception as e:
        logger.error("failed_to_initialize_task_creation_intent", error=str(e), exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(init_default_categories())
    asyncio.run(init_task_creation_intent())

