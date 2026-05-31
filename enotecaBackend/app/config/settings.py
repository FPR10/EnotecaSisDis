from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # --- App ---
    app_name: str = "Enoteca API"
    app_version: str = "1.0.0"
    debug: bool = False

    # --- Database (Azure PostgreSQL Flexible Server) ---
    database_url: str  # es. postgresql+asyncpg://user:pass@host:5432/enoteca

    # --- JWT Authentication ---
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24 ore

    # --- Azure AI Vision (OCR etichette) ---
    azure_vision_endpoint: str = ""
    azure_vision_key: str = ""

    # --- Azure OpenAI (abbinamenti cibo-vino, descrizioni) ---
    azure_openai_endpoint: str = ""
    azure_openai_key: str = ""
    azure_openai_deployment: str = "gpt-4o"

    # --- Azure Blob Storage (immagini etichette) ---
    azure_storage_connection_string: str = ""
    azure_storage_container: str = "etichette"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Restituisce un'istanza singleton di Settings.
    Il decoratore lru_cache garantisce che il .env venga letto una sola volta.
    """
    return Settings()
