"""Initialize default categories in the database."""

import asyncio
from sqlmodel import Session, select

from app.core.config import settings
from app.services.database import engine
from app.services.qdrant_service import qdrant_service
from app.models.category import Category
from app.core.logging import logger


DEFAULT_CATEGORIES = [
    {
        "name": "hr",
        "display_name": "HR (Кадры)",
        "description": "Кадры, зарплата, льготы, ЛК сотрудника, обучение",
        "about_text": "трудовые отношения и персонал — оформление/изменение условий, отпуска/командировки, справки для сотрудника, ЛК, обучение/LMS, льготы/ДМС, индексация/оклад.",
        "common_intents": "согласовать/оформить/изменить; предоставить справку; открыть доступ к ЛК; записать на обучение; исправить начисление.",
        "key_markers": "«отпуск», «приказ/допсоглашение», «ЛК сотрудника», «ДМС/льготы», «2-НДФЛ/182н», «обучение/LMS», «оклад/индексация», «справка для сотрудника», «командировка», «график работы».",
        "example_queries": "оформить отпуск, справка 2-НДФЛ, доступ к ЛК сотрудника, запись на обучение, изменить график работы, льготы/ДМС.",
        "border_cases": "Справка для сотрудника (2-НДФЛ, стаж) → hr; финансовые справки по контрагентам → finance",
        "color": "#a855f7",
        "icon": "users"
    },
    {
        "name": "it",
        "display_name": "IT (Технологии)",
        "description": "Доступы, ПО, сеть, почта, DevOps, инфраструктура",
        "about_text": "учётные записи и права (AD/VPN/SSO/MFA), рабочее ПО и установка, сеть/VPN/Wi-Fi/почта, Exchange/M365, Dev/CI/CD/K8s, бэкапы, мониторинг/логи, VDI/RDP, файлы/хранилища.",
        "common_intents": "создать/восстановить доступ; выдать права/AD; установить ПО; починить сеть/VPN/почту; настроить оборудование (драйвер/принтер); восстановить из бэкапа; устранить инциденты CI/CD/K8s.",
        "key_markers": "«AD/группа/SSO/VPN/MFA», «Teams/Outlook/SharePoint», «почта не приходит», «GitLab/Jenkins/K8s/Helm», «Prometheus/Grafana/Splunk», «RDP/VDI», «принтер не печатает (драйвер/доступ)», «установить ПО», «настроить», «не работает (про ПО/сеть)».",
        "example_queries": "создать учётку AD, установить ПО, проблема с почтой, настроить VPN, восстановить доступ, проблемы с Teams/Outlook, CI/CD pipeline не работает.",
        "border_cases": "Доступ к системам/установка ПО/почта → it; отпуск/ЛК сотрудника → hr. Принтер не печатает (драйвер/права) → it; переставить принтер → office. Outlook не синхронизирует календарь → it; забронировать переговорную → office.",
        "color": "#3b82f6",
        "icon": "cpu"
    },
    {
        "name": "finance",
        "display_name": "Finance (Финансы)",
        "description": "Бухгалтерия, налоги, платежи, ЭДО",
        "about_text": "бухучёт/ЗУП (в части бухгалтерии), налоги (НДС, 6-НДФЛ, книга покупок/продаж), отчётность/декларации, платежи/реестры/банки, ЭДО/ЭП, ERP (1С/SAP/Oracle EBS).",
        "common_intents": "проверить/исправить алгоритм (проводки/начисления); сформировать/выгрузить отчёт/декларацию; настроить налоговые коды/толеранс; оформить платёж/реестр; выдать справки (фин.); настроить ЭП/ЭДО.",
        "key_markers": "«проводки/сверка/реестр», «НДС/6-НДФЛ/книга покупок», «выгрузка отчёта/декларации», «платёж/банк-клиент», «ЭП/Крипто-провайдер», «Диадок/СБИС/Контур», «1С/SAP/Oracle», «бухгалтерия», «налог».",
        "example_queries": "проверить проводки, сформировать декларацию, оформить платёж, настроить ЭДО, выгрузка отчёта, книга покупок/продаж.",
        "border_cases": "Проблемы входа в банк-клиент (ПО/токен) → it; операция платежа → finance",
        "color": "#10b981",
        "icon": "dollar-sign"
    },
    {
        "name": "office",
        "display_name": "Office (Офис)",
        "description": "Пропуска, парковка, переговорные, рабочие места",
        "about_text": "физический офис и сервисы — пропуска/парковка/турникеты, переговорные (бронирование/настройка AV), организация/перенос рабочих мест, ремонт/замена офисного оборудования, гостевой Wi-Fi, телефония, ресепшен.",
        "common_intents": "пропуск оформить/заменить/продлить; парковку добавить/продлить; доступ к турникетам/этажам; переговорные забронировать/настроить; организовать/перенести рабочее место; ремонт/замена офисного оборудования; гостевые сервисы; телефония.",
        "key_markers": "«пропуск/парковка/турникет», «переговорная/проектор/AV», «перенос рабочего места/монтаж», «ресепшен/очередь», «гостевой Wi-Fi», «внутренняя телефония/ATS», «забронировать», «организовать место».",
        "example_queries": "оформить пропуск, продлить парковку, забронировать переговорную, перенести рабочее место, гостевой Wi-Fi, настроить проектор, телефония.",
        "border_cases": None,
        "color": "#f59e0b",
        "icon": "building"
    }
]


def init_categories():
    """Initialize default categories if they don't exist."""
    logger.info("Starting category initialization...")
    
    with Session(engine) as db:
        for cat_data in DEFAULT_CATEGORIES:
            # Check if category exists
            existing = db.exec(
                select(Category).where(Category.name == cat_data["name"])
            ).first()
            
            if existing:
                logger.info(f"Category '{cat_data['name']}' already exists, skipping")
                continue
            
            # Create category
            category = Category(
                name=cat_data["name"],
                display_name=cat_data["display_name"],
                description=cat_data["description"],
                about_text=cat_data["about_text"],
                common_intents=cat_data["common_intents"],
                key_markers=cat_data["key_markers"],
                example_queries=cat_data["example_queries"],
                border_cases=cat_data["border_cases"],
                collection_name=cat_data["name"],
                color=cat_data["color"],
                icon=cat_data["icon"],
                is_active=True,
                collection_created=False
            )
            
            db.add(category)
            db.commit()
            db.refresh(category)
            
            logger.info(f"Created category: {cat_data['name']}")
            
            # Create Qdrant collection
            try:
                qdrant_service.create_collection(
                    collection_name=cat_data["name"],
                    embedding_size=settings.EMBEDDING_DIMENSION
                )
                category.collection_created = True
                db.add(category)
                db.commit()
                logger.info(f"Created Qdrant collection for: {cat_data['name']}")
            except Exception as e:
                logger.error(
                    f"Failed to create Qdrant collection for {cat_data['name']}: {e}",
                    exc_info=True
                )
    
    logger.info("Category initialization completed!")


if __name__ == "__main__":
    init_categories()




