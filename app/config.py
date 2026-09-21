from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    chroma_path: str = "./chroma_data"
    collection_name: str = "documents"
    top_k: int = 4

    # Default seguro: o app assume produção e só afrouxa quando alguém
    # declara ENVIRONMENT=dev explicitamente. Esquecer a variável não pode
    # resultar num serviço aberto.
    environment: Literal["dev", "prod"] = "prod"

    # Comma-separated list of accepted API keys (X-API-Key header). Empty
    # disables auth — dev only, never leave unset in production.
    api_keys: str = ""

    # Origens permitidas no CORS, separadas por vírgula. Vazio = nenhuma.
    cors_origins: str = ""

    rate_limit_per_minute: int = 60

    # Teto do corpo do /ingest. Chunking + embedding de um documento gigante
    # segura um worker por minutos e enche o disco do Chroma.
    max_ingest_bytes: int = 1_000_000

    @property
    def api_key_set(self) -> set[str]:
        return {key.strip() for key in self.api_keys.split(",") if key.strip()}

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
