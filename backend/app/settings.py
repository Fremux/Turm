from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVER_ADDR: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    SERVER_TEST: bool = True
    SERVER_WORKERS: int = 1

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DB_ADDR: str = "db"
    DB_PORT: int = 5432

    


settings = Settings()
