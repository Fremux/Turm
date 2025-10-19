"""Initialize database with organization structure and capability mappings."""

import sys
import time
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from sqlmodel import Session, select
from app.services.database import database_service
from app.models.organization import OrganizationUnit, TaskCapabilityMapping
from app.core.logging import logger
import json


def wait_for_db(max_retries=30, retry_interval=2):
    """Wait for database to be ready."""
    logger.info("Waiting for database to be ready...")
    
    for attempt in range(max_retries):
        try:
            with Session(database_service.engine) as db:
                # Try a simple query - this will fail if tables don't exist, which is ok
                from sqlalchemy import text
                db.exec(text("SELECT 1"))
            logger.info("✅ Database is ready!")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                logger.info(f"Database not ready yet (attempt {attempt + 1}/{max_retries}), waiting...")
                time.sleep(retry_interval)
            else:
                logger.error(f"❌ Database not ready after {max_retries} attempts: {e}")
                return False
    
    return False


def create_tables_if_not_exist():
    """Create organization tables if they don't exist."""
    try:
        with Session(database_service.engine) as db:
            from sqlalchemy import text
            
            # Check if organization_units table exists
            result = db.exec(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'organization_units'
            """)).first()
            
            table_count = result[0] if result else 0
            
            if table_count > 0:
                logger.info("✓ Organization tables already exist")
                return
            
            logger.info("Creating organization tables...")
            
            # Read SQL migration file
            sql_file = Path(__file__).parent / "migrate_organization_tasks.sql"
            if not sql_file.exists():
                logger.error(f"❌ SQL migration file not found: {sql_file}")
                return
            
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
        
        # Execute SQL using psycopg2 directly with autocommit
        import psycopg2
        from app.core.config import settings
        
        conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            database=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD
        )
        conn.autocommit = True
        
        try:
            with conn.cursor() as cursor:
                # Execute the entire SQL file
                cursor.execute(sql_content)
            
            logger.info("✅ Organization tables created successfully")
        finally:
            conn.close()
            
        # Give database a moment to process
        time.sleep(0.2)
    
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()


def load_organization_structure(json_path: str = "users.json"):
    """Load organization structure from JSON file."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            root_data = json.load(f)
        
        logger.info(f"Loaded organization structure from {json_path}")
        
        with Session(database_service.engine) as db:
            # Check if organization already exists
            existing = db.exec(select(OrganizationUnit)).first()
            
            if existing:
                logger.info("✓ Organization structure already loaded, skipping...")
                return
            
            logger.info("Loading organization structure...")
            
            # Load recursively
            _load_unit_recursive(root_data, None, 0, "", db)
            
            db.commit()
            
            total = len(db.exec(select(OrganizationUnit)).all())
            logger.info(f"✅ Loaded {total} organization units")
    
    except FileNotFoundError:
        logger.warning(f"⚠️ File not found: {json_path}, skipping organization load")
    except Exception as e:
        logger.error(f"❌ Error loading organization structure: {e}")


def _load_unit_recursive(unit_data, parent_id, level, parent_path, db):
    """Recursively load organization unit."""
    path = f"{parent_path} > {unit_data['title']}" if parent_path else unit_data['title']
    
    # Check if unit exists
    existing = db.exec(
        select(OrganizationUnit).where(OrganizationUnit.external_id == unit_data['id'])
    ).first()
    
    if existing:
        unit = existing
    else:
        unit = OrganizationUnit(
            external_id=unit_data['id'],
            title=unit_data['title'],
            position=unit_data.get('position'),
            unit_type=unit_data['unit_type'],
            description=unit_data.get('description'),
            parent_id=parent_id,
            level=level,
            path=path,
            capabilities={},
            is_active=True
        )
        db.add(unit)
        db.flush()
    
    # Process children
    for child_data in unit_data.get('children', []):
        _load_unit_recursive(child_data, unit.id, level + 1, path, db)
    
    return unit


def load_capability_mappings():
    """Load capability mappings."""
    
    # Define mappings
    CAPABILITY_MAPPINGS = {
        "it": [
            {
                "action": "Настройка и администрирование AD/доменных служб",
                "keywords": ["ad", "домен", "учетка", "пользователь", "группа", "права доступа", "активный каталог"],
                "unit_external_id": "rosatom-it-l2",
                "priority": 8
            },
            {
                "action": "Настройка VPN и удаленного доступа",
                "keywords": ["vpn", "удаленный доступ", "подключение", "сертификат", "mfa"],
                "unit_external_id": "rosatom-it-net",
                "priority": 9
            },
            {
                "action": "Ремонт и настройка рабочих станций",
                "keywords": ["компьютер", "ноутбук", "монитор", "клавиатура", "мышка", "не работает", "сломался"],
                "unit_external_id": "rosatom-it-l1",
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
                "unit_external_id": "rosatom-facility-tech",
                "priority": 8
            },
            {
                "action": "Управление парковкой и пропусками",
                "keywords": ["парковка", "пропуск", "доступ", "карта", "турникет", "бейдж"],
                "unit_external_id": "rosatom-pass-operator",
                "priority": 7
            },
            {
                "action": "Бронирование и управление переговорками",
                "keywords": ["переговорка", "забронировать", "комната", "оборудование", "проектор"],
                "unit_external_id": "rosatom-meeting-lead",
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
    
    try:
        with Session(database_service.engine) as db:
            # Check if mappings already exist
            existing = db.exec(select(TaskCapabilityMapping)).first()
            
            if existing:
                logger.info("✓ Capability mappings already loaded, skipping...")
                return
            
            logger.info("Loading capability mappings...")
            
            total_created = 0
            
            for category, mappings in CAPABILITY_MAPPINGS.items():
                for mapping_data in mappings:
                    # Find organization unit
                    unit = db.exec(
                        select(OrganizationUnit).where(
                            OrganizationUnit.external_id == mapping_data["unit_external_id"]
                        )
                    ).first()
                    
                    if not unit:
                        logger.warning(f"⚠️ Unit not found: {mapping_data['unit_external_id']}")
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
            
            db.commit()
            logger.info(f"✅ Loaded {total_created} capability mappings")
    
    except Exception as e:
        logger.error(f"❌ Error loading capability mappings: {e}")


def initialize_data():
    """Main initialization function."""
    logger.info("=" * 70)
    logger.info("  DATABASE INITIALIZATION")
    logger.info("=" * 70)
    
    # Wait for database
    if not wait_for_db():
        logger.error("❌ Database initialization failed: database not ready")
        sys.exit(1)
    
    # Create tables if they don't exist
    logger.info("")
    logger.info("Step 0/3: Creating tables if needed...")
    create_tables_if_not_exist()
    
    # Load organization structure
    logger.info("")
    logger.info("Step 1/3: Loading organization structure...")
    load_organization_structure()
    
    # Load capability mappings
    logger.info("")
    logger.info("Step 2/3: Loading capability mappings...")
    load_capability_mappings()
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("  ✅ INITIALIZATION COMPLETE")
    logger.info("=" * 70)


if __name__ == "__main__":
    try:
        initialize_data()
    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

