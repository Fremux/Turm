#!/bin/bash
#
# Скрипт автоматической настройки и запуска проекта через Docker
# Использование: ./setup-docker.sh [environment]
# Где environment: development (по умолчанию), staging, или production
#

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода заголовков
print_header() {
    echo -e "\n${BLUE}===================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================${NC}\n"
}

# Функция для вывода успеха
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Функция для вывода предупреждения
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Функция для вывода ошибки
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Получить окружение из аргумента или использовать development
ENVIRONMENT=${1:-development}

# Проверка валидности окружения
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    print_error "Неверное окружение: $ENVIRONMENT"
    echo "Используйте: development, staging, или production"
    exit 1
fi

print_header "🚀 Настройка Support System - Окружение: $ENVIRONMENT"

# Шаг 1: Проверка зависимостей
print_header "Шаг 1: Проверка зависимостей"

if ! command -v docker &> /dev/null; then
    print_error "Docker не установлен. Установите Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
print_success "Docker найден: $(docker --version)"

if ! command -v docker compose &> /dev/null; then
    print_error "Docker Compose не установлен. Установите Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi
print_success "Docker Compose найден: $(docker compose version)"

# Шаг 2: Проверка файла окружения
print_header "Шаг 2: Проверка файла окружения"

ENV_FILE=".env.${ENVIRONMENT}"

if [ ! -f "$ENV_FILE" ]; then
    print_warning "Файл $ENV_FILE не найден. Создаём шаблон..."
    
    cat > "$ENV_FILE" << 'EOF'
# ============================================
# Application Settings
# ============================================
APP_ENV=ENVIRONMENT_PLACEHOLDER
DEBUG=true
PROJECT_NAME="Support System API"
VERSION="0.1.0"
ENVIRONMENT=ENVIRONMENT_PLACEHOLDER

# ============================================
# Database Configuration (PostgreSQL)
# ============================================
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=support_system
POSTGRES_USER=postgres
POSTGRES_PASSWORD=CHANGE_THIS_PASSWORD

# Alternative variable names (for compatibility)
DB_HOST=db
DB_PORT=5432
DB_NAME=support_system
DB_USER=postgres
DB_PASSWORD=CHANGE_THIS_PASSWORD

# ============================================
# Vector Database (Qdrant)
# ============================================
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=documents

# ============================================
# LLM Configuration
# ============================================
LLM_API_KEY=CHANGE_THIS_API_KEY
LLM_API_BASE=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# ============================================
# Embeddings Configuration
# ============================================
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_API_KEY=CHANGE_THIS_EMBEDDING_KEY

# ============================================
# Security
# ============================================
JWT_SECRET_KEY=CHANGE_THIS_SECRET_KEY
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# ============================================
# Rate Limiting
# ============================================
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# ============================================
# CORS
# ============================================
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000","http://localhost"]
EOF
    
    # Заменить плейсхолдеры
    sed -i "s/ENVIRONMENT_PLACEHOLDER/${ENVIRONMENT}/g" "$ENV_FILE"
    
    # Генерировать секретный ключ если доступен Python
    if command -v python3 &> /dev/null; then
        JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || echo "")
        if [ -n "$JWT_SECRET" ]; then
            sed -i "s/CHANGE_THIS_SECRET_KEY/${JWT_SECRET}/g" "$ENV_FILE"
            print_success "Сгенерирован JWT_SECRET_KEY"
        fi
    fi
    
    print_success "Создан файл $ENV_FILE"
    print_warning "⚠️  ВАЖНО: Отредактируйте $ENV_FILE и укажите:"
    echo "   - POSTGRES_PASSWORD (пароль базы данных)"
    echo "   - LLM_API_KEY (ключ OpenAI или другого LLM провайдера)"
    echo "   - EMBEDDING_API_KEY (ключ для embeddings)"
    echo ""
    read -p "Нажмите Enter после редактирования файла, или Ctrl+C для отмены..."
else
    print_success "Файл $ENV_FILE найден"
fi

# Проверка обязательных переменных
print_header "Шаг 3: Проверка обязательных переменных"

# Загрузить переменные из файла для проверки
source "$ENV_FILE"

MISSING_VARS=()

if [[ -z "$JWT_SECRET_KEY" ]] || [[ "$JWT_SECRET_KEY" == "CHANGE_THIS_SECRET_KEY" ]]; then
    MISSING_VARS+=("JWT_SECRET_KEY")
fi

if [[ -z "$LLM_API_KEY" ]] || [[ "$LLM_API_KEY" == "CHANGE_THIS_API_KEY" ]]; then
    MISSING_VARS+=("LLM_API_KEY")
fi

if [[ -z "$POSTGRES_PASSWORD" ]] || [[ "$POSTGRES_PASSWORD" == "CHANGE_THIS_PASSWORD" ]]; then
    MISSING_VARS+=("POSTGRES_PASSWORD")
fi

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    print_error "Следующие обязательные переменные не установлены в $ENV_FILE:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    echo ""
    print_warning "Отредактируйте $ENV_FILE и установите эти переменные"
    exit 1
fi

print_success "Все обязательные переменные установлены"

# Шаг 4: Остановка существующих контейнеров
print_header "Шаг 4: Остановка существующих контейнеров"

if docker compose ps --services 2>/dev/null | grep -q .; then
    print_warning "Остановка существующих контейнеров..."
    APP_ENV=$ENVIRONMENT docker compose --env-file "$ENV_FILE" down
    print_success "Существующие контейнеры остановлены"
else
    print_success "Нет запущенных контейнеров"
fi

# Шаг 5: Сборка и запуск контейнеров
print_header "Шаг 5: Сборка и запуск контейнеров"

print_warning "Это может занять несколько минут при первом запуске..."
APP_ENV=$ENVIRONMENT docker compose --env-file "$ENV_FILE" up -d --build

if [ $? -eq 0 ]; then
    print_success "Контейнеры успешно запущены"
else
    print_error "Ошибка при запуске контейнеров"
    exit 1
fi

# Шаг 6: Ожидание готовности сервисов
print_header "Шаг 6: Ожидание готовности сервисов"

print_warning "Ожидание запуска базы данных..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker exec ml-postgres pg_isready -U postgres > /dev/null 2>&1; then
        print_success "PostgreSQL готов"
        break
    fi
    attempt=$((attempt + 1))
    echo -n "."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    print_error "PostgreSQL не запустился вовремя"
    print_warning "Проверьте логи: docker compose logs db"
    exit 1
fi

print_warning "Ожидание запуска приложения..."
sleep 10

# Проверка health check
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Приложение готово"
        break
    fi
    attempt=$((attempt + 1))
    echo -n "."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    print_warning "Приложение не ответило на health check"
    print_warning "Это нормально при первом запуске. Проверьте логи: docker compose logs app"
fi

# Шаг 7: Проверка статуса
print_header "Шаг 7: Статус контейнеров"

docker compose ps

# Финальная информация
print_header "✅ Настройка завершена!"

echo -e "${GREEN}Сервисы доступны по следующим адресам:${NC}\n"
echo "  🌐 Web UI:             http://localhost"
echo "  📚 API Docs (Swagger): http://localhost:8000/docs"
echo "  📖 API Docs (ReDoc):   http://localhost:8000/redoc"
echo "  ❤️  Health Check:       http://localhost:8000/health"
echo "  🔍 Qdrant Dashboard:   http://localhost:6333/dashboard"
echo "  📊 Grafana:            http://localhost:3000 (admin/admin)"
echo "  📈 Prometheus:         http://localhost:9090"
echo "  🐳 cAdvisor:           http://localhost:8080"

echo -e "\n${YELLOW}Полезные команды:${NC}\n"
echo "  Просмотр логов:        make logs"
echo "  Логи приложения:       make logs-app"
echo "  Остановить:            make down"
echo "  Перезапустить:         make restart"
echo "  Shell в контейнере:    make shell"
echo "  PostgreSQL shell:      make db-shell"
echo "  Статус:                make status"
echo "  Все команды:           make help"

echo -e "\n${GREEN}Готово к использованию! 🚀${NC}\n"

