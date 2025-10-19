"""Load capability mappings for task assignment."""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from sqlmodel import Session, select
from app.services.database import database_service
from app.models.organization import OrganizationUnit, TaskCapabilityMapping
from app.core.logging import logger


# Define capability mappings: category -> actions -> responsible unit
CAPABILITY_MAPPINGS = {
    "it": [
        {
            "action": "Настройка и администрирование AD/доменных служб",
            "keywords": ["ad", "домен", "учетка", "пользователь", "группа", "права доступа", "активный каталог"],
            "unit_external_id": "rosatom-it-l2",  # L2 support
            "priority": 8
        },
        {
            "action": "Настройка VPN и удаленного доступа",
            "keywords": ["vpn", "удаленный доступ", "подключение", "сертификат", "mfa"],
            "unit_external_id": "rosatom-it-net",  # Network engineers
            "priority": 9
        },
        {
            "action": "Ремонт и настройка рабочих станций",
            "keywords": ["компьютер", "ноутбук", "монитор", "клавиатура", "мышка", "не работает", "сломался"],
            "unit_external_id": "rosatom-it-l1",  # L1 support
            "priority": 7
        },
        {
            "action": "Установка и настройка ПО",
            "keywords": ["установить", "по", "программа", "приложение", "софт", "лицензия"],
            "unit_external_id": "rosatom-it-l1",
            "priority": 6
        },
        {
            "action": "Администрирование баз данных",
            "keywords": ["база данных", "бд", "sql", "oracle", "postgres", "mongodb"],
            "unit_external_id": "rosatom-it-dba",
            "priority": 9
        },
        {
            "action": "Мониторинг и метрики систем",
            "keywords": ["мониторинг", "метрики", "prometheus", "grafana", "zabbix", "алерт"],
            "unit_external_id": "rosatom-it-monitoring-head",
            "priority": 8
        },
    ],
    
    "hr": [
        {
            "action": "Оформление документов и справок",
            "keywords": ["справка", "2-ндфл", "182н", "трудовой договор", "копия", "дубликат"],
            "unit_external_id": "rosatom-hr-docs",
            "priority": 8
        },
        {
            "action": "Расчет и начисление зарплаты",
            "keywords": ["зарплата", "расчетный листок", "премия", "надбавка", "доплата", "начисление"],
            "unit_external_id": "rosatom-hr-payroll-head",
            "priority": 9
        },
        {
            "action": "Оформление отпусков",
            "keywords": ["отпуск", "отгул", "перенести отпуск", "согласовать отпуск"],
            "unit_external_id": "rosatom-hr-specialist",
            "priority": 7
        },
        {
            "action": "Личный кабинет сотрудника",
            "keywords": ["личный кабинет", "лк", "не отображается", "профиль"],
            "unit_external_id": "rosatom-hr-lk",
            "priority": 7
        },
        {
            "action": "Обучение и развитие",
            "keywords": ["обучение", "курс", "тренинг", "lms", "сертификат"],
            "unit_external_id": "rosatom-hr-lms",
            "priority": 6
        },
    ],
    
    "finance": [
        {
            "action": "Бухгалтерский учет и проводки",
            "keywords": ["1с", "бухгалтерия", "проводка", "счет", "документ", "не проводится"],
            "unit_external_id": "rosatom-acc-1c",
            "priority": 8
        },
        {
            "action": "Расчеты с контрагентами",
            "keywords": ["контрагент", "поставщик", "взаиморасчеты", "акт сверки", "задолженность"],
            "unit_external_id": "rosatom-acc-senior",
            "priority": 8
        },
        {
            "action": "Налоговая отчетность",
            "keywords": ["ндс", "налог", "декларация", "отчетность", "фнс"],
            "unit_external_id": "rosatom-acc-tax",
            "priority": 9
        },
        {
            "action": "Электронный документооборот",
            "keywords": ["эдо", "диадок", "сбис", "контур", "упд", "счет-фактура"],
            "unit_external_id": "rosatom-edo-operator",
            "priority": 7
        },
    ],
    
    "office": [
        {
            "action": "Ремонт и обслуживание офисных помещений",
            "keywords": ["лампочка", "починить", "сломалось", "не работает", "ремонт", "свет"],
            "unit_external_id": "rosatom-facility-tech",  # Facility technician
            "priority": 8
        },
        {
            "action": "Управление парковкой и пропусками",
            "keywords": ["парковка", "пропуск", "доступ", "карта", "турникет", "бейдж"],
            "unit_external_id": "rosatom-pass-operator",  # Pass office operator
            "priority": 7
        },
        {
            "action": "Бронирование и управление переговорками",
            "keywords": ["переговорка", "забронировать", "комната", "оборудование", "проектор"],
            "unit_external_id": "rosatom-meeting-lead",  # Meeting room coordinator
            "priority": 6
        },
        {
            "action": "Организация рабочих мест",
            "keywords": ["рабочее место", "стол", "стул", "организовать", "перенести"],
            "unit_external_id": "rosatom-workplace-lead",
            "priority": 7
        },
    ],
}


def load_capability_mappings():
    """Load capability mappings into database."""
    try:
        with Session(database_service.engine) as db:
            # Check if mappings already exist
            existing_count = len(db.exec(select(TaskCapabilityMapping)).all())
            
            if existing_count > 0:
                logger.info(f"Found {existing_count} existing capability mappings")
                response = input("Do you want to reload them? (y/n): ")
                if response.lower() != 'y':
                    logger.info("Skipping capability mappings load")
                    return
                
                # Delete existing mappings
                for mapping in db.exec(select(TaskCapabilityMapping)).all():
                    db.delete(mapping)
                db.commit()
                logger.info("Deleted existing mappings")
            
            total_created = 0
            
            for category, mappings in CAPABILITY_MAPPINGS.items():
                for mapping_data in mappings:
                    # Find the organization unit
                    unit = db.exec(
                        select(OrganizationUnit).where(
                            OrganizationUnit.external_id == mapping_data["unit_external_id"]
                        )
                    ).first()
                    
                    if not unit:
                        logger.warning(f"Unit not found: {mapping_data['unit_external_id']}")
                        continue
                    
                    # Create mapping
                    mapping = TaskCapabilityMapping(
                        category=category,
                        action_type=mapping_data["action"],
                        keywords=mapping_data["keywords"],
                        handled_by_unit_id=unit.id,
                        priority=mapping_data["priority"]
                    )
                    db.add(mapping)
                    total_created += 1
                    
                    logger.info(
                        f"Created mapping: {category} -> {mapping_data['action'][:50]} -> {unit.title}"
                    )
            
            db.commit()
            
            logger.info(f"✅ Successfully created {total_created} capability mappings")
            
            # Show summary by category
            for category in CAPABILITY_MAPPINGS.keys():
                count = len(db.exec(
                    select(TaskCapabilityMapping).where(TaskCapabilityMapping.category == category)
                ).all())
                logger.info(f"  - {category}: {count} mappings")
    
    except Exception as e:
        logger.error(f"❌ Error loading capability mappings: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  LOADING CAPABILITY MAPPINGS")
    print("="*70 + "\n")
    
    load_capability_mappings()
    
    print("\n" + "="*70)
    print("  ✅ DONE")
    print("="*70 + "\n")



