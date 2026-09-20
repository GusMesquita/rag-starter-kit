from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    chroma_path: str = "./chroma_data"
    collection_name: str = "documents"
    top_k: int = 4

    # Comma-separated list of accepted API keys (X-API-Key header). Empty
    # disables auth — dev only, never leave unset in production.
    api_keys: str = ""

    @property
    def api_key_set(self) -> set[str]:
        return {key.strip() for key in self.api_keys.split(",") if key.strip()}


settings = Settings()
