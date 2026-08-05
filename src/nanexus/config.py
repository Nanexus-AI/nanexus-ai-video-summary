from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://nanexus:nanexus@localhost:5432/nanexus"
    redis_url: str = "redis://localhost:6379/0"
    mqtt_host: str = "localhost"
    mqtt_port: int = 1884
    mqtt_topic: str = "frigate/events"
    frigate_base_url: str = "http://localhost:5000"
    frigate_token: str = ""
    embedding_dim: int = 512
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    ai_queue_key: str = "nanexus:ai:events"
    processed_set_key: str = "nanexus:ai:processed"
    # stub | openclip
    ai_mode: str = "openclip"
    ai_device: str = "auto"
    openclip_model: str = "ViT-B-32"
    openclip_pretrained: str = "openai"
    snapshots_dir: str = "data/snapshots"
    public_base_url: str = "http://127.0.0.1:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
