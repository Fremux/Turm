#!/bin/bash
set -e

# Print initial environment values (before loading .env)
echo "Starting with these environment variables:"
echo "APP_ENV: ${APP_ENV:-development}"
echo "Initial Database Host: $( [[ -n ${POSTGRES_HOST:-${DB_HOST:-}} ]] && echo 'set' || echo 'Not set' )"
echo "Initial Database Port: $( [[ -n ${POSTGRES_PORT:-${DB_PORT:-}} ]] && echo 'set' || echo 'Not set' )"
echo "Initial Database Name: $( [[ -n ${POSTGRES_DB:-${DB_NAME:-}} ]] && echo 'set' || echo 'Not set' )"
echo "Initial Database User: $( [[ -n ${POSTGRES_USER:-${DB_USER:-}} ]] && echo 'set' || echo 'Not set' )"

# Load environment variables from the appropriate .env file
if [ -f ".env.${APP_ENV}" ]; then
    echo "Loading environment from .env.${APP_ENV}"
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip comments and empty lines
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "$line" ]] && continue

        # Extract the key
        key=$(echo "$line" | cut -d '=' -f 1)

        # Only set if not already set in environment
        if [[ -z "${!key}" ]]; then
            export "$line"
        else
            echo "Keeping existing value for $key"
        fi
    done <".env.${APP_ENV}"
elif [ -f ".env" ]; then
    echo "Loading environment from .env"
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip comments and empty lines
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "$line" ]] && continue

        # Extract the key
        key=$(echo "$line" | cut -d '=' -f 1)

        # Only set if not already set in environment
        if [[ -z "${!key}" ]]; then
            export "$line"
        else
            echo "Keeping existing value for $key"
        fi
    done <".env"
else
    echo "Warning: No .env file found. Using system environment variables."
fi

# Check required sensitive environment variables
required_vars=("JWT_SECRET_KEY" "LLM_API_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        missing_vars+=("$var")
    fi
done

if [[ ${#missing_vars[@]} -gt 0 ]]; then
    echo "ERROR: The following required environment variables are missing:"
    for var in "${missing_vars[@]}"; do
        echo "  - $var"
    done
    echo "Please provide these variables through environment or .env files."
    exit 1
fi

# Print final environment info
echo -e "\nFinal environment configuration:"
echo "Environment: ${APP_ENV:-development}"

echo "Database Host: $( [[ -n ${POSTGRES_HOST:-${DB_HOST:-}} ]] && echo 'set' || echo 'Not set' )"
echo "Database Port: $( [[ -n ${POSTGRES_PORT:-${DB_PORT:-}} ]] && echo 'set' || echo 'Not set' )"
echo "Database Name: $( [[ -n ${POSTGRES_DB:-${DB_NAME:-}} ]] && echo 'set' || echo 'Not set' )"
echo "Database User: $( [[ -n ${POSTGRES_USER:-${DB_USER:-}} ]] && echo 'set' || echo 'Not set' )"

echo "LLM Model: ${LLM_MODEL:-Not set}"
echo "Debug Mode: ${DEBUG:-false}"

# Wait for database to be ready
echo "Waiting for database to be ready..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if /app/.venv/bin/python -c "import psycopg2; psycopg2.connect(host='${POSTGRES_HOST}', port='${POSTGRES_PORT}', dbname='${POSTGRES_DB}', user='${POSTGRES_USER}', password='${POSTGRES_PASSWORD}')" 2>/dev/null; then
        echo "Database is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo "Attempt $attempt/$max_attempts: Database not ready yet, waiting..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "ERROR: Database failed to become ready after $max_attempts attempts"
    exit 1
fi

# Run database migrations
echo "Running database migrations..."
if [ -f "/app/migrations/create_categories_tables.py" ]; then
    /app/.venv/bin/python /app/migrations/create_categories_tables.py || {
        echo "Warning: Categories migration failed, continuing anyway..."
    }
fi

if [ -f "/app/migrations/create_agents_tables.py" ]; then
    /app/.venv/bin/python /app/migrations/create_agents_tables.py || {
        echo "Warning: Agents migration failed, continuing anyway..."
    }
fi

if [ -f "/app/migrations/add_embedding_settings_to_categories.py" ]; then
    /app/.venv/bin/python /app/migrations/add_embedding_settings_to_categories.py || {
        echo "Warning: Embedding settings migration failed, continuing anyway..."
    }
fi

if [ -f "/app/migrations/create_tasks_table.py" ]; then
    /app/.venv/bin/python /app/migrations/create_tasks_table.py || {
        echo "Warning: Tasks table migration failed, continuing anyway..."
    }
fi

# Initialize default categories if they don't exist
echo "Initializing default categories..."
if [ -f "/app/app/scripts/init_default_data.py" ]; then
    /app/.venv/bin/python /app/app/scripts/init_default_data.py || {
        echo "Warning: Default categories initialization failed, continuing anyway..."
    }
fi

echo "Starting application..."
# Execute the CMD
exec "$@"
