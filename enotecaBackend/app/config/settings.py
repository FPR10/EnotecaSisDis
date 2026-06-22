from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # --- App ---
    app_name: str = "Enoteca API"
    app_version: str = "1.0.0"
    debug: bool = False

    # --- Database (MySQL) ---
    database_url: str

    # --- Azure Entra External ID (autenticazione) ---
    # Trovati su: portale Azure → App registrations → la tua app
    azure_entra_tenant_id: str        # es. "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    azure_entra_client_id: str        # Application (client) ID della tua app registration
    azure_entra_admin_role: str = "Enoteca.Admin"  # nome dell'App Role per gli admin

    # --- Azure AI Vision (OCR etichette) ---
    azure_vision_endpoint: str = ""
    azure_vision_key: str = ""

    # --- Groq (AI generativa: abbinamenti cibo-vino) ---
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # --- Azure Blob Storage (immagini etichette + audit import massivo) ---
    azure_storage_connection_string: str = ""
    azure_storage_container_etichette: str = "etichette"
    azure_storage_container_audit: str = "import-audit"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
