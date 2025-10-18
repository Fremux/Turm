install:
	pip install uv
	uv sync

DOCKER_COMPOSE ?= docker compose

set-env:
	@if [ -z "$(ENV)" ]; then \
		echo "ENV is not set. Usage: make set-env ENV=development|staging|production"; \
		exit 1; \
	fi
	@if [ "$(ENV)" != "development" ] && [ "$(ENV)" != "staging" ] && [ "$(ENV)" != "production" ] && [ "$(ENV)" != "test" ]; then \
		echo "ENV is not valid. Must be one of: development, staging, production, test"; \
		exit 1; \
	fi
	@echo "Setting environment to $(ENV)"
	@bash -c "source scripts/set_env.sh $(ENV)"

prod:
	@echo "Starting server in production environment"
	@bash -c "source scripts/set_env.sh production && ./.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

staging:
	@echo "Starting server in staging environment"
	@bash -c "source scripts/set_env.sh staging && ./.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

dev:
	@echo "Starting server in development environment"
	@bash -c "source scripts/set_env.sh development && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

# Evaluation commands
eval:
	@echo "Running evaluation with interactive mode"
	@bash -c "source scripts/set_env.sh ${ENV:-development} && python -m evals.main --interactive"

eval-quick:
	@echo "Running evaluation with default settings"
	@bash -c "source scripts/set_env.sh ${ENV:-development} && python -m evals.main --quick"

eval-no-report:
	@echo "Running evaluation without generating report"
	@bash -c "source scripts/set_env.sh ${ENV:-development} && python -m evals.main --no-report"

# Streamlit UI commands
streamlit-dev:
	@echo "Starting Streamlit UI in development environment"
	@bash -c "source scripts/set_env.sh development && API_BASE_URL=http://localhost:8000 uv run streamlit run streamlit_app.py --server.port 8501"

streamlit-staging:
	@echo "Starting Streamlit UI in staging environment"
	@bash -c "source scripts/set_env.sh staging && API_BASE_URL=http://localhost:8000 uv run streamlit run streamlit_app.py --server.port 8501"

streamlit-prod:
	@echo "Starting Streamlit UI in production environment"
	@bash -c "source scripts/set_env.sh production && API_BASE_URL=http://localhost:8000 ./.venv/bin/streamlit run streamlit_app.py --server.port 8501"

lint:
	ruff check .

format:
	ruff format .

clean:
	rm -rf .venv
	rm -rf __pycache__
	rm -rf .pytest_cache

docker-build-env:
	@if [ -z "$(ENV)" ]; then \
		echo "ENV is not set. Usage: make docker-build-env ENV=development|staging|production"; \
		exit 1; \
	fi
	@if [ "$(ENV)" != "development" ] && [ "$(ENV)" != "staging" ] && [ "$(ENV)" != "production" ]; then \
		echo "ENV is not valid. Must be one of: development, staging, production"; \
		exit 1; \
	fi
	@./scripts/build-docker.sh $(ENV)

docker-run:
	@ENV_FILE=.env.development; \
	if [ ! -f $$ENV_FILE ]; then \
		echo "Environment file $$ENV_FILE not found. Please create it."; \
		exit 1; \
	fi; \
	APP_ENV=development $(DOCKER_COMPOSE) --env-file $$ENV_FILE up -d --build db app

docker-run-env:
	@if [ -z "$(ENV)" ]; then \
		echo "ENV is not set. Usage: make docker-run-env ENV=development|staging|production"; \
		exit 1; \
	fi
	@if [ "$(ENV)" != "development" ] && [ "$(ENV)" != "staging" ] && [ "$(ENV)" != "production" ]; then \
		echo "ENV is not valid. Must be one of: development, staging, production"; \
		exit 1; \
	fi
	@ENV_FILE=.env.$(ENV); \
	if [ ! -f $$ENV_FILE ]; then \
		echo "Environment file $$ENV_FILE not found. Please create it."; \
		exit 1; \
	fi; \
	APP_ENV=$(ENV) $(DOCKER_COMPOSE) --env-file $$ENV_FILE up -d --build db app
	# @./scripts/ensure-db-user.sh $(ENV)

docker-logs:
	@if [ -z "$(ENV)" ]; then \
		echo "ENV is not set. Usage: make docker-logs ENV=development|staging|production"; \
		exit 1; \
	fi
	@if [ "$(ENV)" != "development" ] && [ "$(ENV)" != "staging" ] && [ "$(ENV)" != "production" ]; then \
		echo "ENV is not valid. Must be one of: development, staging, production"; \
		exit 1; \
	fi
	@ENV_FILE=.env.$(ENV); \
	if [ ! -f $$ENV_FILE ]; then \
		echo "Environment file $$ENV_FILE not found. Please create it."; \
		exit 1; \
	fi; \
	APP_ENV=$(ENV) $(DOCKER_COMPOSE) --env-file $$ENV_FILE logs -f app db

docker-stop:
	@if [ -z "$(ENV)" ]; then \
		echo "ENV is not set. Usage: make docker-stop ENV=development|staging|production"; \
		exit 1; \
	fi
	@if [ "$(ENV)" != "development" ] && [ "$(ENV)" != "staging" ] && [ "$(ENV)" != "production" ]; then \
		echo "ENV is not valid. Must be one of: development, staging, production"; \
		exit 1; \
	fi
	@ENV_FILE=.env.$(ENV); \
	if [ ! -f $$ENV_FILE ]; then \
		echo "Environment file $$ENV_FILE not found. Please create it."; \
		exit 1; \
	fi; \
	APP_ENV=$(ENV) $(DOCKER_COMPOSE) --env-file $$ENV_FILE down

# Docker Compose commands for the entire stack
docker-compose-up:
	@if [ -z "$(ENV)" ]; then \
		echo "ENV is not set. Usage: make docker-compose-up ENV=development|staging|production"; \
		exit 1; \
	fi
	@if [ "$(ENV)" != "development" ] && [ "$(ENV)" != "staging" ] && [ "$(ENV)" != "production" ]; then \
		echo "ENV is not valid. Must be one of: development, staging, production"; \
		exit 1; \
	fi
	@ENV_FILE=.env.$(ENV); \
	if [ ! -f $$ENV_FILE ]; then \
		echo "Environment file $$ENV_FILE not found. Please create it."; \
		exit 1; \
	fi; \
	APP_ENV=$(ENV) $(DOCKER_COMPOSE) --env-file $$ENV_FILE up -d

docker-compose-down:
	@if [ -z "$(ENV)" ]; then \
		echo "ENV is not set. Usage: make docker-compose-down ENV=development|staging|production"; \
		exit 1; \
	fi
	@ENV_FILE=.env.$(ENV); \
	if [ ! -f $$ENV_FILE ]; then \
		echo "Environment file $$ENV_FILE not found. Please create it."; \
		exit 1; \
	fi; \
	APP_ENV=$(ENV) $(DOCKER_COMPOSE) --env-file $$ENV_FILE down

docker-compose-logs:
	@if [ -z "$(ENV)" ]; then \
		echo "ENV is not set. Usage: make docker-compose-logs ENV=development|staging|production"; \
		exit 1; \
	fi
	@ENV_FILE=.env.$(ENV); \
	if [ ! -f $$ENV_FILE ]; then \
		echo "Environment file $$ENV_FILE not found. Please create it."; \
		exit 1; \
	fi; \
	APP_ENV=$(ENV) $(DOCKER_COMPOSE) --env-file $$ENV_FILE logs -f

# Docker Compose shortcuts (no ENV needed)
up:
	@echo "Starting all services in development mode..."
	@APP_ENV=development $(DOCKER_COMPOSE) --env-file .env.development up -d --build

down:
	@echo "Stopping all services..."
	@APP_ENV=development $(DOCKER_COMPOSE) down

restart:
	@echo "Restarting all services..."
	@make down
	@make up

logs:
	@echo "Showing logs for all services..."
	@APP_ENV=development $(DOCKER_COMPOSE) logs -f

logs-app:
	@echo "Showing logs for app service..."
	@APP_ENV=development $(DOCKER_COMPOSE) logs -f app

logs-db:
	@echo "Showing logs for database..."
	@APP_ENV=development $(DOCKER_COMPOSE) logs -f db

status:
	@echo "Checking service status..."
	@APP_ENV=development $(DOCKER_COMPOSE) ps

shell:
	@echo "Opening shell in app container..."
	@docker exec -it ml-app /bin/bash

db-shell:
	@echo "Opening PostgreSQL shell..."
	@docker exec -it ml-postgres psql -U $$(grep POSTGRES_USER .env.development | cut -d '=' -f2) -d $$(grep POSTGRES_DB .env.development | cut -d '=' -f2)

migrate:
	@echo "Running migrations..."
	@docker exec -it ml-app /app/.venv/bin/python /app/migrations/create_categories_tables.py

clean-volumes:
	@echo "⚠️  WARNING: This will delete all data in volumes!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		APP_ENV=development $(DOCKER_COMPOSE) down -v; \
		echo "Volumes deleted."; \
	else \
		echo "Cancelled."; \
	fi

rebuild:
	@echo "Rebuilding app container..."
	@APP_ENV=development $(DOCKER_COMPOSE) up -d --build app

# Production shortcuts
up-prod:
	@echo "Starting all services in production mode..."
	@APP_ENV=production $(DOCKER_COMPOSE) --env-file .env.production up -d --build

down-prod:
	@echo "Stopping production services..."
	@APP_ENV=production $(DOCKER_COMPOSE) down

logs-prod:
	@echo "Showing production logs..."
	@APP_ENV=production $(DOCKER_COMPOSE) logs -f

# Help
help:
	@echo "════════════════════════════════════════════════════════════════════"
	@echo "                    ML API - Available Commands                     "
	@echo "════════════════════════════════════════════════════════════════════"
	@echo ""
	@echo "🚀 Quick Start (Docker Compose):"
	@echo "  make up              Start all services (PostgreSQL, Qdrant, API, Monitoring)"
	@echo "  make down            Stop all services"
	@echo "  make restart         Restart all services"
	@echo "  make logs            Show logs from all services"
	@echo "  make logs-app        Show logs from app only"
	@echo "  make logs-db         Show logs from database only"
	@echo "  make status          Check service status"
	@echo ""
	@echo "🛠️  Development:"
	@echo "  make install         Install dependencies locally (uv)"
	@echo "  make dev             Run server locally in development mode"
	@echo "  make shell           Open shell in app container"
	@echo "  make db-shell        Open PostgreSQL shell"
	@echo "  make migrate         Run database migrations"
	@echo "  make rebuild         Rebuild app container"
	@echo ""
	@echo "🗄️  Database & Data:"
	@echo "  make clean-volumes   Delete all Docker volumes (⚠️  deletes data!)"
	@echo ""
	@echo "🏭 Production:"
	@echo "  make up-prod         Start services in production mode"
	@echo "  make down-prod       Stop production services"
	@echo "  make logs-prod       Show production logs"
	@echo ""
	@echo "📊 Evaluation:"
	@echo "  make eval            Run evaluation with interactive mode"
	@echo "  make eval-quick      Run evaluation with default settings"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  make clean           Clean up local files"
	@echo ""
	@echo "════════════════════════════════════════════════════════════════════"
	@echo "📖 For detailed documentation, see DOCKER_README.md"
	@echo "════════════════════════════════════════════════════════════════════"